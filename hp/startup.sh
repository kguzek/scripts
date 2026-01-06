#!/bin/sh

set -e

pm2 resurrect
pm2 stop 1
pm2 start 1

cd /opt/harbor
sudo docker compose up -d
cd -

