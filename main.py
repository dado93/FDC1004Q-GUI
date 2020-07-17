from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
import capserial
from kivy.properties import ObjectProperty

Builder.load_file('toolbar.kv')

class BottomBar(Label):

    def update_text(self, instance, value):
        self.text = value

class CapSenseContainer(BoxLayout):
    toolbar = ObjectProperty(None)
    bottom_bar = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.serial = capserial.CapSerial()
        super().__init__(**kwargs)
    
    def on_toolbar(self, instance, value):
        self.toolbar.set_serial(self.serial)
    
    def on_bottom_bar(self, instance, value):
        self.serial.bind(message_string=self.bottom_bar.update_text)


class CapSenseApp(App):
    def build(self):
        return CapSenseContainer()

if __name__ == "__main__":
    CapSense = CapSenseApp().run()
    
