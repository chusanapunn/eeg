import mne
import pandas as pd
import sys
import matplotlib.pyplot as plt
import datetime
import win32com.client
import numpy as np
import math
from scipy.fft import fft

# interval= [[123,31424]]
# x=np.multiply(interval,256)
# print(x)
# ---------------------------------------
# num = 12
# digit = int(math.floor(math.log10(num)))
# print(digit)
# rounding_factor = 10 ** digit  # 1000
# rounded_num = math.ceil(num / rounding_factor) * rounding_factor
# print(rounded_num)
# ---------------------------------------
raw = mne.io.read_raw_edf("data/Subject15_11_4_2022/Subject15_11_4_2022 01.001.01  EO.edf")
# # raw.plot(block=True)


# SAMPLING_FREQUENCY   = raw.info['sfreq']
CROP_LENGTH = 10 # seconds
# CROP
data, times = raw[:, 0:(CROP_LENGTH * raw.info['sfreq'])]
print(data[1][:])
fftdata = fft(data[1][:])
print(fftdata.shape)

# # # FULL LENGTH
# data, times = raw[:, :]

# # print(data.shape)
# # print(times.shape)

# RAW_LENGTH = times.shape[0]/SAMPLING_FREQUENCY # seconds

# # print("Raw Length in Seconds : ",RAW_LENGTH) # datapoint/ sampling freq 
# # print(times.shape[0]/raw.info['sfreq'])

# ---------------------------------------
# # REMOVE 19000101 & convert dtype
# def convertDatetimeSample(time_value):
#     if isinstance(time_value, datetime.datetime) or isinstance(time_value, datetime.time) :
#         h, m, s, ms = time_value.strftime("%H:%M:%S:%f").split(":")
#         return(int( ( (int(h)*3600) + (int(m)*60) + int(s)+ (float(ms[:-5])/10) ) * raw.info['sfreq']))
#     else:
#         return None
# # ---------------------------------------
# def convertQtoInt(time_value,code):
#     if (time_value==code):
#         return 1

# trigger = pd.read_excel("data/Subject15_11_4_2022/Subject15_11_4_2022.xlsx")
# EXCEL_DATAPOINT =  RAW_LENGTH*2 # 0.5 second frequency

# # print(EXCEL_DATAPOINT)
# # print(trigger.tail(15))
# trigger['Second'] = trigger['Time'].apply(lambda x: convertDatetimeSample(x) )
# # print(trigger['Second'])

# trigger['BaselineN'] = pd.to_numeric(trigger.Baseline, errors='coerce')
# trigger['Simulate_teeth_scrapingN'] = pd.to_numeric(trigger.Simulate_teeth_scraping, errors='coerce')

# trigger['Q1N'] = trigger["Q1"].apply(lambda x: convertQtoInt(x,"p"))
# trigger['Q2N'] = trigger["Q2"].apply(lambda x: convertQtoInt(x,"q"))
# trigger['Q3N'] = trigger["Q3"].apply(lambda x: convertQtoInt(x,"r"))
# trigger['Q4N'] = trigger["Q4"].apply(lambda x: convertQtoInt(x,"s"))

# trigger['Floss_teeth'] = pd.to_numeric(trigger.Floss_teeth, errors='coerce')
# # print(raw)
# ---------------------------------------
# idx_baseline = np.where(trigger["BaselineN"]==1)[0]
# idx_simulate = np.where(trigger["Simulate_teeth_scrapingN"]==1)[0]
# idx_q1 = np.where(trigger["Q1"] == "p")[0]
# idx_q2 = np.where(trigger["Q2"] == "q")[0]
# idx_q3=  np.where(trigger["Q3"] == "r")[0]
# idx_q4 = np.where(trigger["Q4"] == "s")[0]
# idx_floss = np.where(trigger["Floss_teeth"] == 1)[0]
# idx_stress = np.where(trigger["Stress"]==1)[0]


# def group_number_slices(arr):
#     # Grouping number slice
#     slice_baseline = []
#     start = arr[0]  # always the first index
#     stop = arr[0]
#     # print("start",start)
#     # print('stop',stop)
#     for i in range(1,len(arr)):
#         # print(arr[i],arr[i-1])
#         if (arr[i]==arr[i-1]+1): # continuous
            
#             stop = arr[i]                 # shift stopping point
#         else:                                      # breaking point
            
#             slice_baseline.append([start,stop])    # append slice
#             start = arr[i]                # move starting point
#             if i == len(arr)-1:           # enough index point?
#                 # stop = arr[i+1]
#                 slice_baseline.append([start,stop])    # append last slice
#             stop = arr[i]
#     slice_baseline.append((start,stop))
#     return slice_baseline

# for col_name in trigger.columns:
#     print(col_name)


# interval_baseline = group_number_slices(idx_baseline)
# interval_simulate = group_number_slices(idx_simulate)
# interval_q1 = group_number_slices(idx_q1)
# interval_q2 = group_number_slices(idx_q2)
# interval_q3 = group_number_slices(idx_q3)
# interval_q4 = group_number_slices(idx_q4)
# interval_floss = group_number_slices(idx_floss)
# interval_stress = group_number_slices(idx_stress)

# print(interval_baseline)
# print(interval_simulate)
# print(interval_q1)
# print(interval_q2)
# print(interval_q3)
# print(interval_q4)
# print(interval_floss)
# print(interval_stress)

# # Baseline has 2 interval
# print(interval_baseline[0])
# print(interval_baseline[1])

# plt.plot(trigger['Second'],trigger['BaselineN'],color="black")
# plt.plot(trigger['Second'],trigger['Simulate_teeth_scrapingN'],color="blue")
# plt.plot(trigger['Second'],trigger['Q1N'],color="mistyrose")
# plt.plot(trigger['Second'],trigger['Q2N'],color="tomato")
# plt.plot(trigger['Second'],trigger['Q3N'],color="red")
# plt.plot(trigger['Second'],trigger['Q4N'],color="darkred")
# plt.plot(trigger['Second'],trigger['Floss_teeth'],color="olive")
# plt.show()


# Get time in acummulated seconds - conv, split, multiply and sum
# h,m,s,ms = trigger['Time'][1].strftime("%H:%M:%S:%f").split(":")
# print(float(ms[:-5])/10 +int(s))
# timesample = int( ( (int(h)*3600) + (int(m)*60) + int(s)+ (float(ms[:-5])/10) ) * raw.info['sfreq'])
# print(timesample)









# print(trigger['Baseline'][330:340]) # specify range

# trigger_sample = trigger * raw.info['sfreq']

# Loop through raw signal with time (datapoint/256)
# Cut BASELINE when time BL ==1 ==time at raw signal
# for i in range():
#     if(trigger['Baseline'][i]==1):
#         print(trigger["Time"][i])

# for i in range(data.shape[1]):
#     if(trigger['Baseline'][i]==1):
#         print(trigger["Time"][i])
