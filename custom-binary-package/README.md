# Custom AWS Distributor Package using Sensor Binaries

> [!IMPORTANT]
> As of version v2.2.0 and later, the [official CrowdStrike Distributor Package](../official-package/README.md) supports all AWS regions including GovCloud. The official third party package is the recommended path and will recieve updates quicker than the custom binary package. In cases where the official package can't be used this package can be used instead.

This deployment guide outlines the steps required to build your own distributor package that bundles the CrowdStrike Falcon sensor binaries for Linux and Windows.

## Custom Binary Package vs. Official API Package

This custom binary package method differs from the [official package](../official-package/README.md) in how the sensor is delivered and installed:

| Feature                  | Custom Binary Package                                           | Official Third-Part Package                                            |
| ------------------------ | --------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **Sensor Delivery**      | Sensor binaries are bundled directly in the distributor package | Sensors are downloaded from CrowdStrike API at install time            |
| **API Interaction**      | CrowdStrike API only called once during package creation        | CrowdStrike API called on each instance during every install operation |
| **Network Requirements** | Instances only need access to SSM.                              | Instances need access to CrowdStrike API endpoints                     |
| **Version Control**      | Deploys specific sensor version bundled in package              | Deploys latest sensor version matching filter criteria                 |
| **Region Support**       | Works in all AWS regions including GovCloud                     | Works in all AWS regions including GovCloud                            |
| **Package Updates**      | Rebuild package to change deployed sensor version               | Automatically gets latest matching sensor without rebuild              |
| **Maintenance**          | Rebuild required to change installed sensor version             | No maintenance - always uses latest published distributor package      |

> [!NOTE]
> Both methods do not perform automatic sensor updates. Sensor version updates should be managed using [CrowdStrike Sensor Update Policies](https://falcon.crowdstrike.com/documentation/page/o4c93228/sensor-update-policies).

### When to Use Custom Binary Package

Consider using this custom binary package method when:

- Your instances cannot reach CrowdStrike API endpoints (air-gapped, restricted network)
- You want to control the exact sensor version deployed
- You want to avoid the `aws:executeScript` automation costs associated with the official package (see [official package cost documentation](../official-package/COST-DOCUMENTATION.md)) 


## Requirements
You will need:

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) installed and configured for the account you want to deploy to.
- [Python](https://www.python.org/downloads/) installed.

## Setting up Systems Manager
Distributor is a feature of AWS Systems Manager. In order to use the distributor package, you must first setup AWS Systems Manager. See the [AWS documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-setting-up.html) for more information.

A ssm agent version of `2.3.1550.0` or greater is required.

## Generate API Keys

We will use the CrowdStrike API to download the sensor binaries that will be bundled in the distributor package.

1. In the CrowdStrike console, navigate to **Support and resources** > **API Clients & Keys**. Click **Add new API Client**.
2. Add the following api scopes:

    | Scope           | Permission | Description                                                     |
    | --------------- | ---------- | --------------------------------------------------------------- |
    | Sensor Download | *READ*     | Allows the helper python script to download the sensor binaries |

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
3. Install the required python modules
    ```bash
    pip3 install -r requirements.txt
    ```
4. Run the `create-package.py` script

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

| Parameter                 | Description                                                                          | Required |
| ------------------------- | ------------------------------------------------------------------------------------ | -------- |
| SSM_CID                   | The CID of the CrowdStrike Falcon console to connect to.                             | Yes      |
| SSM_INSTALLTOKEN          | The install token to use when installing the sensor.                                 | No       |
| SSM_WIN_INSTALLPARAMS     | The install parameters to use when installing the sensor on Windows. (Excluding CID) | No       |
| SSM_WIN_UNINSTALLPARAMS   | The uninstall parameters to use when uninstalling the sensor on Windows.             | No       |
| SSM_LINUX_INSTALLPARAMS   | The install parameters to use when installing the sensor on Linux. (Excluding CID)   | No       |
| SSM_LINUX_UNINSTALLPARAMS | The uninstall parameters to use when uninstalling the sensor on Linux.               | No       |

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
