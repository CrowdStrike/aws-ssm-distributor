#!/usr/bin/env sh

set -e

echo 'Uninstalling Falcon Sensor...'
while [ "$#" -ne 0 ]; do
  echo "$1"
  shift
done

echo 'Getting required config params ...'

# Error Hanldling
errout () {
    rc=$?
    echo "[ERROR] Falcon Sensor un-installation failed with $rc while executing '$2' on line $1"
    exit "$rc"
}

trap 'errout "${LINENO}" "${BASH_COMMAND}" ' EXIT

#Starting
sudo dpkg -r falcon-sensor $SSM_LINUX_UNINSTALLPARAMS

#Running clean up
echo "Running cleanup... "

# Verification
if ! pgrep falcon-sensor >/dev/null; then
  echo "Successfully finished uninstall..."
else
  echo "Uninstall failed..."
  exit 1
fi