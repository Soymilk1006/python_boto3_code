import boto3
import time
import paramiko
import os

# Initialize boto3 EC2 resource and client
ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')

# Step 1: Create a security group allowing SSH (port 22) from all IP addresses
security_group_name = 'my-ssh-security-group'
security_group_description = 'Security group for SSH access'

try:
    security_group = ec2.create_security_group(
        GroupName=security_group_name,
        Description=security_group_description
    )
    security_group_id = security_group.id
    print(f'Security Group Created: {security_group_id}')

    ec2_client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }
        ]
    )
    print(f'Ingress Rule Added: SSH from all IPs to {security_group_id}')

except Exception as e:
    print(f'Error creating security group: {e}')
    exit(1)

# Step 2: Create a key pair and save the private key locally
key_pair_name = 'my-ec2-key-pair'
key_file_path = f'{key_pair_name}.pem'

try:
    key_pair = ec2_client.create_key_pair(KeyName=key_pair_name)
    private_key = key_pair['KeyMaterial']

    with open(key_file_path, 'w') as key_file:
        key_file.write(private_key)
    os.chmod(key_file_path, 0o600)
    print(f'Key pair created and saved to {key_file_path}')
except Exception as e:
    print(f'Error creating key pair: {e}')
    exit(1)

# Step 3: Create an EC2 instance using the created security group and key pair
try:
    response = ec2.create_instances(
        ImageId='ami-080660c9757080771',  # Use your preferred AMI ID
        InstanceType='t2.micro',
        MinCount=1,
        MaxCount=1,
        KeyName=key_pair_name,
        SecurityGroupIds=[security_group_id],
    )

    instance = response[0]
    print(f'Waiting for instance {instance.id} to enter running state...')
    instance.wait_until_running()
    instance.load()

    # Get the public DNS name of the instance
    public_dns = instance.public_dns_name
    print(f'Instance Public DNS: {public_dns}')

    # Wait for a while to ensure the instance is ready for SSH connections
    time.sleep(180)

    # Step 4: Use Paramiko to SSH into the instance and execute a command
    key = paramiko.RSAKey(filename=key_file_path)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print('Connecting to the instance...')
        ssh.connect(public_dns, username='ubuntu', pkey=key)  # Replace 'ec2-user' with the appropriate username if needed

        print('Executing command: echo "nihao"')
        stdin, stdout, stderr = ssh.exec_command("echo 'nihao'")
        print('Command output:')
        print(stdout.read().decode())

    finally:
        ssh.close()
        print('Connection closed.')

    # Step 5: Clean up - Terminate the EC2 instance
    print(f'Terminating instance {instance.id}...')
    instance.terminate()
    instance.wait_until_terminated()
    print(f'Instance {instance.id} terminated.')

    # Clean up - Delete the security group
    time.sleep(180)
    print(f'Deleting security group {security_group_id}...')
    ec2_client.delete_security_group(GroupId=security_group_id)
    print(f'Security group {security_group_id} deleted.')

    # Clean up - Delete the key pair and remove the key file
    print(f'Deleting key pair {key_pair_name}...')
    ec2_client.delete_key_pair(KeyName=key_pair_name)
    os.remove(key_file_path)
    print(f'Key pair {key_pair_name} deleted and key file {key_file_path} removed.')

except Exception as e:
    print(f'Error creating EC2 instance or connecting via SSH: {e}')
    # Attempt to clean up resources if an error occurs

    # Terminate the instance if it was created
    if 'instance' in locals():
        print(f'Terminating instance {instance.id} due to error...')
        instance.terminate()
        instance.wait_until_terminated()
        print(f'Instance {instance.id} terminated.')

    # Delete the security group if it was created
    if 'security_group_id' in locals():
        print(f'Deleting security group {security_group_id} due to error...')
        ec2_client.delete_security_group(GroupId=security_group_id)
        print(f'Security group {security_group_id} deleted.')

    # Delete the key pair and remove the key file if it was created
    if 'key_pair_name' in locals():
        print(f'Deleting key pair {key_pair_name} due to error...')
        ec2_client.delete_key_pair(KeyName=key_pair_name)
        if os.path.exists(key_file_path):
            os.remove(key_file_path)
        print(f'Key pair {key_pair_name} deleted and key file {key_file_path} removed.')
