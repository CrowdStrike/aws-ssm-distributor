import json

# import cfnresponse
import boto3
import os
import botocore
from os.path import basename
from botocore.config import Config
import time
import zipfile
import hashlib
import logging

logger = logging.getLogger()
logger.setLevel("INFO")

config = Config(retries={"max_attempts": 10, "mode": "standard"})


def handler(event, context):
    enabled_regions = []
    missing_regions = []

    package_name = event["ResourceProperties"].get(
        "DistributorPackageName", "CrowdStrike-FalconSensor"
    )
    package_verison = event["ResourceProperties"].get(
        "DistributorPackageVersion", "v1.0.0"
    )
    s3_bucket_name = event["ResourceProperties"].get("S3BucketName")

    if s3_bucket_name is None:
        fail_response("S3BucketName is required.")

    try:
        account_client = boto3.client("account", config=config)
        region_paginator = account_client.get_paginator("list_regions")
        region_iterator = region_paginator.paginate(
            RegionOptStatusContains=["ENABLED", "ENABLED_BY_DEFAULT"]
        )

        for page in region_iterator:
            for region in page["Regions"]:
                enabled_regions.append(region["RegionName"])

        for region in enabled_regions:
            if event["RequestType"] in ["Create", "Update"]:
                ssm_client = boto3.client("ssm", region_name=region, config=config)
                try:
                    ssm_client.describe_document(Name=package_name)
                    logger.info(
                        f"Distributor package: {package_name} already exists in {region}"
                    )
                except ssm_client.exceptions.InvalidDocument:
                    logger.info(
                        f"Distributor package: {package_name} is missing in {region}"
                    )
                    missing_regions.append(region)
                except botocore.exceptions.ClientError as error:
                    raise error

        if len(missing_regions) > 0:
            s3_path = f"{package_name}/{package_verison}"
            s3_dir, manifest = create_local_packages(version=package_verison)
            sync_s3(s3_dir, s3_bucket_name, s3_path)

            for region in missing_regions:
                logger.info(
                    f"Creating distribtor package: {package_name} {package_verison} in {region}"
                )
                ssm_client = boto3.client("ssm", region_name=region, config=config)
                create_distributor_package(
                    client=ssm_client,
                    package_name=package_name,
                    manifest=manifest,
                    version=package_verison,
                    bucket=s3_bucket_name,
                    s3_path=s3_path,
                )

        while len(missing_regions) > 0:
            for region in missing_regions:
                ssm_client = boto3.client("ssm", region_name=region, config=config)
                try:
                    document = ssm_client.describe_document(Name=package_name)[
                        "Document"
                    ]
                    status = document["Status"]
                    if status == "Active":
                        logger.info(
                            f"Distributor package: {package_name} {package_verison} successfully created in {region}."
                        )
                        missing_regions.remove(region)
                        continue
                    elif status == "Failed":
                        status_information = document["StatusInformation"]
                        fail_response(
                            f"Distributor package: {package_name} {package_verison} failed during creation in {region}. Reason: {status_information}"
                        )
                    else:
                        logger.info(
                            f"Distributor package: {package_name} {package_verison} is still being created in {region}."
                        )
                except ssm_client.exceptions.InvalidDocument:
                    continue
                except botocore.exceptions.ClientError as error:
                    raise error

            time.sleep(5)

        if missing_regions == 0:
            msg = (
                f"Successfully created {package_name} {package_verison} in all regions."
            )
            logger.info(msg)
            # cfnresponse.send(event, context, cfnresponse.SUCCESS, {"msg": msg})

        else:
            fail_response(
                f"The following regions are still missing the distributor package: {"".join(missing_regions)}"
            )

    except Exception as e:
        fail_response(e)


def fail_response(e):
    responseData = {"error": str(e)}
    logging.error(e)
    # cfnresponse.send(event, context, cfnresponse.FAILED, responseData)
    print(responseData)


def sync_s3(s3_dir, s3_bucket_name, s3_path):
    s3_client = boto3.client("s3")
    for root, _, files in os.walk(s3_dir):
        for file in files:
            file_name = os.path.join(root, file)
            logging.info(f"Uploading {file_name} to {s3_bucket_name}.")
            s3_client.upload_file(
                file_name, s3_bucket_name, os.path.join(s3_path, file_name)
            )


