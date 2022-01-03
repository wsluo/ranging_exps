#tell application "Terminal" to activate
#tell application "System Events" to keystroke "1" using command down
#do script "echo hello"
-- https://apple.stackexchange.com/questions/103621/run-applescript-from-bash-script


tell application "System Events"
    tell process "Terminal"
        set frontmost to true
    end tell
end tell

tell application "Terminal"
    activate
	tell application "System Events" to keystroke "1" using command down
    do script "echo aaa" in window frontmost
	
	tell application "System Events" to keystroke "2" using command down
    do script "echo bbb" in window frontmost
	
	tell application "System Events" 
		key code 48 using control down --48 is the keycode for tab. tab+ctrl: move to next tab
		keystroke "r" 
		keystroke return
	end 
	
	delay 2 --has to delay so that the other command can be received?
	
	
	tell application "System Events" to keystroke "4" using command down
    do script "echo yyy" in window frontmost
	
end tell