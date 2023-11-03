import os
os.environ["KIVY_NO_CONSOLELOG"] = "1"
os.environ["BLEAK_LOGGING"] = "0"

from pylsl import StreamInfo, StreamOutlet
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from kivy.uix.scrollview import ScrollView
from kivy.clock import mainthread
import logging 
import asyncio
import threading
import bleak

from bleak.uuids import uuid16_dict


# Predefined UUID (Universal Unique Identifier) mapping based on the Heart Rate GATT service protocol
uuid16_dict = {v: k for k, v in uuid16_dict.items()}

# UUIDs
PMD_CONTROL = "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8"
PMD_DATA = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"
ECG_WRITE = bytearray([0x02, 0x00, 0x00, 0x01, 0x82,
                      0x00, 0x01, 0x01, 0x0E, 0x00])


ECG_SAMPLING_FREQ = 130

bleak_logger = logging.getLogger("bleak")
bleak_logger.setLevel(10000)

class BluetoothApp(App):
    # Build the GUI
    busychars = ["o...", ".o..", "..o.", "...o"]
    def build(self):
        #if sys.platform=="win32":
        #    import ctypes
        #    ctypes.windll.user32.ShowWindow( ctypes.windll.kernel32.GetConsoleWindow(), 0 )
        Window.size = (400, 200)

        self.devices_layout = BoxLayout(orientation='vertical')
        self.devices_scrollview = ScrollView()
        self.devices_scrollview.add_widget(self.devices_layout)

        self.scan_button = Button(text="Scan for Devices", size_hint=(1, 0.1))
        self.scan_button.bind(on_press=self.scan_for_devices)

        self.cancel_button = Button(text="Cancel", size_hint=(1, 0.1))
        self.cancel_button.bind(on_press=self.stop_scanning)
        
        self.root_layout = BoxLayout(orientation='vertical')
        self.root_layout.add_widget(self.scan_button)
        self.root_layout.add_widget(self.devices_scrollview)
        self.root_layout.add_widget(self.cancel_button)

        return self.root_layout

    def scan_for_devices(self, instance):
        # callback for the scanner: clean the interface
        self.scan_button.disabled = True
        self.devices_layout.clear_widgets()
        threading.Thread(target=self.scan).start()

    def scan(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.async_scan())
        self.scan_button.disabled = False

    async def async_scan(self):
        # scan devices and add the Polars to the interface
        try:
            devices = await bleak.BleakScanner.discover(
                return_adv=True, cb=dict(use_bdaddr=False), scanning_mode='active'
            )
            for d, a in devices.values():
                if "Polar H10" in str(d):
                    self.add_device_button(d, a)
            self.add_busy_label()
        except Exception as e:
            print(f"Error during scanning: {e}")

    @mainthread
    def add_device_button(self, d, a):
        device_button = Button(text=d.name, size_hint=(1, 0.2))
        device_button.bind(on_press=lambda instance, addr=d.address,
                           nm=d.name: self.connect_to_device(addr, nm, instance))
        self.devices_layout.add_widget(device_button)

    @mainthread
    def add_busy_label(self):
        self.busyLabel = Label(text = "", valign = 'middle')
        self.devices_layout.add_widget(self.busyLabel )
        self.busyvalue = 0;
    
    @mainthread
    def update_busy(self):
        self.busyvalue = self.busyvalue+1
        if self.busyvalue == 4:
            self.busyvalue = 0
        self.busyLabel.text = self.busychars[self.busyvalue]	        
        
    def connect_to_device(self, device_address, name, instance):
        # callback for the individual Polar buttons.
        self.OUTLET = self.start_stream(name)
        self.busyLabel.text = "Wait... (Upto a minute...)"
        instance.disabled = True
        threading.Thread(target=self.connect, args=(device_address,)).start()

    def connect(self, address):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.async_connect(address))

    async def async_connect(self, address):
        async with bleak.BleakClient(address) as client:
            await client.read_gatt_char(PMD_CONTROL)
            await client.write_gatt_char(PMD_CONTROL, ECG_WRITE)
            await client.start_notify(PMD_DATA, self.data_conv)
            # print("Collecting ECG data...", flush=True)
            for i in range(10000):
                await asyncio.sleep(1)

    def data_conv(self, sender, data: bytearray):
        if data[0] == 0x00:
            #print(".", end='', flush=True)
            self.update_busy()
            step = 3
            samples = data[10:]
            offset = 0
            while offset < len(samples):
                ecg = self.convert_array_to_signed_int(samples, offset, step)
                offset += step
                self.OUTLET.push_sample([ecg])

    def convert_array_to_signed_int(self, data, offset, length):
        return int.from_bytes(bytearray(data[offset: offset + length]), byteorder="little", signed=True)

    def stop_scanning(self, instance):
        self.loop.stop()
        App.get_running_app().stop()

    def start_stream(self, stream_name):
        info = StreamInfo(stream_name, 'ECG', 1,
                          ECG_SAMPLING_FREQ, 'float32', 'myuid2424')
        info.desc().append_child_value("manufacturer", "Polar")
        channels = info.desc().append_child("channels")

        for c in ["ECG"]:
            channels.append_child("channel") \
                    .append_child_value("name", c) \
                    .append_child_value("unit", "microvolts") \
                    .append_child_value("type", "ECG")

        return StreamOutlet(info, 74, 360)


if __name__ == "__main__":
    BluetoothApp().run()
