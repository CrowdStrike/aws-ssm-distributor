locals {
  falcon_cloud          = lower(var.falcon_cloud)
  secret_storage_method = lower(var.secret_storage_method)

  cloud_mappings = {
    us-1 = "api.crowdstrike.com"
    us-2 = "api.us-2.crowdstrike.com"
    eu-1 = "api.eu-1.crowdstrike.com"
  }

  secret_storage_method_mappings = {
    parameterstore = "ParameterStore"
    secretsmanager = "SecretsManager"
  }
}


# Falcon API Credentials
resource "aws_secretsmanager_secret" "distributor_secret" {
  count = local.secret_storage_method == "secretsmanager" ? 1 : 0

  name        = var.secrets_manager_secret_name
  description = "Falcon API Credentials for CrowdStrike Distributor"
}

resource "aws_secretsmanager_secret_version" "distributor_secret_version" {
  count = local.secret_storage_method == "secretsmanager" ? 1 : 0

  secret_id     = aws_secretsmanager_secret.distributor_secret[0].id
  secret_string = <<EOF
{
  "Cloud": "${local.cloud_mappings[local.falcon_cloud]}",
  "ClientId": "${var.falcon_client_id}",
  "ClientSecret": "${var.falcon_client_secret}"
}
EOF

  depends_on = [aws_secretsmanager_secret.distributor_secret]
}

resource "aws_ssm_parameter" "falcon_cloud" {
  count = local.secret_storage_method == "parameterstore" ? 1 : 0

  name  = var.falcon_cloud_ssm_parameter_name
  type  = "String"
  value = local.cloud_mappings[local.falcon_cloud]
}

resource "aws_ssm_parameter" "falcon_client_id" {
  count = local.secret_storage_method == "parameterstore" ? 1 : 0

  name  = var.falcon_client_id_ssm_parameter_name
  type  = "SecureString"
  value = var.falcon_client_id
}

resource "aws_ssm_parameter" "falcon_client_secret" {
  count = local.secret_storage_method == "parameterstore" ? 1 : 0

  name  = var.falcon_client_secret_ssm_parameter_name
  type  = "SecureString"
  value = var.falcon_client_secret
}

resource "aws_ssm_association" "sensor_deploy" {
  association_name = "CrowdStrike-Sensor-Deploy"

  name = "CrowdStrike-FalconSensorDeploy"

  schedule_expression = var.cron_schedule_expression

  targets {
    key    = "InstanceIds"
    values = ["*"]
  }

  automation_target_parameter_name = "InstanceIds"

  parameters = {
    AutomationAssumeRole     = var.ssm_assume_role_arn
    FalconCloud              = var.falcon_cloud_ssm_parameter_name
    FalconClientId           = var.falcon_client_id_ssm_parameter_name
    FalconClientSecret       = var.falcon_client_secret_ssm_parameter_name
    SecretStorageMethod      = local.secret_storage_method_mappings[local.secret_storage_method]
    SecretsManagerSecretName = var.secrets_manager_secret_name
    LinuxPackageVersion      = var.linux_package_version
    LinuxInstallerParams     = var.linux_installer_params
    WindowsPackageVersion    = var.windows_package_version
    WindowsInstallerParams   = var.windows_installer_params
  }

  depends_on = [
    aws_ssm_parameter.falcon_cloud,
    aws_ssm_parameter.falcon_client_id,
    aws_ssm_parameter.falcon_client_secret,
    aws_secretsmanager_secret_version.distributor_secret_version,
  ]
}
