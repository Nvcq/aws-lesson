import json
import os

import boto3
from botocore.exceptions import ClientError

dbb = boto3.resource('dynamodb', region_name='eu-west-1')
s3 = boto3.client('s3')

def handler(event, context):
  response = {}

  try:
    httpMethod = event.get('httpMethod')
    if not httpMethod or httpMethod != 'GET':
      raise ValueError('Wrong Rest Method')
  
    params = event.get('queryStringParameters') or {}
    user_id = params.get('id')

    if not user_id:
      raise ValueError('Missing user id')

    tableName = os.environ['STORAGE_USERS_NAME']
    table = dbb.Table(tableName)

    bucketName = os.environ['STORAGE_AWSPROJECTBUCKET_BUCKETNAME']

    response['body'] = json.dumps(
      generate_url(user_id=user_id, table=table, bucketName=bucketName)
    )
    response['statusCode'] = 200

  except (Exception, ClientError) as err:
    print(err)
    response['statusCode'] = 400
    response['body'] = { 'error': str(err) }
  
  return response

def generate_url(user_id, table, bucketName):
  user = table.get_item(
    Key={ 'id': user_id },
    ProjectionExpression="firstname, lastname, email, age"
  )

  user = user['Item']

  s3.put_object(
    Bucket=bucketName,
    Body=json.dumps(user),
    Key=f"users/{user_id}.json"
  )

  url = s3.generate_presigned_url(
    'get_object', 
    Params = { 'Bucket': bucketName, 'Key': f"users/{user_id}.json" },
    ExpiresIn = 300
  )

  return { "url": url }
