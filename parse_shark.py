#!/usr/bin/env python3

#/usr/local/bin/tshark

import matplotlib.pyplot as plt

# var r = range_dt / 32768 * 340.29  #for certain version?

import pyshark
import binascii
from datetime import *
import os
import csv
import subprocess

def get_range_and_ul_count(filename, ul_count_cutoff):
    # open the captured file (805.15.4 wireshark capture)
    # cap is a generator
    # remember to GIVE PERMISSION to the file:  sudo chmod 777 filename, or sudo chmod 777 *  to apply to all files
    
    #get the path to tshark
    t_path = subprocess.Popen("which tshark", shell=True, stdout=subprocess.PIPE).stdout.read()
    cap = pyshark.FileCapture(filename,tshark_path=t_path,display_filter='frame contains "Timing"')
    
    #cap.set_debug() #output debugging msg 
    cap.load_packets() #packet_count=1000)
    print(cap)
    
    #print(cap[0])
    #print(dir(cap[0]))

    output = []
    for i in range(len(cap)):
        #t=cap[i].sniff_time # in utc time
        t=cap[i].sniff_timestamp #using unix epoch time
    
        #print(cap[i])
        if 'data' in cap[i]:
            d=cap[i].data.get_field_value('data')
            name = cap[i].wpan.get_field_by_showname('Source') #the sending device
        else:
            #ignore errors
            print('no data???????????')
            continue
    
        ranging_message = bytes.fromhex(d[12:-10]).decode('ascii')
        splitted=ranging_message.split(':')
        range_dt=splitted[1].split(',')[0].strip()
        ul_count=splitted[2].split(',')[0].strip()
        
        #print(ul_count+":")
        if int(ul_count)>=ul_count_cutoff:
            output.append([float(t),name,int(range_dt),int(ul_count),int(range_dt) / 32768 * 340.29])
        #print(t,name,range_dt,ul_count)
        #bytes_object = bytes.fromhex(d[10:]).split(b'\n')[0]
        #ascii_string = bytes_object.decode()
        #print(ascii_string)
        
    saved_file = filename.split('.')[0] + '.csv'    
    with open(saved_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ')
        for r in output:
            writer.writerow(r)
    #print(len(output))
    return output
            
#for quickplot
def quickplot_shark(filename):
    out=get_range_and_ul_count(filename)
    timestamps=[x[0] for x in out]
    timestamps=[x-timestamps[0] for x in timestamps]
    dists=[x[-1] for x in out]
    
    fig, (ax1, ax2) = plt.subplots(2)
    
    
    ax1.scatter(timestamps,dists)
    ax2.scatter(timestamps, [x[3] for x in out])
    ax2.plot(timestamps, [x[3] for x in out])
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Distance')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('UL count')
    plt.tight_layout()
    
    plt.savefig(filename[:-7]+'.png')
    plt.show()
    
#quickplot_shark('./exp/cse_building/level3_run2/capture.pcapng')
#quickplot_shark('./exp/cse_building/level3_circle1_run2/capture.pcapng')
#quickplot_shark('./exp/cse_building/static/level3/capture_7.pcapng')


