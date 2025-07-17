#!/usr/bin/env python3
"""
Test script for BigQuery Data Transmitter with InfluxDB integration
Verifies that both InfluxDB and BigQuery connections are working correctly
"""

import sys
import json
import requests
from datetime import datetime

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    success = True
    
    try:
        from google.cloud import bigquery
        print("✅ google-cloud-bigquery imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import google-cloud-bigquery: {e}")
        print("   Install with: pip install google-cloud-bigquery")
        success = False
    
    try:
        from influxdb_client import InfluxDBClient
        print("✅ influxdb-client imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import influxdb-client: {e}")
        print("   Install with: pip install influxdb-client")
        success = False
    
    return success

def test_configuration():
    """Test if configuration file is valid"""
    print("\nTesting configuration...")
    
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        
        # Check if BigQuery section exists
        if "bigquery" not in config:
            print("❌ BigQuery configuration not found in config.json")
            return False
        
        # Check if InfluxDB section exists
        if "influxdb" not in config:
            print("❌ InfluxDB configuration not found in config.json")
            return False
        
        bq_config = config["bigquery"]
        influx_config = config["influxdb"]
        
        # Check BigQuery required fields
        bq_required_fields = ["project_id", "dataset_id", "table_id"]
        for field in bq_required_fields:
            if field not in bq_config:
                print(f"❌ Missing required BigQuery field: {field}")
                return False
        
        # Check InfluxDB required fields
        influx_required_fields = ["url", "token", "org", "bucket"]
        for field in influx_required_fields:
            if field not in influx_config:
                print(f"❌ Missing required InfluxDB field: {field}")
                return False
        
        if bq_config["project_id"] == "your-gcp-project-id":
            print("⚠️  Please update project_id in config.json with your actual GCP project ID")
            return False
        
        print("✅ Configuration file is valid")
        return True
        
    except FileNotFoundError:
        print("❌ config.json file not found")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config.json: {e}")
        return False

def test_influxdb_connection():
    """Test InfluxDB connection and health"""
    print("\nTesting InfluxDB connection...")
    
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        
        influx_config = config.get("influxdb", {})
        url = influx_config.get("url", "http://localhost:8086")
        
        # Test basic connectivity
        try:
            response = requests.get(f"{url}/ping", timeout=5)
            if response.status_code == 200:
                print("✅ InfluxDB is responding to ping")
            else:
                print(f"⚠️  InfluxDB ping returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot reach InfluxDB at {url}: {e}")
            print("   Make sure InfluxDB is running: docker-compose up -d")
            return False
        
        # Test InfluxDB client connection
        try:
            from influxdb_client import InfluxDBClient
            
            token = influx_config.get("token", "solar-farms-admin-token-super-secret-12345")
            org = influx_config.get("org", "solar-farms")
            
            client = InfluxDBClient(url=url, token=token, org=org)
            health = client.health()
            
            if health.status == "pass":
                print("✅ InfluxDB client connection successful")
                
                # Test if bucket exists
                bucket_name = influx_config.get("bucket", "solar_farms")
                buckets_api = client.buckets_api()
                bucket = buckets_api.find_bucket_by_name(bucket_name)
                
                if bucket:
                    print(f"✅ InfluxDB bucket '{bucket_name}' exists")
                else:
                    print(f"⚠️  InfluxDB bucket '{bucket_name}' not found")
                    print("   Make sure your solar farm simulator is running to create data")
                
                client.close()
                return True
            else:
                print(f"❌ InfluxDB health check failed: {health.status}")
                return False
                
        except Exception as e:
            print(f"❌ InfluxDB client connection failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing InfluxDB connection: {e}")
        return False

