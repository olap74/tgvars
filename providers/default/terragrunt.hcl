# Terragrunt is a thin wrapper for Terraform that provides extra tools for working with multiple Terraform modules,
# remote state, and locking: https://github.com/gruntwork-io/terragrunt
# Configure Terragrunt to automatically store tfstate files in an S3 bucket
remote_state {
  backend = "s3"

  config = {
    encrypt        = true
    bucket         = "terraform-states"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks-testvars"

    # .aws-profile is also used by the docker wrapper scripts.
    # TERRAGRUNT_PROFILE is set to '' by the docker wrapper scripts to force
    # loading credentials from the environment when aws-vault is used.
    profile = get_env("TERRAGRUNT_PROFILE", chomp(file(".aws-profile")))
  }
}

locals {
  terraform_version  = chomp(file("../../.terraform-version"))
  terragrunt_version = chomp(file("../../.terragrunt-version"))
}

terraform_version_constraint = local.terraform_version

terragrunt_version_constraint = ">= ${local.terragrunt_version}"

generate "provider" {
  path      = "gen-terraform.tf"
  if_exists = "overwrite"

  contents = <<EOF
provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

terraform {
  backend "s3" {}

  required_providers {
    aws = {
      version = "~> 4.39"
    }
  }
}
EOF
}

generate "tfenv" {
  path              = ".terraform-version"
  if_exists         = "overwrite"
  disable_signature = true

  contents = <<EOF
${local.terraform_version}
EOF
}

inputs = {
  tags = {
    Terraform  = "true"
    Provider   = "default/${path_relative_to_include()}"
  }
}

terraform {
  after_hook "remove_lock" {
    commands = [
      "apply",
      "console",
      "destroy",
      "import",
      "init",
      "plan",
      "push",
      "refresh",
    ]

    execute = [
      "rm",
      "-f",
      "${get_terragrunt_dir()}/.terraform.lock.hcl",
    ]

    run_on_error = true
  }
}
