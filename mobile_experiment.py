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

#h_offset=0.3625 #right robot from left robot. used for horizontal translation

def dist(a,b):
    return math.sqrt( (a[0]-b[0])**2 + (a[1]-b[1])**2 )

#offset=bot-opo at the same moment
def aln_opo_bot(opo_log,bot_log, offset=0):
    bot_stamps = [a[0]-offset for a in bot_log]
    opo_stamps = [a[0] for a in opo_log]
    
    #bisect.bisect_left(a, x, lo=0, hi=len(a), *, key=None)
    opo_mapping_idxs = []
    
    search_start=0
    for opo_stamp in opo_stamps:
        idx = bisect_left(bot_stamps, opo_stamp, lo=search_start, hi=len(bot_stamps))
        search_start = idx
        
        opo_mapping_idxs.append(idx)
    
    #get the positions and orientations of the bot at the ranging moments of opo
    return opo_mapping_idxs

def aln_tottag_bot():
    return 




def align(opo,tottag,bot1,bot2,h_offset, magic):
    opo_log = get_range_and_ul_count(opo) #[t,name,range_dt,ul_count, dist] note: rx only
    tottag_rssi = get_rssi(tottag) #[timestamp, rssi, channel]
    tottag_raw = get_raw(tottag) # [timestamp, device_id, median, raw]
    bot1_log = get_log(bot1) #[timestamp,[x,y],[q_x,q_y,q_z,q_w]]
    bot2_log = get_log(bot2) #[timestamp,[x,y],[q_x,q_y,q_z,q_w]]

    bot1_yaws = get_yaws(bot1_log)
    bot2_yaws = get_yaws(bot2_log)

    ## align opo and bots
    bot1_stamps=[x[0] for x in bot1_log]
    bot2_stamps=[x[0] for x in bot2_log]
    opo_stamps=[x[0] for x in opo_log]
    
    #interpolate paths
    bot1_interp_x_f=interp1d(bot1_stamps,[m[1][0] for m in bot1_log])
    bot1_interp_y_f=interp1d(bot1_stamps,[m[1][1] for m in bot1_log])
    bot1_interp_yaws_f=interp1d(bot1_stamps,bot1_yaws)
    
    bot2_interp_x_f=interp1d(bot2_stamps,[m[1][0] for m in bot2_log])
    bot2_interp_y_f=interp1d(bot2_stamps,[m[1][1] for m in bot2_log])
    bot2_interp_yaws_f=interp1d(bot2_stamps,bot2_yaws)

    #only considers intersection
    interval_min=max(min(bot1_stamps),min(bot2_stamps),min(opo_stamps))
    interval_max=min(max(bot1_stamps),max(bot2_stamps),max(opo_stamps))

    print('min, max, interval for timestamps:',interval_min,interval_max,interval_max-interval_min)

    opo_log=[x for x in opo_log if (x[0]>=interval_min and x[0]<=interval_max)]
    opo_moments=[x[0] for x in opo_log] #window clipped
    opo_moments_offset=[x-opo_log[0][0] for x in opo_moments]

    bot1_opo_mapping_idxs = aln_opo_bot(opo_log,bot1_log,offset=0)
    bot2_opo_mapping_idxs = aln_opo_bot(opo_log,bot2_log,offset=0)

    bot1_wheres_opo= [[bot1_log[idx][1], bot1_log[idx][2]] for idx in bot1_opo_mapping_idxs]
    bot2_wheres_opo= [[bot2_log[idx][1], bot2_log[idx][2]] for idx in bot2_opo_mapping_idxs]

    #print(len(bot1_wheres_opo),len(bot2_wheres_opo)) #should be equal

    bots_dist_opo_moments = [dist(bot1_wheres_opo[i][0],[bot2_wheres_opo[i][0][0],bot2_wheres_opo[i][0][1]-h_offset]) for i in range(len(bot1_wheres_opo))]
    opo_dist_opo_moments = [x[4] for x in opo_log if (x[0]>=interval_min and x[0]<=interval_max)]

    tottag_ranges = [x[2]/1000 for x in tottag_raw] #convert from mm to m
    tottag_timestamps = [x[0] for x in tottag_raw]

    tottag_timestamps_offset = [x-tottag_timestamps[0]+magic for x in tottag_timestamps] #timestamp start at 0

    #calculate interpolated ground truth.
    interp_sample_timestamps = np.arange(interval_min, interval_max, 0.005)
    interp_sample_timestamps = np.clip(interp_sample_timestamps,interval_min, interval_max)
    bot1_interp_x,bot1_interp_y = bot1_interp_x_f(interp_sample_timestamps),bot1_interp_y_f(interp_sample_timestamps)
    bot2_interp_x,bot2_interp_y = bot2_interp_x_f(interp_sample_timestamps),bot2_interp_y_f(interp_sample_timestamps)
    
    #bot1_interp_yaws = bot1_interp_yaws_f(interp_sample_timestamps,bot1_interp_yaws_f(interp_sample_timestamps))
    #bot2_interp_yaws = bot2_interp_yaws_f(interp_sample_timestamps,bot2_interp_yaws_f(interp_sample_timestamps))

    interp_groundtruth = [dist([bot1_interp_x[i],bot1_interp_y[i]], [bot2_interp_x[i],bot2_interp_y[i]-h_offset]) for i in range(len(interp_sample_timestamps))]
    #relative_yaws = [bot2_interp_yaws[i]-bot1_interp_yaws[i] for i in range(len(interp_sample_timestamps))]
    #calcualte error
    bot1_opo_moments_x, bot1_opo_moments_y = bot1_interp_x_f(opo_moments),bot1_interp_y_f(opo_moments)
    bot2_opo_moments_x, bot2_opo_moments_y = bot2_interp_x_f(opo_moments),bot2_interp_y_f(opo_moments)
    opo_moments_groundtruth = [dist([bot1_opo_moments_x[i],bot1_opo_moments_y[i]], [bot2_opo_moments_x[i],bot2_opo_moments_y[i]-h_offset]) for i in range(len(opo_moments))]
    opo_error=[opo_dist_opo_moments[i]-opo_moments_groundtruth[i] for i in range(len(opo_moments))]
    
    bot1_opo_moments_yaws = bot1_interp_yaws_f(opo_moments)
    bot2_opo_moments_yaws = bot2_interp_yaws_f(opo_moments)
    relative_yaws = [bot2_opo_moments_yaws[i]-bot1_opo_moments_yaws[i] for i in range(len(opo_moments))]
    
    fig, (ax1,ax2) = plt.subplots(2)
    
    ax1.plot(opo_moments_offset,opo_error,color='tab:red')
    ax1.set_ylabel("Error (m)",color='tab:red',fontsize=14)
    ax1_twin=ax1.twinx()
    ax1_twin.plot(opo_moments_offset,relative_yaws,color='tab:blue')
    ax1_twin.set_ylabel("Relative Yaw",color='tab:blue',fontsize=14)
    ax1.title.set_text('Opo Error')
    #plt.show()
    #plt.show()
    #plt.plot(opo_moments_offset,bots_dist_opo_moments,label='ground truth')
    ax2.plot([x-interval_min for x in interp_sample_timestamps],interp_groundtruth,label='ground truth',color='#1f77b4')
    ax2.scatter(opo_moments_offset,opo_dist_opo_moments, label='opo',s=6,color='#ff7f0e')    
 
    tottag_ranges = [tottag_ranges[i] for i in range(len(tottag_timestamps_offset)) if tottag_timestamps_offset[i]>=0]
    tottag_timestamps_offset = [x for x in tottag_timestamps_offset if x>=0] #clipping at 0
    
    ax2.scatter(tottag_timestamps_offset,tottag_ranges,label='tottag',s=6,color='g')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Distance (m)')
    ax2.legend()
    ax2.title.set_text('Opo, Tottag VS Groundtruth')
    plt.tight_layout()
    plt.savefig(path+'aligned.png')
    plt.show()

    ## align tottag uwb and bots
