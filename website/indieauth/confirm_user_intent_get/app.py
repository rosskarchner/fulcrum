import boto3
import os
import json

s3 = boto3.resource("s3")
cognito = boto3.client("cognito-idp")
bucket_name = os.environ["BUCKET"]
user_pool = os.environ["USER_POOL"]


def lambda_handler(event, context):
    state_key = event["queryStringParameters"]["state"]
    code = event["queryStringParameters"]["code"]

    auth_data_object = s3.Object(bucket_name, state_key)
    auth_data_streamingbody = auth_data_object.get()["Body"]
    auth_data_text = auth_data_streamingbody.read().decode("utf-8")
    auth_data = json.loads(auth_data_text)

    client_details = cognito.describe_user_pool_client(
        UserPoolId=user_pool, ClientId=auth_data["upstream_client_id"]
    )

    print(client_details)
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html"},
        "body": auth_data_text,
    }
