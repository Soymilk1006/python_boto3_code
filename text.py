import json
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


class InvalidResponse(Exception):
    def __init__(self, status_code):
        self.status_code = status_code


# Function to query user notes from DynamoDB
def query_user_notes(user_email):
    dynamodb = boto3.resource('dynamodb')
    user_notes_table = dynamodb.Table('user-notes')

    try:
        response = user_notes_table.query(
            KeyConditionExpression=Key('user').eq(user_email),
            ScanIndexForward=False,  # Sort in descending order by create_date
            Limit=10  # Return maximum 10 notes per query
        )
        return response.get('Items', [])
    except ClientError as e:
        raise InvalidResponse(500)


# Function to get authenticated user's email from token
def get_authenticated_user_email(token):
    dynamodb = boto3.resource('dynamodb')
    tokens_table = dynamodb.Table('token-email-lookup')

    try:
        response = tokens_table.get_item(
            Key={'token': token}
        )
        item = response.get('Item')
        if not item:
            raise InvalidResponse(403)
        return item.get('email')
    except ClientError as e:
        raise InvalidResponse(500)


# Function to authenticate user and retrieve user email
def authenticate_user(headers):
    try:
        authentication_header = headers['Authorization']
        token = authentication_header.split(' ')[1] if authentication_header.startswith('Bearer ') else ''
        if not token:
            raise InvalidResponse(400)

        user_email = get_authenticated_user_email(token)
        return user_email

    except KeyError:
        raise InvalidResponse(400)


# Function to build HTTP response
def build_response(status_code, body=None):
    result = {
        'statusCode': str(status_code),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
    }
    if body is not None:
        result['body'] = body

    return result


# Lambda handler function
def handler(event, context):
    try:
        user_email = authenticate_user(event['headers'])
        notes = query_user_notes(user_email)
        return build_response(200, json.dumps(notes))
    except InvalidResponse as e:
        return build_response(e.status_code)