def create_distributor_package(
    client, package_name, manifest, version, bucket, s3_path
):
    client.create_document(
        Name=package_name,
        VersionName=version,
        DocumentType="Package",
        Content=json.dumps(manifest),
        DocumentFormat="JSON",
        Attachments=[
            {
                "Key": "SourceUrl",
                "Values": [f"s3://{bucket}/{s3_path}"],
            }
        ],
    )


def create_local_packages(version):
    build_dir = "/tmp/builds"
    s3_dir = "/tmp/s3"
    manifest_data = {
        "schemaVersion": "2.0",
        "publisher": "Crowdstrike Inc.",
        "description": "The CrowdStrike Falcon cloud platform helps successfully stop breaches, all via a single lightweight agent. Learn how to protect your AWS environment with CrowdStrike at https://github.com/CrowdStrike/aws-ssm-distributor/tree/main/custom-api-package",
        "version": version,
        "packages": {},
        "files": {},
    }

    for platform in DISTROS:
        if platform == "linux":
            install_script = linux_install_script
            uninstall_script = linux_uninstall_script
            file_ext = ".sh"
        else:
            install_script = windows_install_script
            uninstall_script = windows_uninstall_script
            file_ext = ".ps1"

        for distro in DISTROS[platform]:
            name = distro["name"]
            version = distro["version"]
            arch = distro["arch"]
            logger.info("Creating package for {} {} {}".format(name, version, arch))
            distro_dir = "{}{}-{}".format(
                name, version.replace(".*", "").replace("_any", ""), arch
            )
            package_dir = f"{build_dir}/{distro_dir}"

            write_package_script(
                install_script,
                f"{package_dir}/install{file_ext}",
                distro["filter"],
                distro["package_manager"],
            )

            write_package_script(
                uninstall_script,
                f"{package_dir}/uninstall{file_ext}",
                distro["filter"],
                distro["package_manager"],
            )

            zip_file_path = zip_package(
                package_dir=package_dir, zip_name=distro_dir, build_dir=build_dir
            )
            zip_file_name = os.path.basename(zip_file_path)

            if not name in manifest_data["packages"]:
                manifest_data["packages"][name] = {}
            if not version in manifest_data["packages"][name]:
                manifest_data["packages"][name][version] = {}
            if not arch in manifest_data["packages"][name][version]:
                manifest_data["packages"][name][version][arch] = {}

            manifest_data["packages"][name][version][arch] = {"file": zip_file_name}
            manifest_data["files"][zip_file_name] = {
                "checksums": {"sha256": get_digest(zip_file_path)}
            }

            with open(os.path.join(s3_dir, "manifest.json"), "w") as file:
                json.dump(manifest_data, file, indent=4)

            return s3_dir, manifest_data


# cfnresponse.send(event, context, cfnresponse.SUCCESS, response, "Waiter-"+id)


def get_digest(file):
    h = hashlib.sha256()

    with open(file, "rb") as file:
        while True:
            chunk = file.read(h.block_size)
            if not chunk:
                break
            h.update(chunk)
        return h.hexdigest()


def write_package_script(script, dest, filter, package_manager):
    directory = os.path.dirname(dest)
    if directory:
        os.makedirs(directory, exist_ok=True)
    script = script.replace(FILTER_KEYWORD, filter).replace(
        PACKAGE_MANAGER_KEYWORD, package_manager
    )
    with open(dest, "wt") as fout:
        fout.write(script)


def zip_package(package_dir, zip_name, build_dir):
    zip_package_name = f"{build_dir}/s3/{zip_name}.zip"
    logger.info(f"Creating zip file: {zip_package_name}")
    directory = os.path.dirname(zip_package_name)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with zipfile.ZipFile(zip_package_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, basename(file_path))

    return zip_package_name


FILTER_KEYWORD = "<<SENSOR_DOWNLOAD_FILTER>>"
PACKAGE_MANAGER_KEYWORD = "<<PACKAGE_MANAGER>>"

