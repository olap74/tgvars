#!/usr/bin/env python3

import hcl2
import os
import sys
import click
from pathlib import Path

GITDIR = 'git/'
GIT_HTTP_LINK = 'https://github.com/user'
GIT_LINK = 'git::git@github.com:user/repo.git/'
SOURCE_REPO = "source-repo"

def create_readme(readme_file, readme_message):
    try:
        readmef = open(readme_file, "w")
        readmef.write(readme_message)
        readmef.close()
    except Exception as e:
        print ("Cannot open readme file for write")
        print (e.message)

def process_hcl(path,dry_run):
    with open(path, 'r') as content:
        hcl_content = hcl2.load(content)

        sp_path = str(path).replace(GITDIR,'')
        sp_path_splitted = sp_path.split("/")
        current_repo = sp_path_splitted[0]
        repo_path_list = sp_path_splitted[1:]
        repo_path = "/".join(repo_path_list)
        sp_path_splitted[0] = SOURCE_REPO
        sp_path_full = GITDIR + "/".join(sp_path_splitted)
        readme_message = "## Provider was migrated to => ["+current_repo+"](" + GIT_HTTP_LINK + "/"+current_repo+"/tree/main/"+repo_path+")"
        readme_file = sp_path_full.replace('terragrunt.hcl','README.md')
        
        if os.path.isfile(sp_path_full):
            print(f'Provider found in {SOURCE_REPO}')
            if not dry_run:
                create_readme(readme_file, readme_message)
                print (f"Removing {sp_path_full}")
                os.remove(sp_path_full)
            else:
                print("Readme file creation skipped because dry_run is used")
                print(f'{sp_path_full} is NOT removed because dry_run is set')
        
        module_readme = GITDIR + SOURCE_REPO + (hcl_content['terraform'][0]['source']).replace(GIT_LINK,'').replace('?ref=${local.account_vars.locals.modules_source_ref}','') + "/README.md"

        if os.path.isfile(module_readme):
            print("Module README found")
            readmef = open(module_readme, "rt")
            module_readme_data = readmef.read()
            readmef.close()
            if repo_path in module_readme_data:
                print("Found provider entry in module readme")
                old_link = SOURCE_REPO + "/" + repo_path
                new_link = current_repo + "/" + repo_path
                module_readme_data = module_readme_data.replace(old_link, new_link)
                if not dry_run:
                    print("Updating module readme")
                    readmew = open(module_readme, "wt")
                    readmew.write(module_readme_data)
                    readmew.close()
                else:
                    print("Module readme cannot be updated due to dry_run enabled")
            else:
                print("Provider data was not found ")

        else:
            print("Module README not found")

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
