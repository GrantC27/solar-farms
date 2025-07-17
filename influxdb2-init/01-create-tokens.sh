#!/bin/bash
set -e

echo "InfluxDB 2.x Post-Setup Script"
echo "Creating additional users and tokens..."

# Wait for InfluxDB to be fully ready
until curl -f http://localhost:8086/ping; do
  echo "Waiting for InfluxDB to be ready..."
  sleep 2
done

# Wait a bit more for the setup to complete
sleep 10

# Set variables
INFLUX_HOST="http://localhost:8086"
INFLUX_ORG="solar-farms"
INFLUX_BUCKET="solar_farms"
ADMIN_TOKEN="solar-farms-admin-token-super-secret-12345"

echo "Creating additional users and tokens..."

# Create a read-only user token
echo "Creating read-only token..."
influx auth create \
  --host $INFLUX_HOST \
  --token $ADMIN_TOKEN \
  --org $INFLUX_ORG \
  --description "Read-only access for monitoring" \
  --read-bucket $INFLUX_BUCKET \
  --json > /tmp/readonly-token.json

READONLY_TOKEN=$(cat /tmp/readonly-token.json | grep -o '"token":"[^"]*' | cut -d'"' -f4)
echo "Read-only token: $READONLY_TOKEN"

# Create a write-only user token
echo "Creating write-only token..."
influx auth create \
  --host $INFLUX_HOST \
  --token $ADMIN_TOKEN \
  --org $INFLUX_ORG \
  --description "Write-only access for data ingestion" \
  --write-bucket $INFLUX_BUCKET \
  --json > /tmp/writeonly-token.json

WRITEONLY_TOKEN=$(cat /tmp/writeonly-token.json | grep -o '"token":"[^"]*' | cut -d'"' -f4)
echo "Write-only token: $WRITEONLY_TOKEN"

# Create a telegraf-specific token with read/write access
echo "Creating Telegraf token..."
influx auth create \
  --host $INFLUX_HOST \
  --token $ADMIN_TOKEN \
  --org $INFLUX_ORG \
  --description "Telegraf service token" \
  --read-bucket $INFLUX_BUCKET \
  --write-bucket $INFLUX_BUCKET \
  --json > /tmp/telegraf-token.json

TELEGRAF_TOKEN=$(cat /tmp/telegraf-token.json | grep -o '"token":"[^"]*' | cut -d'"' -f4)
echo "Telegraf token: $TELEGRAF_TOKEN"

# Create additional buckets for different data retention periods
echo "Creating additional buckets..."

# Short-term high-frequency data (7 days)
influx bucket create \
  --host $INFLUX_HOST \
  --token $ADMIN_TOKEN \
  --org $INFLUX_ORG \
  --name solar_farms_realtime \
  --retention 168h \
  --description "High-frequency real-time solar farm data (7 days retention)"

# Long-term aggregated data (1 year)
influx bucket create \
  --host $INFLUX_HOST \
  --token $ADMIN_TOKEN \
  --org $INFLUX_ORG \
  --name solar_farms_historical \
  --retention 8760h \
  --description "Historical aggregated solar farm data (1 year retention)"

# Fault and maintenance data (6 months)
influx bucket create \
  --host $INFLUX_HOST \
  --token $ADMIN_TOKEN \
  --org $INFLUX_ORG \
  --name solar_farms_events \
  --retention 4380h \
  --description "Solar farm faults and maintenance events (6 months retention)"

echo "Saving tokens to file for reference..."
cat > /tmp/influxdb-tokens.txt << EOF
InfluxDB 2.x Tokens and Configuration
=====================================

Organization: $INFLUX_ORG
Main Bucket: $INFLUX_BUCKET

Admin Token: $ADMIN_TOKEN
Read-only Token: $READONLY_TOKEN
Write-only Token: $WRITEONLY_TOKEN
Telegraf Token: $TELEGRAF_TOKEN

Additional Buckets Created:
- solar_farms_realtime (7 days retention)
- solar_farms_historical (1 year retention)
- solar_farms_events (6 months retention)

Connection Examples:
===================

Telegraf (use in telegraf.conf):
[[outputs.influxdb_v2]]
  urls = ["http://influxdb:8086"]
  token = "$TELEGRAF_TOKEN"
  organization = "$INFLUX_ORG"
  bucket = "$INFLUX_BUCKET"

Python Client:
from influxdb_client import InfluxDBClient
client = InfluxDBClient(
    url="http://localhost:8086",
    token="$READONLY_TOKEN",
    org="$INFLUX_ORG"
)

Grafana Data Source:
URL: http://influxdb:8086
Organization: $INFLUX_ORG
Token: $READONLY_TOKEN
Default Bucket: $INFLUX_BUCKET
EOF

echo "Setup completed successfully!"
echo "Tokens saved to /tmp/influxdb-tokens.txt"
echo "You can view this file with: docker exec influxdb cat /tmp/influxdb-tokens.txt"