import argparse
import os
import shutil
import subprocess
from urllib.request import urlretrieve

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

files_to_remove = []

python_executable = shutil.which("python3")

if not python_executable:
    python_executable = "python"

DOWNLOAD_HELPER = "https://raw.githubusercontent.com/CrowdStrike/falconpy/main/samples/sensor_download/download_sensor.py"
PACKAGER = "https://raw.githubusercontent.com/CrowdStrike/aws-ssm-distributor/main/custom-api-package/package/packager.py?token=GHSAT0AAAAAAB4JNG73TKW26EJUMMR74XM2ZCIJPKA"

print("Downloading required files...")
urlretrieve(DOWNLOAD_HELPER, "download.py")
files_to_remove.append("download.py")
urlretrieve(PACKAGER, "packager.py")
files_to_remove.append("packager.py")

binary_list = [
    {
        "os": "win",
        "path": "CS_WINDOWS/WindowsSensor.exe"
    },
    {
        "os": "amzn",
        "filter": "2",
        "path": "CS_AMAZON2_x86_64/falcon-sensor.rpm"
    },
    {
        "os": "amzn",
        "filter": "2 - arm64",
        "path": "CS_AMAZON2_ARM64/falcon-sensor.rpm"
    },
    {
        "os": "ubuntu",
        "path": "CS_UBUNTU_x86_64/falcon-sensor.deb"
    }
]

for binary in binary_list:
    command = [
        python_executable,
        "download.py",
        "-k",
        client_id,
        "-s",
        client_secret,
        "-d",
        "-o",
        binary["os"],
        "-f",
        binary["path"],
    ]

    if binary.get("filter"):
        command.extend(["-v", binary["filter"]])

    subprocess.check_call(command)
    files_to_remove.append(binary["path"])

subprocess.check_call([
    "python3",
    "packager.py",
    "-r",
    args.aws_region,
    "-b",
    args.s3bucket,
    "-p",
    args.package_name,
])

for file in files_to_remove:
    print(f"Removing {file}...")
    os.remove(file)

print(f"Package {args.package_name} created successfully in region {args.aws_region}.")
