import boto3

def get_live_instance_ips(auto_scaling_group_name, region_name):
    # Initialize the boto3 client
    client = boto3.client('autoscaling', region_name=region_name)

    # Describe autoscaling group to get instance details
    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[auto_scaling_group_name],
    )

    # Extract instance IDs from the response
    instance_ids = response['AutoScalingGroups'][0]['Instances']

    # Initialize list to store IPs
    instance_ips = []

    # Iterate over instance IDs to fetch IPs
    ec2_client = boto3.client('ec2', region_name=region_name)
    for instance in instance_ids:
        instance_id = instance['InstanceId']
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        instance_ip = response['Reservations'][0]['Instances'][0]['PrivateIpAddress']
        instance_ips.append(instance_ip)

    return instance_ips

# Example usage
if __name__ == "__main__":
    auto_scaling_group_name = 'your-auto-scaling-group-name'
    region_name = 'your-region-name'  # e.g., 'us-east-1'

    instance_ips = get_live_instance_ips(auto_scaling_group_name, region_name)
    print("Live Instance IPs:")
    for ip in instance_ips:
        print(ip)
