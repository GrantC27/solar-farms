Write-Host "Setting up Solar Farm MQTT Simulator with InfluxDB v2..." -ForegroundColor Green

# Stop any existing containers
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Remove existing volumes to ensure clean setup (optional - uncomment if needed)
# Write-Host "Removing existing volumes for clean setup..." -ForegroundColor Yellow
# docker volume rm solar-farms_influxdb_data, solar-farms_influxdb_config 2>$null

# Start the services
Write-Host "Starting services..." -ForegroundColor Yellow
docker-compose up -d

Write-Host "Waiting for InfluxDB to initialize (this may take a minute)..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# Check if InfluxDB is responding
Write-Host "Checking InfluxDB status..." -ForegroundColor Yellow
try {
    docker exec influxdb influx ping
} catch {
    Write-Host "InfluxDB may still be initializing..." -ForegroundColor Yellow
}

# Run the token creation script
Write-Host "Creating additional tokens and buckets..." -ForegroundColor Yellow
try {
    docker exec influxdb /docker-entrypoint-initdb.d/01-create-tokens.sh
} catch {
    Write-Host "Token creation script may have already run" -ForegroundColor Yellow
}

# Display the tokens
Write-Host ""
Write-Host "=== InfluxDB v2 Setup Information ===" -ForegroundColor Cyan
try {
    docker exec influxdb cat /tmp/influxdb-tokens.txt
} catch {
    Write-Host "Tokens file not yet available" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Services available at:" -ForegroundColor Cyan
Write-Host "- MQTT Broker: localhost:1883"
Write-Host "- InfluxDB v2: localhost:8086"
Write-Host "- Grafana: localhost:3000 (admin/admin123)"
Write-Host "- MQTT Explorer: localhost:4000"
Write-Host ""
Write-Host "InfluxDB v2 Configuration:" -ForegroundColor Cyan
Write-Host "- Organization: solar-farms"
Write-Host "- Main Bucket: solar_farms"
Write-Host "- Admin Token: solar-farms-admin-token-super-secret-12345"
Write-Host ""
Write-Host "To view all tokens: docker exec influxdb cat /tmp/influxdb-tokens.txt" -ForegroundColor Yellow
Write-Host "To access InfluxDB UI: http://localhost:8086 (admin/admin123456)" -ForegroundColor Yellow