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
    | /CrowdStrike/Falcon/Cloud | The **BASE URL** from [Generate API Keys](#Generate-API-Keys). | SecureString |
    | /CrowdStrike/Falcon/ClientID | The **CLIENT ID** from [Generate API Keys](#Generate-API-Keys). |SecureString |
    | /CrowdStrike/Falcon/ClientSecret | The **SECRET** from [Generate API Keys](#Generate-API-Keys). | SecureString |
    > **Note:** These are the default parameter names the distributor package looks for. You can use any parameter name you want as long as you override the default values when creating the assocation in the next step.

## Create AWS Systems Manager Association

The CrowdStrike sensor for windows and linux do not share the same release versions. Because of this there are two separate distributor packages. You will need to create an association for each operating system.

1. In the AWS console, go to **AWS Systems Manager** > **Node Management** > **Distributor** > **Third Party**.
2. Select the package for the operating system you want to deploy.
   ![distributor-package](./assets/distributor-third-party-tab.png)
3. Fill in the required parameters. 
    > **Note:** if you used a different parameter name than the default, you will need to override the default values here.
4. Click **Create Association**.


