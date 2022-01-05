#!/usr/bin/env python3
import decimal
import matplotlib.pyplot as plt
from math import *

def get_log(filename):
    log=[]
    with open(filename) as f:
        for line in f.readlines():
            if "INFO" in line:
                continue
            if "^C" in line:
                continue
            if len(line)<40:
                continue
            try:  
                tokens=line.split()
            
                timestamp_second=int(tokens[0][:10])
                timestamp_microsecond=round(float(tokens[0][10:])/1000000000.0,6)
                timestamp = timestamp_second +timestamp_microsecond
            
                #print(line)
                x=float(tokens[1])
                y=float(tokens[2])
            
                q_x=float(tokens[4])
                q_y=float(tokens[5])
                q_z=float(tokens[6])
                q_w=float(tokens[7])
            
                log.append([timestamp,[x,y],[q_x,q_y,q_z,q_w]])
                #print(decimal.Decimal.from_float(timestamp))
            except:
                #print(line,"PARSING ERROR!!!")
                continue  
        return log

#get yaw from Quaternion q
def get_yaw(q):

   q_x,q_y,q_z,q_w=q[0],q[1],q[2],q[3]
   
   #wrong order: roll is yaw???
   #yaw = atan2(2.0*(q_y*q_z + q_w*q_x), q_w*q_w - q_x*q_x - q_y*q_y + q_z*q_z)
   #pitch = asin(-2.0*(q_x*q_z - q_w*q_y))
   #roll = atan2(2.0*(q_x*q_y + q_w*q_z), q_w*q_w + q_x*q_x - q_y*q_y - q_z*q_z)
   
   #roll  = atan2(2.0 * (q_z * q_y + q_w * q_x) , 1.0 - 2.0 * (q_x * q_x + q_y * q_y));
   #pitch = asin(2.0 * (q_y * q_w - q_z * q_x));
   yaw   = atan2(2.0 * (q_z * q_w + q_x * q_y) , - 1.0 + 2.0 * (q_w * q_w + q_x * q_x))
   return yaw
            
def get_yaws(log):
    return [get_yaw(x[2]) for x in log]
    
'''
import os
path='./exp/cse_building/level1_run2/'

for f in os.listdir(path):
    if 'AM' in f or 'PM' in f:
        f=path+f
        ig, (ax1, ax2) = plt.subplots(2)
        log=get_log(f)
        yaws=get_yaws(log)
        ax1.plot(yaws)

        ax2.scatter([x[1][0] for x in log],[x[1][1] for x in log])
        plt.show()
    
'''


#print(get_yaw([0,0,0,1]))


                
                

            