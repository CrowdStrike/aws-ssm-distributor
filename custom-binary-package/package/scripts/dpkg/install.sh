#!/bin/bash
#
# Distributor package installer - Ubuntu based distros
#
filename="falcon-sensor.deb"

install() {
  apt-get install -y libnl-3-200 libnl-genl-3-200
  export DEBIAN_FRONTEND=noninteractive
  dpkg -i "$1"
  echo "/opt/CrowdStrike/falconctl -s -f --cid=$2 $3" 
  /opt/CrowdStrike/falconctl -s -f --cid="$2" $3
  systemctl restart falcon-sensor
  rm $1
}

if pgrep  -u root falcon-sensor >/dev/null 2>&1 ; then
  echo "sensor is already running... exiting"
  exit 0
fi

install $filename $SSM_CID $SSM_LINUX_INSTALLPARAMS