DISTROS = {
    "linux": [
        {
            "name": "amazon",
            "version": "2",
            "arch": "x86_64",
            "package_manager": "yum",
            "filter": "os:'Amazon Linux'+os_version:'2'+platform:'linux'",
        },
        {
            "name": "amazon",
            "version": "2",
            "arch": "arm64",
            "package_manager": "yum",
            "filter": "os:'Amazon Linux'+os_version:'2 - arm64'+platform:'linux'",
        },
        {
            "name": "amazon",
            "version": "2023",
            "arch": "x86_64",
            "package_manager": "yum",
            "filter": "os:'Amazon Linux'+os_version:'2023'+platform:'linux'",
        },
        {
            "name": "amazon",
            "version": "2023",
            "arch": "arm64",
            "package_manager": "yum",
            "filter": "os:'Amazon Linux'+os_version:'2023 - arm64'+platform:'linux'",
        },
        {
            "name": "redhat",
            "version": "7.*",
            "arch": "x86_64",
            "package_manager": "yum",
            "filter": "os:'*RHEL*'+os_version:'7'+platform:'linux'",
        },
        {
            "name": "redhat",
            "version": "8.*",
            "arch": "x86_64",
            "package_manager": "yum",
            "filter": "os:'*RHEL*'+os_version:'8'+platform:'linux'",
        },
        {
            "name": "redhat",
            "version": "8.*",
            "arch": "arm64",
            "package_manager": "yum",
            "filter": "os:'*RHEL*'+os_version:'8 - arm64'+platform:'linux'",
        },
        {
            "name": "redhat",
            "version": "9.*",
            "arch": "x86_64",
            "package_manager": "yum",
            "filter": "os:'*RHEL*'+os_version:'9'+platform:'linux'",
        },
        {
            "name": "redhat",
            "version": "9.*",
            "arch": "arm64",
            "package_manager": "yum",
            "filter": "os:'*RHEL*'+os_version:'9 - arm64'+platform:'linux'",
        },
        {
            "name": "almalinux",
            "version": "8.*",
            "arch": "x86_64",
            "package_manager": "yum",
            "filter": "os:'*RHEL*'+os_version:'8'+platform:'linux'",
        },
        {
            "name": "almalinux",
            "version": "8.*",
            "arch": "arm64",
            "package_manager": "yum",
            "filter": "os:'*RHEL*'+os_version:'8 - arm64'+platform:'linux'",
        },
        {
            "name": "almalinux",
            "version": "9.*",
            "arch": "arm64",
            "package_manager": "yum",
            "filter": "os:'*RHEL*'+os_version:'9 - arm64'+platform:'linux'",
        },
        {
            "name": "almalinux",
            "version": "9.*",
            "arch": "x86_64",
            "package_manager": "yum",
            "filter": "os:'*RHEL*'+os_version:'9'+platform:'linux'",
        },
        {
            "name": "rocky",
            "version": "8.*",
            "arch": "x86_64",
            "package_manager": "yum",
            "filter": "os:'*RHEL*'+os_version:'8'+platform:'linux'",
        },
        {
            "name": "rocky",
            "version": "8.*",
            "arch": "arm64",
            "package_manager": "yum",
            "filter": "os:'*RHEL*'+os_version:'8 - arm64'+platform:'linux'",
        },
        {
            "name": "rocky",
            "version": "9.*",
            "arch": "arm64",
            "package_manager": "yum",
            "filter": "os:'*RHEL*'+os_version:'9 - arm64'+platform:'linux'",
        },
        {
            "name": "rocky",
            "version": "9.*",
            "arch": "x86_64",
            "package_manager": "yum",
            "filter": "os:'*RHEL*'+os_version:'9'+platform:'linux'",
        },
        {
            "name": "centos",
            "version": "7.*",
            "arch": "x86_64",
            "package_manager": "yum",
            "filter": "os:'*CentOS*'+os_version:'7'+platform:'linux'",
        },
        {
            "name": "centos",
            "version": "8.*",
            "arch": "x86_64",
            "package_manager": "yum",
            "filter": "os:'*CentOS*'+os_version:'8'+platform:'linux'",
        },
        {
            "name": "centos",
            "version": "8.*",
            "arch": "arm64",
            "package_manager": "yum",
            "filter": "os:'*CentOS*'+os_version:'8 - arm64'+platform:'linux'",
        },
        {
            "name": "oracle",
            "version": "6.*",
            "arch": "x86_64",
            "package_manager": "yum",
            "filter": "os:'*Oracle*'+os_version:'6'+platform:'linux'",
        },
        {
            "name": "oracle",
            "version": "7.*",
            "arch": "x86_64",
            "package_manager": "yum",
            "filter": "os:'*Oracle*'+os_version:'7'+platform:'linux'",
        },
        {
            "name": "oracle",
            "version": "8.*",
            "arch": "x86_64",
            "package_manager": "yum",
            "filter": "os:'*Oracle*'+os_version:'8'+platform:'linux'",
        },
        {
            "name": "suse",
            "version": "12.*",
            "arch": "x86_64",
            "package_manager": "zypper",
            "filter": "os:'*SLES*'+os_version:'12'+os_version:!~'zLinux'+platform:'linux'",
        },
        {
            "name": "suse",
            "version": "15.*",
            "arch": "x86_64",
            "package_manager": "zypper",
            "filter": "os:'*SLES*'+os_version:'15'+os_version:!~'zLinux'+platform:'linux'",
        },
        {
            "name": "ubuntu",
            "version": "16.*",
            "arch": "x86_64",
            "package_manager": "dpkg",
            "filter": "os:'*Ubuntu*'+os_version:'*16*'+os_version:!'*arm64*'+os_version:!~'zLinux'+platform:'linux'",
        },
        {
            "name": "ubuntu",
            "version": "18.*",
            "arch": "x86_64",
            "package_manager": "dpkg",
            "filter": "os:'*Ubuntu*'+os_version:'*18*'+os_version:!'*arm64*'+os_version:!~'zLinux'+platform:'linux'",
        },
        {
            "name": "ubuntu",
            "version": "20.*",
            "arch": "x86_64",
            "package_manager": "dpkg",
            "filter": "os:'*Ubuntu*'+os_version:'*20*'+os_version:!'*arm64*'+os_version:!~'zLinux'+platform:'linux'",
        },
        {
            "name": "ubuntu",
            "version": "22.*",
            "minor_version": "*",
            "arch": "x86_64",
            "package_manager": "dpkg",
            "filter": "os:'*Ubuntu*'+os_version:'*22*'+os_version:!'*arm64*'+os_version:!~'zLinux'+platform:'linux'",
        },
        {
            "name": "ubuntu",
            "version": "24.*",
            "minor_version": "*",
            "arch": "x86_64",
            "package_manager": "dpkg",
            "filter": "os:'*Ubuntu*'+os_version:'*24*'+os_version:!'*arm64*'+os_version:!~'zLinux'+platform:'linux'",
        },
        {
            "name": "ubuntu",
            "version": "24.*",
            "arch": "arm64",
            "package_manager": "dpkg",
            "filter": "os:'*Ubuntu*'+os_version:'*24*'+os_version:~'arm64'+platform:'linux'",
        },
        {
            "id": "ubuntu22",
            "name": "ubuntu",
            "version": "22.*",
            "arch": "arm64",
            "package_manager": "dpkg",
            "filter": "os:'*Ubuntu*'+os_version:'*22*'+os_version:~'arm64'+platform:'linux'",
        },
        {
            "name": "ubuntu",
            "version": "18.*",
            "arch": "arm64",
            "package_manager": "dpkg",
            "filter": "os:'*Ubuntu*'+os_version:'*18*'+os_version:~'arm64'+platform:'linux'",
        },
        {
            "name": "ubuntu",
            "version": "20.*",
            "arch": "arm64",
            "package_manager": "dpkg",
            "filter": "os:'*Ubuntu*'+os_version:'*20*'+os_version:~'arm64'+platform:'linux'",
        },
        {
            "name": "debian",
            "version": "9.*",
            "arch": "x86_64",
            "package_manager": "dpkg",
            "filter": "os:'Debian'+os_version:'*9*'+os_version:!'*arm64*'+os_version:!~'zLinux'+platform:'linux'",
        },
        {
            "name": "debian",
            "version": "10.*",
            "minor_version": "*",
            "arch": "x86_64",
            "package_manager": "dpkg",
            "filter": "os:'Debian'+os_version:'*10*'+os_version:!'*arm64*'+os_version:!~'zLinux'+platform:'linux'",
        },
        {
            "name": "debian",
            "version": "11.*",
            "arch": "x86_64",
            "package_manager": "dpkg",
            "filter": "os:'Debian'+os_version:'*11*'+os_version:!'*arm64*'+os_version:!~'zLinux'+platform:'linux'",
        },
        {
            "name": "debian",
            "version": "12.*",
            "arch": "x86_64",
            "package_manager": "dpkg",
            "filter": "os:'Debian'+os_version:'*12*'+os_version:!'*arm64*'+os_version:!~'zLinux'+platform:'linux'",
        },
        {
            "name": "debian",
            "version": "12",
            "minor_version": "*",
            "arch": "arm64",
            "package_manager": "dpkg",
            "filter": "os:'Debian'+os_version:'*12*'+os_version:~'arm64'+platform:'linux'",
        },
    ],
    "windows": [
        {
            "name": "windows",
            "version": "_any",
            "arch": "_any",
            "package_manager": "",
            "filter": "os:'Windows'+platform:'windows'",
        }
    ],
}

