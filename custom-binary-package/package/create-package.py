import argparse
from genericpath import exists
import os
from re import split
import resource
import shutil
import subprocess
from urllib.request import urlretrieve

try:
    from falconpy import APIHarness
except ImportError as no_falconpy:
    raise SystemExit(
        "The CrowdStrike SDK must be installed in order to use this utility.\n"
        "Install this application with the command `python3 -m pip install crowdstrike-falconpy`."
    ) from no_falconpy

parser = argparse.ArgumentParser(
    prog="create-package",
    description="Create a ssm distributor package that contains Falcon Sensor binaries",
)

parser.add_argument(
    "-r",
    "--aws_region",
    required=True,
    help="The aws region to create the ssm distributor package in.",
)
parser.add_argument(
    "-b",
    "--s3bucket",
    required=True,
    help="The name of the s3 bucket to upload the required files to.",
)
parser.add_argument(
    "-p",
    "--package_name",
    help="The name of the distributor package to create.",
    default="CrowdStrike-FalconSensor",
)

args = parser.parse_args()

client_id = os.environ.get("FALCON_CLIENT_ID")
client_secret = os.environ.get("FALCON_CLIENT_SECRET")

if not client_id:
    raise ValueError("FALCON_CLIENT_ID environment variable not set.")

if not client_secret:
    raise ValueError("FALCON_CLIENT_SECRET environment variable not set.")

dirs_to_delete = []

python_executable = shutil.which("python3")

if not python_executable:
    python_executable = "python"

binary_list = [
    {
        "filter": "os:'Amazon Linux'+os_version:'2'+platform:'linux'",
        "path": "CS_AMAZON2_x86_64/falcon-sensor.rpm",
        "installer": "yum",
    },
    {
        "filter": "os:'Amazon Linux'+os_version:'2 - arm64'+platform:'linux'",
        "path": "CS_AMAZON2_ARM64/falcon-sensor.rpm",
        "installer": "yum",
    },
    {
        "filter": "os:'Amazon Linux'+os_version:'2023'+platform:'linux'",
        "path": "CS_AMAZON2023_x86_64/falcon-sensor.rpm",
        "installer": "yum",
    },
    {
        "filter": "os:'Amazon Linux'+os_version:'2023 - arm64'+platform:'linux'",
        "path": "CS_AMAZON2023_ARM64/falcon-sensor.rpm",
        "installer": "yum",
    },
    {
        "filter": "os:'*RHEL*'+os_version:'7'+platform:'linux'",
        "path": "CS_RHEL7_x86_64/falcon-sensor.rpm",
        "installer": "yum",
    },
    {
        "filter": "os:'*RHEL*'+os_version:'8'+platform:'linux'",
        "path": "CS_RHEL8_x86_64/falcon-sensor.rpm",
        "installer": "yum",
    },
    {
        "filter": "os:'*RHEL*'+os_version:'8 - arm64'+platform:'linux'",
        "path": "CS_RHEL8_ARM64/falcon-sensor.rpm",
        "installer": "yum",
    },
    {
        "filter": "os:'*RHEL*'+os_version:'9'+platform:'linux'",
        "path": "CS_RHEL9_x86_64/falcon-sensor.rpm",
        "installer": "yum",
    },
    {
        "filter": "os:'*RHEL*'+os_version:'9 - arm64'+platform:'linux'",
        "path": "CS_RHEL9_ARM64/falcon-sensor.rpm",
        "installer": "yum",
    },
    {
        "filter": "os:'*RHEL*'+os_version:'10'+platform:'linux'",
        "path": "CS_RHEL10_x86_64/falcon-sensor.rpm",
        "installer": "yum",
    },
    {
        "filter": "os:'*RHEL*'+os_version:'10 - arm64'+platform:'linux'",
        "path": "CS_RHEL10_ARM64/falcon-sensor.rpm",
        "installer": "yum",
    },
    {
        "path": "CS_ALMALINUX8_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*RHEL*'+os_version:'8'+platform:'linux'",
    },
    {
        "path": "CS_ALMALINUX8_ARM64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*RHEL*'+os_version:'8 - arm64'+platform:'linux'",
    },
    {
        "path": "CS_ALMALINUX9_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*RHEL*'+os_version:'9'+platform:'linux'",
    },
    {
        "path": "CS_ALMALINUX9_ARM64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*RHEL*'+os_version:'9 - arm64'+platform:'linux'",
    },
    {
        "path": "CS_ALMALINUX10_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*RHEL*'+os_version:'10'+platform:'linux'",
    },
    {
        "path": "CS_ALMALINUX10_ARM64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*RHEL*'+os_version:'10 - arm64'+platform:'linux'",
    },
    {
        "path": "CS_ROCKY8_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*RHEL*'+os_version:'8'+platform:'linux'",
    },
    {
        "path": "CS_ROCKY8_ARM64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*RHEL*'+os_version:'8 - arm64'+platform:'linux'",
    },
    {
        "path": "CS_ROCKY9_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*RHEL*'+os_version:'9'+platform:'linux'",
    },
    {
        "path": "CS_ROCKY9_ARM64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*RHEL*'+os_version:'9 - arm64'+platform:'linux'",
    },
    {
        "path": "CS_ROCKY10_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*RHEL*'+os_version:'10'+platform:'linux'",
    },
    {
        "path": "CS_ROCKY10_ARM64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*RHEL*'+os_version:'10 - arm64'+platform:'linux'",
    },
    {
        "path": "CS_CENTOS8_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*CentOS*'+os_version:'8'+platform:'linux'",
    },
    {
        "path": "CS_CENTOS8_ARM64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*CentOS*'+os_version:'8 - arm64'+platform:'linux'",
    },
    {
        "path": "CS_CENTOS9_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*CentOS*'+os_version:'9'+platform:'linux'",
    },
    {
        "path": "CS_CENTOS10_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*CentOS*'+os_version:'10'+platform:'linux'",
    },
    {
        "path": "CS_ORACLE7_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*Oracle*'+os_version:'7'+platform:'linux'",
    },
    {
        "path": "CS_ORACLE7_ARM64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*Oracle*'+os_version:'7 - arm64'+platform:'linux'",
    },
    {
        "path": "CS_ORACLE8_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*Oracle*'+os_version:'8'+platform:'linux'",
    },
    {
        "path": "CS_ORACLE9_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*Oracle*'+os_version:'9'+platform:'linux'",
    },
    {
        "path": "CS_ORACLE10_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*Oracle*'+os_version:'10'+platform:'linux'",
    },
    {
        "path": "CS_ORACLE10_ARM64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*Oracle*'+os_version:'10 - arm64'+platform:'linux'",
    },
    {
        "path": "CS_SLES12_x86_64/falcon-sensor.rpm",
        "installer": "zypper",
        "filter": "os:'*SLES*'+os_version:'12'+os_version:!~'zLinux'+platform:'linux'",
    },
    {
        "path": "CS_SLES15_x86_64/falcon-sensor.rpm",
        "installer": "zypper",
        "filter": "os:'*SLES*'+os_version:'15'+os_version:!~'zLinux'+platform:'linux'",
    },
    {
        "path": "CS_SLES15_ARM64/falcon-sensor.rpm",
        "installer": "zypper",
        "filter": "os:'*SLES*'+os_version:'15 - arm64'+platform:'linux'",
    },
    {
        "path": "CS_UBUNTU_x86_64/falcon-sensor.deb",
        "installer": "dpkg",
        "filter": "os:'*Ubuntu*'+os_version:!'*arm64*'+os_version:!~'zLinux'+platform:'linux'",
    },
    {
        "path": "CS_UBUNTU_ARM64/falcon-sensor.deb",
        "installer": "dpkg",
        "filter": "os:'*Ubuntu*'+os_version:~'arm64'+os_version:!~'zLinux'+platform:'linux'",
    },
    {
        "path": "CS_DEBIAN_x86_64/falcon-sensor.deb",
        "installer": "dpkg",
        "filter": "os:'Debian'+os_version:!'*arm64*'+os_version:!~'zLinux'+platform:'linux'",
    },
    {
        "path": "CS_DEBIAN_ARM64/falcon-sensor.deb",
        "installer": "dpkg",
        "filter": "os:'Debian'+os_version:~'arm64'+os_version:!~'zLinux'+platform:'linux'",
    },
    {
        "path": "CS_WINDOWS/WindowsSensor.exe",
        "installer": "windows",
        "filter": "os:'Windows'+platform:'windows'",
    },
]

