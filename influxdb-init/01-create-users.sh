#!/bin/bash
set -e

# Wait for InfluxDB to be ready
until curl -f http://localhost:8086/ping; do
  echo "Waiting for InfluxDB to be ready..."
  sleep 2
done

echo "InfluxDB is ready. Creating additional users and databases..."

# Create database if it doesn't exist
influx -execute "CREATE DATABASE IF NOT EXISTS solar_farms"

# Create users with different privileges
influx -execute "CREATE USER telegraf WITH PASSWORD 'telegraf123'"
influx -execute "GRANT ALL ON solar_farms TO telegraf"

influx -execute "CREATE USER reader WITH PASSWORD 'reader123'"
influx -execute "GRANT READ ON solar_farms TO reader"

influx -execute "CREATE USER writer WITH PASSWORD 'writer123'"
influx -execute "GRANT WRITE ON solar_farms TO writer"

# Create admin user if not exists
influx -execute "CREATE USER admin WITH PASSWORD 'admin123' WITH ALL PRIVILEGES" || true

echo "User creation completed successfully!"