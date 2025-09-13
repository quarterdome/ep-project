import os
from dotenv import load_dotenv

def connect_to_timestream():
    import boto3
    from botocore.exceptions import ClientError

    # Load environment variables from .env file
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION')

    try:
        client = boto3.client(
            'timestream-write',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        return client
    except ClientError as e:
        print(f"Error connecting to Timestream: {e}")
        return None

def get_timestream_config():
    # Load environment variables from .env file
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    database_name = os.getenv('TIMESTREAM_DATABASE_NAME')
    table_name = os.getenv('TIMESTREAM_TABLE_NAME')
    return database_name, table_name

def upload_metrics(client, telemetry_data):
    """
    Accepts a list of telemetry dicts (from the 'telemetry' key in your JSON files).
    Each dict should have 'measurement', 'tags', 'time', and 'fields'.
    """
    from dateutil import parser

    database_name, table_name = get_timestream_config()

    try:
        records = []
        for entry in telemetry_data:
            dimensions = [
                {'Name': k, 'Value': str(v)}
                for k, v in entry.get('tags', {}).items()
            ]
            dimensions.append({'Name': 'measurement', 'Value': entry['measurement']})

            dt = parser.isoparse(entry['time'])
            timestamp_ms = str(int(dt.timestamp() * 1000))

            for field_name, field_value in entry.get('fields', {}).items():
                if isinstance(field_value, bool):
                    value_type = 'BOOLEAN'
                    value = str(field_value).lower()
                elif isinstance(field_value, int):
                    value_type = 'BIGINT'
                    value = str(field_value)
                elif isinstance(field_value, float):
                    value_type = 'DOUBLE'
                    value = str(field_value)
                else:
                    value_type = 'VARCHAR'
                    value = str(field_value)

                record = {
                    'Dimensions': dimensions,
                    'MeasureName': field_name,
                    'MeasureValue': value,
                    'MeasureValueType': value_type,
                    'Time': timestamp_ms,
                    'TimeUnit': 'MILLISECONDS'
                }
                records.append(record)

        response = client.write_records(
            DatabaseName=database_name,
            TableName=table_name,
            Records=records,
            CommonAttributes={}
        )
        return response
    except Exception as e:
        print(f"Error uploading metrics: {e}")
        return None