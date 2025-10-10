#!/bin/sh

pm2 resurrect
cd /opt/harbor
sudo docker compose up -d
pm2 stop 1
pm2 start 1

