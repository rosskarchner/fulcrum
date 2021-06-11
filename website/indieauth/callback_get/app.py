from urllib.parse import urlencode
import boto3
import os
import json
import requests
import secrets

s3 = boto3.resource("s3")
cognito = boto3.client("cognito-idp")

session_bucket = s3.Bucket(os.environ["SESSION_BUCKET"])
continuation_bucket = s3.Bucket(os.environ["CONTINUATION_BUCKET"])
upstream_token_endpoint = os.environ["UPSTREAM_OAUTH_TOKEN"]
user_pool_id = os.environ["USER_POOL"]
client_id = os.environ["USER_POOL_CLIENT"]
callback_uri = os.environ["USER_POOL_CLIENT_CALLBACK"]
backend_api = os.environ["BACKEND_API"]


def lambda_handler(event, context):
    continuation_key = event["queryStringParameters"]["state"]
    code = event["queryStringParameters"]["code"]

    user_pool_details = cognito.describe_user_pool_client(
        UserPoolId=user_pool_id, ClientId=client_id
    )

    token_call_arguments = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code": code,
        "redirect_uri": callback_uri,
    }

    token_response = requests.post(
        upstream_token_endpoint,
        auth=(client_id, user_pool_details["UserPoolClient"]["ClientSecret"]),
        data=token_call_arguments,
    )

    session_data = token_response.json()

    token_details_response = requests.get(
        backend_api + "/upstream-token-details",
        headers={"Authorization": "Bearer %s" % session_data["access_token"]},
    )

    token_details = token_details_response.json()
    session_data.update(token_details)

    session_data["secret"] = secrets.token_hex()

    upstream_sub = token_details["claims"]["sub"]

    session_expires_in = session_data["expires_in"] - 10

    session_key = secrets.token_hex()
    session_bucket.put_object(Key=session_key, Body=json.dumps(session_data))

    continuation_object = continuation_bucket.Object(continuation_key)
    continuation_raw = continuation_object.get()["Body"].read().decode("utf-8")
    continuation_variables = json.loads(continuation_raw)
    continue_authorization_url = "https://%s/%s/authorization?%s" % (
        os.environ["API_DOMAIN"],
        upstream_sub,
        urlencode(continuation_variables),
    )

    return {
        "statusCode": 302,
        "headers": {
            "Content-Type": "text/html",
            "Set-Cookie": "session=%s; Max-Age=%s Secure; HttpOnly;"
            % (session_key, session_expires_in),
            "Location": continue_authorization_url,
        },
    }
