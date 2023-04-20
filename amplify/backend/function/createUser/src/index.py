import json
import os
import uuid

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

dbb = boto3.resource('dynamodb', region_name='eu-west-1')

def handler(event, context):
  response = {}

  try:
    httpMethod = event.get('httpMethod')
    if not httpMethod or httpMethod != 'POST':
      raise ValueError('Wrong Rest Method')

    body = json.loads(event.get('body'))
    #body = event.get('body')

    print(body)
    tableName = os.environ['STORAGE_USERS_NAME']
    table = dbb.Table(tableName)

    response['body'] = json.dumps(check_user(body=body, table=table))
    response['statusCode'] = 200

  except (Exception, ClientError) as err:
    response['statusCode'] = 400
    response['body'] = { 'error': str(err) }
  
  return response

def check_user(body, table):
  inputs = ['email', 'firstname', 'lastname', 'age']

  for elm in inputs:
    if elm not in body: 
      raise ValueError(f'Missing input: {elm}')
  
  item = table.query(
    IndexName="emailIndex",
    KeyConditionExpression=Key('email').eq(body['email']),
    ProjectionExpression="id, firstname"
  )

  if len(item['Items']) <= 0:

    body['id'] = str(uuid.uuid4())
    table.put_item(
      Item=body
    )
    return { 'user_id': body['id'] }
  else:
    return { 'user_id': item['Items'][0]['id'] }
