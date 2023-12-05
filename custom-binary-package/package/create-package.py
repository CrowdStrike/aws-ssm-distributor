import argparse
from genericpath import exists
import os
from re import split
import resource
import shutil
import subprocess
from urllib.request import urlretrieve

from distro import major_version

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

print("Downloading required files...")

binary_list = [
    {
        "filter": "os:'Amazon Linux'+os_version:'1'+platform:'linux'",
        "path": "CS_AMAZON_x86_64/falcon-sensor.rpm",
        "installer": "yum",
    },
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
        "filter": "os:'*RHEL*'+os_version:'6'+platform:'linux'",
        "path": "CS_RHEL6_x86_64/falcon-sensor.rpm",
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
        "filter": "os:'*CentOS*'+os_version:'6'+platform:'linux'",
        "path": "CS_CENTOS6_x86_64/falcon-sensor.rpm",
        "installer": "yum",
    },
    {
        "path": "CS_CENTOS7_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*CentOS*'+os_version:'7'+platform:'linux'",
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
        "path": "CS_ORACLE6_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*Oracle*'+os_version:'6'+platform:'linux'",
    },
    {
        "path": "CS_ORACLE7_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*Oracle*'+os_version:'7'+platform:'linux'",
    },
    {
        "path": "CS_ORACLE8_x86_64/falcon-sensor.rpm",
        "installer": "yum",
        "filter": "os:'*Oracle*'+os_version:'8'+platform:'linux'",
    },
    {
        "path": "CS_SLES11_x86_64/falcon-sensor.rpm",
        "installer": "zypper",
        "filter": "os:'*SLES*'+os_version:'11'+platform:'linux'",
    },
    {
        "path": "CS_SLES12_x86_64/falcon-sensor.rpm",
        "installer": "zypper",
        "filter": "os:'*SLES*'+os_version:'12'+platform:'linux'",
    },
    {
        "path": "CS_SLES15_x86_64/falcon-sensor.rpm",
        "installer": "zypper",
        "filter": "os:'*SLES*'+os_version:'15'+platform:'linux'",
    },
    {
        "path": "CS_UBUNTU_x86_64/falcon-sensor.deb",
        "installer": "dpkg",
        "filter": "os:'*Ubuntu*'+os_version:'*16/18/20/22*'+os_version:!'*arm64*'+os_version:!~'zLinux'+platform:'linux'",
    },
    {
        "path": "CS_UBUNTU_ARM64/falcon-sensor.deb",
        "installer": "dpkg",
        "filter": "os:'*Ubuntu*'+os_version:'*18/20/22*'+os_version:~'arm64'+os_version:!~'zLinux'+platform:'linux'",
    },
    {
        "path": "CS_DEBIAN_x86_64/falcon-sensor.deb",
        "installer": "dpkg",
        "filter": "os:'Debian'+os_version:'*9/10/11*'+os_version:!'*arm64*'+platform:'linux'",
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
for binary in binary_list:
    sensors = falcon.command(
        action="GetCombinedSensorInstallersByQuery",
        filter=binary["filter"],
        sort="version.desc",
    )
    resources = sensors["body"]["resources"]
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
    if isinstance(download, dict):
        raise SystemExit("Unable to download requested sensor.")

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
