# BigQuery Data Transmitter for Solar Farm Monitoring

This Python program pulls solar farm telemetry data from InfluxDB and transmits it periodically to Google BigQuery. It's designed to work with the existing solar farm monitoring system that uses InfluxDB 2.x for data storage.

## Features

- **InfluxDB Integration**: Pulls real-time data from InfluxDB 2.x using Flux queries
- **Periodic Data Transmission**: Automatically sends data to BigQuery at configurable intervals
- **Historical Data Support**: Can transmit historical data from InfluxDB to BigQuery
- **Flexible Time Ranges**: Query data from specific time periods
- **Automatic Schema Management**: Creates BigQuery dataset and table with proper schema
- **Configurable Settings**: Easy configuration through JSON file
- **Error Handling**: Robust error handling and logging
- **Flexible Execution**: Can run continuously or transmit data once

## Prerequisites

1. **InfluxDB 2.x**: Running instance with solar farm data
2. **Google Cloud Project**: With BigQuery API enabled
3. **Authentication**: Set up authentication for BigQuery
4. **Solar Farm Data**: InfluxDB should contain telemetry data from your solar farm simulator

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements-bigquery.txt
```

2. Set up Google Cloud authentication:

### Option A: Service Account Key
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
```

### Option B: Application Default Credentials
```bash
gcloud auth application-default login
```

### Option C: Environment Variables
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

## Configuration

Update the `config.json` file with your settings:

```json
{
    "influxdb": {
        "url": "http://localhost:8086",
        "token": "solar-farms-admin-token-super-secret-12345",
        "org": "solar-farms",
        "bucket": "solar_farms",
        "query_range": "-5m"
    },
    "bigquery": {
        "project_id": "your-gcp-project-id",
        "dataset_id": "solar_farms",
        "table_id": "telemetry",
        "batch_size": 150,
        "transmission_interval_seconds": 60
    }
}
```

### Configuration Parameters

#### InfluxDB Settings
- `url`: InfluxDB server URL
- `token`: Authentication token for InfluxDB 2.x
- `org`: InfluxDB organization name
- `bucket`: InfluxDB bucket containing solar farm data
- `query_range`: Default time range for queries (e.g., "-5m", "-1h")

