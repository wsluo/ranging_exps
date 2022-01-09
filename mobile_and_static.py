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

from mobile_experiment import dist

def cdf(x, plot=True, *args, **kwargs):
    x, y = sorted(x), np.arange(len(x)) / len(x)
    return plt.plot(x, y, *args, **kwargs) if plot else (x, y)

def align(opo,tottag,bot1,fixed_point, magic):
    opo_log = get_range_and_ul_count(opo) #[t,name,range_dt,ul_count, dist] note: rx only
    tottag_rssi = get_rssi(tottag) #[timestamp, rssi, channel]
    tottag_raw = get_raw(tottag) # [timestamp, device_id, median, raw]
    bot1_log = get_log(bot1) #[timestamp,[x,y],[q_x,q_y,q_z,q_w]]

    bot1_yaws = get_yaws(bot1_log)

    ## align opo and bots
    bot1_stamps=[x[0] for x in bot1_log]
    opo_stamps=[x[0] for x in opo_log]
    
    #interpolate paths
    bot1_interp_x_f=interp1d(bot1_stamps,[m[1][0] for m in bot1_log])
    bot1_interp_y_f=interp1d(bot1_stamps,[m[1][1] for m in bot1_log])

    #only considers intersection
    interval_min=max(min(bot1_stamps),min(opo_stamps))
    interval_max=min(max(bot1_stamps),max(opo_stamps))

    print('min, max, interval for timestamps:',interval_min,interval_max,interval_max-interval_min)

    opo_log=[x for x in opo_log if (x[0]>=interval_min and x[0]<=interval_max)]
    opo_moments=[x[0] for x in opo_log] #window clipped
    opo_moments_offset=[x-opo_log[0][0] for x in opo_moments]
    
    print('opo data points:',len(opo_log))

    opo_dist_opo_moments = [x[4] for x in opo_log if (x[0]>=interval_min and x[0]<=interval_max)]

    tottag_ranges = [x[2]/1000 for x in tottag_raw] #convert from mm to m
    tottag_timestamps = [x[0] for x in tottag_raw]

    tottag_timestamps_offset = [x-tottag_timestamps[0]+magic for x in tottag_timestamps] #timestamp start at 0

    #calculate interpolated ground truth.
    interp_sample_timestamps = np.arange(interval_min, interval_max, 0.002)
    interp_sample_timestamps = np.clip(interp_sample_timestamps,interval_min, interval_max)
    bot1_interp_x,bot1_interp_y = bot1_interp_x_f(interp_sample_timestamps),bot1_interp_y_f(interp_sample_timestamps)

    interp_groundtruth = [dist([bot1_interp_x[i],bot1_interp_y[i]], fixed_point) for i in range(len(interp_sample_timestamps))]
    
    #calcualte error
    bot1_opo_moments_x, bot1_opo_moments_y = bot1_interp_x_f(opo_moments),bot1_interp_y_f(opo_moments)
    opo_moments_groundtruth = [dist([bot1_opo_moments_x[i],bot1_opo_moments_y[i]], fixed_point) for i in range(len(opo_moments))]
    opo_error=[opo_dist_opo_moments[i]-opo_moments_groundtruth[i] for i in range(len(opo_moments))]
    
    #plt.plot(opo_moments_offset,opo_error)
    #plt.show()
    
    #plt.plot(opo_moments_offset,bots_dist_opo_moments,label='ground truth')
    plt.plot([x-interval_min for x in interp_sample_timestamps],interp_groundtruth,label='ground truth',color='#1f77b4')
    plt.scatter(opo_moments_offset,opo_dist_opo_moments, label='opo',s=20,color='#ff7f0e')
    
    tottag_ranges = [tottag_ranges[i] for i in range(len(tottag_timestamps_offset)) if tottag_timestamps_offset[i]>=0]
    tottag_timestamps_offset = [x for x in tottag_timestamps_offset if x>=0] #clipping at 0
    
    plt.scatter(tottag_timestamps_offset,tottag_ranges,label='tottag',s=6,color='g')
    plt.xlabel('Time (s)')
    plt.ylabel('Distance (m)')
    plt.legend()
    plt.savefig(path+'aligned.png')
    plt.show()    
    
