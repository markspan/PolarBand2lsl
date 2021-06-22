# PolarBand2lsl
Send PolarBand H10 Data to an [LSL](https://github.com/sccn/labstreaminglayer) stream.

# Manual:
Install [Python](https://www.anaconda.com/) if you haven't yet

then open an anaconda prompt, and do a 

```
pip install pylsl --user
pip install bleak --user
pip install aioconsole --user
```

to install [pylsl](https://pypi.org/project/pylsl/), [aioconsole](https://github.com/vxgmichel/aioconsole) and [bleak](https://bleak.readthedocs.io/en/latest/) into python.

as **bleak** is used for the bluetooth LE communication, this *should* work on PC, MAC and Linux. 

and then change to the directory where you saved the code (i.e., Polarband2lsl.py).
Change the MAC address in the code to the MAC address of your band first. The MAC address can be found on Windows 10 under Control Panel\Hardware and Sound\Devices and Printers. There you should be able to see the polar device, and its properties will show a 'Unique identifier' (under 'connected device'). This is the MAC address.

The MAC address should be put in the code around line 152. You can also mention the MAC address on the command line by starting the program like this:


``` 
python Polar2LSL -a MACADRESS -s STREAMNAME
```

to get the stream with the name "STREAMNAME" running using the H10 with MAC address "MACADRESS". The defaults are used when you start the stream by typing:

``` 
python Polar2LSL
```
Defaults are "C9:09:F1:4C:AA:4D" for the MAC adress (my band) ans "Polarband" for the STREAMNAME.

You can record the stream with [Labrecorder](https://github.com/labstreaminglayer/App-LabRecorder/releases)

A sample script for peak detection is also provided. Based on [Matlab Documentation](https://nl.mathworks.com/help/wavelet/ug/r-wave-detection-in-the-ecg.html]).
This script uses the xdf import module of LabStreamingLayer (https://github.com/xdf-modules/xdf-Matlab), and the 'findpeaks' function from the MATLAB Signal Processing Toolbox

Also a ibi detection function based on the ibi interpolation created by A.R.van Roon for CARSPAN is provided

![Screenshot 2021-02-25 115853](https://user-images.githubusercontent.com/4105112/110318793-40345100-800e-11eb-9f86-872d7848a1ac.png)
# Stolen from:
[Pareeknikhil](https://towardsdatascience.com/creating-a-data-stream-with-polar-device-a5c93c9ccc59)
