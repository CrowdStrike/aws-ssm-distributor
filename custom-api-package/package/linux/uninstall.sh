#!/bin/bash
echo 'Uninstalling Falcon Sensor...'

# Error Handling
function errout {
    rc="$?"
    echo "[ERROR] Falcon Sensor un-installation failed with $rc while executing '$2' on line $1"
    exit "$rc"
}

trap 'errout "${LINENO}" "${BASH_COMMAND}" ' ERR

# Echo to stderr
function errcho {
    >&2 echo ${@}
}

# Starting
aid="$(sudo /opt/CrowdStrike/falconctl -g --aid | awk -F\" '{print $2}')"
pkg="falcon-sensor"
echo "Running uninstall command for agent $aid ... "

if type dnf >/dev/null 2>&1; then
    sudo dnf remove -q -y "$pkg" || sudo rpm -e --nodeps "$pkg"
elif type yum >/dev/null 2>&1; then
    sudo yum remove -q -y "$pkg" || sudo rpm -e --nodeps "$pkg"
elif type zypper >/dev/null 2>&1; then
    sudo zypper --n remove -y "$pkg" || sudo rpm -e --nodeps "$pkg"
elif type apt >/dev/null 2>&1; then
    DEBIAN_FRONTEND=noninteractive sudo apt-get purge -y "$pkg"
else
   sudo rpm -e --nodeps "$pkg"
fi

# Verification
if ! pgrep falcon-sensor >/dev/null; then
    echo "Successfully finished uninstall..."
else
    errcho "Uninstall failed. Process falcon-sensor is still running."
    exit 1
fi