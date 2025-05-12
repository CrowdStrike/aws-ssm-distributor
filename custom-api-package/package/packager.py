import argparse
import os
import logging
from os.path import basename
import zipfile
import json
import hashlib


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

FILTER_KEYWORD = "<<SENSOR_DOWNLOAD_FILTER>>"
PACKAGE_MANAGER_KEYWORD = "<<PACKAGE_MANAGER>>"


def main():
    parser = argparse.ArgumentParser(
        "This script creates the distribor package .zip files, and generates a manifest.json file that can be used to create the custom api distributor package."
    )
    parser.add_argument(
        "--version", "-v", help="The version of the distributor package.", required=True
    )
    args = parser.parse_args()

    package_version = args.version
    logger.info(f"Creating custom-api distribtor package version: {package_version}")

    distros = {}
    with open("./distros.json", "r") as distro_file:
        distros = json.load(distro_file)

    if len(distros) == 0:
        raise ValueError("Expected distros.json to contain distro information.")

    manifest_data = {
        "schemaVersion": "2.0",
        "publisher": "Crowdstrike Inc.",
        "description": "The CrowdStrike Falcon cloud platform helps successfully stop breaches, all via a single lightweight agent. Learn how to protect your AWS environment with CrowdStrike at https://github.com/CrowdStrike/aws-ssm-distributor/tree/main/custom-api-package",
        "version": package_version,
        "packages": {},
        "files": {},
    }
    base_build_dir = "./builds"

    for platform in distros:
        if platform == "linux":
            install_script = "./linux/install.sh"
            uninstall_script = "./linux/uninstall.sh"
            file_ext = ".sh"
        else:
            install_script = "./windows/install.ps1"
            uninstall_script = "./windows/uninstall.ps1"
            file_ext = ".ps1"

        for distro in distros[platform]:
            name = distro["name"]
            version = distro["version"]
            arch = distro["arch"]
            logger.info("Creating package for {} {} {}".format(name, version, arch))
            distro_dir = "{}{}-{}".format(
                name, version.replace(".*", "").replace("_any", ""), arch
            )
            package_dir = f"{base_build_dir}/package/{distro_dir}"

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

            zip_file_path = zip_package(package_dir, distro_dir, base_build_dir)
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

            with open(f"{base_build_dir}/s3/manifest.json", "w") as file:
                json.dump(manifest_data, file, indent=4)


def zip_package(package_dir, zip_name, base_build_dir):
    zip_package_name = f"{base_build_dir}/s3/{zip_name}.zip"
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


def write_package_script(source, dest, filter, package_manager):
    directory = os.path.dirname(dest)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(source, "rt") as fin, open(dest, "wt") as fout:
        for line in fin:
            fout.write(
                line.replace(FILTER_KEYWORD, filter).replace(
                    PACKAGE_MANAGER_KEYWORD, package_manager
                )
            )


def get_digest(file):
    h = hashlib.sha256()

    with open(file, "rb") as file:
        while True:
            chunk = file.read(h.block_size)
            if not chunk:
                break
            h.update(chunk)
        return h.hexdigest()


if __name__ == "__main__":
    main()
