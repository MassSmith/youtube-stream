#!/bin/bash

ip_addr=$(ifconfig | grep "inet addr" | sed -n 1p | cut -d':' -f2 | cut -d' ' -f1)

for file in $(ls templates | grep html); do
	echo $file
 	cp /usr/local/youtube-stream/templates/$file templates/
	sed -i "s/$ip_addr/local_server_ip/g" templates/$file
done

