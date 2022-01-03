#!/bin/bash

sudo sntp -Ss 192.168.1.2

current_time=$(date +%s)
let duration=200

echo 'current time: ' ${current_time}
let future_time=current_time+40
echo 'future time: ' ${future_time}

echo 'python free_nav.py -i clock2 -t' ${future_time}
echo 'python free_nav.py -i counter2 -t' ${future_time}

osascript <<EOD
tell application "System Events"
    tell process "Terminal"
        set frontmost to true
    end tell
end tell

-- launch , ekf, jlink, telnet, original folder

tell application "Terminal"
    activate
	
	
	tell application "System Events" to keystroke "1" using command down
    do script "roslaunch turtlebot_bringup minimal.launch" in window frontmost
	delay 6
	
	tell application "System Events" to keystroke "6" using command down
    do script "roslaunch turtlebot_bringup minimal.launch" in window frontmost	
	delay 6
	
	tell application "System Events" to keystroke "2" using command down
    do script "roslaunch robot_pose_ekf patlab_robot_pose_ekf.launch" in window frontmost
	delay 1
	
	tell application "System Events" to keystroke "7" using command down
    do script "roslaunch robot_pose_ekf patlab_robot_pose_ekf.launch" in window frontmost
	delay 1
	
	--JLinkExe -Device NRF52840_XXAA -if SWD -speed 4000 -RTTTelnetPort 9201
	--JLinkExe -Device NRF52840_XXAA -if SWD -speed 4000 -RTTTelnetPort 9201
	
	tell application "System Events" to keystroke "4" using command down
    do script "JLinkRTTClient -RTTTelnetPort 9201 |  ts '%.s' | tee ~/patlab/data/rtt_${future_time}.log" in window frontmost
	delay 2
	
	tell application "System Events" to keystroke "9" using command down
    do script "JLinkRTTClient -RTTTelnetPort 9201 |  ts '%.s' | tee ~/patlab/data/rtt2_${future_time}.log" in window frontmost
	delay 2
	
	tell application "System Events" 
		key code 48 using control down --48 is the keycode for tab. tab+ctrl: move to next tab. since we cannot use 10
	end 
	do script "cd ~/patlab" in window frontmost
	do script "python free_nav.py -i counter2 -t ${future_time} -d ${duration}" in window frontmost
	delay 1
	
	tell application "System Events" to keystroke "5" using command down
	do script "cd ~/patlab" in window frontmost
    do script "python free_nav.py -i clock2 -t ${future_time} -d ${duration}" in window frontmost
	delay 1
	
end tell
EOD

#sleep ${duration+10}s
#scp turtlebot@192.168.1.2:~/patlab/data/* . && scp turtlebot@192.168.1.4:~/patlab/data/* .
### remove the data files after that~