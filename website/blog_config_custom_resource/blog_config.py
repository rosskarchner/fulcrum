import os
import json
import boto3

from cfn_custom_resource import lambda_handler, create, update, delete
from botocore.exceptions import ClientError

s3 = boto3.resource("s3")
bucket = s3.Bucket(os.environ["BUCKET"])

ses = boto3.client("ses")


def upload(key, path):
    return bucket.put_object(Key=key, Body=open(path).read())


def upload_if_missing(key, path):
    # based on https://stackoverflow.com/q/44978426
    try:
        s3.Object(os.environ["BUCKET"], key).load()
    except ClientError as e:
        upload(key, path)
        return int(e.response["Error"]["Code"]) != 404

    return True


def is_email_known(email):
    paginator = ses.get_paginator("list_identities")
    for page in paginator.paginate(IdentityType="EmailAddress"):
        email_identities = ses.list_identities(IdentityType="EmailAddress")[
            "Identities"
        ]
        if email in email_identities:
            return True
    return False


def create_or_update(event):
    config_object = bucket.put_object(
        Key="config.json", Body=json.dumps(event["ResourceProperties"])
    )
    upload("_templates/default_feed.mustache", "default_feed.mustache")
    upload("_templates/default_post.mustache", "default_post.mustache")
    upload("media/styles.css", "default_styles.css")

    email = event["ResourceProperties"]["EmailAddress"]
    if not is_email_known(email):
        ses.verify_email_address(EmailAddress=email)

    return (
        "s3://%s/%s" % (config_object.bucket_name, config_object.key),
        event["ResourceProperties"],
    )


@create()
def create(event, context):
    return create_or_update(event)


@update()
def update(event, context):
    return create_or_update(event)


@delete()
def delete(event, context):
    bucket.objects.all().delete()
    return
