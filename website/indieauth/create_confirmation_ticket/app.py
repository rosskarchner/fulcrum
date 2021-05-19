import json


def lambda_handler(event, context):
    # if we've gotten this far, then we know the cognito token is valid,
    # for our user pool. We still need to make sure the sub in the token
    # belongs to the user who started the authentication process
    cognito_sub = event["pathParameters"]["upstream_sub_id"]
    assert event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"] == cognito_sub
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(event["requestContext"]["authorizer"]["jwt"]),
    }
