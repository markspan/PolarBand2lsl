import asyncio
import aioconsole

import os
import signal
import sys
import getopt

from pylsl import StreamInfo, StreamOutlet

from bleak import BleakClient
from bleak.uuids import uuid16_dict

# Predefined UUID (Universal Unique Identifier) mapping based on the Heart Rate GATT service protocol
uuid16_dict = {v: k for k, v in uuid16_dict.items()}

# UUIDs
MODEL_NBR_UUID = f"0000{uuid16_dict.get('Model Number String'):x}-0000-1000-8000-00805f9b34fb"
MANUFACTURER_NAME_UUID = f"0000{uuid16_dict.get('Manufacturer Name String'):x}-0000-1000-8000-00805f9b34fb"
BATTERY_LEVEL_UUID = f"0000{uuid16_dict.get('Battery Level'):x}-0000-1000-8000-00805f9b34fb"
PMD_SERVICE = "FB005C80-02E7-F387-1CAD-8ACD2D8DF0C8"
PMD_CONTROL = "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8"
PMD_DATA = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"
ECG_WRITE = bytearray([0x02, 0x00, 0x00, 0x01, 0x82, 0x00, 0x01, 0x01, 0x0E, 0x00])
ECG_SAMPLING_FREQ = 130
OUTLET = []

def start_stream(stream_name):
    info = StreamInfo(stream_name, 'ECG', 1, ECG_SAMPLING_FREQ, 'float32', 'myuid2424')
    info.desc().append_child_value("manufacturer", "Polar")
    channels = info.desc().append_child("channels")
    
    for c in ["ECG"]:
        channels.append_child("channel") \
                .append_child_value("name", c) \
                .append_child_value("unit", "microvolts") \
                .append_child_value("type", "ECG")

    return StreamOutlet(info, 74, 360)

def data_conv(sender, data: bytearray):
    if data[0] == 0x00:
        print(".", end='', flush=True)
        step = 3
        samples = data[10:]
        offset = 0
        while offset < len(samples):
            ecg = convert_array_to_signed_int(samples, offset, step)
            offset += step
            OUTLET.push_sample([ecg])

def convert_array_to_signed_int(data, offset, length):
    return int.from_bytes(bytearray(data[offset : offset + length]), byteorder="little", signed=True)

def convert_to_unsigned_long(data, offset, length):
    return int.from_bytes(bytearray(data[offset : offset + length]), byteorder="little", signed=False)

async def run(client, debug=False):
    try:
        print("---------Looking for Device------------ ", flush=True)
        await client.connect()
        print("---------Device connected--------------", flush=True)
        model_number = await client.read_gatt_char(MODEL_NBR_UUID)
        print("Model Number: {0}".format("".join(map(chr, model_number))), flush=True)
        manufacturer_name = await client.read_gatt_char(MANUFACTURER_NAME_UUID)
        print("Manufacturer Name: {0}".format("".join(map(chr, manufacturer_name))), flush=True)
        battery_level = await client.read_gatt_char(BATTERY_LEVEL_UUID)
        print("Battery Level: {0}%".format(int(battery_level[0])), flush=True)
        await client.read_gatt_char(PMD_CONTROL)
        print("Collecting GATT data...", flush=True)
        await client.write_gatt_char(PMD_CONTROL, ECG_WRITE)
        print("Writing GATT data...", flush=True)
        await client.start_notify(PMD_DATA, data_conv)
        print("Collecting ECG data...", flush=True)
        await aioconsole.ainput('Running: Press a key to quit')
        await client.stop_notify(PMD_DATA)
        print("Stopping ECG data...", flush=True)
        print("[CLOSED] application closed.", flush=True)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

async def main(address, outlet):
    try:
        async with BleakClient(address) as client:
            tasks = [asyncio.ensure_future(run(client, True))]
            await asyncio.gather(*tasks)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    os.environ["PYTHONASYNCIODEBUG"] = str(0)
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ha:s:", ["ADDRESS=", "STREAMNAME="])
    except getopt.GetoptError:
        print('Polar2LSL.py -a <MACADDRESS> -s <STREAMNAME>', flush=True)
        sys.exit(2)

    STREAMNAME = 'PolarBand'
    ADDRESS = "ec:b0:5b:7b:94:93"
    
    for opt, arg in opts:
        if opt == '-h':
            print('Polar2LSL.py -a <MACADDRESS> -s <STREAMNAME>', flush=True)
            sys.exit()
        elif opt in ("-a", "--ADDRESS"):
            ADDRESS = arg
        elif opt in ("-s", "--STREAMNAME"):
            STREAMNAME = arg
            
    print('MACADDRESS is ', ADDRESS, flush=True)
    print('STREAMNAME is ', STREAMNAME, flush=True)
    OUTLET = start_stream(STREAMNAME)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(ADDRESS, OUTLET))