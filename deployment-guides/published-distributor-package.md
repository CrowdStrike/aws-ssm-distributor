# Offical AWS Distributor Package

This deployment guide outlines the steps required to use the published third party distributor package in AWS. This method prevents the need to build your own packages and publish your own SSM automation documents to AWS.

New versions of the Falcon Distributor Package are published to the AWS every time a new version of the Falcon Sensor is released.

## Generate API Keys

The distributor package uses the CrowdStrike API to download the sensor onto the target Host. It is highly recommended that you create a dedicated API client for the distributor package.

1. In the CrowdStrike console, navigate to **Support and resources** > **API Clients & Keys**. Click **Add new API Client**.
2. Add the following api scopes:

    | Scope | Permission | Description |
    | --- | --- | --- |
    | Installation Tokens | *READ* | Allows the distributor to pull installation tokens from the CrowdStrike API. |
    | Sensor Downloads | *READ* | Allows the distributor to download the sensor from the CrowdStrike API. |

3. Click **Add** to create the API client. The next screen will display the API **CLIENT ID**, **SECRET**, and **BASE URL**. You will need all three for the next step.

## Create AWS Parameter Store Parameters

1. In your AWS console, navigate to **AWS Systems Manager** > **Application Management** > **Parameter Store**.
2. Create the following parameters

    | Default Parameter Name | Parameter Value | Parameter Type |
    | --- | --- | --- |
    | /CrowdStrike/Falcon/Cloud | The **BASE URL** from [Generate API Keys](#generate-api-keys). | SecureString |
    | /CrowdStrike/Falcon/ClientID | The **CLIENT ID** from [Generate API Keys](#generate-api-keys). |SecureString |
    | /CrowdStrike/Falcon/ClientSecret | The **SECRET** from [Generate API Keys](#generate-api-keys). | SecureString |
    > **Note:** These are the default parameter names the distributor package looks for. You can use any parameter name you want as long as you override the default values when creating the assocation in the next step.

## Create AWS Systems Manager Association

The CrowdStrike sensor for windows and linux do not share the same release versions. Because of this there are two separate distributor packages. You will need to create an association for each operating system.

1. In the AWS console, go to **AWS Systems Manager** > **Node Management** > **Distributor** > **Third Party**.
2. Select the package for the operating system you want to deploy.
   ![distributor-package](./assets/distributor-third-party-tab.png)
3. Under **Document** choose **Default at runtime** for **Document Version** (the default document version will always be the most stable)
4. Under **Execution** choose **Rate Control** 
5. Under **Targets**, choose the method you want to use to target hosts. For more information on targeting hosts, see [Targeting](https://docs.aws.amazon.com/systems-manager/latest/userguide/running-automations-map-targets.html).
    > **Note:** Whatever method you choose to target your systems with ensure that the targeted systems are running the correct operating system for the distributor package you are using. See [Example Targeting](#Example-Targeting) for an example of targeting systems based on tags and Resource Groups.
6. Fill in the required parameters. 
    | Parameter Name | Description | Default Value | Required |
    | --- | --- | --- | --- |
    | PackageName | The Distributor package name. For Windows use FalconSensor-Windows, for Linux use FalconSensor-Linux. | **N/a** | Yes |
    | PackageVersion | The version of the package to install. | **N-2** | No |
    | FalconCloud | AWS SSM Parameter store name used to store **BASE URL** [created in the previous step](#create-aws-parameter-store-parameters). | **/CrowdStrike/Falcon/Cloud** | Yes |
    | FalconClientID | AWS SSM Parameter store name used to store **CLIENT ID** [created in the previous step](#create-aws-parameter-store-parameters). | **/CrowdStrike/Falcon/ClientID** | Yes |
    | FalconClientSecret | AWS SSM Parameter store name used to store **SECRET** [created in the previous step](#create-aws-parameter-store-parameters). | **/CrowdStrike/Falcon/ClientSecret** | Yes |
    | AutomationAssumeRole | The ARN of the role that the automation document will assume. | **N/a** | Yes |
    | Action | Whether to install or uninstall | **Install** | No |
    | InstallationType | The installation type. | **Uninstall and reinstall** | No |
    | InstallerParams | The parameters to pass to the installer. | **N/a** | No |

7. Click **Create Association**.


You can also use the AWS CLI to create the state manager association. See the [AWS CLI documentation](https://docs.aws.amazon.com/cli/latest/reference/ssm/create-association.html) for more information.

Here is an example of creating an association using the AWS CLI that targets a Resource Group named `crowdstrike-sensor-deploy-windows`.
```bash
aws ssm create-association \
    --name "CrowdStrike-FalconSensorDeploy" \
    --targets "Key=resource-groups:Name,Values=crowdstrike-sensor-deploy-windows" \
    --parameters "PackageName=FalconSensor-Windows" \
    --association-name "CrowdStrike-FalconSensorDeploy-Windows" \
```

## Example Targeting







