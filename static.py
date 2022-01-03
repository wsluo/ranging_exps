#!/usr/bin/env python3

from parse_shark import get_range_and_ul_count
from parse_tottag import get_rssi, get_raw
from parse_rtt import get_rssi_rtt, get_raw_rtt, merge_tottag
from parse_bot import get_log, get_yaws
import os
from bisect import bisect_left
import math
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import numpy as np
from collections import OrderedDict

'''
tottag='./exp/cse_building/static/level3_old/29@12-14.LOG'
#tottag='rtt2.log'


tottag_rssi=get_rssi(tottag) #[timestamp, rssi, channel]
tottag_raw = get_raw(tottag) #[timestamp, device_id, median, raw]
rssi_time=[a[0] for a in tottag_rssi]
rssi_val=[a[1] for a in tottag_rssi]
raw_time=[a[0] for a in tottag_raw]
raw_dist=[a[2]/1000 for a in tottag_raw]

fig, (ax1, ax2) = plt.subplots(2)

print('raw_time min max:',min(raw_time),max(raw_time))
#print('rssi_time min max:',min(rssi_time),max(rssi_time))
ax1.scatter(rssi_time,rssi_val,s=2)
ax2.scatter(raw_time,raw_dist,s=2)
ax1.set_xlabel('time (s)')
ax1.set_ylabel('RSSI')
ax2.set_xlabel('time (s)')
ax2.set_ylabel('UWB Measurement (m)')
plt.tight_layout()
plt.show()
#plt.savefig(filename[:-7]+'.png',bbox_inches='tight')
'''

#def plot_set(tag1,tag2,opo):   

def process_rtt(path):
    allfiles=os.listdir(path)
    
    distances=[]
    for f in allfiles:
        if f.startswith('capture'):
            suf=f.split('_')[1][:-7].strip()
            distances.append(suf)
    distances=list(sorted(distances))
    alldata=OrderedDict()
            
    for distance in distances:
        tag1=path+'rtt_'+distance+'.log'
        tag2=path+'rtt2_'+distance+'.log'
        opo=path+'capture_'+distance+'.pcapng'
        
        raw1=get_raw_rtt(tag1)
        rssi1=get_rssi_rtt(tag1)
       
        raw2=get_raw_rtt(tag2)
        rssi2=get_rssi_rtt(tag2)
    
        tottag_raw,tottag_rssi = merge_tottag(raw1,rssi1,raw2,rssi2)
        tottag_stamps = [x[0] for x in tottag_raw]
    
        opo_log = get_range_and_ul_count(opo,ul_count_cutoff=40)
        opo_stamps=[x[0] for x in opo_log]
        
        #only considers intersection, tottag included
        interval_min=max(min(opo_stamps),min(tottag_stamps))
        interval_max=min(max(opo_stamps),max(tottag_stamps))

        print('min, max, interval for timestamps:',interval_min,interval_max,interval_max-interval_min)

        # clip opo into the min max window
        opo_log=[x for x in opo_log if (x[0]>=interval_min and x[0]<=interval_max)]
        tottag_raw=[x for x in tottag_raw if (x[0]>=interval_min and x[0]<=interval_max)]
        tottag_rssi=[x for x in tottag_rssi if (x[0]>=interval_min and x[0]<=interval_max)]
       
        rssi_time=[a[0]-interval_min for a in tottag_rssi]
        rssi_val=[a[1] for a in tottag_rssi]
        raw_time=[a[0]-interval_min for a in tottag_raw]
        raw_dist=[a[2]/1000 for a in tottag_raw]
        opo_time=[a[0]-interval_min for a in opo_log]
        opo_dist=[a[2]*340/32768.0 for a in opo_log]
        opo_ul_count=[a[3] for a in opo_log]
    
        '''
        fig, (ax1, ax2) = plt.subplots(2)
        ax1.scatter(rssi_time,rssi_val,s=2)
        ax2.scatter(raw_time,raw_dist,s=2,label='Tottag')
        ax2.scatter(opo_time,opo_dist,s=2,label='Opo')
        ax1.set_xlabel('time (s)')
        ax1.set_ylabel('RSSI')
        ax2.set_xlabel('time (s)')
        ax2.set_ylabel('Measurement (m)')
        plt.legend()
        plt.tight_layout()
        plt.show()
        '''
        alldata[distance]={'rssi_time':rssi_time,'rssi_val':rssi_val,'raw_time':raw_time,'raw_dist':raw_dist,'opo_time':opo_time,'opo_dist':opo_dist,'opo_ul_count':opo_ul_count,'interval_min':interval_min,'interval_max':interval_max}
        
    #concat plot
    concat_rssi_time,concat_rssi_val,concat_raw_time,concat_raw_dist,concat_opo_time,concat_opo_dist,concat_opo_ul_count  = [],[],[],[],[],[],[]
    
    start_time=0
    
    for distance in alldata:
        concat_rssi_time+=[x+start_time for x in alldata[distance]['rssi_time']]
        concat_rssi_val+=alldata[distance]['rssi_val']
        concat_raw_time+=[x+start_time for x in alldata[distance]['raw_time']]
        concat_raw_dist+=alldata[distance]['raw_dist']
        concat_opo_time+=[x+start_time for x in alldata[distance]['opo_time']]
        concat_opo_dist+=alldata[distance]['opo_dist']
        concat_opo_ul_count+=alldata[distance]['opo_ul_count']
        
        start_time+=alldata[distance]['interval_max']-alldata[distance]['interval_min'] + 0.5
        
        
    fig, (ax1, ax2, ax3) = plt.subplots(3)
    ax1.scatter(concat_rssi_time,concat_rssi_val,s=2)
    ax2.scatter(concat_raw_time,concat_raw_dist,s=2,label='Tottag')
    ax2.scatter(concat_opo_time,concat_opo_dist,s=2,label='Opo')
    ax3.scatter(concat_opo_time,concat_opo_ul_count,s=2,label='ul_count')
    ax1.set_xlabel('time (s)')
    ax1.set_ylabel('RSSI')
    ax2.set_xlabel('time (s)')
    ax2.set_ylabel('Measurement (m)')
    ax3.set_xlabel('time(s)')
    ax3.set_ylabel('UL count')
    plt.legend()
    plt.tight_layout()
    plt.savefig(path+'aligned_concat.png')
    plt.show()
    


path='./exp/cse_building/static/level3/'    
process_rtt(path)


#path='./exp/cse_building/static/level1/'    
#process_rtt(path)

#path='./exp/placeA/static/level1/'    #1m: first 2min05s opo data needs discard
#process_rtt(path)

#path='./exp/placeA/static/level3/'    #1m: first 2min05s opo data needs discard
#process_rtt(path)