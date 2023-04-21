import json
import os

import boto3
from botocore.exceptions import ClientError

dbb = boto3.resource('dynamodb')
sm = boto3.client('secretsmanager')
sqs = boto3.client("sqs")

def handler(event, context):
    response = {}

    try:
        httpMethod = event.get('httpMethod')
        if not httpMethod or httpMethod != 'GET':
            raise ValueError('Wrong Rest Method')

        params = event.get('queryStringParameters') or {}
        api_key = params.get('id')
        user_url_webook = params.get('webook_url')

        if not api_key:
            raise ValueError('Missing api_key')

        user_id = get_secret('api_key_awsproject', api_key)

        tableName = os.environ['STORAGE_USERS_NAME']
        table = dbb.Table(tableName)

        # Vérifier si la colonne user_url_webook existe dans la table
        try:
            table.update_item(
                Key={'id': user_id},
                UpdateExpression='SET user_url_webook = :val',
                ExpressionAttributeValues={':val': user_url_webook},
                ConditionExpression='attribute_not_exists(user_url_webook)'
            )
            sqs.sendmessage("queueDiego", user_url_webook)
        except ClientError as e:
            if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
                raise

        queue_url = sqs.get_queue_url(QueueName='QueueDiego')['QueueUrl']
        sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps({"user_id": user_id}))

        response['body'] = json.dumps(get_user(user_id=user_id, table=table))
        response['statusCode'] = 200

    except (Exception, ClientError) as err:
        print(err)
        response['statusCode'] = 400
        response['body'] = {'error': str(err)}

    return response


def get_user(user_id, table):
    user = table.get_item(
        Key={'id': user_id},
        ProjectionExpression="firstname, lastname, email, age, user_url_webook"
    )

    return {'user': user.get('Item')}


def get_secret(secretName, apikey):
    secret = sm.get_secret_value(
        SecretId=secretName
    )

    return json.loads(secret['SecretString'])[apikey]
