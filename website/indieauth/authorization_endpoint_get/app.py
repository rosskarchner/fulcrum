import base64
import functools
import json
import chevron
import hmac
import time
import os
import secrets
import boto3


from urllib.parse import urlencode, urlparse as _urlparse

urlparse = functools.lru_cache(_urlparse)

s3 = boto3.resource("s3")
session_bucket = s3.Bucket(os.environ["SESSION_BUCKET"])
continuation_bucket = s3.Bucket(os.environ["CONTINUATION_BUCKET"])


def session_data(event):
    for cookie in event.get("cookies", []):
        if cookie.startswith("session="):
            session_key = cookie[8:]
            session_raw = (
                session_bucket.Object(session_key).get()["Body"].read().decode("utf-8")
            )
            return session_key, json.loads(session_raw)


def redirect_to_cognito(event):
        params = event["queryStringParameters"]
        continuation_data = params.copy()
        continuation_key = secrets.token_hex()

        continuation_bucket.put_object(
            Key=continuation_key, Body=json.dumps(continuation_data)
        )

        upstream_oauth_args = {}
        upstream_oauth_args["state"] = continuation_key
        upstream_oauth_args["response_type"] = "code"
        upstream_oauth_args["client_id"] = os.environ["USER_POOL_CLIENT"]
        upstream_oauth_args["redirect_uri"] = (
            "https://%s/callback" % event["headers"]["host"]
        )

        upstream_oauth_args["scope"] = "https://indieauth.spec.indieweb.org/login"

        # redirect to cognito

        return {
            "statusCode": 302,
            "headers": {
                "Location": os.environ["UPSTREAM_OAUTH_AUTHORIZE"]
                + "?"
                + urlencode(upstream_oauth_args)
            },
        }

def display_confirmation_screen(event, session_key, session):
    params = event["queryStringParameters"]


def csrf_token(session_key, session):
    now=time.time()
    message="%s@%s" %(session_key, str(now)).encode('utf-8')
    key=session['secret'].encode('utf-8')
    hasher=hmac.new(key, message, digestmod='sha256')
    return "%s@%s" % (hasher.hexdigest(), str(now))

def lambda_handler(event, context):

    session_key, session = session_data(event)

    if (
        session
        and session["claims"]["sub"] == event["pathParameters"]["upstream_sub_id"]
    ):
        print("now what?")
    else:
        return redirect_to_cognito(event)
