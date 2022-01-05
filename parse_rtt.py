#!/usr/bin/env python3
import matplotlib.pyplot as plt

def get_rssi_rtt(filename):
    rssi_list=[]
    
    with open(filename) as f:
        lines = f.readlines()
        
        for line in lines:
            if "### RSSI" in line:
                try:
                    tokens=line.split(':')[1].strip().split(',')
                    rssi, channel=int(tokens[0]), int(tokens[1])
                    timestamp=float(line.split()[0].strip())
                    rssi_list.append([timestamp, rssi, channel])
                    #print(rssi, channel, timestamp)
                except:
                    continue

                
    return rssi_list
    
    
def get_raw_rtt(filename):
    raw_list=[]
    
    with open(filename) as f:
        lines = f.readlines()
        
        i=0
        while i<len(lines):
            line = lines[i]
            if len(line)<=18 or line[18].isdigit()==False:
                i+=1
                continue
            try:
                tokens=[t.strip() for t in line.split()]
                timestamp=float(tokens[0])
                device_id=tokens[2].split(':')[-1]
                median=int(tokens[3])
                
                rawline1=lines[i+1]
                rawline2=lines[i+2]
                raw=[int(a) for a in rawline1.split()[1:] ]+[int(a) for a in rawline2.split()[1:]]
                
                if median > 500000 or median<0 or raw[0]==raw[-1]:
                    i+=1
                    continue
            
                #print(timestamp,device_id,median)
                #print(raw)           
                raw_list.append([timestamp,device_id,median,raw])
                
                i+=3
            except:
                i+=1
                #print('cannot parse:'+line)
                continue

    #due to buffer issues, there might be repeated entries??? 
            
    return raw_list
    
### TODO use more data
def merge_tottag(raw1,rssi1,raw2,rssi2):
        
    raw=[]
    rssi=[]
    
    #without clumping
    combined_raw=[]
    # step1: merge time
    i,j=0,0
    while len(combined_raw)<len(raw1)+len(raw2):
        
        # if 1 is depleted: add from 2
        if i==len(raw1):
            combined_raw.append(raw2[j])
            j+=1
            continue
        # if 2 is depleted: add from 1
        if j==len(raw2):
            combined_raw.append(raw1[i])
            i+=1
            continue
            
        # if neither is depleted       
        if raw1[i][0]<=raw2[j][0]:
            combined_raw.append(raw1[i])
            i+=1
        elif j<len(raw2):
            combined_raw.append(raw2[j])
            j+=1
    
    print('len raw1',len(raw1),'len raw2',len(raw2),'combined:',len(combined_raw))
    
    ### step2: clump
    ### TODO: handle both raw instead of just adding from one side?
    i=0
    while i<len(combined_raw):
        raw.append(combined_raw[i])      
        #the last one
        if i==len(combined_raw)-1:
            break
        # too close to each other
        if combined_raw[i+1][0]-combined_raw[i][0]<=0.05:
            i+=2
        else:
            i+=1
            
    print('clumped raw',len(raw))
    
    ### merge RSSI?    
    #without clumping
    combined_rssi=[]
    # step1: merge time
    i,j=0,0
    #print('len rssi1',len(rssi1),'len rssi2',len(rssi2),'combined:',len(combined_rssi))
    while len(combined_rssi)<len(rssi1)+len(rssi2):
        #print(i,j,len(combined_rssi))
        # if 1 is depleted: add from 2
        if i==len(rssi1):
            combined_rssi.append(rssi2[j])
            j+=1
            continue
        # if 2 is depleted: add from 1
        if j==len(rssi2):
            combined_rssi.append(rssi1[i])
            i+=1
            continue
            
        # if neither is depleted       
        if rssi1[i][0]<=rssi2[j][0]:
            combined_rssi.append(rssi1[i])
            i+=1
        elif j<len(rssi2):
            combined_rssi.append(rssi2[j])
            j+=1
    
    print('len rssi1',len(rssi1),'len rssi2',len(rssi2),'combined:',len(combined_rssi))
    
    ### step2: clump
    ### : handle both raw instead of just adding from one side?
    i=0
    while i<len(combined_rssi):
        rssi.append(combined_rssi[i])      
        #the last one
        if i==len(combined_rssi)-1:
            break
        # too close to each other
        if combined_rssi[i+1][0]-combined_rssi[i][0]<=0.05:
            i+=2
        else:
            i+=1
            
    print('clumped',len(rssi))
       
    return (raw,rssi)    
#get_raw('rtt2.log')