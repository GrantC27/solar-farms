#!/usr/bin/env python3
"""
Example usage of the BigQuery Data Transmitter with InfluxDB integration
This script demonstrates different ways to use the transmitter with real InfluxDB data
"""

import time
import json
from datetime import datetime, timezone, timedelta
from bigquery_transmitter import BigQueryTransmitter, SolarFarmTelemetry

def example_basic_usage():
    """Example 1: Basic usage - pull latest data from InfluxDB and send to BigQuery"""
    print("=== Example 1: Basic Usage (InfluxDB -> BigQuery) ===")
    
    # Initialize transmitter
    transmitter = BigQueryTransmitter()
    
    # Transmit latest data from InfluxDB
    success = transmitter.transmit_once()
    if success:
        print("✅ Successfully transmitted latest data from InfluxDB to BigQuery")
    else:
        print("❌ Failed to transmit data")

def example_custom_time_range():
    """Example 2: Pull data from specific time range"""
    print("\n=== Example 2: Custom Time Range ===")
    
    transmitter = BigQueryTransmitter()
    
    # Get data from last 30 minutes
    success = transmitter.transmit_once(time_range="-30m")
    if success:
        print("✅ Successfully transmitted data from last 30 minutes")
    else:
        print("❌ Failed to transmit data")

def example_historical_data():
    """Example 3: Transmit historical data"""
    print("\n=== Example 3: Historical Data Transmission ===")
    
    transmitter = BigQueryTransmitter()
    
    # Transmit last 6 hours of data
    success = transmitter.transmit_historical_data(hours_back=6)
    if success:
        print("✅ Successfully transmitted 6 hours of historical data")
    else:
        print("❌ Failed to transmit historical data")

def example_continuous_transmission():
    """Example 4: Continuous transmission from InfluxDB"""
    print("\n=== Example 4: Continuous Transmission ===")
    
    transmitter = BigQueryTransmitter()
    
    # Start continuous transmission
    if transmitter.start():
        print("✅ Started continuous transmission from InfluxDB to BigQuery")
        print("Running for 60 seconds...")
        
        # Let it run for 60 seconds
        time.sleep(60)
        
        # Stop transmission
        transmitter.stop()
        print("✅ Stopped transmission")
    else:
        print("❌ Failed to start transmission")

def example_custom_influxdb_config():
    """Example 5: Using custom InfluxDB configuration"""
    print("\n=== Example 5: Custom InfluxDB Configuration ===")
    
    # Create custom configuration with different InfluxDB settings
    custom_config = {
        "influxdb": {
            "url": "http://localhost:8086",
            "token": "your-custom-token",
            "org": "solar-farms",
            "bucket": "solar_farms",
            "query_range": "-10m"
        },
        "bigquery": {
            "project_id": "your-project-id",
            "dataset_id": "test_solar_farms",
            "table_id": "test_telemetry",
            "transmission_interval_seconds": 30
        },
        "logging": {
            "level": "DEBUG",
            "format": "%(asctime)s - %(levelname)s - %(message)s"
        }
    }
    
    # Save custom config
    with open("custom_influx_config.json", "w") as f:
        json.dump(custom_config, f, indent=4)
    
    # Use custom configuration
    transmitter = BigQueryTransmitter("custom_influx_config.json")
    
    # Test with custom config
    success = transmitter.transmit_once()
    if success:
        print("✅ Successfully used custom InfluxDB configuration")
    else:
        print("❌ Failed with custom configuration")

def example_data_inspection():
    """Example 6: Inspect data from InfluxDB before transmission"""
    print("\n=== Example 6: Data Inspection ===")
    
    transmitter = BigQueryTransmitter()
    
    # Get data from InfluxDB without transmitting
    data = transmitter.get_data_from_influxdb(time_range="-15m")
    
    if data:
        print(f"✅ Retrieved {len(data)} records from InfluxDB")
        
        # Show sample data
        if len(data) > 0:
            sample = data[0]
            print(f"Sample record:")
            print(f"  Site ID: {sample.site_id}")
            print(f"  Timestamp: {sample.timestamp}")
            print(f"  Power Output: {sample.power_output} kW")
            print(f"  Solar Irradiance: {sample.solar_irradiance} W/m²")
            print(f"  Temperature: {sample.ambient_temperature}°C")
            print(f"  Status: {sample.operational_status}")
        
        # Now transmit the data
        success = transmitter.transmit_data(data)
        if success:
            print("✅ Successfully transmitted inspected data to BigQuery")
        else:
            print("❌ Failed to transmit inspected data")
    else:
        print("❌ No data retrieved from InfluxDB")

def example_specific_time_range():
    """Example 7: Query specific time range from InfluxDB"""
    print("\n=== Example 7: Specific Time Range Query ===")
    
    transmitter = BigQueryTransmitter()
    
    # Define specific time range (last 2 hours)
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=2)
    
    start_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(f"Querying data from {start_str} to {end_str}")
    
    # Get data for specific time range
    data = transmitter.get_data_from_influxdb_range(start_str, end_str)
    
    if data:
        print(f"✅ Retrieved {len(data)} records for time range")
        
        # Transmit the data
        success = transmitter.transmit_data(data)
        if success:
            print("✅ Successfully transmitted time range data to BigQuery")
        else:
            print("❌ Failed to transmit time range data")
    else:
        print("❌ No data found for specified time range")

def example_error_handling():
    """Example 8: Error handling with InfluxDB connection issues"""
    print("\n=== Example 8: Error Handling ===")
    
    # Try to use invalid InfluxDB configuration
    invalid_config = {
        "influxdb": {
            "url": "http://invalid-host:8086",
            "token": "invalid-token",
            "org": "invalid-org",
            "bucket": "invalid-bucket"
        },
        "bigquery": {
            "project_id": "your-project-id",
            "dataset_id": "test_dataset",
            "table_id": "test_table"
        }
    }
    
    with open("invalid_influx_config.json", "w") as f:
        json.dump(invalid_config, f, indent=4)
    
    transmitter = BigQueryTransmitter("invalid_influx_config.json")
    
    # This should fail gracefully
    success = transmitter.transmit_once()
    if not success:
        print("✅ Error handling worked correctly - invalid InfluxDB config detected")

def main():
    """Run all examples"""
    print("BigQuery Transmitter Examples with InfluxDB Integration")
    print("=" * 60)
    
    try:
        # Run examples
        example_basic_usage()
        example_custom_time_range()
        example_data_inspection()
        example_specific_time_range()
        example_custom_influxdb_config()
        example_error_handling()
        
        # Note: Commented out to avoid long running examples
        # Uncomment the lines below to test these features
        # example_historical_data()
        # example_continuous_transmission()
        
        print("\n" + "=" * 60)
        print("All examples completed!")
        print("\nNote: Make sure your InfluxDB is running and contains solar farm data")
        print("Start your solar farm simulator first to populate InfluxDB with data")
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"\nError running examples: {e}")
    
    # Clean up temporary files
    import os
    for file in ["custom_influx_config.json", "invalid_influx_config.json"]:
        if os.path.exists(file):
            os.remove(file)

if __name__ == "__main__":
    main()