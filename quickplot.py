#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
import math
import statistics
import random
import pandas as pd
import csv
import bisect
from parse_tottag import get_rssi
from parse_rtt import get_rssi_rtt
from parse_rtt import get_raw_rtt
#print(np.genfromtxt('test.txt'))

# Create a data structure to hold the parsed data
tags = {}
# Open the log file
#name = './exp/cse_building/level1_run1/2A@12-13.LOG'
#name = './exp/cse_building/level1_run3/29@12-14.LOG'
#name = './exp/cse_building/level3_run1/29@12-14.LOG'
#name = './exp/cse_building/level3_circle1_run1/2C@12-14.LOG'
#name = './exp/cse_building/level3_circle1_run2/2C@12-14.LOG'
#name = './exp/cse_building/static/level3/29@12-14.LOG'
#name = './exp/cse_building/level3_run2/29@12-15.LOG'
name = './exp/cse_building/static/level3/29@12-19.LOG'
name = './exp/cse_building/level3_run3/rtt.log'

def quickplot_sd(name):
    f = open(name) #min timestamp 1639331573 max timestamp 1639332525 span: 952 #min timestamp 1639331542 max timestamp 1639332501 span: 959
    # Read data from the log file
    for line in f:
        # For now, just ignore these events
        if line[0] == '#':
            continue
        
        try:
            # Parse out the fields
            timestamp,tag_id,distance = line.split()[:3]
            # Convert to meaningful data types
            timestamp = int(timestamp)
            tag_id = tag_id.split(':')[-1]
            distance = int(distance)
            # Filter out bad readings
            if distance == 0 or distance == 999999:
                continue
            # Save this measurement
            if tag_id not in tags:
                tags[tag_id] = []
            tags[tag_id].append((timestamp, distance))
        except:
            print(line)
            continue

    # Done parsing, plot!
    for tag, data in tags.items():
        print("Plotting data for", tag)
        timestamps, dists = zip(*data)
        print('min timestamp',min(timestamps),'max timestamp',max(timestamps), 'span:',max(timestamps)-min(timestamps))
        #print(x_axis)
        #print(y_axis)
    
        fig, (ax1, ax2) = plt.subplots(2)
    
        ax1.scatter([x-min(timestamps) for x in timestamps], dists)
        ax2.plot([x-min(timestamps) for x in timestamps])
        plt.show()
    
        fig.savefig(name[:-4]+'.png')
    
    
        for i in range(1,len(timestamps)):
            if timestamps[i]<timestamps[i-1]:
                print("timestamp decrease from:",timestamps[i-1],'to:',timestamps[i])
                
def quickplot_rtt(name):   
    raw=get_raw_rtt(name)  #[timestamp,device_id,median,raw]      
    rssi=get_rssi_rtt(name) #[timestamp, rssi, channel]

    raw_ts=[x[0] for x in raw]
    rssi_ts=[x[0] for x in rssi]

    fig, (ax1, ax2) = plt.subplots(2)
    ax1.scatter([x-min(raw_ts) for x in raw_ts],[x[2] for x in raw])
    ax2.plot([x-min(rssi_ts) for x in rssi_ts],[x[1] for x in rssi])
    plt.show()
    
    
quickplot_rtt(name)             
