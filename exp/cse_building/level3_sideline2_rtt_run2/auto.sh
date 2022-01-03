#!/bin/bash

sudo sntp -Ss 192.168.1.2 #1.2 is L machine. ntp server is running on 1.2

current_time=$(date +%s)
let duration=120

echo 'current time: ' ${current_time}
let future_time=current_time+33
echo 'future time: ' ${future_time}

echo 'python free_nav.py -i circle_clock1 -t' ${future_time}

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
		
	tell application "System Events" to keystroke "2" using command down
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
	
	
	tell application "System Events" to keystroke "5" using command down
	do script "cd ~/patlab" in window frontmost
    do script "python free_nav.py -i sideline2 -t ${future_time} -d ${duration}" in window frontmost
	delay 1
	
end tell
EOD
#sudo service ntp restart
#sudo ntpd -gq #force sync
#ntpq -p 

sleep ${duration+53}s
date +%s
scp turtlebot@192.168.1.2:~/patlab/data/* . && scp turtlebot@192.168.1.4:~/patlab/data/* .