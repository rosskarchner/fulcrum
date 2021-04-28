import json
import chevron

def lambda_handler(event, context):
    print(json.dumps(event))
    params = event['queryStringParameters']

    with open('get.html') as template:
      return {
          "statusCode": 200,
          "headers":{'Content-Type':'text/html'},
          "body": chevron.render(template=template, data={})
      }