#don't forget sudo chmod 777 for wireshark files


def align_rtt(opo,tag1,tag2,bot1,bot2,h_offset, ul_count_cutoff):
    opo_log = get_range_and_ul_count(opo,ul_count_cutoff) #[t,name,range_dt,ul_count, dist] note: rx only

    #tottag_rssi = get_rssi_rtt(tottag) #[timestamp, rssi, channel]
    #tottag_raw = get_raw_rtt(tottag) # [timestamp, device_id, median, raw]
    
    raw1=get_raw_rtt(tag1)
    rssi1=get_rssi_rtt(tag1)
    
    raw2=get_raw_rtt(tag2)
    rssi2=get_rssi_rtt(tag2)
    
    tottag_raw,tottag_rssi = merge_tottag(raw1,rssi1,raw2,rssi2)
    
    
    bot1_log = get_log(bot1) #[timestamp,[x,y],[q_x,q_y,q_z,q_w]]
    bot2_log = get_log(bot2) #[timestamp,[x,y],[q_x,q_y,q_z,q_w]]

    bot1_yaws = get_yaws(bot1_log)
    bot2_yaws = get_yaws(bot2_log)

    ## align opo and bots
    bot1_stamps=[x[0] for x in bot1_log]
    bot2_stamps=[x[0] for x in bot2_log]
    opo_stamps=[x[0] for x in opo_log]
    
    
    #tottag_ranges = [x[2]/1000 for x in tottag_raw] #convert from mm to m
    tottag_stamps = [x[0] for x in tottag_raw]
    
    #interpolate paths
    bot1_interp_x_f=interp1d(bot1_stamps,[m[1][0] for m in bot1_log])
    bot1_interp_y_f=interp1d(bot1_stamps,[m[1][1] for m in bot1_log])
    bot1_interp_yaws_f=interp1d(bot1_stamps,bot1_yaws)
    
    bot2_interp_x_f=interp1d(bot2_stamps,[m[1][0] for m in bot2_log])
    bot2_interp_y_f=interp1d(bot2_stamps,[m[1][1] for m in bot2_log])
    bot2_interp_yaws_f=interp1d(bot2_stamps,bot2_yaws)

    #only considers intersection, tottag included
    interval_min=max(min(bot1_stamps),min(bot2_stamps),min(opo_stamps),min(tottag_stamps))
    interval_max=min(max(bot1_stamps),max(bot2_stamps),max(opo_stamps),max(tottag_stamps))

    print('min, max, interval for timestamps:',interval_min,interval_max,interval_max-interval_min)

    # clip opo into the min max window
    opo_log=[x for x in opo_log if (x[0]>=interval_min and x[0]<=interval_max)]
    opo_moments=[x[0] for x in opo_log] #window clipped
    opo_moments_offset=[x-interval_min for x in opo_moments]
    
    print('opo data points:',len(opo_log))

    #bot1_opo_mapping_idxs = aln_opo_bot(opo_log,bot1_log,offset=0)
    #bot2_opo_mapping_idxs = aln_opo_bot(opo_log,bot2_log,offset=0)

    #bot1_wheres_opo= [[bot1_log[idx][1], bot1_log[idx][2]] for idx in bot1_opo_mapping_idxs]
    #bot2_wheres_opo= [[bot2_log[idx][1], bot2_log[idx][2]] for idx in bot2_opo_mapping_idxs]

    #print(len(bot1_wheres_opo),len(bot2_wheres_opo)) #should be equal

    #bots_dist_opo_moments = [dist(bot1_wheres_opo[i][0],[bot2_wheres_opo[i][0][0],bot2_wheres_opo[i][0][1]-h_offset]) for i in range(len(bot1_wheres_opo))]
    opo_dist_opo_moments = [x[4] for x in opo_log if (x[0]>=interval_min and x[0]<=interval_max)]


    # clip tottag into the min max window
    tottag_raw=[x for x in tottag_raw if (x[0]>=interval_min and x[0]<=interval_max)]
    tottag_rssi=[x for x in tottag_rssi if (x[0]>=interval_min and x[0]<=interval_max)]
    tottag_moments = [x[0] for x in tottag_raw]
    tottag_moments_offset = [x-interval_min for x in tottag_moments] 
    tottag_dist_tottag_moments = [x[2]/1000 for x in tottag_raw]

    #tottag_timestamps_offset = [x-tottag_timestamps[0]+magic for x in tottag_timestamps] #timestamp start at 0

    #calculate interpolated ground truth.
    interp_sample_timestamps = np.arange(interval_min, interval_max, 0.005)
    interp_sample_timestamps = np.clip(interp_sample_timestamps,interval_min, interval_max)
    bot1_interp_x,bot1_interp_y = bot1_interp_x_f(interp_sample_timestamps),bot1_interp_y_f(interp_sample_timestamps)
    bot2_interp_x,bot2_interp_y = bot2_interp_x_f(interp_sample_timestamps),bot2_interp_y_f(interp_sample_timestamps)
    
    #bot1_interp_yaws = bot1_interp_yaws_f(interp_sample_timestamps,bot1_interp_yaws_f(interp_sample_timestamps))
    #bot2_interp_yaws = bot2_interp_yaws_f(interp_sample_timestamps,bot2_interp_yaws_f(interp_sample_timestamps))

    interp_groundtruth = [dist([bot1_interp_x[i],bot1_interp_y[i]], [bot2_interp_x[i],bot2_interp_y[i]-h_offset]) for i in range(len(interp_sample_timestamps))]
    #relative_yaws = [bot2_interp_yaws[i]-bot1_interp_yaws[i] for i in range(len(interp_sample_timestamps))]
    
    #calcualte opo error
    bot1_opo_moments_x, bot1_opo_moments_y = bot1_interp_x_f(opo_moments),bot1_interp_y_f(opo_moments)
    bot2_opo_moments_x, bot2_opo_moments_y = bot2_interp_x_f(opo_moments),bot2_interp_y_f(opo_moments)
    opo_moments_groundtruth = [dist([bot1_opo_moments_x[i],bot1_opo_moments_y[i]], [bot2_opo_moments_x[i],bot2_opo_moments_y[i]-h_offset]) for i in range(len(opo_moments))]
    opo_error=[opo_dist_opo_moments[i]-opo_moments_groundtruth[i] for i in range(len(opo_moments))]
    
    bot1_opo_moments_yaws = bot1_interp_yaws_f(opo_moments)
    bot2_opo_moments_yaws = bot2_interp_yaws_f(opo_moments)
    relative_yaws_opo_moments = [bot2_opo_moments_yaws[i]-bot1_opo_moments_yaws[i] for i in range(len(opo_moments))]
    
    #calculate tottag error
    bot1_tottag_moments_x, bot1_tottag_moments_y = bot1_interp_x_f(tottag_moments),bot1_interp_y_f(tottag_moments)
    bot2_tottag_moments_x, bot2_tottag_moments_y = bot2_interp_x_f(tottag_moments),bot2_interp_y_f(tottag_moments)
    tottag_moments_groundtruth = [dist([bot1_tottag_moments_x[i],bot1_tottag_moments_y[i]], [bot2_tottag_moments_x[i],bot2_tottag_moments_y[i]-h_offset]) for i in range(len(tottag_moments))]
    tottag_error=[tottag_dist_tottag_moments[i]-tottag_moments_groundtruth[i] for i in range(len(tottag_moments))]
    
    bot1_tottag_moments_yaws = bot1_interp_yaws_f(tottag_moments)
    bot2_tottag_moments_yaws = bot2_interp_yaws_f(tottag_moments)
    relative_yaws_tottag_moments = [bot2_tottag_moments_yaws[i]-bot1_tottag_moments_yaws[i] for i in range(len(tottag_moments))]
    
    fig, (ax1,ax2,ax3) = plt.subplots(3)
    #plot opo error vs bot yaw
    ax1.set_xlim([0, interval_max-interval_min])
    ax1.plot(opo_moments_offset,opo_error,color='tab:red')
    ax1.scatter(opo_moments_offset,opo_error,color='tab:red',s=6)
    ax1.set_ylabel("Error (m)",color='tab:red',fontsize=12)
    ax1_twin=ax1.twinx()
    ax1_twin.plot(opo_moments_offset,relative_yaws_opo_moments,color='tab:blue')
    ax1_twin.scatter(opo_moments_offset,relative_yaws_opo_moments,color='tab:blue',s=6)
    ax1_twin.set_ylabel("Relative Yaw",color='tab:blue',fontsize=12)
    ax1.title.set_text('Opo Error')
    #plot tottag error vs bot yaw
    ax2.set_xlim([0, interval_max-interval_min])
    ax2.plot(tottag_moments_offset,tottag_error,color='tab:red')
    ax2.scatter(tottag_moments_offset,tottag_error,color='tab:red',s=6)
    ax2.set_ylabel("Error (m)",color='tab:red',fontsize=12)
    ax2_twin=ax2.twinx()
    ax2_twin.plot(tottag_moments_offset,relative_yaws_tottag_moments,color='tab:blue')
    ax2_twin.scatter(tottag_moments_offset,relative_yaws_tottag_moments,color='tab:blue',s=6)
    ax2_twin.set_ylabel("Relative Yaw",color='tab:blue',fontsize=12)
    ax2.title.set_text('Tottag Error')
    #plot opo, tottag vs ground truth
    ax3.set_xlim([0, interval_max-interval_min])
    ax3.plot([x-interval_min for x in interp_sample_timestamps],interp_groundtruth,label='ground truth',color='#1f77b4')
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
    plt.show()

