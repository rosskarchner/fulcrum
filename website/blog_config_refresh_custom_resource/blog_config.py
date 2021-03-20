import io
import os
import json

import boto3
from cfn_custom_resource import lambda_handler, create, update, delete

dynamodb = boto3.resource('dynamodb')
table =  dynamodb.Table(os.environ['TABLE'])
stepfunctions = boto3.client('stepfunctions')

def create_or_update(event):

  try:
    table.put_item(
      Item={"PK": "feed::::", "SK":"Feed", "data":"/"},
      ConditionExpression=boto3.dynamodb.conditions.Attr('PK').not_exists()
    )
  except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
    pass

  stepfunctions.start_execution(stateMachineArn=os.environ['STATE_MACHINE_ARN'])
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
