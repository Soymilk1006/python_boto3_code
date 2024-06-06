import boto3
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Function to retrieve secrets from HashiCorp Vault
def get_vault_secret(secret_path, secret_key):
    # Initialize a Vault client
    client = hvac.Client(url='https://your-vault-url.com', token=os.getenv('VAULT_TOKEN'))

    # Retrieve the secret
    try:
        if not client.is_authenticated():
            logger.error("Vault authentication failed.")
            return None

        response = client.secrets.kv.read_secret_version(path=secret_path)
        secret_value = response['data']['data'][secret_key]
        return secret_value

    except Exception as e:
        logger.error(f"Failed to retrieve secret from Vault: {e}")
        return None

def copy_s3_bucket(source_bucket_name, destination_bucket_name, aws_region='us-east-1'):
    try:
        s3 = boto3.resource('s3', region_name=aws_region)
        source_bucket = s3.Bucket(source_bucket_name)
        destination_bucket = s3.Bucket(destination_bucket_name)

        # Create destination bucket if it doesn't exist
        if not destination_bucket.creation_date:
            s3.create_bucket(Bucket=destination_bucket_name,
                             CreateBucketConfiguration={'LocationConstraint': aws_region})

        # Copy objects from source to destination
        for obj in source_bucket.objects.all():
            copy_source = {'Bucket': source_bucket_name, 'Key': obj.key}
            destination_bucket.copy(copy_source, obj.key)
            logger.info(f"Copied {obj.key} from {source_bucket_name} to {destination_bucket_name}")

        return True

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False

def backup_dynamodb_table(table_name, backup_bucket_name, aws_region='ap-southeast-2'):
    try:
        dynamodb = boto3.resource('dynamodb', region_name=aws_region)
        table = dynamodb.Table(table_name)
        backup_key = f'{table_name}-backup.json'

        # Scan table and write to S3
        response = table.scan()
        s3 = boto3.client('s3')
        s3.put_object(Body=str(response['Items']), Bucket=backup_bucket_name, Key=backup_key)
        logger.info(f"Backed up DynamoDB table {table_name} to S3 bucket {backup_bucket_name}")

        return True

    except Exception as e:
        logger.error(f"Failed to backup DynamoDB table {table_name}: {e}")
        return False


def backup_rds_mysql_table(db_instance_identifier, table_name, backup_bucket_name, aws_region='ap-southeast-2'):
    try:
        rds_client = boto3.client('rds', region_name=aws_region)

        # Get RDS instance endpoint from AWS RDS API
        response = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
        endpoint = response['DBInstances'][0]['Endpoint']['Address']

        # Retrieve MySQL credentials from HashiCorp Vault
        db_username = get_vault_secret('path/to/mysql/credentials', 'username')
        db_password = get_vault_secret('path/to/mysql/credentials', 'password')
        db_name = '########'

        if not db_username or not db_password:
            logger.error("Failed to retrieve database credentials from Vault.")
            return False

        # Connect to MySQL database using pymysql
        import pymysql
        conn = pymysql.connect(
            host=endpoint,
            user=db_username,
            password=db_password,
            database=db_name,
            connect_timeout=5,
            cursorclass=pymysql.cursors.DictCursor
        )

        # Backup MySQL table to S3
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name}")
            results = cursor.fetchall()
            import json
            s3 = boto3.client('s3')
            s3.put_object(Body=json.dumps(results), Bucket=backup_bucket_name, Key=f'{table_name}-backup.json')
            logger.info(f"Backed up MySQL table {table_name} to S3 bucket {backup_bucket_name}")

        return True

    except Exception as e:
        logger.error(f"Failed to backup MySQL table {table_name}: {e}")
        return False


def backup_ec2_instance(instance_id, ami_name, snapshot_description):
    try:
        ec2_client = boto3.client('ec2')

        # Create EBS snapshot of root volume
        response = ec2_client.create_snapshot(
            VolumeId=get_root_volume_id(instance_id),
            Description=snapshot_description
        )
        snapshot_id = response['SnapshotId']
        logger.info(f"Created snapshot {snapshot_id} for instance {instance_id}")

        # Create AMI of instance
        response = ec2_client.create_image(
            InstanceId=instance_id,
            Name=ami_name,
            Description=snapshot_description,
            NoReboot=True  # No reboot required for AMI creation
        )
        ami_id = response['ImageId']
        logger.info(f"Created AMI {ami_id} from instance {instance_id}")

        return True

    except Exception as e:
        logger.error(f"Failed to backup instance {instance_id}: {e}")
        return False


def get_root_volume_id(instance_id):
    ec2_client = boto3.client('ec2')
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    root_device_name = response['Reservations'][0]['Instances'][0]['RootDeviceName']
    for block_device_mapping in response['Reservations'][0]['Instances'][0]['BlockDeviceMappings']:
        if block_device_mapping['DeviceName'] == root_device_name:
            return block_device_mapping['Ebs']['VolumeId']


def lambda_handler(event, context):
    # Parameters for S3 bucket copy
    source_bucket_name = 'trip-tribe.com'
    destination_bucket_name = 'trip-tribe.com-backup'
    aws_region = 'ap-southeast-2'

    # Parameters for DynamoDB backup
    dynamodb_table_name = 'triptribe-dynamodb'
    dynamodb_backup_bucket_name = 'triptribe-dynamodb-backup-bucket'

    # Parameters for RDS MySQL backup
    rds_db_instance_identifier = '####'
    mysql_table_name = 'triptribe-mysql'
    mysql_backup_bucket_name = 'triptribe-mysql-backup-bucket'

    # Parameters for EC2 instance backup
    ec2_instance_id = '##########'
    ec2_ami_name = 'BackupAMI'
    ec2_snapshot_description = 'Backup snapshot created by Lambda'

    # Perform S3 bucket copy
    if not copy_s3_bucket(source_bucket_name, destination_bucket_name, aws_region):
        logger.error(f"Failed to copy objects from {source_bucket_name} to {destination_bucket_name}")
        return {
            'statusCode': 500,
            'body': f"Error copying objects from {source_bucket_name} to {destination_bucket_name}"
        }

    # Perform DynamoDB table backup
    if not backup_dynamodb_table(dynamodb_table_name, dynamodb_backup_bucket_name, aws_region):
        logger.error(f"Failed to backup DynamoDB table {dynamodb_table_name}")
        return {
            'statusCode': 500,
            'body': f"Error backing up DynamoDB table {dynamodb_table_name}"
        }

    # Perform RDS MySQL table backup
    if not backup_rds_mysql_table(rds_db_instance_identifier, mysql_table_name, mysql_backup_bucket_name, aws_region):
        logger.error(f"Failed to backup MySQL table {mysql_table_name}")
        return {
            'statusCode': 500,
            'body': f"Error backing up MySQL table {mysql_table_name}"
        }

    # Perform EC2 instance backup
    if not backup_ec2_instance(ec2_instance_id, ec2_ami_name, ec2_snapshot_description):
        logger.error(f"Failed to backup EC2 instance {ec2_instance_id}")
        return {
            'statusCode': 500,
            'body': f"Error backing up EC2 instance {ec2_instance_id}"
        }

    return {
        'statusCode': 200,
        'body': f"Backup completed successfully for S3 bucket, DynamoDB table, RDS MySQL table, and EC2 instance"
    }
