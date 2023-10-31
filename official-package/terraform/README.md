# CrowdStrike Falcon Distributor Terraform Module

This terraform code will create an AWS State Manager association that will install the CrowdStrike Falcon Sensor on all EC2 instances in a region. The CrowdStrike Falcon Sensor is installed using the Official CrowdStrike Distributor package.

By default the terraform code will deploy to all regions supported by the Official Distributor package that are enabled on your account.

You can target a subset of regions by setting the `aws_regions` variable. You can also exclude regions by setting the `exclude_aws_regions` variable. See [Inputs](#inputs) for more information on different options.

This terraform module does the following in each region:

- Stores your Falcon API credentials in SSM Parameter Store or Secrets Manager depending on the value of `secret_storage_method`.
- Creates an IAM Role that allows the automation document to read the Falcon API credentials from SSM Parameter Store or Secrets Manager depending on the value of `secret_storage_method`.
- Creates an AWS State Manager association that, by default, runs every 30 minutes and targets every instance in a region. The scheduled occurance can be changed by setting `cron_schedule_expression`.

## Usage

1. Download terraform code located in [this directory](./). 
2. Export your Falcon API credentials as environment variables. Terraform automatically reads any environment variables prefixed with `TF_VAR_` and treats them as input variables. 

```bash
export TF_VAR_falcon_client_id=...
export TF_VAR_falcon_client_secret=...
```

3. Run the following commands, replace `us-1` with the Falcon Cloud Region you want to use:

```bash
terraform init
terraform apply --var='falcon_cloud=us-1'
```

Check out [Inputs](#inputs) for more information on the available variables.


## Providers

| Name                                                                                               | Version  |
| -------------------------------------------------------------------------------------------------- | -------- |
| <a name="provider_aws"></a> [aws](https://registry.terraform.io/providers/hashicorp/aws/latest)    | ~> 5.0.0 |
| <a name="provider_time"></a> [time](https://registry.terraform.io/providers/hashicorp/time/latest) | n/a      |
## Inputs

| Name                                    | Description                                                                                                                                      | Type           | Default                              | Required |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | -------------- | ------------------------------------ | :------: |
| aws_regions                             | The AWS Regions to deploy the CrowdStrike Falcon Sensor to. Defaults to every region the Official Distributor supports.                          | `list(string)` | `[]`                                 |    no    |
| exclude_aws_regions                     | The AWS Regions to exclude from deployment. Defaults to none. Useful for when you want to deploy to most supported except a few.                 | `list(string)` | `[]`                                 |    no    |
| falcon_cloud                            | The Falcon Cloud Region to use. One of `us-1, us-2, eu-1`                                                                                        | `string`       | n/a                                  |   yes    |
| falcon_client_id                        | The Client ID of the Falcon API Credentials                                                                                                      | `string`       | n/a                                  |   yes    |
| falcon_client_secret                    | The Client Secret of the Falcon API Credentials.                                                                                                 | `string`       | n/a                                  |   yes    |
| secret_storage_method                   | The method to use for storing the Falcon API credentials. One of `SSM, SecretsManager`                                                           | `string`       | `"SSM"`                              |    no    |
| secrets_manager_secret_name             | The name of the Secrets Manager secret that will be created to store the Falcon API credentials.                                                 | `string`       | `"CrowdStrike/Falcon/Distributor"`   |    no    |
| falcon_cloud_ssm_parameter_name         | The name of the SSM parameter that will be created to store the Falcon Cloud Region.                                                             | `string`       | `"/CrowdStrike/Falcon/Cloud"`        |    no    |
| falcon_client_id_ssm_parameter_name     | The name of the SSM parameter that will be created to store the Falcon API Client ID.                                                            | `string`       | `"/CrowdStrike/Falcon/ClientId"`     |    no    |
| falcon_client_secret_ssm_parameter_name | The name of the SSM parameter that will be created to store the Falcon API Client Secret.                                                        | `string`       | `"/CrowdStrike/Falcon/ClientSecret"` |    no    |
| cron_schedule_expression                | The cron schedule expression for the AWS State Manager association. Defaults to every hour.                                                      | `string`       | `"cron(0 0 */1 * * ? *)"`            |    no    |
| linux_installer_params                  | The parameters to pass to the Linux installer at install time.                                                                                   | `string`       | `""`                                 |    no    |
| linux_package_version                   | The version of the CrowdStrike Falcon Sensor package to install on Linux. Example 7.0.4.2333, installs N-1 version if no version is specified.   | `string`       | `""`                                 |    no    |
| windows_installer_params                | The parameters to pass to the Windows installer at install time.                                                                                 | `string`       | `""`                                 |    no    |
| windows_package_version                 | The version of the CrowdStrike Falcon Sensor package to install on Windows. Example 7.0.4.2333, installs N-1 version if no version is specified. | `string`       | `""`                                 |    no    |
## Outputs

| Name             | Description                                                      |
| ---------------- | ---------------------------------------------------------------- |
| deployed_regions | The regions being managed by the CrowdStrike Distributor package |
