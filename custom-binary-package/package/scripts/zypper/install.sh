#!/usr/bin/env bash
filename="falcon-sensor.rpm"

install() {
  INSTALLER="${1}"
  zypper -n --no-gpg-checks install "${INSTALLER}"
  echo "/opt/CrowdStrike/falconctl -s -f --cid=$2 $3" 
  /opt/CrowdStrike/falconctl -s -f --cid="$2" $3
  rm $1
}

if pgrep  -u root falcon-sensor >/dev/null 2>&1 ; then
  echo "sensor is already running... exiting"
  exit 0
fi

install $filename $SSM_CID $SSM_LINUX_INSTALLPARAMS