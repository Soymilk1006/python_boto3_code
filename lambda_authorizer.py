import json
import boto3
from botocore.exceptions import ClientError


def get_authenticated_user_email(token):
    dynamodb = boto3.resource('dynamodb')
    tokens_table = dynamodb.Table('authorization_table')
    try:
        response = tokens_table.get_item(
            Key={'token': token}
        )
        item = response.get('Item')
        if not item:
            return False
        return item.get('email')
    except ClientError as e:
        print("ClientError: ", e)
        return False


def lambda_handler(event, context):
    auth_header = event.get('authorizationToken')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        print(token)

        result = get_authenticated_user_email(token)

        if result:
            auth = "Allow"
        else:
            auth = "Deny"
    else:
        auth = "Deny"

    policyDocument = {
        "principalId": "any-api-principle-id",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Resource": ["arn:aws:execute-api:ap-southeast-2:335441918609:8kech69enh/test/GET/data"],
                    "Effect": auth
                }
            ]
        },
        "context": {
            "email": result if result else "unauthorized"
        }
    }

    print("policyDocument:", policyDocument)

    return policyDocument
