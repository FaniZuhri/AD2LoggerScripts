"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2018-07-19

   Requires:                       
       Python 3.11
"""

from ctypes import *
from SDK.dwfconstants import *
from datetime import datetime
import math
import time
import sys
import csv
import pytz
# import matplotlib.pyplot as plt
# import numpy

level_trigger_choosed = 0
last_state = 0

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

print("####################### Log Data with Edge Trigger Type #####################")

try:
    level_trigger_choosed = float(input("Insert the desired trigger level in Volt (float number):  "))

except ValueError:
    print("Invalid Value, Exit")
    sys.exit(1)

try:
    slopetype = int(input("Insert the desired slope type: \n \
                          0 - Rising Event \n \
                          1 - Falling Event \n \
                          2 - Either \n \
                          Value Choosed (0-2):  "))
except ValueError:
    print("Invalid Value, Exit")
    sys.exit(1)

if slopetype > 2 or slopetype < 0:
    print("Invalid Value, Exit")
    sys.exit(1)



level_trigger_choosed = round(level_trigger_choosed, 2)

print("Trigger level selcted: " + str(level_trigger_choosed) + "V")

hdwf = c_int()
sts = c_byte()
secLog = .01 # logging rate in seconds
nSamples = 10
rgdSamples = (c_double*nSamples)()
cValid = c_int(0)

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

print("Opening first device")
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))
# 2nd configuration for Analog Discovery with 16k analog-in buffer
#dwf.FDwfDeviceConfigOpen(c_int(-1), c_int(1), byref(hdwf)) 

def power_off_device():
    # close the file
    f.close()
    print("Log saved with name " + file_name + " at ./data folder")
    dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_bool(False))
    dwf.FDwfDeviceCloseAll()

def start_logging():
    data_array = []
    meas_time = datetime.now(tz_JKT).strftime("%y/%m/%d %H:%M:%S")
    data_array.append(f"{meas_time}")
    
    dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
    dwf.FDwfAnalogInStatusSamplesValid(hdwf, byref(cValid))
    
    for channel in range(2):
        dwf.FDwfAnalogInStatusData(hdwf, channel, byref(rgdSamples), nSamples) # get value each channel
        
        dc = sum(rgdSamples)/len(rgdSamples)
        dc = round(dc, 2)

        print("Acq ch" + str(channel) + " at "+str(meas_time)+" average: "+ str(dc) +"V")
        # break
        data_array.append(f"{dc}")

    writer.writerow(data_array)

if hdwf.value == hdwfNone.value:
    szError = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szError)
    print("failed to open device\n"+str(szError.value))
    quit()

'''
print("Generating square wave...")
#                                    AWG 1     carrier
dwf.FDwfAnalogOutNodeEnableSet(hdwf, c_int(0), c_int(0), c_bool(True))
dwf.FDwfAnalogOutNodeFunctionSet(hdwf, c_int(0), c_int(0), funcSquare)
dwf.FDwfAnalogOutNodeFrequencySet(hdwf, c_int(0), c_int(0), c_double(10))
dwf.FDwfAnalogOutNodeOffsetSet(hdwf, c_int(0), c_int(0), c_double(1.0))
dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, c_int(0), c_int(0), c_double(1.0))
dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_bool(True))
'''

#set up acquisition
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(nSamples/secLog))
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(nSamples))

#channel 0
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(5))
dwf.FDwfAnalogInChannelAttenuationSet(hdwf, c_int(0), c_double(10))

#channel 1
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(1), c_bool(True))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(1), c_double(5))
dwf.FDwfAnalogInChannelAttenuationSet(hdwf, c_int(1), c_double(10))

######## Use the Analog In Trigger #################
dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcDetectorAnalogIn) #one of the analog in channels

########### or use trigger from other instruments or external trigger #############
#dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcExternal1) 

#set up tridwfgger
dwf.FDwfAnalogInTriggerAutoTimeoutSet(hdwf, c_double(0)) #disable auto trigger
dwf.FDwfAnalogInTriggerTypeSet(hdwf, trigtypeEdge)
dwf.FDwfAnalogInTriggerChannelSet(hdwf, c_int(0)) # first channel

dwf.FDwfAnalogInTriggerLevelSet(hdwf, c_double(level_trigger_choosed))
dwf.FDwfAnalogInTriggerConditionSet(hdwf, c_int(slopetype))
# dwf.FDwfAnalogInTriggerConditionSet(hdwf, DwfTriggerSlopeEither) 

tz_JKT = pytz.timezone('Asia/Jakarta')

init_time = datetime.now(tz_JKT)

file_name = str(datetime.now(tz_JKT))[:19] + " batt_log.csv"

# open the file in the write mode
print("creating file...")
f = open('./data/' + (file_name).replace(":", "_"), 'w', newline='')

print("file created with name " + file_name + " at ./data folder")
# create the csv writer
writer = csv.writer(f)

# wait at least 2 seconds with Analog Discovery for the offset to stabilize, before the first reading after device open or offset/range change
time.sleep(2)

print("Starting repeated acquisitions")
dwf.FDwfAnalogInConfigure(hdwf, c_bool(False), c_bool(True))

# new acquisition is started automatically after done state
while True:
    try:
        while True:
            dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))

            if sts.value == DwfStateDone.value:
                # dwf.FDwfAnalogInTriggerAutoTimeoutSet(hdwf, c_double(0.001))
                # dwf.FDwfAnalogInAcquisitionModeSet(hdwf, c_int(1)) #acqmodeScanShift
                break
            # continue
            time.sleep(0.001)
        
        start_logging()
        

    except KeyboardInterrupt:
        break
        # pass

    except dwfercInvalidParameter0:
        break
        # pass

power_off_device()


