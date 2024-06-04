import boto3
from botocore.exceptions import ClientError
import logging
import time
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
class Media:
    """Encapsulates an Amazon DynamoDB table of movie data."""

    def __init__(self, dyn_resource):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        """
        self.dyn_resource = dyn_resource
        self.table = None

    def check_table_exists(self, table_name):
        """
        Check whether a DynamoDB table exists.

        :param table_name: The name of the table to check.
        :return: True if the table exists, False otherwise.
        """
        try:
            self.dyn_resource.Table(table_name).load()
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            else:
                raise

    def get_or_create_table(self, table_name):
        """
        Get an existing DynamoDB table or create a new one if it doesn't exist.

        :param table_name: The name of the table to get or create.
        :return: The DynamoDB table.
        """
        if self.check_table_exists(table_name):
            print(f"Table '{table_name}' exists.")
            self.table = self.dyn_resource.Table(table_name)
        else:
            print(f"Table '{table_name}' does not exist. Creating...")
            self.table = self.create_table(table_name)
        return self.table

    def create_table(self, table_name):
        """
        Creates an Amazon DynamoDB table with a global secondary index.

        :param table_name: The name of the table to create.
        :return: The newly created table.
        """
        try:
            table = self.dyn_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
                    {"AttributeName": "size", "KeyType": "RANGE"},  # Sort key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "id", "AttributeType": "S"},
                    {"AttributeName": "filetype", "AttributeType": "S"},
                    {"AttributeName": "size", "AttributeType": "N"},
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 10,
                    "WriteCapacityUnits": 10,
                },
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'FileTypeIndex',
                        'KeySchema': [
                            {'AttributeName': 'filetype', 'KeyType': 'HASH'},
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 10,
                            'WriteCapacityUnits': 10,
                        }
                    },
                ]
            )
            table.wait_until_exists()
            print(f"Table '{table_name}' created successfully.")
            return table
        except ClientError as e:
            print(f"Error creating table '{table_name}': {e}")
            raise

    def insert_values(self, values):
        """
        Insert values into the DynamoDB table.

        :param values: A list of dictionaries representing items to insert.
        """
        try:
            start_time = time.time()
            with self.table.batch_writer() as batch:
                for value in values:
                    logger.info(f"Inserting item: {value['id']}, {value['size']}")
                    batch.put_item(Item=value)
            end_time = time.time()
            logger.info(f"the value inserted successfully in {end_time - start_time:.2f} seconds.")
        except ClientError as e:
            logger.error(f"Error inserting values: {e}")
            raise
