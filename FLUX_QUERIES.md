# Flux Query Examples for Solar Farm Data

This file contains common Flux queries for analyzing solar farm data in InfluxDB v2.

## Basic Data Retrieval

### Get all telemetry data from the last hour
```flux
from(bucket: "solar_farms")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
```

### Get data for a specific solar farm
```flux
from(bucket: "solar_farms")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r.site_id == "FARM_001")
```

## Power Generation Analysis

### Average power output by farm (last 24 hours)
```flux
from(bucket: "solar_farms")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "power_output")
  |> group(columns: ["site_id"])
  |> mean()
```

### Peak power output per hour
```flux
from(bucket: "solar_farms")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "power_output")
  |> aggregateWindow(every: 1h, fn: max)
  |> group(columns: ["site_id"])
```

### Total energy generation by country
```flux
from(bucket: "solar_farms")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "energy_generated")
  |> group(columns: ["country"])
  |> sum()
```

## Environmental Data

### Temperature correlation with power output
```flux
temp_data = from(bucket: "solar_farms")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "ambient_temperature")
  |> group(columns: ["site_id"])

power_data = from(bucket: "solar_farms")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "power_output")
  |> group(columns: ["site_id"])

join(tables: {temp: temp_data, power: power_data}, on: ["_time", "site_id"])
```

### Solar irradiance vs power efficiency
```flux
from(bucket: "solar_farms")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "solar_irradiance" or r._field == "power_output")
  |> pivot(rowKey: ["_time", "site_id"], columnKey: ["_field"], valueColumn: "_value")
  |> map(fn: (r) => ({
      r with
      efficiency: r.power_output / r.solar_irradiance
    }))
```

## Fault and Maintenance Analysis

### Active faults by severity
```flux
from(bucket: "solar_farms")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "solar_farm_faults")
  |> filter(fn: (r) => r._field == "fault_active")
  |> filter(fn: (r) => r._value == true)
  |> group(columns: ["severity"])
  |> count()
```

### Maintenance schedule overview
```flux
from(bucket: "solar_farms")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "solar_farm_maintenance")
  |> filter(fn: (r) => r._field == "maintenance_active")
  |> group(columns: ["site_id", "maintenance_type"])
  |> count()
```

### Fault frequency by farm
```flux
from(bucket: "solar_farms")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "solar_farm_faults")
  |> filter(fn: (r) => r._field == "fault_count")
  |> group(columns: ["site_id"])
  |> sum()
  |> sort(columns: ["_value"], desc: true)
```

## Performance Metrics

### System efficiency over time
```flux
from(bucket: "solar_farms")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "system_efficiency")
  |> aggregateWindow(every: 1h, fn: mean)
  |> group(columns: ["site_id"])
```

### Inverter performance comparison
```flux
from(bucket: "solar_farms")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "inverter_efficiency")
  |> group(columns: ["site_id"])
  |> mean()
  |> sort(columns: ["_value"], desc: true)
```

## Weather Impact Analysis

### Power output vs weather conditions
```flux
from(bucket: "solar_farms")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "solar_farm_weather")
  |> filter(fn: (r) => r._field == "cloud_cover" or r._field == "humidity")
  |> pivot(rowKey: ["_time", "site_id"], columnKey: ["_field"], valueColumn: "_value")
```

### Daily energy generation by weather
```flux
from(bucket: "solar_farms")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "energy_generated")
  |> aggregateWindow(every: 1d, fn: sum)
  |> group(columns: ["site_id"])
```

## Alerting Queries

### Farms with low power output
```flux
from(bucket: "solar_farms")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "power_output")
  |> group(columns: ["site_id"])
  |> mean()
  |> filter(fn: (r) => r._value < 1000.0)  // Less than 1000W average
```

### High temperature alerts
```flux
from(bucket: "solar_farms")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "module_temperature")
  |> filter(fn: (r) => r._value > 85.0)  // Above 85°C
  |> group(columns: ["site_id"])
  |> last()
```

### System offline detection
```flux
from(bucket: "solar_farms")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "system_status")
  |> group(columns: ["site_id"])
  |> last()
  |> filter(fn: (r) => r._value != "online")
```

## Data Aggregation

### Hourly energy production summary
```flux
from(bucket: "solar_farms")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "energy_generated")
  |> aggregateWindow(every: 1h, fn: sum)
  |> group(columns: ["site_id"])
```

### Daily performance summary
```flux
from(bucket: "solar_farms")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
  |> filter(fn: (r) => r._field == "power_output" or r._field == "system_efficiency")
  |> aggregateWindow(every: 1d, fn: mean)
  |> pivot(rowKey: ["_time", "site_id"], columnKey: ["_field"], valueColumn: "_value")
```

## Tips for Writing Flux Queries

1. **Always specify a time range** with `range()` to limit data scanned
2. **Filter early** in the pipeline to reduce data processing
3. **Use appropriate aggregation windows** for time-series data
4. **Group by relevant tags** to organize results
5. **Use `yield()` to name result tables** when returning multiple datasets
6. **Test queries in the InfluxDB UI** before using in applications

## Common Functions

- `range()` - Specify time range
- `filter()` - Filter data based on conditions
- `group()` - Group data by columns
- `aggregateWindow()` - Time-based aggregation
- `mean()`, `sum()`, `max()`, `min()` - Statistical functions
- `pivot()` - Reshape data from long to wide format
- `join()` - Combine multiple data streams
- `map()` - Transform data with custom functions
- `sort()` - Sort results
- `limit()` - Limit number of results