def process_rtt(path, exp_type, offset, ul_count_cutoff=40):
    allfiles=os.listdir(path)
    
    opo=path+[f for f in allfiles if f.endswith('.pcapng')][0]

    tag1=path+[f for f in allfiles if f.startswith('rtt_')][0]
    tag2=path+[f for f in allfiles if f.startswith('rtt2_')][0]
    
    print(tag1,tag2)
    
    if exp_type == 'clock_counter_2':
        bot1=path+[f for f in allfiles if f.endswith('clock2')][0]
        bot2=path+[f for f in allfiles if f.endswith('counter2')][0]
        
    align_rtt(opo,tag1,tag2,bot1,bot2,offset, ul_count_cutoff)

'''
path='./exp/cse_building/level1_run1/'
allfiles=os.listdir(path)
opo=path+[f for f in allfiles if f.endswith('.pcapng')][0]
tottag=path+"2C@12-13.LOG"
bot1=path+"2021_12_13-11_11_56_AM_clock2"
bot2=path+"2021_12_13-11_12_09_AM_counter2"

align(opo,tottag,bot1,bot2,0.3625,-310) #  #2C: -310
'''
  
'''
path='./exp/cse_building/level1_run2/'
allfiles=os.listdir(path)
opo=path+[f for f in allfiles if f.endswith('.pcapng')][0]
tottag=path+"2C@12-13.LOG"
bot1=path+"2021_12_13-03_03_45_PM_clock2"
bot2=path+"2021_12_13-03_03_54_PM_counter2"

align(opo,tottag,bot1,bot2,0.3625,3.4) #2C: 3.4
'''

