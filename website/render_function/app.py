import json
import logging
import time
import traceback
import os, os.path
import pathlib
import chevron

import boto3

s3 = boto3.client('s3')
bucket_name = os.environ['SITE_BUCKET']

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

def lambda_handler(event, context):
  try:
    LOGGER.info('Event structure: %s', event)

    config_response = s3.get_object(
      Bucket=bucket_name,
      Key='config.json'
    )

    config = json.loads(config_response['Body'].read().decode('utf-8'))
    template_response= s3.get_object(
      Bucket=bucket_name,
      Key='_templates/default_feed.mustache'
    )
    template=template_response['Body'].read().decode('utf-8')
    print(template)
    rendered_template = chevron.render(template=template, data=config)
    s3.put_object(
      Bucket=bucket_name,
      Key='index.html',
      Body=rendered_template,
      ContentType='text/html',
      ACL='public-read'
      )

    return

  except Exception as e:
    traceback.print_exc()

    response_data = {
        'statusCode': 500,
        'error': str(e)
    }

    return response_data