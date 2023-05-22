# Custom AWS Distributor Package using Sensor Binaries

This deployment guide outlines the steps required to build your own distributor package that bundles the CrowdStrike Falcon sensor binaries for Linux and Windows.

This removes the need to use the CrowdStrike API removing the risk of API rate limiting.

## Requirements
You will need:

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) installed and configured for the account you want to deploy to.
- [Python](https://www.python.org/downloads/) installed.

## Generate API Keys

We will use the CrowdStrike API to download the sensor binaries that will be bundled in the distributor package.

1. In the CrowdStrike console, navigate to **Support and resources** > **API Clients & Keys**. Click **Add new API Client**.
2. Add the following api scopes:

    | Scope               | Permission | Description                                                                  |
    | ------------------- | ---------- | ---------------------------------------------------------------------------- |
    | Sensor Download     | *READ*     | Allows the helper python script to download the sensor binaries              |

3. Click **Add** to create the API client. The next screen will display the API **CLIENT ID**, **SECRET**, and **BASE URL**. You will need all three for the next step.

    <details><summary>picture</summary>
    <p>

    ![api-client-keys](./../official-package/assets/api-client-keys.png)

    </p>
    </details>

> Note: This page is only shown once. Make sure you copy **CLIENT ID**, **SECRET**, and **BASE URL** to a secure location.

## Create the Distributor Package

All commands should be ran from the `./custom-binary-package/package` directory.

1. Download or clone this repository
    ```bash
    git clone https://github.com/CrowdStrike/aws-ssm-distributor.git
    ``` 
2. Change to the `package` directory
    ```bash
    cd aws-ssm-distributor/custom-binary-package/package
    ```
3. Update `agent_list.json` with the operating systems you want to target.

    <details>
      <summary>Expand for details</summary>

      The `agent_list.json` file should list all the directories that will be included in the package. The file should be in json format and contain a list of objects containing the following keys:

    | Key             | Description                                                                                                                                                                                |
    | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
    | `dir`           | The directory that contains the install scripts                                                                                                                                            |
    | `file`          | The name of the zip file that will be created                                                                                                                                              |
    | `name`          | The `code value` used by SSM Distributor. See [here](https://docs.aws.amazon.com/systems-manager/latest/userguide/distributor.html#what-is-a-package-platforms) for a list of valid values |
    | `arch_type`     | The architecture type of the binary. See [here](https://docs.aws.amazon.com/systems-manager/latest/userguide/distributor.html#what-is-a-package-platforms) for a list of valid values      |
    | `major_version` | The major OS version. Must match the exact release version of the operating system Amazon Machine Image (AMI) that you're targeting.                                                       |
    | `minor_version` | The minor OS version. Must match the exact release version of the operating system Amazon Machine Image (AMI) that you're targeting.                                                       |
    | `id`            | Optional unique id                                                                                                                                                                         |

    Below is an example `agent_list.json` file that creates a SSM Distributor package that contains install instructions for the following operating systems:

    * Amazon Linux 2
    * Amazon Linux 2 ARM64
    * All supported Windows versions

    ```json
    {
      "linux": [
        {
          "id": "amzn2",
          "dir": "CS_AMAZON2_x86_64",
          "file": "CS_AMAZON2_x86_64.zip",
          "name": "amazon",
          "major_version": "2",
          "minor_version": "",
          "arch_type": "x86_64",
        },
        {
          "id": "amzn2",
          "dir": "CS_AMAZON2_ARM64",
          "file": "CS_AMAZON2_arm64.zip",
          "name": "amazon",
          "major_version": "2",
          "minor_version": "",
          "arch_type": "arm64",
        }
      ],
      "windows": [
        {
          "dir": "CS_WINDOWS",
          "file": "CS_WINDOWS.zip",
          "id": "windows",
          "name": "windows",
          "major_version": "_any",
          "minor_version": "",
          "arch_type": "_any",
        }
      ]
    }
    ```
    </details>

4. Install the required python modules
    ```bash
    pip3 install -r requirements.txt
    ```
5. Run the `create-package.py` script

   This script will download the sensor binaries and create the SSM Distributor package.

   1. Add your CrowdStrike API credentials as environment variables.
        
        ```bash
        export FALCON_CLIENT_ID=<YOUR_CLIENT_ID>
        export FALCON_CLIENT_SECRET=<YOUR_CLIENT_SECRET>
        ```
    2. Run the `create-package.py` script with the appropriate parameters.

      | Parameter | Description                                                | Required | Default                      |
      | --------- | ---------------------------------------------------------- | -------- | ---------------------------- |
      | `-r`      | The aws region to create the ssm distributor package in.   | Yes      | **N/A**                      |
      | `-b`      | The name of the s3 bucket to upload the required files to. | Yes      | **N/A**                      |
      | `-p`      | The name of the distributor package to create.             | No       | **CrowdStrike-FalconSensor** |

    ```bash
    python3 create-package.py -r <AWS_REGION> -b <S3BUCKET> -p <DISTRIBUTOR_PACKAGE_NAME>
    ```
## Usage

Once you've published the package you can use the `AWS-ConfigureAWSPackage` run command to install the CrowdStrike Falcon sensor on your instances. Refer to the [command documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/distributor-working-with-packages-deploy.html) for more information on different ways to deploy your package.

You can pass the following parameters to the `additional-arguments` parameter of the `AWS-ConfigureAWSPackage` run command to modify the default behavior of the package:

| Parameter | Description | Required |
| --------- | ----------- | -------- |
| SSM_CID | The CID of the CrowdStrike Falcon console to connect to. | Yes |
| SSM_INSTALLTOKEN | The install token to use when installing the sensor. | No |
| SSM_WIN_INSTALLPARAMS | The install parameters to use when installing the sensor on Windows. | No |
| SSM_WIN_UNINSTALLPARAMS | The uninstall parameters to use when uninstalling the sensor on Windows. | No |
| SSM_LINUX_INSTALLPARAMS | The install parameters to use when installing the sensor on Linux. | No |
| SSM_LINUX_UNINSTALLPARAMS | The uninstall parameters to use when uninstalling the sensor on Linux. | No |

### Example

Here is an example of creating a SSM State Manager association to install the CrowdStrike sensor on all instances in a region. State manager associations keep a persistent state. Meaning, if you add new instances to the region they will automatically have the sensor installed.

Refer to the [AWS-ConfigureAWSPackage](https://docs.aws.amazon.com/systems-manager/latest/userguide/distributor-working-with-packages-deploy.html) for all ways to deploy your package.

```bash
aws ssm create-association \
    --name "AWS-ConfigureAWSPackage" \
    --targets "Key=InstanceIds,Values=*" \
    --parameters '{"action":["Install"],"installationType":["Uninstall and reinstall"],"version":[""],"additionalArguments":["{\n\"SSM_CID\": \"123123123123\",\n\"SSM_WIN_INSTALLPARAMS\": \"GROUPING_TAGS=tag2,tag1\"\n}"],"name":["CrowdStrike-FalconSensor"]}' \
    --association-name "crowdstrike-falcon-sensor-deploy" \
    --automation-target-parameter-name "InstanceIds" \
    --region "us-east-1"
```

## FAQ

### How do I upgrade/downgrade the sensor?

CrowdStrike Falcon Sensor upgrades and downgrades should be handled by update policies. The distributor package will not upgrade or downgrade the sensor. The distributor package should be used to install the sensor and then allow update policies to manage the sensor version.