linux_install_script = r"""#!/bin/bash
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
SSM_CS_LINUX_INSTALLPARAMS="${SSM_CS_LINUX_INSTALLPARAMS//\\\`/\\\``}"
SSM_CS_LINUX_INSTALLPARAMS="${SSM_CS_LINUX_INSTALLPARAMS//\\\$/\\\$}"
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
"""

linux_uninstall_script = r"""#!/bin/bash
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
"""

windows_install_script = r"""[CmdletBinding()]
param()

#########
# Setup #
#########

Write-Output 'Installing Falcon Sensor...'
    
$ErrorActionPreference = "Stop"
    
function Convert-EncodeQueryParameter {
    param (
        [Parameter(Mandatory = $true)]
        [string]$QueryParameter
    )
        
    return $QueryParameter.Replace("+", "%2b").Replace("'", "%27").Replace(":", "%3a").Replace(" ", "%20")
}
    
$agentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue
    
if ($agentService) {
    Write-Output 'Falcon Sensor already installed... if you want to update or downgrade, please use Sensor Update Policies in the CrowdStrike console. Please see: https://falcon.crowdstrike.com/documentation/66/sensor-update-policies for more information.'
    Exit 0
}

if (-not $env:SSM_CS_CCID) {
    throw "Missing required parameter $($env:SSM_CS_CCID). If the required parameter was passed to the package, ensure the target instance has a ssm agent version of 2.3.1550.0 or greater installed."
}

$baseFilter = "os:'Windows'+platform:'windows'"

if ($env:SSM_CS_WINDOWS_VERSION) {
    $sensorFilter = Convert-EncodeQueryParameter -QueryParameter ($baseFilter + "+version:'${env:SSM_CS_WINDOWS_VERSION}'")
    $queryString = "limit=1&filter=${sensorFilter}"
    Write-Output "Version specified, grabbing the exact version: ${env:SSM_CS_WINDOWS_VERSION}. Query string: ${queryString}"
}
else {
    # If no version is specified, we will grab the n-1 version that matches the base filter
    $sensorFilter = Convert-EncodeQueryParameter -QueryParameter $baseFilter
    $queryString = "limit=1&offset=1&sort=version&filter=${sensorFilter}"
    Write-Output "No version specified, grabbing the n-1 version that matches the base filter. Query string: ${queryString}"
}

$headers = @{
    'Authorization' = "Bearer ${env:SSM_CS_AUTH_TOKEN}"
    'User-Agent'    = 'crowdstrike-custom-api-distributor-package/v2.0.0'
}  

$installArguments = @(
    , '/install'
    , '/quiet'
    , '/norestart'
    , "CID=${env:SSM_CS_CCID}"
    , 'ProvWaitTime=1200000'
)

$Space = ' '
if ($env:SSM_CS_WINDOWS_INSTALLPARAMS) {
    $installArguments += $env:SSM_CS_WINDOWS_INSTALLPARAMS.Split($Space)
}    

if ($env:SSM_CS_INSTALLTOKEN) {
    $installArguments += "ProvToken=${env:SSM_CS_INSTALLTOKEN}"
}

$proxy = ""

if ($installArguments -match "app_proxyname") {
    Write-Output "Proxy settings detected in arguments, using proxy settings to communicate with the CrowdStrike api"
    foreach ($arg in $installArguments) {
        $field = $arg.Split("=")
        
        if ($field[0] -eq "app_proxyname") {
            $proxy_host = $field[1].Replace("http://", "").Replace("https://", "")
            Write-Output "Proxy host ${proxy_host} found in arguments"
        }    

        if ($field[0] -eq "app_proxyport") {
            $proxy_port = $field[1]
            Write-Output "Proxy port ${proxy_port} found in arguments"
        }    
    }    

    if ($proxy_port -ne "") {
        $proxy = "http://${proxy_host}:${proxy_port}"
    }    
    else {
        $proxy = "http://${proxy_host}"
    }    

    $proxy = $proxy.Replace("'", "").Replace("`"", "")
    Write-Output "Using proxy: ${proxy} to communicate with the CrowdStrike Apis"
}    

###################
# Sensor Download #
###################

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$maxRetry = 15
$retryCount = 0
$retryDelaySeconds = 10

do {
    $uri = "https://${env:SSM_CS_HOST}/sensors/combined/installers/v1?${queryString}"
    Write-Output "Grabbing the Sha256 of the falcon sensor package, Calling $uri"
    try {
        if ($proxy -ne "") {
            $resp = Invoke-WebRequest -Method Get -Proxy $proxy -Uri $uri -Headers $headers -UseBasicParsing -ErrorAction Stop
        }    
        else {
            $resp = Invoke-WebRequest -Method Get -Uri $uri -Headers $headers -UseBasicParsing -ErrorAction Stop
        }    
    }    
    catch {
        $resp = $_.Exception.Response

        if ($null -eq $resp) {
            throw "Unexpected error: $($_.Exception.Message)"
        }    

        if ($resp.StatusCode -eq 429) {
            $retryCount++
            Write-Output "Rate limit exceeded, retrying in ${retryDelaySeconds} seconds... (retry ${retryCount} of ${maxRetry})"
            Start-Sleep -Seconds $retryDelaySeconds
        }    
    }    
} while ($retryCount -lt $maxRetry -and $resp.StatusCode -eq 429)    

if ($resp.StatusCode -eq 429) {
    throw "Rate limit exceeded, and max retries (${maxRetry}) reached."
}    

if ($resp.StatusCode -ne 200) {
    throw "Unexpected response code: $($resp.StatusCode) Response: $($resp.Content)"
}    
$content = ConvertFrom-Json -InputObject $resp.Content
# CHECK IF $content.resources IS EMPTY
# IF EMPTY, THROW ERROR
if ($content.resources.Count -eq 0) {
    throw "No sensor found for filter: ${queryString} Response: $($resp.Content)"
}
# Check if $resp.resources HAS MORE THAN 1 ELEMENT
# IF MORE THAN 1 ELEMENT, THROW ERROR
if ($content.resources.Count -gt 1) {
    throw "More than one sensor found for filter: ${queryString} Response: $($resp.Content)"
}    
# IF NOT EMPTY, CHECK IF $resp.resources[0].signed_url IS EMPTY/NULL or $resp.resources[0].name IS EMPTY/NULL
# IF EMPTY/NULL, THROW ERROR
if ($null -eq $content.resources[0].sha256 -or $null -eq $content.resources[0].name) {
    throw "Resources returned, but were missing the sha256 or name field. Please report this error. Response: $($resp.Content)"
}    

$installerName = $content.resources[0].name
$installerSha256 = $content.resources[0].sha256
$version = $content.resources[0].version

$ProgressPreference = 'SilentlyContinue'
$maxRetry = 15
$retryCount = 0
$retryDelaySeconds = 10
$installerPath = Join-Path -Path $PSScriptRoot -ChildPath $installerName

do {
    $uri = "https://${env:SSM_CS_HOST}/sensors/entities/download-installer/v1?id=$installerSha256"
    Write-Output "Downloading the package matching Sha256: $installerSha256. Calling $uri"
    try {
        if ($proxy -ne "") {
            $resp = Invoke-WebRequest -Method Get -Proxy $proxy -Uri $uri -Headers $headers -UseBasicParsing -OutFile $installerPath -ErrorAction Stop
        }    
        else {
            $resp = Invoke-WebRequest -Method Get -Uri $uri -Headers $headers -UseBasicParsing -OutFile $installerPath -ErrorAction Stop
        }    
    }    
    catch {
        $resp = $_.Exception.Response

        if ($null -eq $resp) {
            throw "Unexpected error: $($_.Exception.Message)"
        }    

        if ($resp.StatusCode -eq 429) {
            $retryCount++
            Write-Output "Rate limit exceeded, retrying in ${retryDelaySeconds} seconds... (retry ${retryCount} of ${maxRetry})"
            Start-Sleep -Seconds $retryDelaySeconds
        }    
    }    
} while ($retryCount -lt $maxRetry -and $resp.StatusCode -eq 429)    

if ($resp.StatusCode -eq 429) {
    throw "Rate limit exceeded, and max retries (${maxRetry}) reached."
}    

if (-not (Test-Path -Path $installerPath)) {
    throw "Failed to download the file. Error $(ConvertTo-Json $resp -Depth 10)"
} 

###########
# Install #
###########

Write-Host "Installer downloaded to: $installerPath"
Write-Output "Running installer for sensor version: ${version} with arguments: $installArguments"
$installerProcess = Start-Process -FilePath $installerPath -ArgumentList $installArguments -PassThru -Wait

if ($installerProcess.ExitCode -ne 0) {
    throw "Installer returned exit code $($installerProcess.ExitCode)"
}

$agentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue
if (-not $agentService) {
    throw 'Installer completed, but CSAgent service is missing...'
}
elseif ($agentService.Status -eq 'Running') {
    Write-Output 'CSAgent service running...'
}
else {
    throw 'Installer completed, but CSAgent service is not running...'
}

Write-Output "Falcon Sensor version ${version} installed successfully."
"""

