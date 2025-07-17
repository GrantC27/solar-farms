# InfluxDB v2 Migration Guide

## Overview

This project has been migrated from InfluxDB v1.x to InfluxDB v2.x. This document outlines the changes made and how to work with the new setup.

## Key Changes

### 1. InfluxDB v2 Features
- **Token-based authentication** instead of username/password
- **Organizations and buckets** instead of databases
- **Flux query language** instead of InfluxQL
- **Built-in web UI** for data exploration and management
- **Better time series data handling** and performance

### 2. Docker Compose Changes
- Updated to `influxdb:2.7` image
- New initialization parameters:
  - `DOCKER_INFLUXDB_INIT_MODE=setup`
  - `DOCKER_INFLUXDB_INIT_USERNAME=admin`
  - `DOCKER_INFLUXDB_INIT_PASSWORD=admin123456`
  - `DOCKER_INFLUXDB_INIT_ORG=solar-farms`
  - `DOCKER_INFLUXDB_INIT_BUCKET=solar_farms`
  - `DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=solar-farms-admin-token-super-secret-12345`

### 3. Telegraf Configuration Changes
- Changed from `[[outputs.influxdb]]` to `[[outputs.influxdb_v2]]`
- Now uses token authentication instead of username/password
- Specifies organization and bucket instead of database

### 4. New Bucket Structure
- **solar_farms** (30 days) - Main telemetry data
- **solar_farms_realtime** (7 days) - High-frequency real-time data
- **solar_farms_historical** (1 year) - Long-term aggregated data
- **solar_farms_events** (6 months) - Faults and maintenance events

## Authentication Tokens

The system creates several tokens for different use cases:

### Admin Token
- **Token**: `solar-farms-admin-token-super-secret-12345`
- **Permissions**: Full administrative access
- **Use**: System administration, Grafana datasource

### Telegraf Token
- **Permissions**: Read/Write access to solar_farms bucket
- **Use**: Data ingestion from MQTT

### Read-only Token
- **Permissions**: Read access to solar_farms bucket
- **Use**: Monitoring applications, reporting tools

### Write-only Token
- **Permissions**: Write access to solar_farms bucket
- **Use**: Data ingestion applications

## Grafana Integration

### Data Sources Configured
1. **InfluxDB-v2** (Default) - Main data source with admin token
2. **InfluxDB-v2-ReadOnly** - Read-only access for dashboards
3. **InfluxDB-v2-Historical** - Historical data bucket
4. **InfluxDB-v2-Events** - Events and maintenance data

### Query Language
Grafana now uses **Flux** instead of InfluxQL. Example queries:

#### InfluxQL (v1) - Old
```sql
SELECT mean("power_output") FROM "solar_farm_telemetry" 
WHERE time >= now() - 1h 
GROUP BY time(5m), "site_id"
```

#### Flux (v2) - New
```flux
from(bucket: "solar_farms")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "power_output")
  |> aggregateWindow(every: 5m, fn: mean)
  |> group(columns: ["site_id"])
```

## Web UI Access

InfluxDB v2 includes a built-in web interface:
- **URL**: http://localhost:8086
- **Username**: admin
- **Password**: admin123456

Features available in the UI:
- Data exploration with Flux queries
- Dashboard creation
- Token management
- Bucket management
- Task scheduling
- Alerting

## API Changes

### v1 API (Deprecated)
```bash
curl -G 'http://localhost:8086/query' \
  --data-urlencode "db=solar_farms" \
  --data-urlencode "q=SELECT * FROM solar_farm_telemetry LIMIT 10"
```

### v2 API (Current)
```bash
curl -X POST 'http://localhost:8086/api/v2/query' \
  -H 'Authorization: Token solar-farms-admin-token-super-secret-12345' \
  -H 'Content-Type: application/vnd.flux' \
  -d 'from(bucket:"solar_farms") |> range(start:-1h) |> limit(n:10)'
```

## Python Client Example

```python
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Initialize client
client = InfluxDBClient(
    url="http://localhost:8086",
    token="solar-farms-admin-token-super-secret-12345",
    org="solar-farms"
)

# Write data
write_api = client.write_api(write_options=SYNCHRONOUS)
point = Point("solar_farm_telemetry") \
    .tag("site_id", "FARM_001") \
    .field("power_output", 1500.5) \
    .time(datetime.utcnow(), WritePrecision.NS)

write_api.write(bucket="solar_farms", record=point)

# Query data
query_api = client.query_api()
query = '''
from(bucket: "solar_farms")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r.site_id == "FARM_001")
'''
result = query_api.query(query)
```

## Migration Steps

If you're migrating from an existing v1 setup:

1. **Backup existing data** (if needed):
   ```bash
   docker exec influxdb influxd backup -database solar_farms /backup
   ```

2. **Stop old containers**:
   ```bash
   docker-compose down
   ```

3. **Update configuration** (already done in this migration)

4. **Start new containers**:
   ```bash
   ./setup.sh  # or setup.ps1 on Windows
   ```

5. **Import data** (if you have backups):
   - Use the InfluxDB v2 UI or CLI tools to import data
   - Convert InfluxQL queries to Flux in Grafana dashboards

## Troubleshooting

### Common Issues

1. **Token not working**:
   - Check token in `/tmp/influxdb-tokens.txt`
   - Verify organization and bucket names

2. **Grafana connection issues**:
   - Ensure Flux query language is selected
   - Verify token has appropriate permissions

3. **Telegraf not writing data**:
   - Check telegraf logs: `docker logs solar-farm-telegraf`
   - Verify token permissions for write access

### Useful Commands

```bash
# View all tokens
docker exec influxdb cat /tmp/influxdb-tokens.txt

# Check InfluxDB status
docker exec influxdb influx ping

# List buckets
docker exec influxdb influx bucket list

# View Telegraf logs
docker logs solar-farm-telegraf

# Access InfluxDB CLI
docker exec -it influxdb influx
```

## Security Considerations

1. **Change default tokens** in production environments
2. **Use environment variables** for sensitive tokens
3. **Implement proper token rotation** policies
4. **Restrict network access** to InfluxDB ports
5. **Enable TLS** for production deployments

## Performance Benefits

InfluxDB v2 provides several performance improvements:
- Better compression algorithms
- Improved query performance with Flux
- More efficient storage engine
- Better handling of high cardinality data
- Built-in downsampling capabilities

## Next Steps

1. **Update existing dashboards** to use Flux queries
2. **Set up data retention policies** for different buckets
3. **Configure alerting** using InfluxDB v2's built-in features
4. **Implement proper backup strategies** for production use
5. **Consider setting up clustering** for high availability