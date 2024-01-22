include {
  path = find_in_parent_folders()
}

locals {
    account_vars = read_terragrunt_config(find_in_parent_folders("account.hcl"))
    region_vars = read_terragrunt_config(find_in_parent_folders("region.hcl"))
    ssm_vars = jsondecode(run_cmd(
        "aws", "ssm", "get-parameter", 
        "--profile", "${local.account_vars.locals.aws_profile}",
        "--region", "${local.account_vars.locals.main_region}",
        "--name", "${local.account_vars.locals.common_params}",
        "--with-decryption",
        "--query", "Parameter.Value", "--output", "text"
    ))
    s3_vars = jsondecode(run_cmd(
        "aws", "s3", "cp",
        "--profile", "${local.account_vars.locals.aws_profile}",
        "--region", "${local.account_vars.locals.main_region}",
        "${local.account_vars.locals.params_file}",
        "-"
    ))
}

terraform {
    source = "${get_parent_terragrunt_dir()}/../../modules//test_module"
}

inputs = merge(
    local.account_vars.locals,
    local.region_vars.locals,
    local.ssm_vars.locals,
    local.s3_vars.locals
)
