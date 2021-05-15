import base64
import functools
import json
import chevron
import hmac
import time
import os

from urllib.parse import urlparse as _urlparse

import boto3

secrets = boto3.client("secretsmanager")

urlparse = functools.lru_cache(_urlparse)

# by populating these at the module level, we create the potential
# for it to fall briefly out of sync after a secret rotation. Because all subsequent
# requests will use the VersionId, I think this is OK.
secret_data = secrets.get_secret_value(SecretId=os.environ["HMAC_SECRET_ARN"])
hmac_key = json.loads(secret_data["SecretString"])["key"]
hmac_key_version = secret_data["VersionId"]


def is_valid_url(url, allow_non_http=False):
    parsed_url = urlparse(url)
    protocol_ok = allow_non_http or parsed_url.scheme.lower() in ["http", "https"]
    return bool(protocol_ok and parsed_url.netloc)


def lambda_handler(event, context):
    params = event["queryStringParameters"]

    if all(
        [
            is_valid_url(params["client_id"]),
            is_valid_url(params["redirect_uri"], allow_non_http=True),
            ("me" not in params or is_valid_url(params["me"])),
        ]
    ):
        now = time.time()
        query_string = event["rawQueryString"]
        upstream_sub_id = event["pathParameters"]["upstream_sub_id"]
        message = upstream_sub_id + query_string + str(now)
        hashed = hmac.new(
            hmac_key.encode("utf-8"), message.encode("utf-8"), "sha256"
        ).hexdigest()
        csrf_token = "%s@%s@%s" % (hashed, hmac_key_version, now)

        template_context = {
            "query_string": base64.b64encode(bytes(query_string, encoding="utf-8")).decode("utf-8"),
            "upstream_sub_id": upstream_sub_id,
            "csrf_token": csrf_token,
            "client_id": params["client_id"],
            "scope": params.get("scope"),
        }

        with open("get.html") as template:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "text/html"},
                "body": chevron.render(template=template, data=template_context),
            }
