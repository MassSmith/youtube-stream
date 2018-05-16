#!/bin/bash
# author: gfw-breaker

server_home=/usr/local/youtube-stream

## install system dependencies
yum install -y python python-pip vim sysstat

## install python libraries
pip install flask pafy youtube-dl requests py_lru_cache

## deploy code
mkdir -p ${server_home}
cp -R * ${server_home}

ipaddr=$(ifconfig | grep "inet addr" | sed -n 1p | cut -d':' -f2 | cut -d' ' -f1)
sed -i "s/localhost/$ipaddr/g" ${server_home}/upstreams.json

## setup monitor
cp check.sh /root
cat >> /var/spool/cron/root << EOF
* * * * * /root/check.sh
EOF

## enable and start service
chmod +x yt-stream
cp yt-stream /etc/init.d
chkconfig yt-stream on
service yt-stream restart