windows_uninstall_script = r"""[CmdletBinding()]
param()

Write-Output 'Uninstalling Falcon Sensor...'

# Configures the TLS version to use for secure connections
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$agentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue
if (-not $agentService) {
  Write-Output 'CSAgent service not installed...'
  Exit 0
}

# Retrieves the package for the CrowdStrike Windows Sensor using PowerShell's Get-Package cmdlet
$package = Get-Package -Name 'CrowdStrike Windows Sensor'

# Retrieves the path to the uninstall executable from the package metadata
$uninstallString = $package.Metadata['BundleCachePath']

# Sets up the arguments to be passed to the uninstall executable
$uninstallArgs = '/uninstall /quiet' + $env:SSM_WIN_UNINSTALLPARAMS

if ($env:MAINTENANCE_TOKEN) {
  $uninstallArgs += ' MAINTENANCE_TOKEN=' + $env:MAINTENANCE_TOKEN
}

# Starts the uninstall process and waits for it to complete
Write-Output "Uninstalling with arguments: $uninstallArgs"
$uninstallProcess = Start-Process -FilePath $uninstallString -ArgumentList $uninstallArgs -PassThru -Wait

# Checks the exit code of the uninstall process and throws an exception if it is not 0
if ($uninstallProcess.ExitCode -ne 0) {
  Write-Output "Failed to uninstall with exit code: $($uninstallProcess.ExitCode)"
  exit 1
}

# Retrieves the status of the CSAgent service and throws an exception if it is still running after the uninstall
$agentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue
if ($agentService -and $agentService.Status -eq 'Running') {
  Write-Output 'Uninstall process completed, but CSAgent service is still running. Uninstall failed for unknown reason...'
  exit 1 
}

# Checks if the CrowdStrike registry key was successfully removed and throws an exception if it still exists
if (Test-Path -Path HKLM:\System\Crowdstrike) {
  Write-Output 'CrowdStrike registry key still exists. Uninstall failed.'
  exit 1
}

# Checks if the CrowdStrike driver was successfully removed and throws an exception if it still exists
if (Test-Path -Path "${env:SYSTEMROOT}\System32\drivers\CrowdStrike") {
  Write-Output 'CrowdStrike driver still exists. Uninstall failed.'
  exit 1
}

Write-Output 'Successfully finished uninstall...'"""

if __name__ == "__main__":
    handler(
        {
            "ResourceProperties": {
                "DistributorPackageName": "CrowdStrike-FalconSensorTest",
                "S3BucketName": "ffalor-state-manager1",
            },
            "RequestType": "Create",
        },
        "",
    )
