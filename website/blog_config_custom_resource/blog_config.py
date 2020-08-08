import io
import os
import json

import boto3
from cfn_custom_resource import lambda_handler, create, update, delete

s3_client = boto3.client("s3")
s3 = boto3.resource("s3")
sf = boto3.client('stepfunctions')
bucket_name = os.environ['THEME_BUCKET']
bucket = s3.Bucket(bucket_name)

dynamodb = boto3.resource('dynamodb')
table =  dynamodb.Table(os.environ['TABLE'])
stepfunctions = boto3.client('stepfunctions')

def create_or_update(event):

  def upload_file_if_key_does_not_exist(filename, key):
    try:
      s3_client.head_object(Bucket=bucket_name, Key= key)
    except s3_client.exceptions.ClientError:
      bucket.upload_file(filename, key)

  upload_file_if_key_does_not_exist('default_template.mustache', 'template.mustache') 
  upload_file_if_key_does_not_exist('default_styles.css', 'styles.css') 

  resource_id = 'https://' + event["ResourceProperties"]['domain'] + '/'

  try:
    table.put_item(
      Item={"PK": "feed::::", "SK":"Feed", "data":"/"},
      ConditionExpression=boto3.dynamodb.conditions.Attr('PK').not_exists()
    )
  except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
    pass

  stepfunctions.start_execution(stateMachineArn=os.environ['DESIGN_REFRESH_STATE_MACHINE'])
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