def process_rtt(path, exp_type, fixed_point, ul_count_cutoff=40):
    allfiles=os.listdir(path)
    
    opo=path+[f for f in allfiles if f.endswith('.pcapng')][0]

    tag1=path+[f for f in allfiles if f.startswith('rtt_')][0]
    tag2=path+[f for f in allfiles if f.startswith('rtt2_')][0]
    
    print(tag1,tag2)
    
    if exp_type == 'circle_clock1':
        bot1=path+[f for f in allfiles if f.endswith('circle_clock1')][0]
    if exp_type == 'sideline2':
        bot1=path+[f for f in allfiles if f.endswith('sideline2')][0]
        
        
    #align_rtt(opo,tag1,tag2,bot1,fixed_point, ul_count_cutoff)
    
    opo_log = get_range_and_ul_count(opo, ul_count_cutoff) #[t,name,range_dt,ul_count, dist] note: rx only
    
    raw1=get_raw_rtt(tag1)
    rssi1=get_rssi_rtt(tag1)
    
    raw2=get_raw_rtt(tag2)
    rssi2=get_rssi_rtt(tag2)
    
    tottag_raw,tottag_rssi = merge_tottag(raw1,rssi1,raw2,rssi2)  # [timestamp, device_id, median, raw] [timestamp, rssi, channel]
    tottag_stamps = [x[0] for x in tottag_raw]

    bot1_log = get_log(bot1) #[timestamp,[x,y],[q_x,q_y,q_z,q_w]]
    bot1_yaws = get_yaws(bot1_log)

    ## align opo and bots
    bot1_stamps=[x[0] for x in bot1_log]
    opo_stamps=[x[0] for x in opo_log]
    
    #interpolate paths
    bot1_interp_x_f=interp1d(bot1_stamps,[m[1][0] for m in bot1_log])
    bot1_interp_y_f=interp1d(bot1_stamps,[m[1][1] for m in bot1_log])
    bot1_interp_yaws_f=interp1d(bot1_stamps,bot1_yaws)
    
    #only considers intersection
    interval_min=max(min(bot1_stamps),min(opo_stamps),min(tottag_stamps))
    interval_max=min(max(bot1_stamps),max(opo_stamps),max(tottag_stamps))
    
    # print('opo delay:',min(opo_stamps)-min(bot1_stamps))

    print('min, max, interval for timestamps:',interval_min,interval_max,interval_max-interval_min)

    opo_log=[x for x in opo_log if (x[0]>=interval_min and x[0]<=interval_max)]
    opo_moments=[x[0] for x in opo_log] #window clipped
    opo_moments_offset=[x-interval_min for x in opo_moments]
    
    print('opo data points:',len(opo_log))

    opo_dist_opo_moments = [x[4] for x in opo_log if (x[0]>=interval_min and x[0]<=interval_max)]


    tottag_raw=[x for x in tottag_raw if (x[0]>=interval_min and x[0]<=interval_max)]
    tottag_rssi=[x for x in tottag_rssi if (x[0]>=interval_min and x[0]<=interval_max)]
    tottag_moments = [x[0] for x in tottag_raw]
    tottag_moments_offset = [x-interval_min for x in tottag_moments] 
    tottag_dist_tottag_moments = [x[2]/1000 for x in tottag_raw]

    #calculate interpolated ground truth.
    interp_sample_timestamps = np.arange(interval_min, interval_max, 0.002)
    interp_sample_timestamps = np.clip(interp_sample_timestamps,interval_min, interval_max)
    bot1_interp_x,bot1_interp_y = bot1_interp_x_f(interp_sample_timestamps),bot1_interp_y_f(interp_sample_timestamps)
    
    bot1_interp_yaws = bot1_interp_yaws_f(interp_sample_timestamps)

    interp_groundtruth = [dist([bot1_interp_x[i],bot1_interp_y[i]], fixed_point) for i in range(len(interp_sample_timestamps))]
    relative_yaws = [0-bot1_interp_yaws[i] for i in range(len(interp_sample_timestamps))]
    
    #calcualte opo error
    bot1_opo_moments_x, bot1_opo_moments_y = bot1_interp_x_f(opo_moments),bot1_interp_y_f(opo_moments)
    opo_moments_groundtruth = [dist([bot1_opo_moments_x[i],bot1_opo_moments_y[i]], fixed_point) for i in range(len(opo_moments))]
    opo_error=[opo_dist_opo_moments[i]-opo_moments_groundtruth[i] for i in range(len(opo_moments))]
    
    bot1_opo_moments_yaws = bot1_interp_yaws_f(opo_moments)
    #relative_yaws_opo_moments = [0-bot1_opo_moments_yaws[i] for i in range(len(opo_moments))]
    
    #calculate tottag error
    bot1_tottag_moments_x, bot1_tottag_moments_y = bot1_interp_x_f(tottag_moments),bot1_interp_y_f(tottag_moments)
    tottag_moments_groundtruth = [dist([bot1_tottag_moments_x[i],bot1_tottag_moments_y[i]],fixed_point) for i in range(len(tottag_moments))]
    tottag_error=[tottag_dist_tottag_moments[i]-tottag_moments_groundtruth[i] for i in range(len(tottag_moments))]
    
    bot1_tottag_moments_yaws = bot1_interp_yaws_f(tottag_moments)
    #relative_yaws_tottag_moments = [0-bot1_tottag_moments_yaws[i] for i in range(len(tottag_moments))]
    

    
    '''
    #plt.plot(opo_moments_offset,opo_error)
    #plt.show()
    
    #plt.plot(opo_moments_offset,bots_dist_opo_moments,label='ground truth')
    plt.plot([x-interval_min for x in interp_sample_timestamps],interp_groundtruth,label='ground truth',color='#1f77b4')
    plt.scatter(opo_moments_offset,opo_dist_opo_moments, label='opo',s=6,color='#ff7f0e') 
    plt.scatter(tottag_moments_offset,tottag_dist_tottag_moments,label='tottag',s=6,color='g')
    plt.xlabel('Time (s)')
    plt.ylabel('Distance (m)')
    plt.legend()
    '''
    
    interp_sample_timestamps_offset=[x-interval_min for x in interp_sample_timestamps]
    fig, (ax1,ax2,ax3) = plt.subplots(3)
    #plot opo error vs bot yaw
    ax1.set_xlim([0, interval_max-interval_min])
    ax1.plot(opo_moments_offset,opo_error,color='tab:red')
    ax1.scatter(opo_moments_offset,opo_error,color='tab:red',s=6)
    ax1.set_ylabel("Error (m)",color='tab:red',fontsize=12)
    ax1_twin=ax1.twinx()
    ax1_twin.plot(interp_sample_timestamps_offset,relative_yaws,color='tab:blue')
    #ax1_twin.scatter(interp_sample_timestamps_offset,relative_yaws,color='tab:blue',s=6)
    ax1_twin.set_ylabel("Relative Yaw",color='tab:blue',fontsize=12)
    ax1.title.set_text('Opo Error')
    #plot tottag error vs bot yaw
    ax2.set_xlim([0, interval_max-interval_min])
    ax2.plot(tottag_moments_offset,tottag_error,color='tab:red')
    ax2.scatter(tottag_moments_offset,tottag_error,color='tab:red',s=6)
    ax2.set_ylabel("Error (m)",color='tab:red',fontsize=12)
    ax2_twin=ax2.twinx()
    ax2_twin.plot(interp_sample_timestamps_offset,relative_yaws,color='tab:blue')
    #ax2_twin.scatter(interp_sample_timestamps_offset,relative_yaws,color='tab:blue',s=6)
    ax2_twin.set_ylabel("Relative Yaw",color='tab:blue',fontsize=12)
    ax2.title.set_text('Tottag Error')
    #plot opo, tottag vs ground truth
    ax3.set_xlim([0, interval_max-interval_min])
    ax3.plot(interp_sample_timestamps_offset,interp_groundtruth,label='ground truth',color='#1f77b4')
    ax3.scatter(opo_moments_offset,opo_dist_opo_moments, label='opo',s=20,color='#ff7f0e')
    ax3.scatter(tottag_moments_offset,tottag_dist_tottag_moments,label='tottag',s=6,color='g')
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Distance (m)')
    ax3.legend()
    ax3.title.set_text('Opo, Tottag vs Groundtruth')
    
    plt.tight_layout()    
    plt.savefig(path+'aligned.png')
    plt.show()
    
    plt.scatter([a[0]-interval_min for a in tottag_rssi],[a[1] for a in tottag_rssi])
    plt.title('RSSI')
    plt.xlabel('Time (s)')
    plt.show()
    
    #plt.hist(opo_error, cumulative=True, label='opo error CDF', histtype='step', alpha=0.8)
    cdf([abs(x) for x in opo_error],label='opo error CDF')
    cdf([abs(x) for x in tottag_error],label='tottag error CDF')    
    plt.xlabel('Absolute Error (m)')     
    plt.savefig(path+'error_cdf.png')
    plt.legend()
    plt.show()    
    
