from pylsl import StreamInfo, StreamOutlet, local_clock
import asyncio
import math
import os
import signal
import sys
import time
import sys, getopt

import pandas as pd
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

startTime = -1
ecg_session_data = []

exitPressed = False
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
    outlet = StreamOutlet(info, 74, 360)



## Keyboard Interrupt Handler
def keyboardInterrupt_handler(signum, frame):
    print("  key board interrupt received...")
    print("----------------Recording stopped------------------------")
    print(signum,frame)


## Bit conversion of the Hexadecimal stream
def data_conv(sender, data: bytearray):
    global startTime, outlet
    if data[0] == 0x00:
        print(".", end = '', flush=True)
        #if startTime == -1:
        #    startTime = convert_to_unsigned_long(data, 1, 8) / 1000000.0
        #timeStamp = (convert_to_unsigned_long(data, 1, 8) / 1000000.0) - startTime
        step = 3
        samples = data[10:]
        offset = 0
        while offset < len(samples):
            #odata =[0,0]
            ecg = convert_array_to_signed_int(samples, offset, step)
            offset += step
            #odata[0] = ecg
            #odata[1] = timeStamp
            #ecg_session_data.extend([odata])
            outlet.push_sample([ecg])
            

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

    ## Writing characteristic description to control point for request of UUID (defined above) ##

    await client.is_connected()
    print("---------Device connected--------------")

    model_number = await client.read_gatt_char(MODEL_NBR_UUID)
    print("Model Number: {0}".format("".join(map(chr, model_number))))

    manufacturer_name = await client.read_gatt_char(MANUFACTURER_NAME_UUID)
    print("Manufacturer Name: {0}".format("".join(map(chr, manufacturer_name))))

    battery_level = await client.read_gatt_char(BATTERY_LEVEL_UUID)
    print("Battery Level: {0}%".format(int(battery_level[0])))

    att_read = await client.read_gatt_char(PMD_CONTROL)

    await client.write_gatt_char(PMD_CONTROL, ECG_WRITE)

    ## ECG stream started
    await client.start_notify(PMD_DATA, data_conv)

    print("Collecting ECG data...")

    ## Collecting ECG data for 1 minute/ 60 seconds
    await asyncio.sleep(40000)

    ## Writing the collected data into a  CSV file on local system ##
    #df_ecg = pd.DataFrame(ecg_session_data)
    #df_ecg.to_csv("df_ecg_polar.csv")

    ## Stop the stream once data is collected
    await client.stop_notify(PMD_DATA)
    print("Stopping ECG data...")
    print("[CLOSED] application closed.")

    sys.exit(0)


async def main(argv):

    try:
        async with BleakClient(ADDRESS) as client:
            signal.signal(signal.SIGINT, keyboardInterrupt_handler)
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

    StartStream(STREAMNAME)
    os.environ["PYTHONASYNCIODEBUG"] = str(1)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(sys.argv[1:]))
