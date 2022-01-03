#!/usr/bin/env python3
import matplotlib.pyplot as plt

def get_rssi(filename):
    rssi_list=[]
    
    with open(filename) as f:
        lines = f.readlines()
        
        for line in lines:
            if "RSSI" in line:
                try:
                    tokens=line.split(':')[1].strip().split(',')
                    rssi, channel, timestamp=int(tokens[0]), int(tokens[1]), int(tokens[2])
                    rssi_list.append([timestamp, rssi, channel])
                    #print(rssi, channel, timestamp)
                except:
                    continue

                
    return rssi_list
    
    
def get_raw(filename):
    raw_list=[]
    
    with open(filename) as f:
        lines = f.readlines()
        
        for line in lines:
            if line[0]=='#':
                continue
            try:
                tokens=[t.strip() for t in line.split()]
                timestamp=int(tokens[0])
                device_id=tokens[1].split(':')[-1]
                median=int(tokens[2])
                raw=[int(tokens[i]) for i in range(3,len(tokens))]
                
                if median > 500000:
                    continue
            
                #print(timestamp,device_id,median)
                #print(raw)           
                raw_list.append([timestamp,device_id,median,raw])
            except:
                print('cannot parse:'+line)
                continue

            
    return raw_list
                

#get_raw('./29@01-09.LOG')              