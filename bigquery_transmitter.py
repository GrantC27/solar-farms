#!/usr/bin/env python3
"""
BigQuery Data Transmitter for Solar Farm Monitoring
Pulls data from InfluxDB and transmits it periodically to Google BigQuery
"""

import json
import time
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import threading
from dataclasses import dataclass, asdict

try:
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound
    from google.auth import load_credentials_from_file
    from google.oauth2 import service_account
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False
    print("Warning: google-cloud-bigquery not installed. Install with: pip install google-cloud-bigquery")

try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.query_api import QueryApi
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    print("Warning: influxdb-client not installed. Install with: pip install influxdb-client")

@dataclass
class SolarFarmTelemetry:
    """Data class for solar farm telemetry data"""
    timestamp: str
    site_id: str
    farm_name: str
    country: str
    latitude: float
    longitude: float
    power_output: float
    energy_generated: float
    energy_consumed: float
    energy_exported: float
    solar_irradiance: float
    ambient_temperature: float
    module_temperature: float
    wind_speed: float
    humidity: float
    inverter_efficiency: float
    system_efficiency: float
    fault_count: int
    maintenance_mode: bool
    operational_status: str

class InfluxDBReader:
    """Handles reading data from InfluxDB 2.x"""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config.get('influxdb', {})
        self.logger = logger
        self.client = None
        self.query_api = None
        
        if INFLUXDB_AVAILABLE:
            self._initialize_client()
        else:
            self.logger.error("InfluxDB client not available")
    
    def _initialize_client(self):
        """Initialize InfluxDB client"""
        try:
            url = self.config.get('url', 'http://localhost:8086')
            token = self.config.get('token', 'solar-farms-admin-token-super-secret-12345')
            org = self.config.get('org', 'solar-farms')
            
            self.client = InfluxDBClient(url=url, token=token, org=org)
            self.query_api = self.client.query_api()
            
            # Test connection
            health = self.client.health()
            if health.status == "pass":
                self.logger.info("InfluxDB client initialized successfully")
            else:
                self.logger.warning(f"InfluxDB health check: {health.status}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize InfluxDB client: {e}")
            self.client = None
            self.query_api = None
    
    def get_latest_telemetry_data(self, time_range: str = "-5m") -> List[SolarFarmTelemetry]:
        """Get latest telemetry data from InfluxDB"""
        if not self.query_api:
            self.logger.error("InfluxDB client not initialized")
            return []
        
        try:
            bucket = self.config.get('bucket', 'solar_farms')
            
            # Flux query to get latest telemetry data
            query = f'''
            from(bucket: "{bucket}")
              |> range(start: {time_range})
              |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
              |> group(columns: ["site_id"])
              |> last()
              |> pivot(rowKey: ["_time", "site_id"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            self.logger.debug(f"Executing query: {query}")
            result = self.query_api.query(query)
            
            telemetry_data = []
            for table in result:
                for record in table.records:
                    try:
                        # Extract data from the record
                        telemetry = self._create_telemetry_from_record(record)
                        if telemetry:
                            telemetry_data.append(telemetry)
                    except Exception as e:
                        self.logger.warning(f"Error processing record: {e}")
                        continue
            
            self.logger.info(f"Retrieved {len(telemetry_data)} telemetry records from InfluxDB")
            return telemetry_data
            
        except Exception as e:
            self.logger.error(f"Error querying InfluxDB: {e}")
            return []
    
    def get_telemetry_data_range(self, start_time: str, end_time: str) -> List[SolarFarmTelemetry]:
        """Get telemetry data for a specific time range"""
        if not self.query_api:
            self.logger.error("InfluxDB client not initialized")
            return []
        
        try:
            bucket = self.config.get('bucket', 'solar_farms')
            
            # Flux query to get data in time range
            query = f'''
            from(bucket: "{bucket}")
              |> range(start: {start_time}, stop: {end_time})
              |> filter(fn: (r) => r._measurement == "solar_farm_telemetry")
              |> group(columns: ["site_id", "_time"])
              |> pivot(rowKey: ["_time", "site_id"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            self.logger.debug(f"Executing range query: {query}")
            result = self.query_api.query(query)
            
            telemetry_data = []
            for table in result:
                for record in table.records:
                    try:
                        telemetry = self._create_telemetry_from_record(record)
                        if telemetry:
                            telemetry_data.append(telemetry)
                    except Exception as e:
                        self.logger.warning(f"Error processing record: {e}")
                        continue
            
            self.logger.info(f"Retrieved {len(telemetry_data)} records from InfluxDB for time range")
            return telemetry_data
            
        except Exception as e:
            self.logger.error(f"Error querying InfluxDB range: {e}")
            return []
    
    def _create_telemetry_from_record(self, record) -> Optional[SolarFarmTelemetry]:
        """Create SolarFarmTelemetry object from InfluxDB record"""
        try:
            # Get the record values - InfluxDB pivot creates columns for each field
            values = record.values
            
            # Extract site_id and timestamp
            site_id = values.get('site_id', f'UNKNOWN_{random.randint(1, 999):03d}')
            timestamp = values.get('_time')
            
            if timestamp:
                timestamp_str = timestamp.isoformat()
            else:
                timestamp_str = datetime.now(timezone.utc).isoformat()
            
            # Helper function to safely get float values
            def safe_float(key: str, default: float = 0.0) -> float:
                val = values.get(key)
                if val is None:
                    return default
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return default
            
            # Helper function to safely get int values
            def safe_int(key: str, default: int = 0) -> int:
                val = values.get(key)
                if val is None:
                    return default
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return default
            
            # Helper function to safely get string values
            def safe_str(key: str, default: str = '') -> str:
                val = values.get(key)
                return str(val) if val is not None else default
            
            # Helper function to safely get boolean values
            def safe_bool(key: str, default: bool = False) -> bool:
                val = values.get(key)
                if val is None:
                    return default
                if isinstance(val, bool):
                    return val
                if isinstance(val, str):
                    return val.lower() in ('true', '1', 'yes', 'on')
                try:
                    return bool(int(val))
                except (ValueError, TypeError):
                    return default
            
            # Create telemetry object with data from InfluxDB
            telemetry = SolarFarmTelemetry(
                timestamp=timestamp_str,
                site_id=site_id,
                farm_name=safe_str('farm_name', f'Solar Farm {site_id}'),
                country=safe_str('country', 'Unknown'),
                latitude=safe_float('latitude'),
                longitude=safe_float('longitude'),
                power_output=safe_float('power_output'),
                energy_generated=safe_float('energy_generated'),
                energy_consumed=safe_float('energy_consumed'),
                energy_exported=safe_float('energy_exported'),
                solar_irradiance=safe_float('solar_irradiance'),
                ambient_temperature=safe_float('ambient_temperature'),
                module_temperature=safe_float('module_temperature'),
                wind_speed=safe_float('wind_speed'),
                humidity=safe_float('humidity'),
                inverter_efficiency=safe_float('inverter_efficiency'),
                system_efficiency=safe_float('system_efficiency'),
                fault_count=safe_int('fault_count'),
                maintenance_mode=safe_bool('maintenance_mode'),
                operational_status=safe_str('operational_status', 'UNKNOWN')
            )
            
            return telemetry
            
        except Exception as e:
            self.logger.error(f"Error creating telemetry from record: {e}")
            return None
    
    def close(self):
        """Close InfluxDB client"""
        if self.client:
            self.client.close()

class BigQueryTransmitter:
    """Handles periodic transmission of data from InfluxDB to BigQuery"""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize the BigQuery transmitter"""
        self.config = self._load_config(config_file)
        self.logger = self._setup_logging()
        self.client = None
        self.dataset_id = self.config.get('bigquery', {}).get('dataset_id', 'solar_farms')
        self.table_id = self.config.get('bigquery', {}).get('table_id', 'telemetry')
        self.project_id = self.config.get('bigquery', {}).get('project_id')
        self.running = False
        self.thread = None
        
        # Initialize InfluxDB reader
        self.influxdb_reader = InfluxDBReader(self.config, self.logger)
        
        if BIGQUERY_AVAILABLE:
            self._initialize_bigquery()
        else:
            self.logger.error("BigQuery client not available. Please install google-cloud-bigquery")
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Add BigQuery configuration if not present
            if 'bigquery' not in config:
                config['bigquery'] = {
                    'project_id': 'your-gcp-project-id',
                    'dataset_id': 'solar_farms',
                    'table_id': 'telemetry',
                    'batch_size': 100,
                    'transmission_interval_seconds': 60,
                    'service_account_path': None,
                    'service_account_info': None
                }
            
            # Add InfluxDB configuration if not present
            if 'influxdb' not in config:
                config['influxdb'] = {
                    'url': os.getenv('INFLUXDB_URL', 'http://localhost:8086'),
                    'token': os.getenv('INFLUXDB_TOKEN', 'solar-farms-admin-token-super-secret-12345'),
                    'org': os.getenv('INFLUXDB_ORG', 'solar-farms'),
                    'bucket': os.getenv('INFLUXDB_BUCKET', 'solar_farms'),
                    'query_range': os.getenv('INFLUXDB_QUERY_RANGE', '-5m')
                }

                # Save updated config
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=4)

            return config
        except FileNotFoundError:
            self.logger.error(f"Configuration file {config_file} not found")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing configuration file: {e}")
            return {}
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.get('logging', {}).get('level', 'INFO')),
            format=self.config.get('logging', {}).get('format', '%(asctime)s - %(levelname)s - %(message)s')
        )
        return logging.getLogger(__name__)
    
    def _initialize_bigquery(self):
        """Initialize BigQuery client with authentication and ensure dataset/table exist"""
        try:
            credentials = None

            # Try service account key file first
            service_account_path = self.config.get('bigquery', {}).get('service_account_path')
            if service_account_path:
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_path,
                    scopes=['https://www.googleapis.com/auth/bigquery']
                )
                self.logger.info("Using service account credentials from file")

            # Try service account info from config
            elif 'service_account_info' in self.config.get('bigquery', {}):
                service_account_info = self.config['bigquery']['service_account_info']
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=['https://www.googleapis.com/auth/bigquery']
                )
                self.logger.info("Using service account credentials from config")

            # Initialize client with credentials
            if credentials:
                if self.project_id:
                    self.client = bigquery.Client(project=self.project_id, credentials=credentials)
                else:
                    self.client = bigquery.Client(credentials=credentials)
                    self.project_id = self.client.project
            else:
                # Fall back to default credentials (ADC)
                if self.project_id:
                    self.client = bigquery.Client(project=self.project_id)
                else:
                    self.client = bigquery.Client()
                    self.project_id = self.client.project
                self.logger.info("Using Application Default Credentials")

            self._ensure_dataset_exists()
            self._ensure_table_exists()
            self.logger.info("BigQuery client initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize BigQuery client: {e}")
            self.client = None
    
    def _ensure_dataset_exists(self):
        """Ensure the BigQuery dataset exists"""
        dataset_ref = self.client.dataset(self.dataset_id)
        
        try:
            self.client.get_dataset(dataset_ref)
            self.logger.info(f"Dataset {self.dataset_id} already exists")
        except NotFound:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"  # Change as needed
            dataset = self.client.create_dataset(dataset)
            self.logger.info(f"Created dataset {self.dataset_id}")
    
    def _ensure_table_exists(self):
        """Ensure the BigQuery table exists with proper schema"""
        table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
        
        try:
            self.client.get_table(table_ref)
            self.logger.info(f"Table {self.table_id} already exists")
        except NotFound:
            schema = [
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("site_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("farm_name", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("country", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("latitude", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("longitude", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("power_output", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("energy_generated", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("energy_consumed", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("energy_exported", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("solar_irradiance", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("ambient_temperature", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("module_temperature", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("wind_speed", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("humidity", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("inverter_efficiency", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("system_efficiency", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("fault_count", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("maintenance_mode", "BOOLEAN", mode="NULLABLE"),
                bigquery.SchemaField("operational_status", "STRING", mode="NULLABLE"),
            ]
            
            table = bigquery.Table(table_ref, schema=schema)
            table = self.client.create_table(table)
            self.logger.info(f"Created table {self.table_id}")
    
    def get_data_from_influxdb(self, time_range: Optional[str] = None) -> List[SolarFarmTelemetry]:
        """Get data from InfluxDB"""
        if not INFLUXDB_AVAILABLE:
            self.logger.error("InfluxDB client not available")
            return []
        
        if time_range is None:
            time_range = self.config.get('influxdb', {}).get('query_range', '-5m')
        
        return self.influxdb_reader.get_latest_telemetry_data(time_range)
    
    def get_data_from_influxdb_range(self, start_time: str, end_time: str) -> List[SolarFarmTelemetry]:
        """Get data from InfluxDB for a specific time range"""
        if not INFLUXDB_AVAILABLE:
            self.logger.error("InfluxDB client not available")
            return []
        
        return self.influxdb_reader.get_telemetry_data_range(start_time, end_time)
    
    def transmit_data(self, data: List[SolarFarmTelemetry]) -> bool:
        """Transmit data to BigQuery"""
        if not self.client:
            self.logger.error("BigQuery client not initialized")
            return False
        
        if not data:
            self.logger.warning("No data to transmit")
            return True
        
        try:
            table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
            table = self.client.get_table(table_ref)
            
            # Convert dataclass objects to dictionaries
            rows_to_insert = [asdict(item) for item in data]
            
            # Insert data
            errors = self.client.insert_rows_json(table, rows_to_insert)
            
            if errors:
                self.logger.error(f"Failed to insert rows: {errors}")
                return False
            else:
                self.logger.info(f"Successfully transmitted {len(data)} records to BigQuery")
                return True
                
        except Exception as e:
            self.logger.error(f"Error transmitting data to BigQuery: {e}")
            return False
    
    def _transmission_loop(self):
        """Main transmission loop that runs in a separate thread"""
        interval = self.config.get('bigquery', {}).get('transmission_interval_seconds', 3000)
        
        while self.running:
            try:
                # Get data from InfluxDB
                data = self.get_data_from_influxdb()
                
                if data:
                    # Transmit to BigQuery
                    success = self.transmit_data(data)
                    
                    if success:
                        self.logger.info(f"Transmitted batch of {len(data)} records from InfluxDB to BigQuery")
                    else:
                        self.logger.error("Failed to transmit data batch")
                else:
                    self.logger.info("No new data available in InfluxDB")
                
                # Wait for next transmission
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in transmission loop: {e}")
                time.sleep(interval)
    
    def start(self):
        """Start the periodic data transmission"""
        if not BIGQUERY_AVAILABLE:
            self.logger.error("Cannot start: BigQuery client not available")
            return False
        
        if not INFLUXDB_AVAILABLE:
            self.logger.error("Cannot start: InfluxDB client not available")
            return False
        
        if not self.client:
            self.logger.error("Cannot start: BigQuery client not initialized")
            return False
        
        if not self.influxdb_reader.client:
            self.logger.error("Cannot start: InfluxDB client not initialized")
            return False
        
        if self.running:
            self.logger.warning("Transmitter is already running")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._transmission_loop, daemon=True)
        self.thread.start()
        self.logger.info("BigQuery transmitter started - pulling data from InfluxDB")
        return True
    
    def stop(self):
        """Stop the periodic data transmission"""
        if not self.running:
            self.logger.warning("Transmitter is not running")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("BigQuery transmitter stopped")
    
    def transmit_once(self, time_range: Optional[str] = None) -> bool:
        """Transmit data once (for testing purposes)"""
        if not self.client:
            self.logger.error("BigQuery client not initialized")
            return False
        
        if not self.influxdb_reader.client:
            self.logger.error("InfluxDB client not initialized")
            return False
        
        data = self.get_data_from_influxdb(time_range)
        return self.transmit_data(data)
    
    def transmit_historical_data(self, hours_back: int = 24) -> bool:
        """Transmit historical data from InfluxDB to BigQuery"""
        if not self.client or not self.influxdb_reader.client:
            self.logger.error("Clients not initialized")
            return False
        
        # Calculate time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours_back)
        
        start_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        self.logger.info(f"Retrieving historical data from {start_str} to {end_str}")
        
        data = self.get_data_from_influxdb_range(start_str, end_str)
        
        if data:
            return self.transmit_data(data)
        else:
            self.logger.warning("No historical data found")
            return True
    
    def close(self):
        """Close connections"""
        if self.influxdb_reader:
            self.influxdb_reader.close()

def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BigQuery Data Transmitter for Solar Farm Monitoring")
    parser.add_argument("--config", default="config.json", help="Configuration file path")
    parser.add_argument("--once", action="store_true", help="Transmit data once and exit")
    parser.add_argument("--historical", type=int, help="Transmit historical data (hours back)")
    parser.add_argument("--time-range", default=None, help="Time range for data query (e.g., -1h, -30m)")
    
    args = parser.parse_args()
    
    transmitter = BigQueryTransmitter(args.config)
    
    try:
        if args.historical:
            # Transmit historical data
            success = transmitter.transmit_historical_data(args.historical)
            if success:
                print(f"Successfully transmitted historical data ({args.historical} hours)")
            else:
                print("Failed to transmit historical data")
                exit(1)
        elif args.once:
            # Transmit once and exit
            success = transmitter.transmit_once(args.time_range)
            if success:
                print("Successfully transmitted data from InfluxDB to BigQuery")
            else:
                print("Failed to transmit data")
                exit(1)
        else:
            # Start periodic transmission
            if transmitter.start():
                try:
                    print("BigQuery transmitter started (pulling from InfluxDB). Press Ctrl+C to stop...")
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nStopping transmitter...")
                    transmitter.stop()
            else:
                print("Failed to start BigQuery transmitter")
                exit(1)
    finally:
        transmitter.close()

if __name__ == "__main__":
    main()