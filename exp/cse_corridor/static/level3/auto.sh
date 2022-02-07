#!/bin/bash
ntp_server=192.168.0.102
sudo sntp -Ss ${ntp_server} #1.2 is L machine. ntp server is running on 1.2

current_time=$(date +%s)

osascript <<EOD
tell application "System Events"
    tell process "Terminal"
        set frontmost to true
    end tell
end tell

-- launch , ekf, jlink, telnet, original folder

tell application "Terminal"
    activate
	
	--JLinkExe -Device NRF52840_XXAA -if SWD -speed 4000 -RTTTelnetPort 9201
	--JLinkExe -Device NRF52840_XXAA -if SWD -speed 4000 -RTTTelnetPort 9201
	
	tell application "System Events" to keystroke "4" using command down
	--do script "echo aaa_$1" in window frontmost
    do script "JLinkRTTClient -RTTTelnetPort 9201 |  ts '%.s' | tee ~/patlab/data/rtt_$1.log" in window frontmost
	delay 2
	
	tell application "System Events" to keystroke "9" using command down
	--do script "echo bbb_$1" in window frontmost
    do script "JLinkRTTClient -RTTTelnetPort 9201 |  ts '%.s' | tee ~/patlab/data/rtt2_$1.log" in window frontmost
	delay 2
	
end tell
EOD
#sudo service ntp restart
#sudo ntpd -gq #force sync
#ntpq -p 

#sleep ${duration+43}s
#scp turtlebot@192.168.0.102:~/patlab/data/* . && scp turtlebot@192.168.0.101:~/patlab/data/* .