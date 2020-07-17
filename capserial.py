import serial
import serial.tools.list_ports as list_ports
import threading
import time
import kivy.properties
from kivy.event import EventDispatcher
import struct

class CapSerial(EventDispatcher):
    connected = kivy.properties.NumericProperty(defaultvalue=0)
    message_string = kivy.properties.StringProperty('')
    sensor_is_present = kivy.properties.BooleanProperty(False)

    def __init__(self):
        '''
        '''
        self.port = ''
        self.baudrate = 9600
        find_port_thread = threading.Thread(target=self.find_port, daemon=True)
        find_port_thread.start()
        self.sample_rate_dict = {
            '100 Hz': 1,
            '200 Hz': 2,
            '400 Hz': 3
        }
        self.packet_header = 0xA0
        self.packet_tail = 0xC0
        self.sensor_check_packet = 0x00
        self.sample_rate_packet = 0x01
        #self.channel_settings_packet = 0x01
        self.read_packets = False
        self.bind(connected=self.connected_callback)
    
    def connected_callback(self, instance, value):
        # Start reading packet thread
        
        if (value == 2):
            while(self.serial.inWaiting() > 0):
                self.serial.read()
            read_packet_thread = threading.Thread(target=self.read_packet, daemon=True)
            read_packet_thread.start()
            self.read_packets = True
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
                self.serial.write('t'.encode('utf-8'))
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
        sample_rate_val = self.sample_rate_dict[value]
        packet = self.create_sample_rate_packet(sample_rate_val)
        for by in packet:
            self.serial.write(by.encode('utf-8'))

    def create_sample_rate_packet(self, value):
        packet = []
        packet[0] = self.packet_header
        packet[1] = self.sample_rate_packet
        packet[2] = value
        packet[3] = self.packet_taila

    def read_serial_data(self, n=1):
        return self.serial.read(n)

    def read_packet(self):
        self.serial.write('t'.encode('utf-8'))
        self.state = 0
        while(self.read_packets):
            if (self.serial.inWaiting() > 0):
                data_read = self.read_serial_data(1)
                #print(int(data_read))
                if (self.state == 0):
                    if(struct.unpack('B', data_read)[0] == 0xA0):
                        print(struct.unpack('B', data_read)[0])
                        self.state = 1
                elif (self.state == 1):
                    unpacked_value = struct.unpack('B', data_read)[0]
                    if unpacked_value == self.sample_rate_packet:
                        pass
                    elif unpacked_value == self.sensor_check_packet:
                        error = self.handle_sensor_check_packet()
                    if (not error):
                        self.state = 2
                    else:
                        self.state = 0
                elif (self.state == 2 and data_read == 0xC0):
                    self.state = 0

    def handle_sensor_check_packet(self):
        data_read = self.read_serial_data(1)
        data_read = struct.unpack('B', data_read)[0]
        if (data_read == 1):
            self.sensor_is_present = True
        else:
            self.sensor_is_present = False

