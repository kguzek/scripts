#!/bin/sh

pm2 resurrect
cd /opt/harbor
sudo docker compose up -d

