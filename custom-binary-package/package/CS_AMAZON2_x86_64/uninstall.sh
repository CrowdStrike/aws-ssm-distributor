#!/usr/bin/env bash

echo 'Uninstalling Falcon Sensor...'
while (( "$#" )); do
  echo "$1"
  shift
done
echo 'Getting required config params ...'

# Error Hanldling
function errout {
    rc=$?
    echo "[ERROR] Falcon Sensor un-installation failed with $rc while executing '$2' on line $1"
    exit $rc
}

trap 'errout "${LINENO}" "${BASH_COMMAND}" ' ERR

sudo yum -y remove falcon-sensor $LINUX_UNINSTALLPARAMS

echo "Running cleanup... "

# Verification
if ! pgrep falcon-sensor >/dev/null; then
  echo "Successfully finished uninstall..."
else
  echo "Uninstall failed..."
  exit 1
fi