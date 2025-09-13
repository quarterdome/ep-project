# Metrics Uploader

This project is designed to upload metrics from JSON files to AWS Timestream for later plotting and analysis. The main components of the project include a script for uploading metrics, utility functions for interacting with AWS Timestream, and a sample JSON file demonstrating the expected metrics format.

## Project Structure

```
metrics-uploader
├── data
│   └── sample.json          # Sample JSON file containing metrics data
├── src
│   ├── uploader.py          # Main script for uploading metrics to AWS Timestream
│   └── utils
│       └── timestream_helper.py  # Helper functions for AWS Timestream interaction
├── requirements.txt         # List of dependencies for the project
├── .env                     # Environment variables for AWS credentials and Timestream details
└── README.md                # Documentation for the project
```

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd metrics-uploader
   ```

2. **Install dependencies**:
   Ensure you have Python and pip installed, then run:
   ```
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Create a `.env` file in the root directory and add your AWS credentials and Timestream database details. Example:
   ```
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   TIMESTREAM_DATABASE=your_database_name
   TIMESTREAM_TABLE=your_table_name
   ```

## Usage

To upload metrics from the JSON files in the `data` directory, run the following command:
```
python src/uploader.py
```

## Metrics Format

The JSON files should follow this structure:
```json
{
    "metrics": [
        {
            "name": "metric_name",
            "value": 123.45,
            "timestamp": "2023-01-01T00:00:00Z"
        }
    ]
}
```

Ensure that the `metrics` array contains objects with the required fields: `name`, `value`, and `timestamp`.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.