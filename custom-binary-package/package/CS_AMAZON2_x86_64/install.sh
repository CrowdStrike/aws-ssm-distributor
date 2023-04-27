#!/bin/bash
#
# Distributor package installer - Amazon Linux 2 / RPM based distros
#
filename="falcon-sensor.rpm"

rpmInstall() {
  yum install libnl -y
  rpm -ivh "$1"
  echo "/opt/CrowdStrike/falconctl -s -f --cid=$2 $3" >>log.txt
  /opt/CrowdStrike/falconctl -s -f --cid="$2" $3
  systemctl restart falcon-sensor
  rm $1
}

if pgrep  -u root falcon-sensor >/dev/null 2>&1 ; then
  echo "sensor is already running... exiting"
  exit 0
fi

rpmInstall $filename $CID $LINUX_INSTALLPARAMS