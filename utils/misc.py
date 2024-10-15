import math
import datetime
import numpy as np

def convertQtoInt( time_value, code):
    if (time_value==code):
        return 1
    
def roundup_datapoint( num ): # (digit - 1) (1230 -> 1300) (4->3)
    digit = int(math.floor(math.log10(num))) # 3
    rounding_factor = 10 ** digit  # 1000
    rounded_num = math.ceil(num / rounding_factor) * rounding_factor # divide, round up then multiply back
    # print("Round num ", num)
    # print("Di ", digit)
    # print("rn ", rounded_num)
    
    return rounded_num

def group_number(arr):
    # Grouping number slice
    interval = []
    start = arr[0]  # always the first index
    stop = arr[0]
    # print("start",start)
    # print('stop',stop)
    for i in range(1,len(arr)):
        # print(arr[i],arr[i-1])
        if (arr[i]==arr[i-1]+1): # continuous
            stop = arr[i]                 # shift stopping point
        else: # breaking point                             
            interval.append([start-1,stop])    # append slice
            start = arr[i]                # move starting point
            # if i == len(arr)-1:           # enough index point?
            #     # stop = arr[i+1]
            #     interval.append([start,stop])    # append last slice
            stop = arr[i]
    interval.append((start-1,stop))
    print(interval)
    return interval

def convert_datetime_sample( time_value, fs):
    if isinstance(time_value, datetime.datetime) or isinstance(time_value, datetime.time) :
        h, m, s, ms = time_value.strftime("%H:%M:%S:%f").split(":")
        return(int( ( (int(h)*3600) + (int(m)*60) + int(s)+ (float(ms[:-5])/10))* fs))
    else:
        return None

def convert_timescale(interval,fs):
    # Modify : Trigger to time scale
    second = np.multiply(interval,.5) # In Second
    # length = second[0][1]-second[0][0]
    interval_datapoint = np.multiply(second,fs).astype(int) # Raw fs
    # print("### ", segment," IsExtend?", self.segmentExtend)
    # print("Trigger Interval:", interval)
    # print("Time (second)   :", second,"## Length :", length, " second")
    # print("Raw Datapoint   :", interval_datapoint)
    return interval_datapoint