import boto3

def get_secret(secret_name):
    # Create a session using your AWS credentials
    session = boto3.session.Session()

    # Determine if the secret is in Parameter Store or Secrets Manager
    if secret_name.startswith('/'):
        # Assume it's from AWS Systems Manager Parameter Store (SSM)
        ssm_client = session.client('ssm')

        # Retrieve the parameter
        try:
            response = ssm_client.get_parameter(Name=secret_name, WithDecryption=True)
            secret_value = response['Parameter']['Value']
            return secret_value
        except ssm_client.exceptions.ParameterNotFound:
            print(f"Parameter {secret_name} not found in Parameter Store.")
            return None
        except Exception as e:
            print(f"Error retrieving parameter {secret_name} from Parameter Store: {e}")
            return None
    else:
        # Assume it's from AWS Secrets Manager
        secretsmanager_client = session.client('secretsmanager')

        # Retrieve the secret
        try:
            response = secretsmanager_client.get_secret_value(SecretId=secret_name)
            if 'SecretString' in response:
                secret_value = response['SecretString']
            else:
                secret_value = response['SecretBinary']  # For binary secrets
            return secret_value
        except secretsmanager_client.exceptions.ResourceNotFoundException:
            print(f"Secret {secret_name} not found in Secrets Manager.")
            return None
        except Exception as e:
            print(f"Error retrieving secret {secret_name} from Secrets Manager: {e}")
            return None

# Example usage
if __name__ == "__main__":
    # Replace with your secret or parameter name
    secret_name_parameter_store = '/your/parameter/name'
    secret_name_secrets_manager = 'your-secret-name'

    # Retrieve secret from Parameter Store
    secret_value_parameter_store = get_secret(secret_name_parameter_store)
    if secret_value_parameter_store:
        print(f"Retrieved secret from Parameter Store: {secret_value_parameter_store}")

    # Retrieve secret from Secrets Manager
    secret_value_secrets_manager = get_secret(secret_name_secrets_manager)
    if secret_value_secrets_manager:
        print(f"Retrieved secret from Secrets Manager: {secret_value_secrets_manager}")
