import argparse
import os
import logging
import json


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

    manifest_data = {}
    base_build_dir = "./build"

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
            distro_dir = "{}{}-{}".format(name, version.replace(".*", ""), arch)

            write_package_script(
                install_script,
                f"{base_build_dir}/{distro_dir}/install{file_ext}",
                distro["filter"],
                distro["package_manager"],
            )

            write_package_script(
                uninstall_script,
                f"{base_build_dir}/{distro_dir}/uninstall{file_ext}",
                distro["filter"],
                distro["package_manager"],
            )


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


if __name__ == "__main__":
    main()
