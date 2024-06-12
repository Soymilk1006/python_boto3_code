import pymongo
import hvac

# HashiCorp Vault settings
vault_url = 'https://your-vault-url.com'
vault_token = 'your_vault_token'

# MongoDB connection settings
mongo_uri = None

# Function to retrieve secrets from Vault
def get_mongodb_credentials_from_vault():
    try:
        # Initialize Vault client
        client = hvac.Client(url=vault_url, token=vault_token)


        secret_path = 'secret/data/mongodb'

        # Retrieve secrets from Vault
        response = client.secrets.kv.read_secret_version(path=secret_path)

        # Extract username and password from Vault response
        if 'data' in response['data']:
            data = response['data']['data']
            username = data.get('username')
            password = data.get('password')
            return username, password
        else:
            print(f"Secrets not found or accessible at path: {secret_path}")
            return None, None

    except hvac.exceptions.VaultError as e:
        print(f"Vault error: {e}")
        return None, None

# Function to connect to MongoDB and retrieve data
def connect_to_mongodb():
    try:
        # Retrieve MongoDB credentials from Vault
        username, password = get_mongodb_credentials_from_vault()

        # Construct MongoDB URI with retrieved credentials
        if username and password:
            global mongo_uri
            mongo_uri = f"mongodb://{username}:{password}@hostname:port/mydatabase"

            # Connect to MongoDB
            client = pymongo.MongoClient(mongo_uri)

            # Access database and collection
            db = client.get_database()
            collection = db.get_collection('your_collection_name')

            # Example query
            documents = collection.find()

            # Print documents
            for document in documents:
                print(document)

    except pymongo.errors.ConnectionFailure as e:
        print(f"Error connecting to MongoDB: {e}")

    finally:
        # Close MongoDB connection
        client.close()

# Execute function to connect and query MongoDB
connect_to_mongodb()
