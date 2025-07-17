# InfluxDB v1 Configuration Backup

This file contains the original InfluxDB v1 configuration for reference.

## Original docker-compose.yml (InfluxDB section)

```yaml
  influxdb:
    image: influxdb:1.8
    container_name: influxdb
    ports:
      - "8086:8086"
    environment:
      # Database configuration
      - INFLUXDB_DB=solar_farms
      # Regular user for telegraf
      - INFLUXDB_USER=telegraf
      - INFLUXDB_USER_PASSWORD=telegraf123
      # Admin user
      - INFLUXDB_ADMIN_USER=admin
      - INFLUXDB_ADMIN_PASSWORD=admin123
      # Enable authentication
      - INFLUXDB_HTTP_AUTH_ENABLED=true
      # Additional user creation
      - INFLUXDB_READ_USER=reader
      - INFLUXDB_READ_USER_PASSWORD=reader123
      - INFLUXDB_WRITE_USER=writer
      - INFLUXDB_WRITE_USER_PASSWORD=writer123
    volumes:
      - influxdb_data:/var/lib/influxdb
      - ./influxdb-init:/docker-entrypoint-initdb.d
    networks:
      - solar-farm-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8086/ping"]
      interval: 30s
      timeout: 10s
      retries: 5
```

## Original telegraf.conf (Output section)

```toml
# Output to InfluxDB
[[outputs.influxdb]]
  urls = ["http://influxdb:8086"]
  database = "solar_farms"
  username = "telegraf"
  password = "telegraf123"
  retention_policy = ""
  write_consistency = "any"
  timeout = "5s"
  # Add these additional settings for authentication
  skip_database_creation = false
  # If using InfluxDB 1.x with authentication enabled
  # auth_method = "basic"
```

## Original Grafana Datasource Configuration

```yaml
apiVersion: 1

datasources:
  - name: InfluxDB
    type: influxdb
    access: proxy
    url: http://influxdb:8086
    database: solar_farms
    user: reader
    password: reader123
    isDefault: true
    editable: true
```

## Users Created in v1

1. **admin** (password: admin123) - Full administrative privileges
2. **telegraf** (password: telegraf123) - Full access to solar_farms database
3. **reader** (password: reader123) - Read-only access
4. **writer** (password: writer123) - Write access

## Migration Notes

- Database `solar_farms` became bucket `solar_farms`
- Username/password authentication became token-based
- InfluxQL queries need to be converted to Flux
- Retention policies are now configured per bucket
- Web UI is now built-in (was separate Chronograf)

## Rollback Instructions

If you need to rollback to InfluxDB v1:

1. Stop current containers:
   ```bash
   docker-compose down
   ```

2. Replace docker-compose.yml influxdb section with the v1 configuration above

3. Replace telegraf.conf output section with the v1 configuration above

4. Update Grafana datasource configuration to use v1 format

5. Restore the influxdb-init directory with v1 scripts

6. Start containers:
   ```bash
   docker-compose up -d
   ```