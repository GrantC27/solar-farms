# Grafana Dashboard Migration to InfluxDB v2

## Overview

The Grafana dashboards have been updated to work with InfluxDB v2 and use Flux queries instead of InfluxQL. This document explains the changes made and how to use the new dashboards.

## Changes Made

### 1. Datasource Updates
- **Old**: `InfluxDB-SolarFarms` (InfluxDB v1)
- **New**: `InfluxDB-v2`, `InfluxDB-v2-Events`, `InfluxDB-v2-Historical`

### 2. Query Language Migration
- **Old**: InfluxQL queries with `SELECT`, `FROM`, `WHERE`, `GROUP BY`
- **New**: Flux queries with `from()`, `range()`, `filter()`, `group()`, `aggregateWindow()`

### 3. Dashboard Files

#### Main Dashboard: `solar-farm-dashboard.json`
- Updated all panels to use Flux queries
- Added template variables for Country and Site ID filtering
- Enhanced with proper InfluxDB v2 datasource references
- Improved error handling and data visualization

#### Enhanced Dashboard: `solar-farm-enhanced-dashboard.json`
- Additional KPI panels (Total Power, Active Farms, Average Efficiency, Active Faults)
- Better legend configurations with statistics
- Color-coded table cells with thresholds
- Separate panels for fault and maintenance data using the events bucket
- Enhanced filtering capabilities

## Query Migration Examples

### Power Output by Country

**Old InfluxQL:**
```sql
SELECT mean("power_output_kw_sum") 
FROM "solar_farm_telemetry_by_country" 
WHERE $timeFilter 
GROUP BY time($__interval), "country" fill(null)
```

**New Flux:**
```flux
from(bucket: "solar_farms")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "power_output")
  |> group(columns: ["country"])
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

### System Status Count

**Old InfluxQL:**
```sql
SELECT count("power_output_kw") 
FROM "solar_farm_telemetry" 
WHERE $timeFilter 
GROUP BY "system_status"
```

**New Flux:**
```flux
from(bucket: "solar_farms")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "system_status")
  |> group(columns: ["system_status"])
  |> count()
  |> yield(name: "count")
```

### Complex Table Query with Joins

**New Flux (Enhanced Feature):**
```flux
telemetry = from(bucket: "solar_farms")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "power_output" or r._field == "system_efficiency")
  |> group(columns: ["site_id"])
  |> last()
  |> pivot(rowKey: ["site_id"], columnKey: ["_field"], valueColumn: "_value")

static = from(bucket: "solar_farms")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "solar_farm_static")
  |> filter(fn: (r) => r._field == "system_capacity_kw" or r._field == "site_name")
  |> group(columns: ["site_id"])
  |> last()
  |> pivot(rowKey: ["site_id"], columnKey: ["_field"], valueColumn: "_value")

join(tables: {telemetry: telemetry, static: static}, on: ["site_id"])
  |> map(fn: (r) => ({
      site_id: r.site_id,
      site_name: r.site_name,
      power_output: r.power_output,
      capacity_utilization: (r.power_output / r.system_capacity_kw) * 100.0
    }))
```

## New Features

### 1. Template Variables
Both dashboards now include template variables for dynamic filtering:

- **Country**: Multi-select dropdown populated from static data
- **Site ID**: Multi-select dropdown for specific farm selection

### 2. Multiple Datasources
- **InfluxDB-v2**: Main telemetry data
- **InfluxDB-v2-Events**: Fault and maintenance data (6-month retention)
- **InfluxDB-v2-Historical**: Long-term aggregated data (1-year retention)

### 3. Enhanced Visualizations

#### KPI Panels (Enhanced Dashboard)
- Total Power Output with color thresholds
- Active Solar Farms count
- Average System Efficiency
- Active Faults alert panel

#### Improved Table
- Color-coded cells based on performance thresholds
- Calculated fields (capacity utilization)
- Better sorting and filtering

#### Time Series Enhancements
- Legend with statistics (mean, max)
- Multi-tooltip mode for better data comparison
- Proper units and formatting

## Dashboard Installation

### Automatic Provisioning
The dashboards are automatically loaded via Grafana provisioning:

1. **Configuration**: `grafana/provisioning/dashboards/dashboards.yml`
2. **Dashboard Files**: `grafana/dashboards/`
3. **Datasources**: `grafana/provisioning/datasources/influxdb.yml`

### Manual Import
If needed, you can manually import the dashboards:

1. Open Grafana at `http://localhost:3000`
2. Go to **Dashboards** → **Import**
3. Upload the JSON file or paste the content
4. Select the appropriate datasource

