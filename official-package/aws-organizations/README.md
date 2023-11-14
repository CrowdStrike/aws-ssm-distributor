# CrowdStrike Falcon Distributor for AWS Organizations

This AWS SAM deployment will create an AWS State Manager association in each child account and region in an AWS Organization. Each Association will install the CrowdStrike Falcon Sensor on all SSM-Managed EC2 instances in a region. The CrowdStrike Falcon Sensor is installed using the Official CrowdStrike Distributor package.

This deployment provisions the following in each region:

- Stores your Falcon API credentials in SSM Parameter Store or Secrets Manager depending on the value of `SecretStorageMethod`.
- Creates an IAM Role that allows the automation document to read the Falcon API credentials from SSM Parameter Store or Secrets Manager depending on the value of `SecretStorageMethod`.
- Creates an AWS State Manager association that runs at a rate or scheduled occurence based on the value of `ScheduleExpression`.

## Usage

1. Install AWS SAM. [AWS SAM Installation Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
2. Configure AWS CLI with the credentials for your Organization Management account. [AWS CLI Configuration Guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)
3. Download the code located in [this directory](./). 
4. Review and update the parameter values in [samconfig.toml](./samconfig.toml)
5. Run the following command:

```bash
python3 crowdstrike-ssm-distributor-deploy.py
```

Check out [Parameters](#parameters) for more information on the available variables.

## Parameters

| Name                                    | Description                                                                                                                                      | Type           | Default                              | Required |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | -------------- | ------------------------------------ | :------: |
| s3_bucket                             | The AWS S3 Bucket to upload SAM Deployment files.                         | `string` | `[]`                                 |    yes    |
| Regions                             | The AWS Regions to deploy the CrowdStrike Falcon Sensor to.                         | `list(string)` | `[]`                                 |    yes    |
| ProvisionOU                     | The AWS Organization OU to deploy the CrowdStrike Falcon Sensor to.  To deploy to the entire organization, provide the root OU (r-****).  Multiple OUs may be provided separated by commas.         | `list(string)` | `[]`                                 |    yes    |
| FalconClientID                            | The Client Id of the Falcon API Credentials.                                                                                        | `string`       | n/a                                  |   yes    |
| FalconSecret                        | The Secret of the Falcon API Credentials.                                                                                                      | `string`       | n/a                                  |   yes    |
| BaseURL                    | The Base URL of the Falcon API Credentials.                                                                                                 | `string`       | n/a                                  |   yes    |
| SecretStorageMethod                   | The method to use for storing the Falcon API credentials. One of `ParameterStore, SecretsManager`                                                           | `string`       | `"ParameterStore"`                              |    yes    |
| SecretsManagerSecretName             | The name of the Secrets Manager secret that will be created to store the Falcon API credentials.                                                 | `string`       | `"CrowdStrike/Falcon/Distributor"`   |    yes    |
| FalconClientIdParameter         | The name of the SSM parameter that will be created to store the Falcon Client Id.                                                             | `string`       | `"/CrowdStrike/Falcon/Cloud"`        |    yes    |
| FalconSecretParameter     | The name of the SSM parameter that will be created to store the Falcon API Secret.                                                            | `string`       | `"/CrowdStrike/Falcon/ClientId"`     |    yes    |
| BaseURLParameter | The name of the SSM parameter that will be created to store the Falcon API Base URL.                                                        | `string`       | `"/CrowdStrike/Falcon/Cloud"` |    yes    |
| DocumentVersion                | The version of the SSM document to associate with the target. Allowed values: $DEFAULT, $LATEST, or a numeric verion eg. '2'                                                      | `string`       | `"$DEFAULT"`            |    yes    |
| Action                  | Specify whether or not to install or uninstall the package.                                                                                   | `string`       | `"install"`                                 |    yes    |
| ApplyOnlyAtCronInterval                   | By default, when you create a new association, the system runs it immediately after it is created and then according to the schedule you specified. Specify true if you don't want an association to run immediately after you create it.   | `string`       | `"true"`                                 |    yes    |
| ScheduleExpression                | The cron schedule expression for the AWS State Manager association. Defaults to every hour.                                                                                 | `string`       | `"cron(0 0 */1 * * ? *)"`                                 |    yes    |
| AutomationAssumeRole                 | Execution Role name for CrowdStrike SSM Distributor Package. | `string`       | `"crowdstrike-distributor-deploy-role"`                                 |    yes    |
| MaxErrors                 | The number of errors that are allowed before the system stops sending requests to run the association on additional targets. You can specify either an absolute number of errors, for example 10, or a percentage of the target set, for example 10%. | `string`       | `"10%"`                                 |    yes    |
| MaxConcurrency                 | The maximum number of targets allowed to run the association at the same time. You can specify a number, for example 10, or a percentage of the target set, for example 10%. | `string`       | `"20%"`                                 |    yes    |
| ComplianceSeverity                 | The severity level that is assigned to the association. | `string`       | `"UNSPECIFIED"`                                 |    yes    |

## Uninstall

1. To uninstall sensors in a particular account/region: Navigate to the the Association in Systems Manager > State Manager. Change 'Action' to 'uninstall' and select "Apply Association Now".
2. To uninstall all sensors deployed by the SAM Deployment: In samconfig.toml, update the value of 'action' to 'uninstall' and re-run `python3 crowdstrike-ssm-distributor-deploy.py`.  A changeset will be applied and all associations will be re-applied with the uninstall action.
3. To remove the SAM Deployment associations and stacksets from your account: validate the paramater values in samconfig.toml and run `python3 crowdstrike-ssm-distributor-delete.py` **Note** this will not uninstall sensors, see step two. 