def test_influxdb_data():
    """Test if InfluxDB contains solar farm data"""
    print("\nTesting InfluxDB data availability...")
    
    try:
        from influxdb_client import InfluxDBClient
        
        with open("config.json", "r") as f:
            config = json.load(f)
        
        influx_config = config.get("influxdb", {})
        url = influx_config.get("url", "http://localhost:8086")
        token = influx_config.get("token", "solar-farms-admin-token-super-secret-12345")
        org = influx_config.get("org", "solar-farms")
        bucket = influx_config.get("bucket", "solar_farms")
        
        client = InfluxDBClient(url=url, token=token, org=org)
        query_api = client.query_api()
        
        # Query for recent telemetry data
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: -1h)
          |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
          |> limit(n: 1)
        '''
        
        result = query_api.query(query)
        
        has_data = False
        for table in result:
            if len(table.records) > 0:
                has_data = True
                break
        
        if has_data:
            print("✅ InfluxDB contains solar farm telemetry data")
            
            # Count total records
            count_query = f'''
            from(bucket: "{bucket}")
              |> range(start: -1h)
              |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
              |> count()
            '''
            
            count_result = query_api.query(count_query)
            total_records = 0
            for table in count_result:
                for record in table.records:
                    total_records += record.get_value()
            
            print(f"   Found {total_records} records in the last hour")
            
        else:
            print("⚠️  No solar farm telemetry data found in InfluxDB")
            print("   Start your solar farm simulator to generate data:")
            print("   python solar_farm_simulator.py")
        
        client.close()
        return has_data
        
    except Exception as e:
        print(f"❌ Error checking InfluxDB data: {e}")
        return False

def test_bigquery_authentication():
    """Test BigQuery authentication"""
    print("\nTesting BigQuery authentication...")
    
    try:
        from google.cloud import bigquery
        
        # Try to create a client
        client = bigquery.Client()
        
        # Try to list datasets (this requires authentication)
        datasets = list(client.list_datasets(max_results=1))
        
        print(f"✅ BigQuery authentication successful for project: {client.project}")
        return True
        
    except Exception as e:
        print(f"❌ BigQuery authentication failed: {e}")
        print("   Make sure you have set up authentication:")
        print("   - Service account key: export GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json")
        print("   - Or run: gcloud auth application-default login")
        return False

def test_transmitter_initialization():
    """Test if the transmitter can be initialized"""
    print("\nTesting transmitter initialization...")
    
    try:
        from bigquery_transmitter import BigQueryTransmitter
        
        transmitter = BigQueryTransmitter()
        
        if transmitter.client is None:
            print("❌ BigQuery client not initialized")
            return False
        
        if transmitter.influxdb_reader.client is None:
            print("❌ InfluxDB client not initialized")
            return False
        
        print("✅ Transmitter initialized successfully")
        transmitter.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize transmitter: {e}")
        return False

def test_data_retrieval():
    """Test data retrieval from InfluxDB"""
    print("\nTesting data retrieval from InfluxDB...")
    
    try:
        from bigquery_transmitter import BigQueryTransmitter
        
        transmitter = BigQueryTransmitter()
        data = transmitter.get_data_from_influxdb(time_range="-1h")
        
        if data:
            print(f"✅ Successfully retrieved {len(data)} records from InfluxDB")
            
            # Check data structure
            first_record = data[0]
            if hasattr(first_record, 'site_id') and hasattr(first_record, 'timestamp'):
                print("✅ Data structure is correct")
            else:
                print("❌ Data structure is incorrect")
                return False
        else:
            print("⚠️  No data retrieved from InfluxDB (this may be normal if no data exists)")
        
        transmitter.close()
        return True
        
    except Exception as e:
        print(f"❌ Data retrieval failed: {e}")
        return False

def main():
    """Run all tests"""
    print("BigQuery Transmitter with InfluxDB Integration - Setup Test")
    print("=" * 65)
    print(f"Test started at: {datetime.now()}")
    print()
    
    tests = [
        test_imports,
        test_configuration,
        test_influxdb_connection,
        test_influxdb_data,
        test_bigquery_authentication,
        test_transmitter_initialization,
        test_data_retrieval
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 65)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Make sure your solar farm simulator is running")
        print("2. Update config.json with your GCP project ID")
        print("3. Run: python bigquery_transmitter.py --once")
        print("4. Check your BigQuery console for the data")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Start InfluxDB: docker-compose up -d")
        print("- Start solar farm simulator to generate data")
        print("- Set up BigQuery authentication")
        print("- Update config.json with correct settings")
        return 1

if __name__ == "__main__":
    sys.exit(main())