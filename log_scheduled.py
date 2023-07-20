'''

Welcome to GDB Online.
GDB online is an online compiler and debugger tool for C, C++, Python, Java, PHP, Ruby, Perl,
C#, VB, Swift, Pascal, Fortran, Haskell, Objective-C, Assembly, HTML, CSS, JS, SQLite, Prolog.
Code, Compile, Run and Debug online from anywhere in world.

'''
from ctypes import *
import math
from datetime import datetime
import time
import pytz
import matplotlib.pyplot as plt
import sys
import csv

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")
    
hdwf = c_int()
sts = c_byte()
secLog = .001 # logging rate in seconds
nSamples = 10
rgdSamples = (c_double*nSamples)()
cValid = c_int(0)

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

print("Opening first device")
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

if hdwf.value == 0:
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    print("failed to open device")
    quit()

print("Data logging in progress...")

#set up acquisition
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(5))
dwf.FDwfAnalogInAcquisitionModeSet(hdwf, c_int(1)) #acqmodeScanShift
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(nSamples/secLog))
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(nSamples))

#wait at least 2 seconds for the offset to stabilize
time.sleep(1)

#begin acquisition
dwf.FDwfAnalogInConfigure(hdwf, c_int(0), c_int(1))

tz_JKT = pytz.timezone('Asia/Jakarta')

try:
    # TODO: write code...
    while True:
        
        init_time = datetime.now(tz_JKT)
        # print(str(init_time) + "\n")
        
        time.sleep(1)
        
        if datetime.now().minute == 14 or datetime.now().minute == 29 or datetime.now().minute == 44 or datetime.now().minute == 59:
            
            # open the file in the write mode
            f = open('./data/' + (str(datetime.now(tz_JKT))[:19] + ' batt_log' + '.csv').replace(":", "_"), 'w', newline='')

            # create the csv writer
            writer = csv.writer(f)
            
            print("Start logging at " + str(datetime.now(tz_JKT).time())[:8])
            
            data_index = 0
            
            while True:
                data_array = []
                
                data_index += 1
                data_array.append(f"{data_index}")
                
                current_time = datetime.now(tz_JKT)
                # print(str(current_time) + "\n")
                
                time_delta = current_time - init_time
                duration_in_s = time_delta.total_seconds()
            
                time.sleep(secLog)
                
                dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
                dwf.FDwfAnalogInStatusSamplesValid(hdwf, byref(cValid))
                
                for iChannel in range(2):
                    dwf.FDwfAnalogInStatusData(hdwf, c_int(iChannel), byref(rgdSamples), cValid) # get channel 1 data
                    
                    dc = 0
                    
                    for i in range(nSamples):
                        dc += rgdSamples[i]
                    
                    dc /= nSamples
                    
                    dcrms = 0
                    acrms = 0
                    
                    for i in range(nSamples):
                        dcrms += rgdSamples[i] ** 2
                        acrms += (rgdSamples[i]-dc) ** 2
                    
                    dcrms /= nSamples
                    dcrms = math.sqrt(dcrms)
                    
                    acrms /= nSamples
                    acrms = math.sqrt(acrms)
                    
                    # print(f"CH:{iChannel+1} DC:{dc:.3f}V DCRMS:{dcrms:.3f}V ACRMS:{acrms:.3f}V")
                    
                    # dc = dc * 10
                    
                    data_array.append(f"{dc:.3f}")
                    
                # write a row to the csv file
                writer.writerow(data_array)
            
                if duration_in_s > 300:
                    print("Log saved at " + str(datetime.now(tz_JKT).time())[:8])                    
                    
                    # close the file
                    f.close()
                    
                    break
    
except KeyboardInterrupt:
    pass

dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_bool(False))
dwf.FDwfDeviceCloseAll()

print("end")