''' 
path='./exp/cse_building/level1_run3/'
allfiles=os.listdir(path)
opo=path+[f for f in allfiles if f.endswith('.pcapng')][0]
tottag=path+"29@12-14.LOG"
bot1=path+"2021_12_13-06_30_05_PM_clock2"
bot2=path+"2021_12_13-06_30_16_PM_counter2"

align(opo,tottag,bot1,bot2,0.3625,-5)
'''

'''
path='./exp/cse_building/level3_run1/' #1639491084
allfiles=os.listdir(path)
opo=path+[f for f in allfiles if f.endswith('.pcapng')][0]
tottag=path+"2C@12-14.LOG"
bot1=path+"2021_12_14-06_11_03_AM_clock2"
bot2=path+"2021_12_14-06_11_12_AM_counter2"
align(opo,tottag,bot1,bot2,0.3625,-283.1)
'''

'''
path='./exp/cse_building/level3_run2/' #1639491084
allfiles=os.listdir(path)
opo=path+[f for f in allfiles if f.endswith('.pcapng')][0]
tottag=path+"29@12-15.LOG"
bot1=path+"2021_12_15-09_36_35_AM_clock2"
bot2=path+"2021_12_15-09_36_42_AM_counter2"
align(opo,tottag,bot1,bot2,0.3640,-11.8)
#
'''
    


