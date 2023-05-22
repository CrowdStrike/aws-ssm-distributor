# Custom AWS Distributor Package using the CrowdStrike API
> IMPORTANT: It is highly recommended that you use the [official CrowdStrike Distributor Package](../official-package/README.md) instead. They both use the CrowdStrike API to download the CrowdStrike sensor, but the official package is maintained by CrowdStrike and removes the need to build and maintain your own package. This guide is provided for customers who operate in regions where the official package is not available.

This deployment guide outlines the steps required to build your own distributor package that uses the CrowdStrike API's to downloaded and install the CrowdStrike sensor.

## Setting up Systems Manager
Distributor is a feature of AWS Systems Manager. In order to use the distributor package, you must first setup AWS Systems Manager. See the [AWS documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-setting-up.html) for more information.

## Create the Distributor Package

> The default installed version will be (latest-release)-1. For example if the latest release of the linux sensor is 5.34.9918 the DEFAULT version installed would be 5.33.9808. It is expected that once installed, sensor versions will be managed via the falcon console.

All commands should be ran from the `./custom-api-package/package` directory.

1. Download or clone this repository
    ```bash
    git clone https://github.com/CrowdStrike/aws-ssm-distributor.git
    ``` 
2. Change to the `package` directory
    ```bash
    cd aws-ssm-distributor/custom-api-package/package
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
5. Run the packager script
      | Parameter | Description                                                | Required | Default                      |
      | --------- | ---------------------------------------------------------- | -------- | ---------------------------- |
      | `-r`      | The aws region to create the ssm distributor package in.   | Yes      | **N/A**                      |
      | `-b`      | The name of the s3 bucket to upload the required files to. | Yes      | **N/A**                      |
      | `-p`      | The name of the distributor package to create.             | No       | **CrowdStrike-FalconSensor** |

    ```bash
    python3 packager.py -r <AWS_REGION> -b <S3BUCKET> -p <DISTRIBUTOR_PACKAGE_NAME>
    ```

## Generate API Keys

The distributor package uses the CrowdStrike API to download the sensor onto the target instance. It is highly recommended that you create a dedicated API client for the distributor package.

1. In the CrowdStrike console, navigate to **Support and resources** > **API Clients & Keys**. Click **Add new API Client**.
2. Add the following api scopes:

    | Scope               | Permission | Description                                                                  |
    | ------------------- | ---------- | ---------------------------------------------------------------------------- |
    | Installation Tokens | *READ*     | Allows the distributor to pull installation tokens from the CrowdStrike API. |
    | Sensor Download     | *READ*     | Allows the distributor to download the sensor from the CrowdStrike API.      |

3. Click **Add** to create the API client. The next screen will display the API **CLIENT ID**, **SECRET**, and **BASE URL**. You will need all three for the next step.

    <details><summary>picture</summary>
    <p>

    ![api-client-keys](./../official-package/assets/api-client-keys.png)

    </p>
    </details>

> Note: This page is only shown once. Make sure you copy **CLIENT ID**, **SECRET**, and **BASE URL** to a secure location.

## Create AWS Parameter Store Parameters

The distributor package uses AWS Systems Manager Parameter Store to store the API keys. You can create the parameters in the AWS console or using the AWS CLI.

The following parameters must be created:

| Default Parameter Name           | Parameter Value                                                 | Parameter Type |
| -------------------------------- | --------------------------------------------------------------- | -------------- |
| /CrowdStrike/Falcon/Cloud        | The **BASE URL** from [Generate API Keys](#generate-api-keys).  | SecureString   |
| /CrowdStrike/Falcon/ClientId     | The **CLIENT ID** from [Generate API Keys](#generate-api-keys). | SecureString   |
| /CrowdStrike/Falcon/ClientSecret | The **SECRET** from [Generate API Keys](#generate-api-keys).    | SecureString   |
> **Note:** These are the default parameter names the distributor package looks for. You can use any parameter name you want as long as you override the default values when creating the association in the next step.

<details><summary>Using the AWS Console</summary>
<p>

1. In your AWS console, navigate to **AWS Systems Manager** > **Application Management** > **Parameter Store**.
2. Create the parameters mentioned in the table above.

</p>
</details>

<details><summary>Using the AWS CLI</summary>
<p>

We can use the `aws ssm put-parameter` command to create the parameters from the CLI. See the [put-parameter documentation](https://docs.aws.amazon.com/cli/latest/reference/ssm/put-parameter.html) for more information.

```bash
aws ssm put-parameter \
    --name "/CrowdStrike/Falcon/ClientId" \
    --type "SecureString" \
    --description "CrowdStrike Falcon API Client ID for the distributor package" \
    --region "us-east-1" \
    --value "CLIENT_ID"
```

```bash 
aws ssm put-parameter \
    --name "/CrowdStrike/Falcon/ClientSecret" \
    --type "SecureString" \
    --description "CrowdStrike Falcon API Secret for the distributor package" \
    --region "us-east-1" \
    --value "SECRET"
```
```bash
aws ssm put-parameter \
    --name "/CrowdStrike/Falcon/Cloud" \
    --type "SecureString" \
    --description "CrowdStrike Falcon API Base URL for the distributor package" \
    --region "us-east-1" \
    --value "BASE_URL"
