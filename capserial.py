import serial
import serial.tools.list_ports as list_ports
import threading
import time
import kivy.properties
from kivy.event import EventDispatcher
import struct
from kivy.clock import Clock
from functools import partial

PACKET_HEADER = 0xA0
PACKET_TAIL = 0xC0
SENSOR_CHECK_PACKET_ID = 0x00
SAMPLE_RATE_PACKET_ID = 0x01
MAN_ID_PACKET_ID = 0x02
DEV_ID_PACKET_ID = 0x03
CH_SETTINGS_PACKET_ID = 0x04

class ChannelSettings(object):
    def __init__(self, channel=1):
        self.channel = channel
        self.offset = 0
        self.gain = 0
        self.capdac = 0
        self.pos = 0
        self.neg = 0

    def set_channel(self, channel):
        self.channel = channel
    
    def set_offset(self, offset):
        self.offset = offset

    def set_pos_input(self, pos):
        self.pos = channel
    
    def set_neg_input(self, neg):
        self.neg = neg
    
    def set_capdac(self, capdac):
        self.capdac = capdac
    

class CapSerial(EventDispatcher):
    connected = kivy.properties.NumericProperty(defaultvalue=0)
    message_string = kivy.properties.StringProperty('')
    sensor_is_present = kivy.properties.BooleanProperty(False)
    manufacturer_id = kivy.properties.NumericProperty(0xFFFF)
    device_id = kivy.properties.NumericProperty(0xFFFF)
    sample_rate = kivy.properties.NumericProperty(0xFF)

    def __init__(self):
        '''
        '''
        self.port = ''
        self.baudrate = 9600
        
        self.SAMPLE_RATE_DICT = {
            '100 Hz': 1,
            '200 Hz': 2,
            '400 Hz': 3
        }
        self.read_packets = False
        self.bind(connected=self.connected_callback)
        self.bind(sensor_is_present=self.sensor_is_present_callback)
        self.ch_settings = []
        for i in range(4):
            self.ch_settings.append(ChannelSettings())
        
        find_port_thread = threading.Thread(target=self.find_port, daemon=True)
        find_port_thread.start()
        
    
    def connected_callback(self, instance, value):
        '''
        '''
        if (value == 2):
            while(self.serial.inWaiting() > 0):
                self.serial.read()
            self.message_string = 'Started thread for reading incoming data'
            self.read_packets = True
            read_packet_thread = threading.Thread(target=self.read_packet, daemon=True)
            read_packet_thread.start()
            time.sleep(2)
            self.message_string = 'Starting retrieving sensor configuration...'
            self.serial.write('t'.encode('utf-8'))

    def find_port(self):
        capsense_found = False
        while (not capsense_found):
            ports = list_ports.comports()
            for port in ports:
                capsense_found = self.check_capsense(port.device)
                if (capsense_found):
                    self.port = port.device
                    self.connect()
                    break

    def check_capsense(self, portname):
        self.message_string = 'Checking: {}'.format(portname)
        try:
            port = serial.Serial(port=portname, baudrate=self.baudrate)
            if (port.is_open):
                port.write('v'.encode('utf-8'))
                time.sleep(2)
                received_string = ''
                while (port.in_waiting > 0):
                    received_string += port.read().decode('utf-8', errors='replace')
                if ('$$$' in received_string):
                    self.message_string = 'Device found on port: {}'.format(portname)
                    self.connected = 1
                    return True
        except serial.SerialException:
            return False
        except ValueError:
            return False
        return False
    
    def connect(self):
        try:
            self.message_string = 'Connecting to port: {}'.format(self.port)
            self.serial = serial.Serial(port=self.port, baudrate=self.baudrate, write_timeout=0, timeout=2)
            if (self.serial.is_open):
                self.message_string = 'Successfully connected to port: {}'.format(self.port)
                self.connected = 2
                return 0
        except serial.SerialException:
            self.message_string = 'Could not connect to port: {}'.format(portname)
            return 2
        except ValueError:
            self.message_string = 'Could not connect to port: {}'.format(portname)
            return 1

    def send_channel_settings(self):
        pass

    def send_sample_rate(self, value):
        sample_rate_val = self.SAMPLE_RATE_DICT[value]
        packet = self.create_sample_rate_packet(sample_rate_val)
        self.serial.write(packet)
        Clock.schedule_once(lambda dt: self.serial.write('u'.encode('utf-8')))

    def create_sample_rate_packet(self, value):
        packet = [0,0,0,0]
        packet[0] = PACKET_HEADER
        packet[1] = SAMPLE_RATE_PACKET_ID
        packet[2] = value
        packet[3] = PACKET_TAIL
        return packet

    def read_serial_data(self, n=1):
        return self.serial.read(n)

    def read_packet(self):
        self.state = 0
        while(self.read_packets):
            if (self.serial.inWaiting() > 0):
                data_read = self.read_serial_data(1)
                if (self.state == 0):
                    if(struct.unpack('B', data_read)[0] == PACKET_HEADER):
                        self.state = 1
                elif (self.state == 1):
                    unpacked_value = struct.unpack('B', data_read)[0]
                    print(unpacked_value)
                    error = False
                    if unpacked_value == SAMPLE_RATE_PACKET_ID:
                        error = self.handle_sample_rate_packet()
                    elif unpacked_value == SENSOR_CHECK_PACKET_ID:
                        error = self.handle_sensor_check_packet()
                    elif unpacked_value == MAN_ID_PACKET_ID:
                        error = self.handle_man_id_packet()
                    elif unpacked_value == DEV_ID_PACKET_ID:
                        error = self.handle_device_id_packet()
                    elif unpacked_value == CH_SETTINGS_PACKET_ID:
                        error = self.handle_ch_settings_packet()
                    self.state = 2
                elif (self.state == 2):
                    if(struct.unpack('B', data_read)[0] == 0xC0):
                        self.state = 0

    def handle_ch_settings_packet(self):
        data_read = self.read_serial_data(1)
        ch_num = struct.unpack('B', data_read)[0]
        self.ch_settings[ch_num].channel = ch_num >> 5
        self.ch_settings[ch_num].capdac = ch_num & 0xF
        data_read = self.read_serial_data(1)

        offset = self.read_serial_data(2)
        offset = struct.unpack('2B', offset)
        print(offset)
        offset = offset[0] << 8 | offset[1]
        self.ch_settings[ch_num].offset = (int)(offset / (1<<11))
        print(self.ch_settings[ch_num].offset)
        gain = self.read_serial_data(2)
        gain = struct.unpack('2B', gain)
        print(gain)
        gain = gain[0] << 8 | gain[1]
        print(gain)
        self.ch_settings[ch_num].gain = (int)(gain / (1<<14))
        print(self.ch_settings[ch_num].gain)

    def handle_sensor_check_packet(self):
        data_read = self.read_serial_data(1)
        data_read = struct.unpack('B', data_read)[0]
        if (data_read == 1):
            self.sensor_is_present = True
            self.message_string = 'Sensor found on I2C bus'
        else:
            self.sensor_is_present = False
            self.message_string = 'Sensor not found on I2C bus'
        return False
    
    def handle_man_id_packet(self):
        if (self.serial.in_waiting < 2):
            return True
        else:
            data_read = self.read_serial_data(2)
            data_read = struct.unpack('2B', data_read)
            self.manufacturer_id = data_read[0] << 8 | data_read[1]
            self.message_string = 'Manufacturer ID retrieved'
            return False
    
    def handle_device_id_packet(self):
        if (self.serial.in_waiting < 2):
            return True
        else:
            data_read = self.read_serial_data(2)
            data_read = struct.unpack('2B', data_read)
            self.device_id = data_read[0] << 8 | data_read[1]
            self.message_string = 'Device ID retrieved'
        return False

    def handle_sample_rate_packet(self):
        print('Sample rate packet')
        if (self.serial.in_waiting < 1):
            return True
        else:
            data_read = self.read_serial_data(1)
            data_read = struct.unpack('B', data_read)[0]
            print(data_read)
            self.sample_rate = data_read
            self.message_string = 'Sample rate retrieved: {}'.format(self.sample_rate)
        return False

    def sensor_is_present_callback(self, instance, value):
        '''
        @brief Callback for property #sensor_is_present

        This callback is called when the value of the property
        #sensor_is_present changes. This occurs during the initial
        configuration of the sensor. If it is found that the sensor
        is connected on the I2C bus, then we start retrieving its
        settings.
        '''
        if (value == True):
            # call my_callback in 5 seconds
            Clock.schedule_once(self.send_manufacturer_id_command, 1)
            Clock.schedule_once(self.send_device_id_command, 3)
            Clock.schedule_once(self.send_sample_rate_command, 5)
            Clock.schedule_once(partial(self.send_channel_settings, 1), 7)
            Clock.schedule_once(partial(self.send_channel_settings, 2), 9)
            Clock.schedule_once(partial(self.send_channel_settings, 3), 11)
            Clock.schedule_once(partial(self.send_channel_settings, 4), 13)
            
    def send_channel_settings(self, value, *largs):
        self.message_string = 'Retrieving channel settings for channel {}'.format(value)
        if (value == 1):
            self.serial.write('g'.encode('utf-8'))
        elif(value == 2):
            self.serial.write('h'.encode('utf-8'))
        elif(value == 3):
            self.serial.write('j'.encode('utf-8'))
        elif(value == 4):
            self.serial.write('i'.encode('utf-8'))
        
    
    def send_manufacturer_id_command(self, dt):
        self.message_string = 'Retrieving manufacturer ID..'
        self.serial.write('m'.encode('utf-8'))

    def send_device_id_command(self, dt):
        self.message_string = 'Retrieving device ID..'
        self.serial.write('d'.encode('utf-8'))
    
    def send_sample_rate_command(self, dt):
        self.message_string = 'Retrieving sample rate..'
        self.serial.write('u'.encode('utf-8'))