#### BigQuery Settings
- `project_id`: Your Google Cloud Project ID
- `dataset_id`: BigQuery dataset name (will be created if it doesn't exist)
- `table_id`: BigQuery table name (will be created if it doesn't exist)
- `batch_size`: Number of records to process in each batch
- `transmission_interval_seconds`: Time interval between transmissions

## Usage

### Test Your Setup

First, verify that everything is configured correctly:

```bash
python test_bigquery_setup.py
```

This will test:
- InfluxDB connectivity and data availability
- BigQuery authentication
- Configuration validity
- Data retrieval functionality

### Continuous Transmission

Run the program to start continuous data transmission:

```bash
python bigquery_transmitter.py
```

The program will:
1. Connect to InfluxDB and BigQuery
2. Query latest telemetry data from InfluxDB
3. Transform and transmit data to BigQuery
4. Repeat at configured intervals
5. Continue until interrupted with Ctrl+C

### One-time Transmission

To transmit data once and exit:

```bash
python bigquery_transmitter.py --once
```

### Custom Time Range

Specify a custom time range for data query:

```bash
python bigquery_transmitter.py --once --time-range "-30m"
```

### Historical Data Transmission

Transmit historical data from InfluxDB:

```bash
python bigquery_transmitter.py --historical 24
```

This will transmit the last 24 hours of data.

### Custom Configuration

Use a different configuration file:

```bash
python bigquery_transmitter.py --config my_config.json
```

## Data Flow

1. **InfluxDB Query**: Program queries InfluxDB using Flux queries
2. **Data Transformation**: Converts InfluxDB records to structured format
3. **BigQuery Transmission**: Sends transformed data to BigQuery
4. **Error Handling**: Logs any issues and continues operation

## InfluxDB Data Structure

The program expects the following measurements in InfluxDB:

### solar_farm_telemetry
- `power_output`: Current power output (kW)
- `energy_generated`: Energy generated (kWh)
- `energy_consumed`: Energy consumed (kWh)
- `energy_exported`: Energy exported (kWh)
- `solar_irradiance`: Solar irradiance (W/m²)
- `ambient_temperature`: Ambient temperature (°C)
- `module_temperature`: Module temperature (°C)
- `wind_speed`: Wind speed (m/s)
- `humidity`: Humidity (%)
- `inverter_efficiency`: Inverter efficiency (0-1)
- `system_efficiency`: System efficiency (0-1)
- `fault_count`: Number of active faults
- `maintenance_mode`: Maintenance mode status (boolean)
- `operational_status`: Operational status (string)

### Tags
- `site_id`: Unique farm identifier
- `farm_name`: Human-readable farm name
- `country`: Country location
- `latitude`: Geographic latitude
- `longitude`: Geographic longitude

## BigQuery Schema

The program creates a BigQuery table with the following schema:

| Field Name | Type | Mode | Description |
|------------|------|------|-------------|
| timestamp | TIMESTAMP | REQUIRED | Data collection timestamp |
| site_id | STRING | REQUIRED | Unique farm identifier |
| farm_name | STRING | NULLABLE | Human-readable farm name |
| country | STRING | NULLABLE | Country location |
| latitude | FLOAT | NULLABLE | Geographic latitude |
| longitude | FLOAT | NULLABLE | Geographic longitude |
| power_output | FLOAT | NULLABLE | Current power output (kW) |
| energy_generated | FLOAT | NULLABLE | Energy generated (kWh) |
| energy_consumed | FLOAT | NULLABLE | Energy consumed (kWh) |
| energy_exported | FLOAT | NULLABLE | Energy exported (kWh) |
| solar_irradiance | FLOAT | NULLABLE | Solar irradiance (W/m²) |
| ambient_temperature | FLOAT | NULLABLE | Ambient temperature (°C) |
| module_temperature | FLOAT | NULLABLE | Module temperature (°C) |
| wind_speed | FLOAT | NULLABLE | Wind speed (m/s) |
| humidity | FLOAT | NULLABLE | Humidity (%) |
| inverter_efficiency | FLOAT | NULLABLE | Inverter efficiency (0-1) |
| system_efficiency | FLOAT | NULLABLE | System efficiency (0-1) |
| fault_count | INTEGER | NULLABLE | Number of active faults |
| maintenance_mode | BOOLEAN | NULLABLE | Maintenance mode status |
| operational_status | STRING | NULLABLE | Operational status |

## Flux Queries Used

The program uses the following types of Flux queries:

### Latest Data Query
```flux
from(bucket: "solar_farms")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> group(columns: ["site_id"])
  |> last()
  |> pivot(rowKey: ["_time", "site_id"], columnKey: ["_field"], valueColumn: "_value")
```

### Historical Data Query
```flux
from(bucket: "solar_farms")
  |> range(start: 2024-01-01T00:00:00Z, stop: 2024-01-01T23:59:59Z)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> group(columns: ["site_id", "_time"])
  |> pivot(rowKey: ["_time", "site_id"], columnKey: ["_field"], valueColumn: "_value")
```

## Monitoring and Logging

The program provides comprehensive logging:

- InfluxDB connection status
- Data retrieval results
- BigQuery transmission status
- Error messages and troubleshooting information
- Performance metrics

Log level can be configured in the `config.json` file.

## Error Handling

The program handles various error scenarios:

- InfluxDB connection failures
- BigQuery API errors
- Network connectivity issues
- Authentication problems
- Data validation issues
- Missing or malformed data

## Integration with Existing System

This transmitter integrates seamlessly with your existing solar farm monitoring system:

1. **InfluxDB Data Source**: Reads from the same InfluxDB instance used by Grafana
2. **Real-time Processing**: Processes data as it's generated by your simulator
3. **Historical Backfill**: Can transmit historical data for analysis
4. **Minimal Impact**: Runs independently without affecting other components

## Performance Considerations

- **Query Efficiency**: Uses optimized Flux queries with appropriate time ranges
- **Batch Processing**: Processes data in configurable batches
- **Memory Usage**: Efficient memory usage for large datasets
- **Network Usage**: Minimizes network calls through batching
- **BigQuery Costs**: Monitor BigQuery usage and costs

## Troubleshooting

### Common Issues

1. **InfluxDB Connection Error**:
   - Verify InfluxDB is running: `docker-compose ps`
   - Check URL and token in config.json
   - Ensure bucket exists and contains data

2. **No Data Retrieved**:
   - Start your solar farm simulator to generate data
   - Check time range in query
   - Verify measurement names match

3. **BigQuery Authentication Error**:
   - Set up authentication credentials
   - Verify project ID is correct
   - Check BigQuery API is enabled

4. **Permission Denied**:
   - Ensure service account has BigQuery permissions:
     - BigQuery Data Editor
     - BigQuery Job User

### Debug Mode

Enable debug logging by setting the log level in config.json:

```json
{
    "logging": {
        "level": "DEBUG"
    }
}
```

### Data Validation

The program includes data validation to handle:
- Missing fields in InfluxDB records
- Type conversion errors
- Invalid timestamps
- Null or empty values

## Example Workflows

### Daily Data Sync
```bash
# Transmit yesterday's data
python bigquery_transmitter.py --historical 24
```

### Real-time Monitoring
```bash
# Start continuous transmission
python bigquery_transmitter.py
```

### Data Backfill
```bash
# Transmit last week's data
python bigquery_transmitter.py --historical 168
```

### Testing
```bash
# Test with recent data
python bigquery_transmitter.py --once --time-range "-15m"
```

## License

This program is part of the Solar Farm MQTT Simulator project.