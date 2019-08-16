#!/bin/bash
# author: gfw-breaker

server_home=/usr/local/youtube-stream
git_url="https://raw.githubusercontent.com/gfw-breaker/ssr-accounts/master/README.md"

## install system dependencies
#yum install -y python python-pip vim sysstat
yum install -y  vim sysstat gcc zlib zlib-devel openssl openssl-devel
cd /usr/src
wget https://www.python.org/ftp/python/2.7.16/Python-2.7.16.tgz
tar xzf Python-2.7.16.tgz
cd Python-2.7.16
./configure
make altinstall

cd /usr/src
curl  https://bootstrap.pypa.io/get-pip.py | python2.7 -
## install python libraries
pip install flask pafy youtube-dl requests py_lru_cache

## deploy code
server_ip=$(curl -4 ip.sb)
#server_ip=$(ifconfig | grep "inet addr" | sed -n 1p | cut -d':' -f2 | cut -d' ' -f1)
#portal_ip=$(curl -s ${git_url} | grep 8888 | cut -d'/' -f3 | cut -d':' -f1)

sed -i "s/local_server_ip/${server_ip}/g" server.py
for f in $(ls templates/*.html); do
    sed -i "s/local_server_ip/${server_ip}/g" ${f}
done
mkdir -p ${server_home}
cp -R * ${server_home}

## enable and start service
chmod +x yt-stream
cp yt-stream /etc/init.d
chkconfig yt-stream on
service yt-stream start