def main():
    '''
    #for this experiment, the wireshark is delayed  
    path='./exp/cse_building/level3_circle1_run1/'
    allfiles=os.listdir(path)
    opo=path+[f for f in allfiles if f.endswith('.pcapng')][0]
    tottag=path+"2C@12-14.LOG" #2C: -166? 29: -140?
    bot1=path+"2021_12_14-01_00_38_PM_circle_clock1"
    align(opo,tottag,bot1,[0,-0.3625],-166)
    '''

    '''
    path='./exp/cse_building/level3_circle1_run2/'
    allfiles=os.listdir(path)
    opo=path+[f for f in allfiles if f.endswith('.pcapng')][0]
    tottag=path+"29@12-14.LOG" #29: -18? 
    bot1=path+"2021_12_14-03_05_25_PM_circle_clock1"
    align(opo,tottag,bot1,[0,-0.364],-18)
    '''
    '''
    path='./exp/cse_building/level3_circle1_rtt_run1/'
    process_rtt(path, 'circle_clock1', [0,-0.3775], ul_count_cutoff=65)
    '''
    '''   
    path='./exp/cse_building/level3_sideline2_rtt_run1/'
    process_rtt(path, 'sideline2', [0,-0.3625], ul_count_cutoff=65)
    '''
    '''    
    path='./exp/cse_building/level3_sideline2_rtt_run2_wrong/' # not a line...
    process_rtt(path, 'sideline2', [0,-0.3780], ul_count_cutoff=65)
    '''
    '''  
    path='./exp/cse_building/level3_sideline2_rtt_run2/'
    process_rtt(path, 'sideline2', [0,-0.3700], ul_count_cutoff=65)  
    '''

    '''   
    path='./exp/cse_building/level3_sideline2_rtt_run3/'
    process_rtt(path, 'sideline2', [0,-0.3725], ul_count_cutoff=65)    
    '''

    '''
    path='./exp/cse_building/level3_sideline2_rtt_run4/'
    process_rtt(path, 'sideline2', [0,-0.3780], ul_count_cutoff=65)  
    ''' 
    #path='./exp/cse_building/level1_circle1_rtt_run1/'    
    #process_rtt(path, 'circle_clock1', [0,-0.3680], ul_count_cutoff=65)   

    #path='./exp/cse_building/level1_circle1_rtt_run2/'
    #process_rtt(path, 'circle_clock1', [0,-0.3635], ul_count_cutoff=65) 

    #path='./exp/cse_building/level1_circle1_rtt_run3/'
    #process_rtt(path, 'circle_clock1', [0,-0.3730], ul_count_cutoff=65)


    #path='./exp/cse_building/level1_sideline2_rtt_run1/'
    #process_rtt(path, 'sideline2', [0,-0.3785], ul_count_cutoff=65)


    #path='./exp/cse_building/level1_sideline2_rtt_run2/'
    #process_rtt(path, 'sideline2', [0,-0.3805], ul_count_cutoff=65)

    #path='./exp/cse_building/level1_sideline2_rtt_run3/'
    #process_rtt(path, 'sideline2', [0,-0.3780], ul_count_cutoff=65)

    #path='./exp/cse_building/level1_sideline2_rtt_run4/'
    #process_rtt(path, 'sideline2', [0,-0.3755], ul_count_cutoff=65)


    #path='./exp/placeA/level1_sideline2_rtt_run1/'
    #process_rtt(path, 'sideline2', [0,-0.3732], ul_count_cutoff=65)
    #0.3732

    #path='./exp/placeA/level1_sideline2_rtt_run2/'
    #process_rtt(path, 'sideline2', [0,-0.3715], ul_count_cutoff=65)


    #path='./exp/placeA/level1_sideline2_rtt_run3/' #missing late rssi
    #process_rtt(path, 'sideline2', [0,-0.3760], ul_count_cutoff=65)
    #0.3760

    #path='./exp/placeA/level1_sideline2_rtt_run4/' #missing late rssi
    #process_rtt(path, 'sideline2', [0,-0.3707], ul_count_cutoff=65)
    #0.3707

    #path='./exp/placeA/level1_sideline2_rtt_run5/' #missing late rssi
    #process_rtt(path, 'sideline2', [0,-0.3707], ul_count_cutoff=65)


    #path='./exp/placeA/level1_circle1_rtt_run1/'    
    #process_rtt(path, 'circle_clock1', [0,-0.3755], ul_count_cutoff=65)  
    #0.3755

    #path='./exp/placeA/level1_circle1_rtt_run2/'    
    #process_rtt(path, 'circle_clock1', [0,-0.3630], ul_count_cutoff=65) 



    #0.3630
    #path='./exp/placeA/level1_circle1_rtt_run3/'    
    #process_rtt(path, 'circle_clock1', [0,-0.3770], ul_count_cutoff=65) 

    #path='./exp/placeA/level3_sideline2_rtt_run1/'
    #process_rtt(path, 'sideline2', [0,-0.3590], ul_count_cutoff=65)


    #path='./exp/placeA/level3_sideline2_rtt_run2/'
    #process_rtt(path, 'sideline2', [0,-0.3795], ul_count_cutoff=65)


    #path='./exp/placeA/level3_sideline2_rtt_run3/'
    #process_rtt(path, 'sideline2', [0,-0.3735], ul_count_cutoff=65)
    #0.3735

    #path='./exp/placeA/level3_sideline2_rtt_run4/'
    #process_rtt(path, 'sideline2', [0,-0.3750], ul_count_cutoff=65)
    #0.3750


    #path='./exp/placeA/level3_circle1_rtt_run1/'    
    #process_rtt(path, 'circle_clock1', [0,-0.3725], ul_count_cutoff=65) 

    #path='./exp/placeA/level3_circle1_rtt_run2/'    
    #process_rtt(path, 'circle_clock1', [0,-0.3690], ul_count_cutoff=65) 
    #0.3690

    #path='./exp/placeA/level3_circle1_rtt_run3/'     ##missing much rssi
    #process_rtt(path, 'circle_clock1', [0,-0.3690], ul_count_cutoff=65) 

    #path='./exp/placeA/level3_circle1_rtt_run4/'     ##missing some tottag data
    #process_rtt(path, 'circle_clock1', [0,-0.3780], ul_count_cutoff=65) 

    #path='./exp/placeA/level3_circle1_rtt_run6/'     ##missing some tottag data
    #process_rtt(path, 'circle_clock1', [0,-0.3615], ul_count_cutoff=65)
    
    #path='./exp/placeB/level3_sideline2_rtt_run1/'
    #process_rtt(path, 'sideline2', [0,-0.3775], ul_count_cutoff=65)
    ##0.3775
    
    #path='./exp/placeB/level3_sideline2_rtt_run2/'
    #process_rtt(path, 'sideline2', [0,-0.3690], ul_count_cutoff=65)
    #03690
    
    #path='./exp/placeB/level3_sideline2_rtt_run3/'
    #process_rtt(path, 'sideline2', [0,-0.3745], ul_count_cutoff=65)
    
    #path='./exp/placeB/level3_sideline2_rtt_run4/'
    #process_rtt(path, 'sideline2', [0,-0.3700], ul_count_cutoff=65)
    #0.3700
    
    #path='./exp/placeB/level3_circle1_rtt_run1/'    
    #process_rtt(path, 'circle_clock1', [0,-0.3743], ul_count_cutoff=65)
    #0.3743
    
    
    #path='./exp/placeB/level3_circle1_rtt_run2/'    
    #process_rtt(path, 'circle_clock1', [0,-0.3600], ul_count_cutoff=65)
    #0.3600
    
    #path='./exp/placeB/level3_circle1_rtt_run3/'    
    #process_rtt(path, 'circle_clock1', [0,-0.3625], ul_count_cutoff=65)
    #0.3625
    
    #path='./exp/placeB/level3_circle1_rtt_run4/'    
    #process_rtt(path, 'circle_clock1', [0,-0.3565], ul_count_cutoff=65)    
    #0.3565
    
    #path='./exp/placeB/level1_sideline2_rtt_run1/'
    #process_rtt(path, 'sideline2', [0,-0.3770], ul_count_cutoff=65)    
    #0.3770
    
    #path='./exp/placeB/level1_sideline2_rtt_run2/'
    #process_rtt(path, 'sideline2', [0,-0.3690], ul_count_cutoff=65)
    #0.3690
    
    
    #path='./exp/placeB/level1_sideline2_rtt_run3/'
    #process_rtt(path, 'sideline2', [0,-0.3680], ul_count_cutoff=65)
    #0.3680
    
    #path='./exp/placeB/level1_sideline2_rtt_run4/'
    #process_rtt(path, 'sideline2', [0,-0.3655], ul_count_cutoff=65)
    #0.3655
    
    #path='./exp/placeB/level1_sideline2_rtt_run5/'
    #process_rtt(path, 'sideline2', [0,-0.3660], ul_count_cutoff=65)
    #0.3660
    
    #path='./exp/placeB/level1_circle1_rtt_run1/'    
    #process_rtt(path, 'circle_clock1', [0,-0.3695], ul_count_cutoff=65)
    #0.3695
    
    #path='./exp/placeB/level1_circle1_rtt_run2/'    
    #process_rtt(path, 'circle_clock1', [0,-0.3670], ul_count_cutoff=65)
    #0.3670
    
    #path='./exp/placeB/level1_circle1_rtt_run3/'    
    #process_rtt(path, 'circle_clock1', [0,-0.3650], ul_count_cutoff=65)
    #0.3650
    
    #path='./exp/placeB/level1_circle1_rtt_run4/'    
    #process_rtt(path, 'circle_clock1', [0,-0.3715], ul_count_cutoff=65)    
    #0.3715
if __name__ == "__main__":
   # stuff only to run when not called via 'import' here
   main()