import boto3
import datetime


def lambda_handler(event, context):
    # Initialize boto3 clients
    ec2_client = boto3.client('ec2')

    # Get current UTC time
    current_time = datetime.datetime.utcnow()

    # Check if it's a weekend (Saturday or Sunday)
    if current_time.weekday() in [5, 6]:  # 5 is Saturday, 6 is Sunday
        # Describe instances to find running instances
        response = ec2_client.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )

        # Stop instances that are running
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                print(f"Stopping instance {instance_id}...")
                ec2_client.stop_instances(InstanceIds=[instance_id])

    # Print statement for CloudWatch Logs
    print('Function executed successfully')
