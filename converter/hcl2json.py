#!/usr/bin/env python3

import hcl2
import os
import json
import click
from pathlib import Path
import logging
import boto3
from botocore.exceptions import ClientError

def file_save(file, json_string, env, bucket, path, s3_client):
    filepath = str(file)
    output_file = filepath.replace('hcl', 'json')
    print(output_file)
    
    try:
        s3_client.put_object(
            Body=json_string, 
            Bucket=bucket, 
            Key=output_file
        )
    except ClientError as e:
         logging.error(e)
         return False

def convert(file, env, bucket, path, s3_client):
    with open(file, 'r') as content:
        hcl_content = hcl2.load(content)
        js_content = {}
        js_content['locals'] = hcl_content['locals'][0]
        json_string = json.dumps(js_content)
        file_save(file, json_string, env, bucket, path, s3_client)

@click.command()
@click.option('--path', envvar='HCL2JSON_PATH', default="", required=False, help="Path to hcl files")
@click.option('--env', envvar='HCL2JSON_ENV', default="default", required=False, help="AWS Profile")
@click.option('--bucket', envvar='HCL2JSON_BUCKET', default="terragrunt-vars", required=False, help="Variables bucket")
def main(path, env, bucket):

    session = boto3.Session(profile_name=env)
    s3_client = session.client('s3')

    if not path:
        path = "./"

    for file in Path(path).rglob('*.hcl'):
        convert(file, env, bucket, path, s3_client)

if __name__ == '__main__':
    main()