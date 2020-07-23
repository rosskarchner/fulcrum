import io
import os
import json

import boto3
from cfn_custom_resource import lambda_handler, create, update, delete

s3_client = boto3.client("s3")
s3 = boto3.resource("s3")
sf = boto3.client('stepfunctions')

def create_or_update(event):
    bucket_name = os.environ['THEME_BUCKET']

    bucket = s3.Bucket(bucket_name)
    template_clean= True
    css_clean = True

    # This will be a flag that stops the bucket watching function from
    # from kicking off a design refresh prematurely
    bucket.upload_file('LOCK','LOCK')

    def upload_file_if_key_does_not_exist(filename, key):
      try:
        s3_client.head_object(Bucket=bucket_name, Key= key)
      except s3_client.exceptions.ClientError:
        bucket.upload_file(filename, key)

    upload_file_if_key_does_not_exist('default_template.mustache', 'template.mustache') 
    upload_file_if_key_does_not_exist('default_styles.css', 'styles.css') 

    resource_id = 'https://' + event["ResourceProperties"]['domain'] + '/'

    s3_client.delete_object(Bucket=bucket_name,Key='LOCK')

    return resource_id, event['ResourceProperties']


@create()
def create(event, context):
    return create_or_update(event)


@update()
def update(event, context):
    return create_or_update(event)


@delete()
def delete(event, context):
    return
