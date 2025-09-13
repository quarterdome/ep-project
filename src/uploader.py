import os
import json
import boto3
from botocore.exceptions import ClientError
from utils.timestream_helper import connect_to_timestream, upload_metrics

def load_metrics_from_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def main():
    data_directory = '../data'
    metrics_files = [f for f in os.listdir(data_directory) if f.endswith('.json')]
    
    if not metrics_files:
        print("No JSON files found in the data directory.")
        return

    client = connect_to_timestream()

    for metrics_file in metrics_files:
        file_path = os.path.join(data_directory, metrics_file)
        metrics_data = load_metrics_from_json(file_path)
        
        try:
            upload_metrics(client, metrics_data)
            print(f"Successfully uploaded metrics from {metrics_file}.")
        except ClientError as e:
            print(f"Failed to upload metrics from {metrics_file}: {e}")

if __name__ == "__main__":
    main()