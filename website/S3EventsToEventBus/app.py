import json
import boto3
import os

client = boto3.client('events')

def NotificationRecordToBusEvent(record):
    event = {
                'Time': record['eventTime'],
                'Source': record['eventSource'],
                'EventBusName': os.environ['BUS'],
                'DetailType': 'Simplified S3 notification',
                'Detail': json.dumps({
                    'bucket': record['s3']['bucket']['name'],
                    'operation':record['eventName'],
                    'key': record['s3']['object']['key']
                })
            }
    return event


def lambda_handler(event, context):
    entries = [NotificationRecordToBusEvent(record) for record in event['Records']]
    response=client.put_events(Entries=entries)
    print(json.dumps(response))