#!/bin/bash
#
# Distributor package installer - Amazon Linux 2 / RPM based distros
#

# Check if service is running and if it is exit 0.
if pgrep -u root falcon-sensor >/dev/null 2>&1 ; then
  echo "Falcon Sensor already installed... if you want to update or downgrade, please use Sensor Update Policies in the CrowdStrike console. Please see: https://falcon.crowdstrike.com/documentation/66/sensor-update-policies for more information."
  exit 0
fi

filename="falcon-sensor.rpm"

# Install package
rpm -qa | grep falcon-sensor || yum install "$filename" -y

# Configure sensor
echo "/opt/CrowdStrike/falconctl -s -f --cid=$SSM_CID $SSM_LINUX_INSTALLPARAMS"
/opt/CrowdStrike/falconctl -s -f --cid="$SSM_CID" $SSM_LINUX_INSTALLPARAMS

# Restart service
systemctl restart falcon-sensor

# Verify service is running
if pgrep -u root falcon-sensor >/dev/null 2>&1 ; then
  echo "Falcon Sensor successfully installed and running"
  exit 0
else
  echo "Installation failed. Process falcon-sensor is not running."
  exit 1
fi
