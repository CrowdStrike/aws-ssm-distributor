#!/bin/bash
if pgrep  -u root falcon-sensor >/dev/null 2>&1 ; then
  echo "Falcon Sensor already installed... if you want to update or downgrade, please use Sensor Update Policies in the CrowdStrike console. Please see: https://falcon.crowdstrike.com/documentation/66/sensor-update-policies for more information."
  exit 0
fi

# Error Handling
function errout {
    rc="$?"
    echo "[ERROR] Falcon Sensor installation failed with $rc while executing '$2' on line $1"
    exit "$rc"
}

trap 'errout "${LINENO}" "${BASH_COMMAND}" ' ERR

# Echo to stderr
function errcho {
    >&2 echo ${@}
    exit 1
}

#For logging the commands we run.  NOTE: remember not to log URLs or tokens!
function RUN {
    echo "info: Running [$*]"
    "$@"
}

function EncodeQueryParameter {
  QueryParameter="$1"
  QueryParameter="${QueryParameter//+/%2b}"
  QueryParameter="${QueryParameter//\'/%27}"
  QueryParameter="${QueryParameter//:/%3a}"
  QueryParameter="${QueryParameter// /%20}"
  echo "$QueryParameter"
}

# Starting
echo 'Installing Falcon Sensor...'

# Parameters
INSTALLER_LOC="/tmp"

# Get config params
echo 'Getting required config params ...'

if [[ -z "$SSM_CS_CCID" ]]; then
    errcho "Missing required param SSM_CS_CCID. If the required parameter was passed to the package, ensure the target instance has a ssm agent version of 2.3.1550.0 or greater installed."
    exit 1
fi

proxy=""
proxy_name=""
proxy_port=""

CCID="${SSM_CS_CCID}"
INSTALLTOKEN="${SSM_CS_INSTALLTOKEN}"
SSM_CS_LINUX_INSTALLPARAMS="${SSM_CS_LINUX_INSTALLPARAMS:-}"
SSM_CS_LINUX_INSTALLPARAMS="${SSM_CS_LINUX_INSTALLPARAMS//\`/\\\`}"
SSM_CS_LINUX_INSTALLPARAMS="${SSM_CS_LINUX_INSTALLPARAMS//\$/\\\$}"
declare -a INSTALLPARAMS="($SSM_CS_LINUX_INSTALLPARAMS)"

for arg in "${INSTALLPARAMS[@]}"; do
    if [[ $arg == *"--aph="* ]]; then
        proxy_name="${arg#*=}"
        # Remove https/http
        proxy_name="${proxy_name//http*:'//'}"
        echo "Proxy host $proxy_name found in arguments"
    elif [[ $arg == *"--app="* ]]; then       
        proxy_port="${arg#*=}"
        echo "Proxy port $proxy_port found in arguments"
    fi
done

if [ -n "$proxy_name" ] && [ -n "$proxy_port" ]; then
    proxy="http://$proxy_name:$proxy_port"
elif [ -n "$proxy_name" ]; then
    proxy="http://$proxy_name"
fi

if [ -n "$proxy" ]; then
    proxy="${proxy//\"}"
    proxy="${proxy//\'}"
    echo "Proxy settings detected in arguments, using proxy: $proxy to communicate with the CrowdStrike Apis"
fi

userAgent="crowdstrike-custom-api-distributor-package/v2.0.0"

BASE_FILTER="<<SENSOR_DOWNLOAD_FILTER>>"
BASE_URL="https://${SSM_CS_HOST}/sensors/combined/installers/v1?limit=1&sort=version"

if [[ -n $SSM_CS_LINUX_VERSION ]]; then
    FILTER="${BASE_FILTER}+version:'${SSM_CS_LINUX_VERSION}'"
    URL="$BASE_URL&filter=$(EncodeQueryParameter "$FILTER")"
    echo "Version specified, grabbing the exact version: ${SSM_CS_LINUX_VERSION}. Filter: ${FILTER}"
else
    FILTER="${BASE_FILTER}"
    URL="$BASE_URL&offset=1&filter=$(EncodeQueryParameter "$FILTER")"
    echo "No version specified, grabbing the n-1 version that matches the base filter. Filter: ${FILTER}"
fi

# Getting installer
echo 'Getting installer sha256...'
if ! _resp="$(curl -x "$proxy" --retry 15 --retry-delay 10 -sf -H "Authorization: Bearer ${SSM_CS_AUTH_TOKEN}" -H "User-Agent: $userAgent" "$URL")" ; then
    errcho "Failed grabbing presigned url: $URL (exit status $?)..."
fi

if ! grep -q -e "name" -e "sha256" <<<"${_resp}"; then
    errcho "No sha256 or package name returned from api call: $_resp..."
fi

_fname="$(echo -n "${_resp}" | grep "name" | cut -d\" -f4)"
_sha256="$(echo -n "${_resp}" | grep "sha256" | cut -d\" -f4)"
_version="$(echo -n "${_resp}" | grep '"version"' | cut -d\" -f4)"

_binary_path="${INSTALLER_LOC}/${_fname}"
_download_url="https://$SSM_CS_HOST/sensors/entities/download-installer/v1?id=$_sha256"

echo "Downloading sensor binary matching sha256 $_sha256..."
if ! _resp="$(curl -x "$proxy" --retry 15 --retry-delay 10 -sf -H "Authorization: Bearer ${SSM_CS_AUTH_TOKEN}" -H "User-Agent: $userAgent" "$_download_url" -o "${_binary_path}")" ; then
    errcho "Failed downloading binary: $_download_url (exit status $?)..."
fi

sensor_install_dpkg()
{
    INSTALLER="$(realpath "$1")"
    RUN export DEBIAN_FRONTEND=noninteractive
    RUN apt-get update
    RUN apt-get -y install "$INSTALLER"
}

sensor_install_yum()
{
    INSTALLER="${1}"
    sudo rpm -qa | grep falcon-sensor || yum install "${INSTALLER}" -y
}

sensor_install_zypper()
{
    INSTALLER="${1}"
    sudo zypper -n --no-gpg-checks install "${INSTALLER}"
}

echo "Running install command (installing ${_binary_path}) sensor version: ${_version}..."

case "<<PACKAGE_MANAGER>>" in
  "dpkg")
    sensor_install_dpkg "${_binary_path}"
    ;;
  "yum")
    sensor_install_yum "${_binary_path}"
    ;;
  "zypper")
    sensor_install_zypper "${_binary_path}"
    ;;
  *)
    errcho "Unknown package manager."
    exit 1
    ;;
esac

if [[ "$INSTALLTOKEN" ]]; then
       echo "Passing installation token..."
       INSTALLPARAMS+=("--provisioning-token=$INSTALLTOKEN")
fi

INSTALLPARAMS+=("--cid=$CCID")

# Configure Falcon sensor
RUN /opt/CrowdStrike/falconctl -s "${INSTALLPARAMS[@]}"

# Start Falcon sensor
if [[ -L "/sbin/init" ]]
then
    RUN systemctl start falcon-sensor
else
    RUN sudo service falcon-sensor start
fi

# Sleep before verification
sleep 5s

# Verification
if ps -e | grep falcon-sensor &>/dev/null ;
then
    unset SSM_CS_INSTALLTOKEN
    unset SSM_CS_LINUX_INSTALLPARAMS
    unset SSM_CS_CCID
    unset SSM_CS_AUTH_TOKEN
    unset SSM_CS_HOST
    rm "${_binary_path}" || true
    echo "Falcon Sensor version ${_version} installed successfully."
else
    errcho "Installation failed. Process falcon-sensor is not running."
    exit 1
fi
