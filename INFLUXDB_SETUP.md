# InfluxDB User Creation Setup

## Problem Solved

The original Docker Compose configuration was not properly creating InfluxDB users on container initialization. This has been fixed with the following changes:

## Changes Made

### 1. Updated docker-compose.yml

- **Specified InfluxDB 1.8 image**: Changed from `influxdb` to `influxdb:1.8` for consistent behavior
- **Added proper environment variables**: Configured user creation variables
- **Added initialization volume**: Mounted `./influxdb-init:/docker-entrypoint-initdb.d` for custom scripts
- **Added health check**: Ensures InfluxDB is ready before other services start
- **Fixed container name**: Changed "solar-farm-grana" to "solar-farm-grafana"
- **Added service dependencies**: Telegraf now waits for InfluxDB to be healthy

### 2. Created InfluxDB Initialization Scripts

- **influxdb-init/01-create-users.sh**: Automatically creates users when container starts
- **influxdb-init/README.md**: Documentation for the initialization process

### 3. Updated Telegraf Configuration

- **Added username field**: `username = "telegraf"` in the InfluxDB output configuration
- This ensures proper authentication with the created user

### 4. Created Alternative InfluxDB 2.x Configuration

- **docker-compose.influxdb2.yml**: Ready-to-use configuration for InfluxDB 2.x upgrade
- Includes proper token-based authentication setup

## Users Created

The initialization script creates the following users:

1. **admin** (password: admin123)
   - Full administrative privileges
   - Can manage all databases and users

2. **telegraf** (password: telegraf123)
   - Full access to the `solar_farms` database
   - Used by Telegraf service for data ingestion

3. **reader** (password: reader123)
   - Read-only access to the `solar_farms` database
   - Useful for monitoring and reporting tools

4. **writer** (password: writer123)
   - Write access to the `solar_farms` database
   - Can insert data but not modify database structure

## How to Use

### Quick Start

**Linux/Mac:**
```bash
./setup.sh
```

**Windows:**
```powershell
.\setup.ps1
```

### Manual Start

```bash
docker-compose down
docker-compose up -d
```

### Verify User Creation

After the containers are running, you can verify users were created:

```bash
docker exec influxdb influx -execute "SHOW USERS"
```

## Service Access

- **MQTT Broker**: localhost:1883
- **InfluxDB**: localhost:8086
- **Grafana**: localhost:3000 (admin/admin123)
- **MQTT Explorer**: localhost:4000

## Troubleshooting

### If users are not created:

1. Check container logs:
   ```bash
   docker logs influxdb
   ```

2. Manually run the initialization script:
   ```bash
   docker exec influxdb /docker-entrypoint-initdb.d/01-create-users.sh
   ```

3. Verify InfluxDB is running:
   ```bash
   docker exec influxdb influx -execute "SHOW DATABASES"
   ```

### For InfluxDB 2.x Migration

If you want to upgrade to InfluxDB 2.x later:

1. Replace the influxdb service in docker-compose.yml with the configuration from `docker-compose.influxdb2.yml`
2. Update telegraf.conf to use the InfluxDB v2 output plugin (example provided in the file)
3. Update any Grafana data sources to use token authentication

## Security Notes

- Default passwords are used for development/testing
- Change passwords in production environments
- Consider using Docker secrets for sensitive data in production
- The initialization script only runs on first container creation