from pylsl import StreamInfo, StreamOutlet
import asyncio
import aioconsole 
import os
import signal
import sys
import getopt

from bleak import BleakClient
from bleak.uuids import uuid16_dict


""" Predefined UUID (Universal Unique Identifier) mapping are based on Heart Rate GATT service Protocol that most
Fitness/Heart Rate device manufacturer follow (Polar H10 in this case) to obtain a specific response input from 
the device acting as an API """

uuid16_dict = {v: k for k, v in uuid16_dict.items()}

## UUID for model number ##
MODEL_NBR_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
    uuid16_dict.get("Model Number String")
)


## UUID for manufacturer name ##
MANUFACTURER_NAME_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
    uuid16_dict.get("Manufacturer Name String")
)

## UUID for battery level ##
BATTERY_LEVEL_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
    uuid16_dict.get("Battery Level")
)

## UUID for connection establishment with device ##
PMD_SERVICE = "FB005C80-02E7-F387-1CAD-8ACD2D8DF0C8"

## UUID for Request of stream settings ##
PMD_CONTROL = "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8"

## UUID for Request of start stream ##
PMD_DATA = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"

## UUID for Request of ECG Stream ##
ECG_WRITE = bytearray([0x02, 0x00, 0x00, 0x01, 0x82, 0x00, 0x01, 0x01, 0x0E, 0x00])

## For Polar H10  sampling frequency ##
ECG_SAMPLING_FREQ = 130

OUTLET = []


def StartStream(STREAMNAME):

    info = StreamInfo(STREAMNAME, 'ECG', 1,ECG_SAMPLING_FREQ, 'float32', 'myuid2424')

    info.desc().append_child_value("manufacturer", "Polar")
    channels = info.desc().append_child("channels")
    for c in ["ECG"]:
        channels.append_child("channel")\
            .append_child_value("name", c)\
            .append_child_value("unit", "microvolts")\
            .append_child_value("type", "ECG")
    
    # next make an outlet; we set the transmission chunk size to 74 samples and
    # the outgoing buffer size to 360 seconds (max.)
    return StreamOutlet(info, 74, 360)



## Bit conversion of the Hexadecimal stream
def data_conv(sender, data: bytearray):
    #global OUTLET
    if data[0] == 0x00:
        print(".", end = '', flush=True)
        step = 3
        samples = data[10:]
        offset = 0
        while offset < len(samples):
            ecg = convert_array_to_signed_int(samples, offset, step)
            offset += step
            OUTLET.push_sample([ecg])
            

def convert_array_to_signed_int(data, offset, length):
    return int.from_bytes(
        bytearray(data[offset : offset + length]), byteorder="little", signed=True,
    )


def convert_to_unsigned_long(data, offset, length):
    return int.from_bytes(
        bytearray(data[offset : offset + length]), byteorder="little", signed=False,
    )


## ASynchronous task to start the data stream for ECG ##
async def run(client, debug=False):

    print("---------Looking for Device------------ ", flush=True)

    await client.is_connected()
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

    ## ECG stream started
    await client.start_notify(PMD_DATA, data_conv)

    print("Collecting ECG data...", flush=True)

    await aioconsole.ainput('Running: Press a key to quit')
    await client.stop_notify(PMD_DATA)
    print("Stopping ECG data...", flush=True)
    print("[CLOSED] application closed.", flush=True)
    sys.exit(0)


async def main(ADDRESS, OUTLET):
    try:
        async with BleakClient(ADDRESS) as client:
            tasks = [
                asyncio.ensure_future(run(client, True)),
            ]

            await asyncio.gather(*tasks)
    except:
        pass


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:],"ha:s:",["ADDRESS=","STREAMNAME="])
    except getopt.GetoptError:
        print ('Polar2LSL.py -a <MACADDRESS> -s <STREAMNAME>', flush=True)
        sys.exit(2)
    # Defaults:
    STREAMNAME = 'PolarBand'
    ADDRESS = "C7:4C:DA:51:37:51"
    #ADDRESS = "C9:09:F1:4C:AA:4D"
    
    for opt, arg in opts:
        if opt == '-h':
            print ('Polar2LSL.py -a <MACADDRESS> -s <STREAMNAME>', flush=True)
            sys.exit()
        elif opt in ("-a", "--ADDRESS"):
            ADDRESS = arg
        elif opt in ("-s", "--STREAMNAME"):
            STREAMNAME = arg
            
    print ('MACADDRESS is ', ADDRESS, flush=True)
    print ('STREAMNAME is ', STREAMNAME, flush=True)

    OUTLET = StartStream(STREAMNAME)
    
    os.environ["PYTHONASYNCIODEBUG"] = str(1)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(ADDRESS, OUTLET))