```

</p>
</details>

## Create AWS IAM Role

The distributor package uses an AWS IAM role to assume when running the AWS Systems Manager Automation document. The role is used for the following:

- Create/Read/Update AWS Systems Manager Parameter Store parameters
- Describe AWS EC2 instances to determine the platform
- Run the `AWS-ConfigureAWSPackage` document to install the sensor

<details><summary>Using CloudFormation</summary>

A CloudFormation template with the required permissions is available under the [cloudformation](./cloudformation) directory.

You can use the below command to download the template and create the stack.

```bash
curl -s -o ./iam-role.yaml "https://raw.githubusercontent.com/crowdstrike/aws-ssm-distributor/main/custom-api-package/cloudformation/iam-role.yaml" \
&& aws cloudformation create-stack \
  --stack-name crowdstrike-distributor-deploy-role \
  --template-body file://iam-role.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```
</details>

<details>> <summary>Using the AWS CLI</summary>

We can use the `aws iam create-role` command to create the role from the CLI. See the [create-role documentation](https://docs.aws.amazon.com/cli/latest/reference/iam/create-role.html) for more information.

```bash
aws iam create-role \
    --role-name "crowdstrike-distributor-deploy-role" \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ssm.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }' \
    --description "Role for running SSM automation documents" \
    --max-session-duration 3600 \
    --permissions-boundary "arn:aws:iam::aws:policy/service-role/AmazonSSMAutomationRole"
```
</details>

## Create the AWS Systems Manager Automation Document

This document is the entrypoint to the distributor package. It does many things like generating an oauth token, creating the installation token, and running the `AWS-ConfigureAWSPackage` document to install the sensor.

Here is an example of using the `aws ssm create-automation-document` command to create the document. See the [create-automation-document documentation](https://docs.aws.amazon.com/cli/latest/reference/ssm/create-automation-document.html) for more information.

> The below command assumes you are in the `aws-ssm-distributor/custom-api-package` directory.
```bash
aws ssm create-document \
  --content file://automation-doc.yaml \
  --name 'CrowdStrike-FalconSensorInstall' \
  --document-format YAML \
  --document-type Automation \
  --region us-east-1
```

This document has the following parameters:

| Parameter Name         | Description                                                                                                                      | Default Value                    | Required |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- | -------- |
| AutomationAssumeRole   | The ARN of the role that the automation document will assume.                                                                    | N/a                              | Yes      |
| PackageName            | The name chosen when uploading the distributor package in the [previous step](#create-the-distributor-package).                  | CrowdStrike-FalconSensor         | No       |
| PackageVersion         | The version of the distributor package.                                                                                          | N/a                              | No       |
| FalconCloud            | AWS SSM Parameter store name used to store **BASE URL** [created in the previous step](#create-aws-parameter-store-parameters).  | /CrowdStrike/Falcon/Cloud        | Yes      |
| FalconClientId         | AWS SSM Parameter store name used to store **CLIENT ID** [created in the previous step](#create-aws-parameter-store-parameters). | /CrowdStrike/Falcon/ClientId     | Yes      |
| FalconClientSecret     | AWS SSM Parameter store name used to store **SECRET** [created in the previous step](#create-aws-parameter-store-parameters).    | /CrowdStrike/Falcon/ClientSecret | Yes      |
| Action                 | Whether to install or uninstall                                                                                                  | Install                          | No       |
| InstallationType       | The installation type.                                                                                                           | Uninstall and reinstall          | No       |
| WindowsInstallerParams   | The parameters to pass to the installer on Windows nodes.                                                                        | N/a                              | No       |
| LinuxInstallerParams     | The parameters to pass to the installer on Linux nodes.                                                                          | N/a                              | No       |
| WindowsUninstallParams | The parameters to pass to the uninstaller on Windows nodes.                                                                      | N/a                              | No       |
| LinuxUninstallParams   | The parameters to pass to the uninstaller on Linux nodes.                                                                        | N/a                              | No       |


## Using the AWS Systems Manager Distributor Package

Once you've completed the above steps you are ready to start using the distributor package and the aws automation document. You will not execute the distributor package directly. Instead, you will use the automation document we created in the previous step.

The automation document creates the required parameters that will be passed to the distributor package. You can execute the automation document in many ways. See the [AWS documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/running-automations.html) for more information.

This guide will cover using the AWS Systems Manager State Manager to install the sensor on all of our target instances.

### Using AWS Systems Manager State Manager

Using State Manager associations, we can create a single association that will install the sensor on all of our target instances. The association will use the AWS Systems Manager Distributor package to install the sensor. For more information on State Manager, see the [AWS documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-state-about.html).


We can use the `aws ssm create-association` command to create the association from the CLI. See the [create-association documentation](https://docs.aws.amazon.com/cli/latest/reference/ssm/create-association.html) for more information.

Here is an example of creating an association using the AWS CLI that targets all instances. Refer to the [table above](#create-the-aws-systems-manager-automation-document) for more information on the parameters.

```bash
aws ssm create-association \
    --name "CrowdStrike-FalconSensorInstall" \
    --targets "Key=InstanceIds,Values=*" \
    --parameters "AutomationAssumeRole=arn:aws:iam::111111111:role/crowdstrike-ssm-assume-role,PackageName=CrowdStrike-FalconSensor" \
    --association-name "crowdstrike-falcon-sensor-deploy" \
    --automation-target-parameter-name "InstanceIds" \
    --region "us-east-1"
``` 