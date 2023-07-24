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
from termcolor import colored

########################## VAR DECLARATIONS ############################

last_state = 0
dio_used = 0
pin_masking_bit = 1
is_triggered = 0
dwRead = c_uint32()
hdwf = c_int()
sts = c_byte()
secLog = .01 # logging rate in seconds
nSamples = 10
rgdSamples = (c_double*nSamples)()
cValid = c_int(0)

########################################################################


################# ANALOG DISCOVERY INITIALIZATION ####################

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

print("####################### Log Data with DIO Trigger #####################")


version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

print("Opening first device")
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))
# 2nd configuration for Analog Discovery with 16k analog-in buffer
#dwf.FDwfDeviceConfigOpen(c_int(-1), c_int(1), byref(hdwf))

if hdwf.value == hdwfNone.value:
    szError = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szError);
    print("failed to open device\n"+str(szError.value))
    quit()

########################################################################
 
################# GET THE TRIGGER TYPE ############################# 
try:
    dio_used = int(input("Select DIO pin used (0-7):  "))

except ValueError:
    print("Invalid Value, Exit")
    sys.exit(1)

if dio_used > 7 or dio_used < 0:
    print("Invalid Value, Exit")
    sys.exit(1)

pin_masking_bit = pin_masking_bit << dio_used

try:
    slopetype = int(input("Insert the desired DIO trigger type: \n \
                          0 - Rising Event \n \
                          1 - Falling Event \n \
                          Value Choosed (0-1):  "))
except ValueError:
    print("Invalid Value, Exit")
    sys.exit(1)

if slopetype > 1 or slopetype < 0:
    print("Invalid Value, Exit")
    sys.exit(1)

print(colored("DIO pin " + str(dio_used) + " is selected with " + \
      ("falling" if slopetype == 1 else "rising") + " event.", \
        "green", "on_white"))

#####################################################################

########################## DWF CONFIG ###############################

#set up acquisition
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(nSamples/secLog))
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(nSamples))
dwf.FDwfAnalogInAcquisitionModeSet(hdwf, c_int(1)) #acqmodeScanShift

#channel 0
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(5))
dwf.FDwfAnalogInChannelAttenuationSet(hdwf, c_int(0), c_double(10))

#channel 1
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(1), c_bool(True))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(1), c_double(5))
dwf.FDwfAnalogInChannelAttenuationSet(hdwf, c_int(1), c_double(10))

######################################################################


############################# FILE CONFIG ##############################

tz_JKT = pytz.timezone('Asia/Jakarta')

init_time = datetime.now(tz_JKT)

file_name = str(init_time)[:19] + " batt_log.csv"

# open the file in the write mode
print("creating file...")
f = open('./data/' + (file_name).replace(":", "_"), 'w', newline='')

print(colored("file created with name " + file_name + " at ./data folder", "green", "on_white"))
# create the csv writer
writer = csv.writer(f)

#######################################################################

def power_off_device():
    # close the file
    f.close()
    print(colored("Log saved with name " + file_name + " at ./data folder", "green", "on_white"))
    dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_bool(False))
    dwf.FDwfDeviceCloseAll()

def start_logging():
    data_array = []
    meas_time = datetime.now(tz_JKT).strftime("%H:%M:%S")
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
    time.sleep(0.5)

# wait at least 2 seconds with Analog Discovery for the offset to stabilize, before the first reading after device open or offset/range change
time.sleep(2)

print("Starting repeated acquisitions")
dwf.FDwfAnalogInConfigure(hdwf, c_bool(False), c_bool(True))

# enable output/mask on 8 LSB IO pins, from DIO 0 to 7
dwf.FDwfDigitalIOOutputEnableSet(hdwf, c_int(pin_masking_bit))

while True:
    try:
        while True:
            # fetch digital IO information from the device 
            dwf.FDwfDigitalIOStatus(hdwf) 

            # read state of all pins, regardless of output enable
            dwf.FDwfDigitalIOInputStatus(hdwf, byref(dwRead))

            if slopetype == 0: # rising event

                # start logging if pin input is high
                if dwRead.value & pin_masking_bit == 1:
                    break

            else: # falling event
                
                # start logging if pin input is low
                if dwRead.value & pin_masking_bit == 0:
                    break

        start_logging()
        
    except KeyboardInterrupt:
        break

    except dwfercInvalidParameter0:
        break

power_off_device()