'''  
path='./exp/cse_building/level3_run3/'
process_rtt(path,'clock_counter_2',0.3715, ul_count_cutoff=40)
'''
    
    
'''
allfiles=os.listdir(path) 
opo=path+[f for f in allfiles if f.endswith('.pcapng')][0]

tag1=path+'rtt.log'
tag2=path+'rtt2.log'

bot1=path+"2021_12_28-12_37_27_AM_clock2"
bot2=path+"2021_12_28-12_37_35_AM_counter2" 
align_rtt(opo,tag1,tag2,bot1,bot2,0.3715)
'''


#path='./exp/cse_building/level3_rtt_run1/' #this run, the opo monitor starts a bit later
#process_rtt(path,'clock_counter_2',0.3725)

    

#path='./exp/cse_building/level3_rtt_run2/' #in rtt, around 1640895384.917603, repeated entries in raw file? buffer problem?
#process_rtt(path,'clock_counter_2',0.3620, ul_count_cutoff=40)



#path='./exp/cse_building/level3_rtt_run3/' #this run, missing many tottag data due to jlink issues
#process_rtt(path,'clock_counter_2',0.3685,ul_count_cutoff=40)



#path='./exp/cse_building/level3_rtt_run4/' 
#process_rtt(path,'clock_counter_2',0.3770,ul_count_cutoff=57)


   
#path='./exp/cse_building/level1_rtt_run1/'  ### missing some rssi
#process_rtt(path,'clock_counter_2',0.3675,ul_count_cutoff=40) 
   
