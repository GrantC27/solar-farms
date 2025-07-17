import influxdb_client
from google.cloud import bigquery
from google.oauth2 import service_account
import os
import time
import datetime

# InfluxDB settings
INFLUXDB_URL = os.environ.get("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.environ.get("INFLUXDB_TOKEN", "solar-farms-admin-token-super-secret-12345")
INFLUXDB_ORG = os.environ.get("INFLUXDB_ORG", "solar-farms")
INFLUXDB_BUCKET = "solar_farms"

# GCP settings
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "worple91-ha")
GCP_DATASET_ID = os.environ.get("GCP_DATASET_ID", "solar_farms")
GCP_TABLE_ID_STATIC = os.environ.get("GCP_TABLE_ID_STATIC", "static_data")
GCP_TABLE_ID_TELEMETRY = os.environ.get("GCP_TABLE_ID_TELEMETRY", "telemetry_data")
GCP_SERVICE_ACCOUNT_FILE = os.environ.get("GCP_SERVICE_ACCOUNT_FILE", "service-account.json")

def get_influxdb_data(measurement):
    """Gets data from InfluxDB and pivots it."""
    client = influxdb_client.InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    query_api = client.query_api()

    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -1m)
      |> filter(fn: (r) => r._measurement == "{measurement}")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> group(columns: ["site_id"])
    '''

    result = query_api.query(query, org=INFLUXDB_ORG)
    return result

def send_data_to_gcp(data, table_id):
    """Sends data to Google BigQuery, creating the table if it doesn't exist."""
    credentials = service_account.Credentials.from_service_account_file(GCP_SERVICE_ACCOUNT_FILE)
    client = bigquery.Client(credentials=credentials, project=GCP_PROJECT_ID)
    dataset_ref = client.dataset(GCP_DATASET_ID)
    table_ref = dataset_ref.table(table_id)

    rows_to_insert = []
    for table in data:
        for record in table.records:
            row = record.values
            for key, value in row.items():
                if isinstance(value, datetime.datetime):
                    row[key] = value.isoformat()
            rows_to_insert.append(row)

    if not rows_to_insert:
        print(f"No data to insert into {table_id}")
        return

    try:
        client.get_table(table_ref)  # Make an API request.
    except Exception as e:
        print(f"Table {table_id} not found. Creating table...")
        schema = []
        first_row = rows_to_insert[0]
        for key, value in first_row.items():
            # More specific check for timestamp
            if key.lower() == '_time' or key.lower() == 'time':
                field_type = "TIMESTAMP"
            elif isinstance(value, bool):
                field_type = "BOOL"
            elif isinstance(value, int):
                field_type = "INT64"
            elif isinstance(value, float):
                field_type = "FLOAT64"
            else:
                field_type = "STRING"
            schema.append(bigquery.SchemaField(key, field_type))

        table = bigquery.Table(table_ref, schema=schema)
        client.create_table(table)
        print(f"Table {table_id} created.")
        # Wait for table to be created and schema to be available.
        time.sleep(5)

    errors = client.insert_rows_json(table_ref, rows_to_insert)
    if not errors:
        print(f"New data inserted into {table_id}")
    else:
        print(f"Errors while inserting data into {table_id}: {errors}")

def main():
    """Main function to run the data transfer."""
    while True:
        static_data = get_influxdb_data("solar_farm_static")
        telemetry_data = get_influxdb_data("solar_farm_telemetry")

        # send_data_to_gcp(static_data, GCP_TABLE_ID_STATIC)
        send_data_to_gcp(telemetry_data, GCP_TABLE_ID_TELEMETRY)

        print("Sleeping for 60 seconds...")
        time.sleep(60)

if __name__ == "__main__":
    main()
