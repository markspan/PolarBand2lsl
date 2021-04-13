# PolarBand2lsl
Send PolarBand H10 Data to an [LSL](https://github.com/sccn/labstreaminglayer) stream.

# Manual:
Install [Python](https://www.anaconda.com/) if you haven't yet

then open an anaconda prompt, and do a 

```
pip install pylsl --user
pip install bleak --user
```

to install [pylsl](https://pypi.org/project/pylsl/) and [bleak](https://bleak.readthedocs.io/en/latest/) into python.

as **bleak** is used for the bluetooth LE communication, this *should* work on PC, MAC and Linux. 

and then change to the dir with this code.
Change the MAC address in the code to the MAC address of your band first.

do a 

``` 
python Polar2LSL
```

to get the stream running.

You can record the stream with [Labrecorder](https://github.com/labstreaminglayer/App-LabRecorder/releases)

A sample script for peak detection is also provided. Based on [Matlab Documentation](https://nl.mathworks.com/help/wavelet/ug/r-wave-detection-in-the-ecg.html]).
This script uses the xdf import module of LabStreamingLayer (https://github.com/xdf-modules/xdf-Matlab), and the 'findpeaks' function from the MATLAB Signal Processing Toolbox

Also a ibi detection function based on the ibi interpolation created by A.R.van Roon for CARSPAN is provided

![Screenshot 2021-02-25 115853](https://user-images.githubusercontent.com/4105112/110318793-40345100-800e-11eb-9f86-872d7848a1ac.png)
# Stolen from:
[Pareeknikhil](https://towardsdatascience.com/creating-a-data-stream-with-polar-device-a5c93c9ccc59)
