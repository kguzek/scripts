#!/bin/sh

set -e

# prompt for password at start rather than after running pm2
sudo -v

source "$HOME/.nvm/nvm.sh"
pm2 resurrect
pm2 stop 1
pm2 start 1

cd /opt/harbor
sudo docker compose up -d
cd -

