import boto3

# Initialize Boto3 client for IAM
iam_client = boto3.client('iam')

# Step 1: Create a new IAM group
group_name = 'S3CloudWatchGroup'

try:
    response = iam_client.create_group(
        GroupName=group_name,
        Path='/'
    )
    print(f"Group '{group_name}' created successfully.")
except Exception as e:
    print(f"Error creating group: {e}")

# Step 2: Attach policies to the group (S3 and CloudWatch)
try:
    # Attach S3 full access policy
    iam_client.attach_group_policy(
        GroupName=group_name,
        PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess'
    )
    print("S3 full access policy attached to the group.")

    # Attach CloudWatch full access policy
    iam_client.attach_group_policy(
        GroupName=group_name,
        PolicyArn='arn:aws:iam::aws:policy/CloudWatchFullAccess'
    )
    print("CloudWatch full access policy attached to the group.")
except Exception as e:
    print(f"Error attaching policies to group: {e}")

# Step 3: Create a new IAM user
user_name = 'JohnLi'

try:
    response = iam_client.create_user(
        UserName=user_name,
        Path='/'
    )
    print(f"User '{user_name}' created successfully.")
except Exception as e:
    print(f"Error creating user: {e}")

# Step 4: Add the user to the group
try:
    iam_client.add_user_to_group(
        UserName=user_name,
        GroupName=group_name
    )
    print(f"User '{user_name}' added to group '{group_name}' successfully.")
except Exception as e:
    print(f"Error adding user to group: {e}")

# Cleanup: Delete the IAM user and group
try:
    # Remove user from the group before deleting the user
    iam_client.remove_user_from_group(
        UserName=user_name,
        GroupName=group_name
    )
    print(f"User '{user_name}' removed from group '{group_name}' successfully.")

    # Delete the IAM user
    iam_client.delete_user(
        UserName=user_name
    )
    print(f"IAM user '{user_name}' deleted successfully.")

    # Delete the IAM group
    iam_client.delete_group(
        GroupName=group_name
    )
    print(f"IAM group '{group_name}' deleted successfully.")
except Exception as e:
    print(f"Error cleaning up resources: {e}")
