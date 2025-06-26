data "aws_regions" "all" {}

locals {
  cs_supported_regions = [
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "af-south-1",
    "ap-east-1",
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-south-1",
    "ap-southeast-1",
    "ap-southeast-2",
    "ca-central-1",
    "eu-central-1",
    "eu-north-1",
    "eu-south-1",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "me-south-1",
    "sa-east-1",
  ]

  # target regions is the subset of regions that are supported by CrowdStrike and were targeted by the user either by passing in aws_regions or by defaulting to all supported regions (data.aws_regions.all.names)
  target_regions = length(var.aws_regions) == 0 ? [for region in data.aws_regions.all.names : region if contains(local.cs_supported_regions, region)] : [for region in var.aws_regions : region if contains(local.cs_supported_regions, region)]

  # regions are the regions we will deploy to, which is the target regions minus the excluded regions
  regions = [for region in local.target_regions : region if !contains(var.exclude_aws_regions, region)]
}

resource "aws_iam_role" "ssm_assume_role" {
  name = "crowdstrike-distributor-deploy-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ssm.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachments_exclusive" "ssm_assume_role" {
  role_name   = aws_iam_role.ssm_assume_role.name
  policy_arns = lower(var.secret_storage_method) == "secretsmanager" ? [
    "arn:aws:iam::aws:policy/service-role/AmazonSSMAutomationRole",
    "arn:aws:iam::aws:policy/SecretsManagerReadWrite",
    ] : [
    "arn:aws:iam::aws:policy/service-role/AmazonSSMAutomationRole",
  ]
}

resource "time_sleep" "ssm_assume_role" {
  triggers = {
    ssm_assume_role_arn = aws_iam_role.ssm_assume_role.arn
  }
  create_duration = "10s"
}


module "crowdstrike_distributor_us_east_1" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"us-east-1") ? 1 : 0

  providers = {
    aws = aws.us_east_1
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_us_east_2" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"us-east-2") ? 1 : 0

  providers = {
    aws = aws.us_east_2
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_us_west_1" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"us-west-1") ? 1 : 0

  providers = {
    aws = aws.us_west_1
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_us_west_2" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"us-west-2") ? 1 : 0

  providers = {
    aws = aws.us_west_2
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_af_south_1" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"af-south-1") ? 1 : 0

  providers = {
    aws = aws.af_south_1
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_ap_east_1" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"ap-east-1") ? 1 : 0

  providers = {
    aws = aws.ap_east_1
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_ap_northeast_1" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"ap-northeast-1") ? 1 : 0

  providers = {
    aws = aws.ap_northeast_1
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_ap_northeast_2" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"ap-northeast-2") ? 1 : 0

  providers = {
    aws = aws.ap_northeast_2
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_ap_south_1" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"ap-south-1") ? 1 : 0

  providers = {
    aws = aws.ap_south_1
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_ap_southeast_1" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"ap-southeast-1") ? 1 : 0

  providers = {
    aws = aws.ap_southeast_1
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_ap_southeast_2" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"ap-southeast-2") ? 1 : 0

  providers = {
    aws = aws.ap_southeast_2
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_ca_central_1" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"ca-central-1") ? 1 : 0

  providers = {
    aws = aws.ca_central_1
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_eu_central_1" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"eu-central-1") ? 1 : 0

  providers = {
    aws = aws.eu_central_1
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_eu_north_1" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"eu-north-1") ? 1 : 0

  providers = {
    aws = aws.eu_north_1
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_eu_south_1" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"eu-south-1") ? 1 : 0

  providers = {
    aws = aws.eu_south_1
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_eu_west_1" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"eu-west-1") ? 1 : 0

  providers = {
    aws = aws.eu_west_1
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_eu_west_2" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"eu-west-2") ? 1 : 0

  providers = {
    aws = aws.eu_west_2
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_eu_west_3" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"eu-west-3") ? 1 : 0

  providers = {
    aws = aws.eu_west_3
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_me_south_1" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"me-south-1") ? 1 : 0

  providers = {
    aws = aws.me_south_1
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

module "crowdstrike_distributor_sa_east_1" {
  source = "./modules/crowdstrike-distributor"

  count = contains(local.regions,"sa-east-1") ? 1 : 0

  providers = {
    aws = aws.sa_east_1
  }

  ssm_assume_role_arn = time_sleep.ssm_assume_role.triggers["ssm_assume_role_arn"]
  linux_package_version = var.linux_package_version
  windows_package_version = var.windows_package_version
  linux_installer_params = var.linux_installer_params
  windows_installer_params = var.windows_installer_params
  cron_schedule_expression = var.cron_schedule_expression

  falcon_client_id = var.falcon_client_id
  falcon_client_secret = var.falcon_client_secret
  falcon_cloud = var.falcon_cloud

  secret_storage_method = var.secret_storage_method
  secrets_manager_secret_name = var.secrets_manager_secret_name
  falcon_cloud_ssm_parameter_name = var.falcon_cloud_ssm_parameter_name
  falcon_client_id_ssm_parameter_name = var.falcon_client_id_ssm_parameter_name
  falcon_client_secret_ssm_parameter_name = var.falcon_client_secret_ssm_parameter_name

  depends_on = [
    aws_iam_role.ssm_assume_role
  ]
}

