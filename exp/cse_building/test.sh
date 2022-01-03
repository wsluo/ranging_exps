current_time=$(date +%s)

echo 'current time: ' ${current_time}
let future_time=current_time+40
echo 'future time: ' ${future_time}

#wireshark -i '/dev/cu.usbmodemD9F38B854E611' -k -S

echo 'python free_nav.py -i clock2 -t' ${future_time}
echo 'python free_nav.py -i counter2 -t' ${future_time}

#ssh -t turtlebot@192.168.1.4  "date +%s"

#python free_nav.py -i clock2 -t