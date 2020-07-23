import json
import chevron

#import mf2py


import base64
import os
import secrets

import boto3
import jwt

CMK_ID = os.environ["CMK"]
kms_client = boto3.client("kms")
 
 
def clean_authorization_params(request_params):
  response_type = request_params.get("response_type", "id")
  assert response_type in ["id", "code"]
  required_params = ["me", "client_id", "redirect_uri", "state"]
  cleaned_dict = {"response_type": response_type}
  for param in required_params:
     cleaned_dict[param] = request_params[param]
  if response_type == "code":
     cleaned_dict["scope"] = request_params.get(
         "scope", "create update delete media"
     )
  return cleaned_dict
 
 
def authorization_state_token(request_params):
  payload = clean_authorization_params(request_params)
  payload["aud"] = "indieauth_state"
  signing_key = secrets.token_bytes()
  encrypted_signing_key = kms_client.encrypt(KeyId=CMK_ID, Plaintext=signing_key)[
     "CiphertextBlob"
  ]

  return jwt.encode(
     payload,
     signing_key,
     algorithm="HS256",
     headers={"kid": base64.b64encode(encrypted_signing_key).decode("utf8")},
  )


def lambda_handler(event, context):
    request_params = event['queryStringParameters']
    my_state = authorization_state_token(request_params)
    debug = json.dumps(event)
    with open('get.html') as template:
      return {
          "statusCode": 200,
          "headers":{'Content-Type':'text/html'},
          "body": chevron.render(template, {'debug':debug,
                                             'state_token':my_state})
      }
