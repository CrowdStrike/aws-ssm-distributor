variable "aws_regions" {
  description = "The AWS Regions to deploy the CrowdStrike Falcon Sensor to. Defaults to every region the Official Distributor supports."
  type        = list(string)
  default = []
}

variable "exclude_aws_regions" {
  description = "The AWS Regions to exclude from deployment. Defaults to none. Useful for when you want to deploy to most supported except a few."
  type        = list(string)
  default     = []
}

# State Manager Association Variables
variable "linux_package_version" {
  description = "The version of the CrowdStrike Falcon Sensor package to install on Linux. Example 7.0.4.2333, installs N-1 version if no version is specified."
  type        = string
  default     = ""
}

variable "windows_package_version" {
  description = "The version of the CrowdStrike Falcon Sensor package to install on Windows. Example 7.0.4.2333, installs N-1 version if no version is specified."
  type        = string
  default     = ""
}

variable "linux_installer_params" {
  description = "The parameters to pass to the Linux installer at install time."
  type        = string
  default     = ""
}

variable "windows_installer_params" {
  description = "The parameters to pass to the Windows installer at install time."
  type        = string
  default     = ""
}

variable "cron_schedule_expression" {
  description = "The cron schedule expression for the AWS State Manager association. Defaults to every hour."
  type        = string
  default     = "cron(0 0 */1 * * ? *)"
}

# Falcon API Credentials Variables 
variable "secret_storage_method" {
  description = "The method to use for storing the Falcon API credentials. Defaults to SSM."
  type        = string
  default     = "SSM"

  validation {
    condition     = contains(["ssm", "secretsmanager"], lower(var.secret_storage_method))
    error_message = "Secret Storage Method must be one of SSM or SecretsManager. (case-insensitive)"
  }
}

variable "secrets_manager_secret_name" {
  description = "The name of the Secrets Manager secret that will be created to store the Falcon API credentials."
  type        = string
  default     = "CrowdStrike/Falcon/Distributor"

  validation {
    condition     = length(var.secrets_manager_secret_name) <= 64
    error_message = "Secret Name must be less than or equal to 64 characters."
  }
}

variable "falcon_cloud" {
  description = "The Falcon Cloud Region to use."
  type        = string

  validation {
    condition     = contains(["us-1", "us-2", "eu-1"], lower(var.falcon_cloud))
    error_message = "Cloud must be one of us-1, us-2 or eu-1. (case-insensitive)"
  }
}

variable "falcon_client_id" {
  description = "The Client ID of the Falcon API Credentials"
  type        = string
  sensitive   = true
}

variable "falcon_client_secret" {
  description = "The Client Secret of the Falcon API Credentials"
  type        = string
  sensitive   = true
}

variable "falcon_cloud_ssm_parameter_name" {
  description = "The name of the SSM parameter that will be created to store the Falcon Cloud Region."
  type        = string
  default     = "/CrowdStrike/Falcon/Cloud"
}

variable "falcon_client_id_ssm_parameter_name" {
  description = "The name of the SSM parameter that will be created to store the Falcon API Client ID."
  type        = string
  default     = "/CrowdStrike/Falcon/ClientId"
}

variable "falcon_client_secret_ssm_parameter_name" {
  description = "The name of the SSM parameter that will be created to store the Falcon API Client Secret."
  type        = string
  default     = "/CrowdStrike/Falcon/ClientSecret"
}
