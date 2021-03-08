# PolarBand2lsl
 Send PolarBand H10 Data to an LSL

# Manual:
Install [Python](https://www.anaconda.com/) if you haven't yet

then open an anaconda prompt, and do a 
'''
pip install pylsl --user
pip install bleak --user
'''
and then change to the dir with this code.
Change the MAC address in the code to the MAC address of your band first.

do a 

''' python
python Polar2LSL
'''
to get the stream running.

You can record the stream with [Labrecorder](https://github.com/labstreaminglayer/App-LabRecorder/releases)

a sample script for peak detection is also provided. Based on [Matlab Documentation](https://nl.mathworks.com/help/wavelet/ug/r-wave-detection-in-the-ecg.html])


# Stolen from:
[Pareeknikhil](https://towardsdatascience.com/creating-a-data-stream-with-polar-device-a5c93c9ccc59)
