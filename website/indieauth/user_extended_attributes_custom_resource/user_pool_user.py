import os
import json
import boto3

from cfn_custom_resource import lambda_handler, create, update, delete
from botocore.exceptions import ClientError

cognito = boto3.client("cognito-idp")


def create_or_update(event):
    provided_properties = event["ResourceProperties"]
    UserPoolId = provided_properties["UserPoolId"]
    Username = provided_properties["Username"]

    user_details = cognito.admin_get_user(UserPoolId=UserPoolId, Username=Username)
    attributes = {
        attrib["Name"]: attrib["Value"] for attrib in user_details["UserAttributes"]
    }

    return (
        "userpool://%s/%s" % (UserPoolId, Username),
        attributes,
    )


@create()
def create(event, context):
    return create_or_update(event)


@update()
def update(event, context):
    return create_or_update(event)


@delete()
def delete(event, context):
    pass
