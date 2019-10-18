#!/bin/bash
# author: gfw-breaker
#CentOS 7

server_home=/usr/local/youtube-stream
#git_url="https://raw.githubusercontent.com/gfw-breaker/ssr-accounts/master/README.md"

## install system dependencies
#yum install -y python python-pip vim sysstat
yum install -y  sysstat gcc zlib zlib-devel openssl openssl-devel
cd /usr/src
wget https://www.python.org/ftp/python/2.7.16/Python-2.7.16.tgz
tar xzf Python-2.7.16.tgz
cd Python-2.7.16
./configure
make altinstall

cd /usr/src
curl https://bootstrap.pypa.io/get-pip.py | python2.7 -
## install python libraries
pip install flask pafy youtube-dl requests py_lru_cache Flask-APScheduler supervisor

cd /root/youtube-stream
## deploy code
#server_ip=$(curl -4 ip.sb)
#server_ip=$(ifconfig | grep "inet addr" | sed -n 1p | cut -d':' -f2 | cut -d' ' -f1)
#portal_ip=$(curl -s ${git_url} | grep 8888 | cut -d'/' -f3 | cut -d':' -f1)

#sed -i "s/local_server_ip/${server_ip}/g" server.py
#for f in $(ls templates/*.html); do
#    sed -i "s/local_server_ip/${server_ip}/g" ${f}
#done
echo "{}">cache.json
mkdir -p ${server_home}
cp -R * ${server_home}

## enable and start service
#chmod +x yt-stream
#cp yt-stream /etc/init.d
#chkconfig yt-stream on
#service yt-stream start

cd /root
wget https://getcaddy.com -O getcaddy
chmod +x getcaddy

#sudo ./getcaddy personal http.ipfilter,http.ratelimit,http.cache,hook.service
./getcaddy personal http.ipfilter,http.ratelimit,http.cache,tls.dns.cloudflare,hook.service

mkdir -p /etc/caddy
mkdir -p /var/log/caddy
mkdir -p /var/www/video
mkdir -p /var/www/video/cache
cat <<EOF >/etc/caddy/Caddyfile
:80 {
     root /var/www/
     log /var/log/caddy/access.log {
         rotate_size 3 # Rotate a log when it reaches 3 MB
         rotate_age  365  # Keep rotated log files for 365 days
         rotate_keep 1000  # Keep at most 1000 rotated log files
         rotate_compress # Compress rotated log files in gzip format
     }
     errors /var/log/caddy/errors.log
     tls off
     gzip
     proxy / localhost:9999 {
        transparent
        except /video
     }
}
EOF
caddy -service install -agree -email www@youtube.org -conf /etc/caddy/Caddyfile
caddy -service start

echo_supervisord_conf
echo_supervisord_conf > /etc/supervisord.conf
mkdir /etc/supervisor.d
cat <<EOF >>/etc/supervisord.conf
[include]
files = /etc/supervisor.d/*.conf
EOF

cat <<EOF >/etc/supervisor.d/youtube_streams.conf
[program:youtube-streams]
command=/usr/local/bin/python2.7 -u /usr/local/youtube-stream/server.py
EOF

cat <<EOF >/usr/lib/systemd/system/supervisord.service
[Unit]
Description=Process Monitoring and Control Daemon

[Service]
Type=forking
ExecStart=/usr/local/bin/supervisord -c /etc/supervisord.conf 
ExecStop=/usr/local/bin/supervisorctl shutdown
ExecReload=/usr/local/bin/supervisorctl reload
killMode=process
Restart=on-failure
RestartSec=42s

[Install]
WantedBy=multi-user.target
EOF

systemctl start supervisord
systemctl enable supervisord
