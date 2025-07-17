#!/bin/bash

echo "Setting up Solar Farm MQTT Simulator with InfluxDB v2..."

# Make the initialization script executable (Linux/Mac)
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "win32" ]]; then
    chmod +x influxdb2-init/01-create-tokens.sh
    echo "Made initialization script executable"
fi

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down

# Remove existing volumes to ensure clean setup (optional - uncomment if needed)
# echo "Removing existing volumes for clean setup..."
# docker volume rm solar-farms_influxdb_data solar-farms_influxdb_config 2>/dev/null || true

# Start the services
echo "Starting services..."
docker-compose up -d

echo "Waiting for InfluxDB to initialize (this may take a minute)..."
sleep 60

# Check if InfluxDB is responding
echo "Checking InfluxDB status..."
docker exec influxdb influx ping || echo "InfluxDB may still be initializing..."

# Run the token creation script
echo "Creating additional tokens and buckets..."
docker exec influxdb /docker-entrypoint-initdb.d/01-create-tokens.sh || echo "Token creation script may have already run"

# Display the tokens
echo ""
echo "=== InfluxDB v2 Setup Information ==="
docker exec influxdb cat /tmp/influxdb-tokens.txt 2>/dev/null || echo "Tokens file not yet available"

echo ""
echo "Setup complete!"
echo ""
echo "Services available at:"
echo "- MQTT Broker: localhost:1883"
echo "- InfluxDB v2: localhost:8086"
echo "- Grafana: localhost:3000 (admin/admin123)"
echo "- MQTT Explorer: localhost:4000"
echo ""
echo "InfluxDB v2 Configuration:"
echo "- Organization: solar-farms"
echo "- Main Bucket: solar_farms"
echo "- Admin Token: solar-farms-admin-token-super-secret-12345"
echo ""
echo "To view all tokens: docker exec influxdb cat /tmp/influxdb-tokens.txt"
echo "To access InfluxDB UI: http://localhost:8086 (admin/admin123456)"