#!/usr/bin/env python3
import matplotlib.pyplot as plt


#convert  x-right, y-up coordinate to ros coordinates
def convert_to_ros_coordinate(C):
    converted=[]
    for c in C:
        converted.append([c[1], -c[0], 0])
    return converted    

def print_waypoints(points):
    for p in points:
        print(' '.join([str(x) for x in p]))  
    print('')  
    
def mirror(C):
    return [[x[0],-x[1],x[2]] for x in C]
    
def view(route):
    X=[0]+[x[0] for x in route]
    Y=[0]+[x[1] for x in route]
    plt.plot(X,Y)
    plt.show()
    
def view_pair(route1,route2):
    X1=[0]+[x[0] for x in route1]
    Y1=[0]+[x[1] for x in route1]
    plt.plot(X1,Y1,label='left')
    X2=[0]+[x[0] for x in route2]
    Y2=[0]+[x[1] for x in route2]
    plt.plot(X2,Y2,label='right')
    plt.legend()
    plt.show()
        
#clockwise1_coordinate=[[0,1,0],[1,1,0],[1,0,0],[0,0,0]]   
#convert_to_ros_coordinate(clockwise1_coordinate)

#cclockwise1_coordinate=[[0,1,0],[-1,1,0],[-1,0,0],[0,0,0]] 
#convert_to_ros_coordinate(cclockwise1_coordinate)        
    
#test_bot.txt: counterclock 1m squares    
'''  
log=get_log('test_bot.txt')
plt.scatter([x[1][0] for x in log],[x[1][1] for x in log])
plt.show()
yaws=get_yaws(log)
plt.plot(yaws)
plt.show()
'''

new_counter=[
[1.5, 0, 0],    
[1.5, 1, 0],
[0.5, 1, 0],
[0.5, 0, 0],    
]
print('new_counterclock1 (on right side)')
counter1=convert_to_ros_coordinate(new_counter)
print_waypoints(counter1)
#view(new_counter)

new_clock=[
[-1.5,0,0],
[-1.5,1,0],
[-0.5,1,0],
[-0.5,0,0],    
]

print('new_clock1 (on left side)')
clock1=mirror(convert_to_ros_coordinate(new_counter))
print_waypoints(clock1)
#view(new_clock)
#view_pair(new_counter,new_clock)

new_counter=[
[2.5, 0, 0],    
[2.5, 2, 0],
[0.5, 2, 0],
[0.5, 0, 0],    
]
print('new_counterclock2 (on right side)')
counter2=convert_to_ros_coordinate(new_counter)
print_waypoints(counter2)

new_clock=[
[-2.5,0,0],
[-2.5,2,0],
[-0.5,2,0],
[-0.5,0,0],    
]

print('new_clock2 (on left side)')
clock2=mirror(convert_to_ros_coordinate(new_counter))
print_waypoints(clock2)


new_counter=[
[3.5, 0, 0],    
[3.5, 3, 0],
[0.5, 3, 0],
[0.5, 0, 0],    
]
print('new_counterclock3 (on right side)')
counter3=convert_to_ros_coordinate(new_counter)
print_waypoints(counter3)

new_clock=[
[-3.5,0,0],
[-3.5,3,0],
[-0.5,3,0],
[-0.5,0,0],    
]

print('new_clock3 (on left side)')
clock3=mirror(convert_to_ros_coordinate(new_counter))
print_waypoints(clock3)

#centered
circle_clock=[
[-1+0.3625,0,0],
[0+0.3625,1,0],
[1+0.3625,0,0],
[0+0.3625,-1,0]   
]

print('circle_clock1')
circle_clock1=convert_to_ros_coordinate(circle_clock)
print_waypoints(circle_clock1)

#side line
circle_clock=[
[-0.5,0,0],
[-0.5,2,0],
]

print('sideline2')
sideline2=convert_to_ros_coordinate(circle_clock)
print_waypoints(sideline2)
#f = open('./exp/test.log','w')
#f.write("test"])
#f.close()

view_pair(clock2, counter2)