#path='./exp/cse_building/level1_rtt_run2/' 
#process_rtt(path,'clock_counter_2',0.3805,ul_count_cutoff=40)   
        
#path='./exp/cse_building/level1_rtt_run3/'  
#process_rtt(path,'clock_counter_2',0.3675,ul_count_cutoff=40)   

#path='./exp/cse_building/level1_rtt_run4/'  
#process_rtt(path,'clock_counter_2',0.3705,ul_count_cutoff=40) 


#path='./exp/placeA/level1_rtt_run1/' #missing first half tottag data
#process_rtt(path,'clock_counter_2',0.3615,ul_count_cutoff=40) 

#path='./exp/placeA/level1_rtt_run2/' #sparse tottag data #missing much rssi
#process_rtt(path,'clock_counter_2',0.3720,ul_count_cutoff=40)     

#path='./exp/placeA/level1_rtt_run3/' #sparse tottag data 
#process_rtt(path,'clock_counter_2',0.3690,ul_count_cutoff=40)  

#path='./exp/placeA/level1_rtt_run4/' #sparse tottag data 
#process_rtt(path,'clock_counter_2',0.3670   ,ul_count_cutoff=40) 

#path='./exp/placeA/level1_rtt_run5/'  ### first good run
#process_rtt(path,'clock_counter_2',0.3630   ,ul_count_cutoff=40) 

#path='./exp/placeA/level1_rtt_run6/'  ### second good run
#process_rtt(path,'clock_counter_2',0.3770   ,ul_count_cutoff=40) 

#0.3667
#path='./exp/placeA/level1_rtt_run7/' ### third good run
#process_rtt(path,'clock_counter_2',0.3667  ,ul_count_cutoff=40) 


#path='./exp/placeA/level3_rtt_run1/' #missing many tottag data
#process_rtt(path,'clock_counter_2',0.3665,ul_count_cutoff=40) 

#path='./exp/placeA/level3_rtt_run2/' #missing many tottag data
#process_rtt(path,'clock_counter_2',0.3720,ul_count_cutoff=40)

#path='./exp/placeA/level3_rtt_run3/' #missing many tottag data
#process_rtt(path,'clock_counter_2',0.3710,ul_count_cutoff=40)

#path='./exp/placeA/level3_rtt_run4/' #not many useful data
#process_rtt(path,'clock_counter_2',0.3770,ul_count_cutoff=40)
#0.3770

#path='./exp/placeA/level3_rtt_run5/' #not many useful data
#process_rtt(path,'clock_counter_2',0.3710,ul_count_cutoff=40)

#path='./exp/placeA/level3_rtt_run6/' #junk
#process_rtt(path,'clock_counter_2',0.3710,ul_count_cutoff=40)

#path='./exp/placeA/level3_rtt_run7/' #another junk
#process_rtt(path,'clock_counter_2',0.3630,ul_count_cutoff=40)

path='./exp/placeA/level3_rtt_run8/' #more data
process_rtt(path,'clock_counter_2',0.3785,ul_count_cutoff=40)
#0.3785

## TODO  fix the right tottag? which always disconnect when moving