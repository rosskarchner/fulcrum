import boto3

dynamodb = boto3.resource('dynamodb')
table =  dynamodb.Table(os.environ['TABLE'])

def lambda_handler(event, context):
  renderable_feeds = table.query(IndexName='GS1')
  return renderable_feeds.get('Items', [])
