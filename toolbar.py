from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
import re
from kivy.properties import ObjectProperty, NumericProperty
import capserial
from kivy.event import EventDispatcher

class DeviceLabel(Label):

    def change_color(self, instance, value):
        if (value== 1):
            self.set_background_color(1,1,0,1.0)
            self.text = 'Device found'
            self.color = (0,0,0,1)
        elif (value == 2):
            self.set_background_color(0,.5,0,1)
            self.text = 'Device connected'
            self.color = (1,1,1,1)

    def set_background_color(self, r, g, b, a):   
        self.canvas.before.clear()
        with self.canvas.before:
            Color(r, g, b, a)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect,
                  size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class SensorLabel(Label):

    def change_color(self, instance, value):
        if (value== True):
            self.set_background_color(0,0.5,0,1.0)
            self.text = 'Sensor Found'
            self.color = (1,1,1,1)
        elif (value == False):
            self.set_background_color(0.8,0.2,0.2,1)
            self.text = 'Sensor Not Found'
            self.color = (1,1,1,1)

    def set_background_color(self, r, g, b, a):   
        self.canvas.before.clear()
        with self.canvas.before:
            Color(r, g, b, a)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect,
                  size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class ManufacturerIdLabel(SensorLabel):

    def change_color(self, instance, value):
        if (value == 0x5449):
            self.color = (1,1,1,1)
            self.set_background_color(0,0.5,0,1.0)
            self.text = 'Man Id: 0x{:04X}'.format(value)
            
        elif (value == 0xFFFF):
            self.set_background_color(0.8,0.2,0.2,1)
            self.text = 'Man Id: Err'
            self.color = (1,1,1,1)
    
class DeviceIdLabel(SensorLabel):

    def change_color(self, instance, value):
        if (value == 0x1004):
            self.set_background_color(0,0.5,0,1.0)
            self.text = 'Dev Id: 0x{:04X}'.format(value)
            self.color = (1.,1.,1.,1)
        elif (value == 0xFFFF):
            self.set_background_color(0.8,0.2,0.2,1)
            self.text = 'Dev Id: Err'
            self.color = (1,1,1,1)

class FloatInput(TextInput):

    pat = re.compile('[^0-9]')
    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        return super(FloatInput, self).insert_text(s, from_undo=from_undo)

class ToolBar(BoxLayout):
    device_label = ObjectProperty(None)
    sensor_label = ObjectProperty(None)
    manufacturer_id_label = ObjectProperty(None)
    device_id_label = ObjectProperty(None)
    sample_rate_spinner = ObjectProperty(None)
    channel_configuration = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sample_rate_updated_first = False

    def sample_rate_updated(self, instance, value):
        for key in self.serial.SAMPLE_RATE_DICT.keys():
            if (value == self.serial.SAMPLE_RATE_DICT[key]):
                self.sample_rate_spinner.text = key
                break

    def sample_rate_change(self):
        if (not(self.sample_rate_updated_first)):
            print('Sample rate change: {}'.format(self.sample_rate_spinner.text))
            self.serial.send_sample_rate(self.sample_rate_spinner.text)

    def set_serial(self, serial):
        self.serial = serial
        self.serial.bind(connected=self.device_label.change_color)
        self.serial.bind(sensor_is_present=self.enable_widgets)
        self.serial.bind(sensor_is_present=self.sensor_label.change_color)
        self.serial.bind(manufacturer_id=self.manufacturer_id_label.change_color)
        self.serial.bind(device_id=self.device_id_label.change_color)
        self.serial.bind(sample_rate=self.sample_rate_updated)
    
    def enable_widgets(self, instance, sensor_is_present):
        if (sensor_is_present == False):
            self.sensor_label.disabled = True
            self.sample_rate.disabled = True
            self.channel_configuration.disabled = True
        else:
            self.sensor_label.disabled = False
            self.sample_rate.disabled = False
            self.channel_configuration.disabled = False
        