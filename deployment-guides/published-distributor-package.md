# Offical AWS Distributor Package

This deployment guide outlines the steps required to use the published third party distributor package in AWS. This method prevents the need to build your own packages and publish your own SSM automation documents to AWS.

New versions of the Falcon Distributor Package are published to the AWS Marketplace every time a new version of the Falcon Sensor is released.

## Generate API Keys

The distributor package uses the CrowdStrike API to download the sensor onto the target Host.

In the CrowdStrike console, navigate to **Settings** > **API Clients & Keys**.

| Scope | Permission |
| --- | --- |
| Installation Tokens | *READ* |
| Sensor Downloads | *READ* |


