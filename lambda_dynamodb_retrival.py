import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key


def query_user_notes(user_email):
    dynamodb = boto3.resource('dynamodb')
    user_notes_table = dynamodb.Table('user-notes')

    try:
        result = user_notes_table.query(
            KeyConditionExpression=(Key("user").eq(user_email)),
            ScanIndexForward=False,
            Limit=10
        )
        return result.get('Items', [])
    except ClientError as e:
        return False


def lambda_handler(event, context):
    print(event)
    email = event['requestContext']['authorizer']['email']
    print("email:", email)
    result = query_user_notes(email)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Hello from your backend Lambda!',
            'items': result
        })
    }
