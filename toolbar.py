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
            self.color = (0,0,0,1)

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
        print('change color')
        if (value== True):
            self.set_background_color(0,0.5,0,1.0)
            self.text = 'Sensor Found'
            self.color = (0,0,0,1)
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
    sample_rate_spinner = ObjectProperty(None)
    channel_configuration = ObjectProperty(None)

    def sample_rate_change(self):
        print('Sample rate change: {}'.format(self.sample_rate_spinner.text))

    def set_serial(self, serial):
        self.serial = serial
        self.serial.bind(connected=self.device_label.change_color)
        self.serial.bind(connected=self.enable_widgets)
        self.serial.bind(sensor_is_present=self.sensor_label.change_color)
    
    def enable_widgets(self, instance, value):
        if (value == 0 or value == 1):
            self.sensor_label.disabled = True
            self.sample_rate.disabled = True
            self.channel_configuration.disabled = True
        if (value == 2):
            self.sensor_label.disabled = False
            self.sample_rate.disabled = False
            self.channel_configuration.disabled = False
        