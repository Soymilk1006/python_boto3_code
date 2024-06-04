import boto3
import csv
from movies import Movies

# Initialize Boto3 DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')

# Create an instance of the Movies class
movies = Movies(dynamodb)

# Check if the table exists and get or create it
table_name = 'MoviesTable'
movies_table = movies.get_or_create_table(table_name)

# Path to the CSV file
csv_file_path = 'netflix_titles.csv'

# Read CSV file and prepare data for insertion
values_to_insert = []
with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        item = {
            'show_id': row['show_id'],
            'title': row['title'],
            'type': row['type'],
            'director': row['director'],
            'cast': row['cast'],
            'country': row['country'],
            'date_added': row['date_added'],
            'release_year': int(row['release_year']),
            'rating': row['rating'],
            'duration': row['duration'],
            'listed_in': row['listed_in'],
            'description': row['description']
        }
        values_to_insert.append(item)

# Insert values into the table
movies.insert_values(values_to_insert)
