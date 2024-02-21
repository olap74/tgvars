#!/usr/bin/env python3

import hcl2
import os
import sys
import click
from pathlib import Path
from jinja2 import Template
import re
import glob


### Defining constants
ENVS_LIST = ['dev','prod','stage']
REGIONS = ['ap-northeast-1','ap-southeast-1','ap-southeast-2','ca-central-1','eu-central-1','eu-west-2','us-east-1','us-west-2']
GIT_LINK = "git::git@github.com:user/repo.git"

def process_hcl(path,dry_run):
    ### Loading hcl file
    with open(path, 'r') as content:
        hcl_content = hcl2.load(content)
        ### Checking if common_vars already exists. That means provider was modified already
        if 'locals' in hcl_content:
            test = hcl_content['locals'][0]['common_vars']
            if test:
                print("File was transformed already...")
        else:
            ### Taking variables from Terraform config of terragrunt.hcl file
            variable_args = hcl_content['terraform'][0]['extra_arguments'][0]['vars']['arguments']
            ### Taking source (path to module). The main task is to find path starting from "modules" directory.
            source = hcl_content['terraform'][0]['source']
            ### Removing Terraform prefixes and converting to list by "/" pattern
            source_path = source.replace('${get_parent_terragrunt_dir()}','').split("/")
            ### Removing empty elements and alements containing ".."
            source_path = [x for x in source_path if x != '' and x != '..']
            ### Merging path to string with "/" as a delimiter. After this step we have a path to module drom repository root.
            source_path_local = "/".join(source_path)
            ### Adding path to module to the git link
            source_path_new = f'{GIT_LINK}//{source_path_local}?ref=${{local.account_vars.locals.modules_source_ref}}'
            vars_list = {}
            extra_vars_content = []
            extra_vars_path = str(path).replace('terragrunt.hcl','') + "*.tfvars"
            extra_vars_files = glob.glob(extra_vars_path)
            if len(extra_vars_files) > 0:
                for tfvars_file in extra_vars_files:
                    print(tfvars_file)
                    try:
                        with open(tfvars_file) as f:
                            lines = f.read().splitlines()
                            clear_lines = list(filter(None, lines))
                            extra_vars_content.extend(clear_lines)
                    except Exception as e:
                        print (f"Cannont process tfvars file {e}")

            count = 0
            ### Processing variables
            for arg in variable_args:
                ### Processing common variables
                if "variables" in arg:
                    ### Removing all possible Terragrunt commands and "..". Also replacing variable files extension from tfvars to hcl
                    arg = arg.replace('-var-file=${get_parent_terragrunt_dir()}/variables','').replace('-var-file=${get_terragrunt_dir()}/','').replace('/variables','').replace('..','').replace('tfvars','hcl')
                    ### Removing possible multiplied slashes
                    _RE_COMBINE_SLASHES = re.compile(r"\/+")
                    arg = _RE_COMBINE_SLASHES.sub("/", arg).strip()

                    ### Looking up for Terragrunt variable name for Terraform variables location. For this purpose getting a variable file name and removing extension
                    key_selection = arg.split("/")
                    key = key_selection[-1].replace('.hcl','')
                    key_name = ''
                    ### Looking up for standard common_vars, region_vars and env_vars
                    if key in ENVS_LIST:
                        key_name = 'env_vars'
                    elif key == 'common':
                        key_name = 'common_vars'
                    elif key in REGIONS and 'clusters' not in key_selection:
                        key_name = 'region_vars'
                    ### If this variable file is something else using "extra_vars" name with incremental number at the end.
                    else:
                        count += 1
                        key_name = f'extra_vars{count}'
                    ### Saving new variables name and link that will be added to 'locals' section
                    vars_list[key_name] = f'read_terragrunt_config("${{get_parent_terragrunt_dir()}}/variables{arg}")'
                ### Processing module variables in the same way. Replacing name and replacing Terragrunt functions
                elif '..' in arg:
                    arg = arg.replace('-var-file=','').replace('tfvars','hcl')
                    key_selection = arg.split("/")
                    key = key_selection[-1].replace('.hcl','').replace('-','_')
                    arg = f'read_terragrunt_config("{arg}")'
                    count += 1
                    key = f'{key}{count}'
                    vars_list[key] = arg

            ### Defining a script location. This is needed to define where new terragrunt.hcl template is located
            template_file = __file__.replace('migration.py','terragrunt.hcl.j2')
            try:
                ### Processing template file
                with open(template_file) as file_:
                    template = Template(file_.read()).render(source = source_path_new, vars = vars_list, extra_vars = extra_vars_content)
            except:
                print('Error! Template not found!')
                sys.exit(2)
                
            #print(template)
            ### Saving original terragrunt.hcl to terragrunt.old file and saving a new file from template to terragrunt.hcl
            backup = str(path).replace('hcl','old')
            if not dry_run:
                print("Writing the new config...")
                os.rename(path, backup)
                output = open(path, 'w')
                output.writelines(template)
                output.close()

@click.command()
@click.option('--path', envvar='HCL2JSON_PATH', required=True, help="Path to providers")
@click.option('--dry-run/--apply', envvar='HCL2JSON_DRY_RUN', default=True, help="Enable read-only (Default: enabled)")
def main(path,dry_run):
    env_path = path
    
    ### Looking up for files terragrunt.hcl under path specified
    for path in Path(env_path).rglob('terragrunt.hcl'):
        print(f'Processing file {path}')
        process_hcl(path,dry_run)
        print("--------------------------")

if __name__ == '__main__':
    main()