## Usage Guide

### 1. Accessing Dashboards
- **Main Dashboard**: "Solar Farm Monitoring Dashboard - InfluxDB v2"
- **Enhanced Dashboard**: "Solar Farm Monitoring Dashboard - Enhanced v2"

### 2. Using Template Variables
- **Country Filter**: Select one or more countries to focus on specific regions
- **Site ID Filter**: Choose specific solar farms for detailed analysis
- **All Option**: Select "All" to view data from all farms/countries

### 3. Time Range Selection
- Use Grafana's time picker to select different time ranges
- Dashboards automatically adjust aggregation windows based on selected range
- Recommended ranges: 1h, 6h, 24h, 7d

### 4. Panel Interactions
- **Zoom**: Click and drag on time series charts to zoom in
- **Legend**: Click legend items to show/hide series
- **Tooltip**: Hover over data points for detailed information
- **Table Sorting**: Click column headers to sort data

## Troubleshooting

### Common Issues

1. **No Data Displayed**
   - Verify InfluxDB v2 is running and accessible
   - Check that the solar farm simulator is publishing data
   - Ensure Telegraf is writing data to the correct bucket

2. **Query Errors**
   - Verify datasource configuration in Grafana
   - Check InfluxDB v2 token permissions
   - Ensure bucket names match the configuration

3. **Template Variables Not Loading**
   - Check that static data exists in the `solar_farms` bucket
   - Verify the template variable queries are correct
   - Refresh the dashboard or reload Grafana

### Useful Commands

```bash
# Check if data exists in InfluxDB
docker exec influxdb influx query 'from(bucket:"solar_farms") |> range(start:-1h) |> limit(n:10)'

# View Grafana logs
docker logs solar-farm-grafana

# Restart Grafana
docker-compose restart grafana

# Check Telegraf data ingestion
docker logs solar-farm-telegraf
```

## Performance Considerations

### Query Optimization
- Use appropriate time ranges to limit data scanned
- Leverage the `aggregateWindow()` function for time-based aggregation
- Use `group()` to organize data efficiently
- Apply filters early in the query pipeline

### Dashboard Performance
- Avoid overly complex queries in high-refresh panels
- Use appropriate refresh intervals (30s recommended)
- Consider using the historical bucket for long-term trend analysis

## Advanced Features

### Custom Queries
You can create custom panels with your own Flux queries:

1. Add a new panel to the dashboard
2. Select the appropriate InfluxDB v2 datasource
3. Write your Flux query using the examples in `FLUX_QUERIES.md`
4. Configure visualization options

### Alerting
Set up alerts using Grafana's alerting features:

1. Create alert rules based on Flux queries
2. Configure notification channels
3. Set appropriate thresholds for solar farm metrics

### Data Export
Export data for analysis:

1. Use the panel menu to download data as CSV
2. Create custom queries in the InfluxDB v2 web UI
3. Use the InfluxDB v2 API for programmatic access

## Migration Checklist

- [x] Updated datasource references to InfluxDB v2
- [x] Converted all InfluxQL queries to Flux
- [x] Added template variables for filtering
- [x] Enhanced visualizations with better formatting
- [x] Created separate panels for different data types
- [x] Added color thresholds and conditional formatting
- [x] Improved table with calculated fields
- [x] Added KPI panels for key metrics
- [x] Configured automatic dashboard provisioning
- [x] Created comprehensive documentation

## Next Steps

1. **Test the dashboards** with live data from the solar farm simulator
2. **Customize panels** based on specific monitoring requirements
3. **Set up alerting** for critical metrics
4. **Create additional dashboards** for specific use cases
5. **Train users** on the new Flux query language and features