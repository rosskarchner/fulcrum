import base64
import functools
import itertools
import hmac
import json
import mf2py
import time
import os
import secrets

from urllib.parse import parse_qs, urlencode, urlparse as _urlparse

import boto3

secretsmanager = boto3.client("secretsmanager")

s3 = boto3.resource("s3")
bucket = s3.Bucket(os.environ["BUCKET"])

urlparse = functools.lru_cache(_urlparse)
mf2_parse = functools.lru_cache(mf2py.parse)


@functools.lru_cache  # a particualr version will always return the same secret
def hmac_secret_key(VersionId):
    secret_data = secretsmanager.get_secret_value(
        SecretId=os.environ["HMAC_SECRET_ARN"], VersionId=VersionId
    )
    return json.loads(secret_data["SecretString"])["key"]


@functools.lru_cache
def client_name_and_icon(client_id):
    client_data = mf2_parse(url=client_id)

    for item in client_data["items"]:
        if "h-app" in item["type"] or "h-x-app" in item["type"]:
            return (
                item["properties"].get("name", [client_id])[0],
                item["properties"].get("logo", [None])[0],
            )

    return client_id, None


def validate_csrf_token(token, query_string, upstream_sub_id, max_age_seconds=60):
    incoming_digest, hmac_key_version, timestamp = token.split("@")
    now = time.time()
    if now - float(timestamp) <= max_age_seconds:
        message = upstream_sub_id + query_string + timestamp
        hmac_key = hmac_secret_key(hmac_key_version)

        new_digest = hmac.new(
            hmac_key.encode("utf-8"), message.encode("utf-8"), "sha256"
        ).hexdigest()

    return hmac.compare_digest(incoming_digest, new_digest)


def lambda_handler(event, context):
    if event["isBase64Encoded"]:
        decoded_body = base64.b64decode(event["body"])
        parsed_body = parse_qs(decoded_body)
    else:
        parsed_body = parse_qs(event["body"])
    flattened_form_data = {
        k.decode("utf-8"): v[0].decode("utf-8") for k, v in sorted(parsed_body.items())
    }

    decoded_query_string = base64.b64decode(flattened_form_data["query_string"]).decode(
        "utf-8"
    )
    token_is_valid = validate_csrf_token(
        flattened_form_data["csrf_token"],
        decoded_query_string,
        flattened_form_data["upstream_sub_id"],
    )

    if token_is_valid:
        auth_endpoint_query_args = parse_qs(decoded_query_string)
        flattened_endpoint_query_args = {
            k: v[0]
            for k, v in auth_endpoint_query_args.items()
        }
    client_name, client_icon = client_name_and_icon(
        flattened_endpoint_query_args["client_id"]
    )

    flattened_endpoint_query_args["client_name"] = client_name
    flattened_endpoint_query_args["client_icon"] = client_icon
    flattened_endpoint_query_args["profile_url"] = flattened_endpoint_query_args.get(
        "me"
    )  # TODO get url from cognito

    # stash auth_data into bucket, key is new "state" value for the upstream
    # authorization URL

    state = secrets.token_hex()
    bucket.put_object(Key=state, Body=json.dumps(flattened_endpoint_query_args))

    upstream_oauth_args = {}
    upstream_oauth_args["state"] = state
    upstream_oauth_args["response_type"] = "code"
    upstream_oauth_args["client_id"] = os.environ["USER_POOL_CLIENT"]
    upstream_oauth_args["redirect_uri"] = (
        "https://%s/callback" % event["headers"]["host"]
    )

    if "scope" in flattened_endpoint_query_args:
        upstream_oauth_args["scope"] = "https://indieauth.spec.indieweb.org/token"
    else:
        upstream_oauth_args["scope"] = "https://indieauth.spec.indieweb.org/profile"

    # generate cognito URL

    return {
        "statusCode": 302,
        "headers": {
            "Location": os.environ["UPSTREAM_OAUTH_AUTHORIZE"]
            + "?"
            + urlencode(upstream_oauth_args)
        },
    }
