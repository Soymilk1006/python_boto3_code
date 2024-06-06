import time
import boto3
import os
import zipfile
import json
from media import Media
from pathlib import Path

# Initialize AWS SDK client
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')
iam_client = boto3.client('iam')
dynamodb = boto3.resource('dynamodb')

### Create s3 bucket ###
bucket_name = 'media-library-bucket123'
# bucket = s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={
#     'LocationConstraint': 'ap-southeast-2',
# }, )

### Create Dynamodb table ###
table_name = 'media-library-table'
media = Media(dynamodb)
table = media.get_or_create_table(table_name)

# Configuration
function_name = 'my-lambda-function'
zip_file_name = 'lambda_function.zip'
handler_name = 'lambda_function.lambda_handler'  
role_name = 'LambdaS3CloudWatchDynamodbRole'
# Name of the IAM role
policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [  # Necessary to interact with s3 objects
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::*/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem"  # Necessary to update dynamodb table
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/media-library-table"
        }
    ]
}

try:
    # Check if role exists
    role_response = iam_client.get_role(RoleName=role_name)
    role_arn = role_response['Role']['Arn']
    print(f"IAM role '{role_name}' already exists. Using existing role ARN: {role_arn}")

except iam_client.exceptions.NoSuchEntityException:
    # Create IAM role
    print(f"IAM role '{role_name}' does not exist. Creating new role...")

    # Create IAM role
    role_response = iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        })
    )

    # Attach policy to the role
    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName='LambdaS3CloudWatchDynamodbRole',
        PolicyDocument=json.dumps(policy_document)
    )

    # Get role ARN
    role_arn = role_response['Role']['Arn']
    print(f"IAM role '{role_name}' created successfully. Role ARN: {role_arn}")

# ZIP the Lambda function script
# with zipfile.ZipFile(zip_file_name, 'w') as zip:
#     zip.write('lambda_function.py')  # Change to your script name

# Upload the ZIP file to Lambda
time.sleep(5)
with open(zip_file_name, 'rb') as f:
    create_function_response = lambda_client.create_function(
        FunctionName=function_name,
        Runtime='python3.12',
        Role=role_arn,  # Change to your Lambda execution role ARN
        Handler=handler_name,
        Code={'ZipFile': f.read()},
    )
print(f"Function ARN is: {create_function_response['FunctionArn']}")
# Clean up
os.remove(zip_file_name)

# Lambda function to permit S3 bucket trigger  ###

# Wait till the bucket is created
s3_client.get_waiter('bucket_exists').wait(Bucket=bucket_name)
# Get the bucket arn
bucket_arn = f'arn:aws:s3:::{bucket_name}'
lambda_client.add_permission(
    FunctionName=function_name,
    StatementId='metadata_triger',
    Action='lambda:InvokeFunction',
    Principal='s3.amazonaws.com',
    SourceArn=bucket_arn
)

time.sleep(5)
# Define the event configuration
event_configuration = {
    'LambdaFunctionConfigurations': [
        {
            'LambdaFunctionArn': create_function_response['FunctionArn'],
            'Events': ['s3:ObjectCreated:*']
        }
    ]
}

# Configure the S3 event trigger
s3_client.put_bucket_notification_configuration(
    Bucket=bucket_name,
    NotificationConfiguration=event_configuration
)


def upload_to_s3(local_file_path, bucket_name):
    key = Path(local_file_path).name
    s3_client.upload_file(Filename=local_file_path, Bucket=bucket_name, Key=key)
    return f"{bucket_name}/{key}"


time.sleep(10)
for data in Path("data/").glob("*"):
    upload_to_s3(data, bucket_name)
