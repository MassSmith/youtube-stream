#!/bin/bash

time=$(date "+%y-%m-%d %H:%M:%S")

## check CPU usage
#cpuPer=$(top -b -n 1 | grep Cpu | awk '{print $2}' | cut -d'.' -f1)

cpuPer=$(top -b -n 1  | grep python | sed -n 1p | awk '{print $9}' | cut -d'.' -f1)
echo "[$time] CPU usage: $cpuPer%" | tee -a sc.log

if [[ $cpuPer -gt 90 ]]; then
	echo "[$time] restarting server..." | tee -a sc.log
	/etc/init.d/yt-stream restart
	exit
fi

## check port
ip="localhost"
port="9999"      

(sleep 1
echo logout ) | telnet $ip $port > temp.txt

count=`grep -c Connected temp.txt`

if [ $count -gt 0 ]; then
	echo "[$time] Server port is listening..." | tee -a sc.log
else
	echo "[$time] restarting server..." | tee -a sc.log
	/etc/init.d/yt-stream restart
	exit
fi