falcon = APIHarness(
    client_id=os.environ.get("FALCON_CLIENT_ID"),
    client_secret=os.environ.get("FALCON_CLIENT_SECRET"),
)

print("Downloading required files...")

for binary in binary_list:
    if os.path.exists(binary["path"]):
        print(f"Skipping download - {binary['path']} already exists")
        os_dir = os.path.dirname(binary["path"])
        dirs_to_delete.append(os_dir)
        continue

    sensors = falcon.command(
        action="GetCombinedSensorInstallersByQuery",
        filter=binary["filter"],
        sort="version.desc",
    )

    if not isinstance(sensors, dict):
        raise SystemExit(
            f"API call failed for filter: {binary['filter']}. "
            f"Expected dict response, got {type(sensors).__name__}."
        )

    if sensors.get("status_code") != 200:
        error_msg = sensors.get("body", {}).get("errors", [{}])[0].get("message", "Unknown error")
        raise SystemExit(
            f"API error while querying sensors for filter: {binary['filter']}. "
            f"Status code: {sensors.get('status_code')}, Error: {error_msg}"
        )

    if "body" not in sensors:
        raise SystemExit(
            f"API response missing 'body' for filter: {binary['filter']}. "
            f"Full response: {sensors}"
        )

    resources = sensors["body"].get("resources", [])
    if len(resources) == 0:
        raise SystemExit(
            f"Unable to find sensor that matches filter: {binary['filter']}"
        )
    if len(resources) > 1:
        sensor = resources[1]
    else:
        sensor = resources[0]

    sha = sensor["sha256"]
    sensor_os = sensor["os"]
    sensor_os_version = sensor["os_version"]
    sensor_name = sensor["name"]

    print(f"Downloading {sensor_name} for {sensor_os} {sensor_os_version}")

    download = falcon.command(action="DownloadSensorInstallerById", id=sha)

    if not download:
        raise SystemExit(
            f"Failed to download sensor {sensor_name}. The download returned empty content."
        )

    if isinstance(download, dict):
        error_msg = download.get("body", {}).get("errors", [{}])[0].get("message", "Unknown error")
        raise SystemExit(
            f"API error while downloading sensor {sensor_name}. "
            f"Status code: {download.get('status_code')}, Error: {error_msg}"
        )

    os_dir = os.path.dirname(binary["path"])
    os.makedirs(os_dir, exist_ok=True)
    with open(binary["path"], "wb") as save_file:
        save_file.write(download)
    shutil.copytree(
        f"./scripts/{binary['installer']}", f"{os_dir}/", dirs_exist_ok=True
    )
    dirs_to_delete.append(os_dir)

subprocess.check_call(
    [
        "python3",
        "packager.py",
        "-r",
        args.aws_region,
        "-b",
        args.s3bucket,
        "-p",
        args.package_name,
    ]
)
for d in dirs_to_delete:
    shutil.rmtree(d)
print(f"Package {args.package_name} created successfully in region {args.aws_region}.")
