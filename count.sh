#!/bin/bash

grep "vv=" /usr/local/youtube-stream/access.log  | cut -d'&' -f1 | grep -v werk | awk '{print $7","$1}' | sed 's/\/vs?vv=//g' | sort | uniq | cut -d',' -f1 | uniq -c | sort -k1nr | awk '{print $1":"$2}' > vs.txt

rm vrank.txt

for line in $(cat vs.txt); do
	count=$(echo $line | cut -d':' -f1)
	v=$(echo $line | cut -d':' -f2)
	url="https://www.youtube.com/watch?v=$v"
	#echo $url
	title=$(youtube-dl -e $url)
	#youtube-dl -e $url
	echo -e "$count\t$title" | tee -a vrank.txt
done


