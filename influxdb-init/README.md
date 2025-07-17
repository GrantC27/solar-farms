# InfluxDB Initialization

This directory contains initialization scripts for InfluxDB to create users and databases on container startup.

## Files

- `01-create-users.sh`: Creates the necessary users and grants appropriate permissions

## Users Created

1. **telegraf** (password: telegraf123) - Full access to solar_farms database
2. **reader** (password: reader123) - Read-only access to solar_farms database  
3. **writer** (password: writer123) - Write access to solar_farms database
4. **admin** (password: admin123) - Full administrative privileges

## Usage

The scripts in this directory are automatically executed when the InfluxDB container starts for the first time. The container will wait for InfluxDB to be ready before creating users.

## InfluxDB Version

This configuration is set up for InfluxDB 1.8. If you need to use InfluxDB 2.x, see the docker-compose.influxdb2.yml file for an alternative configuration.