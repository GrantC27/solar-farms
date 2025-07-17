#!/usr/bin/env python3
"""
Solar Farm MQTT Simulator
Simulates 150 solar farms worldwide and publishes telemetry data to MQTT broker
"""

import json
import random
import time
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any
import paho.mqtt.client as mqtt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SolarFarmSimulator:
    def __init__(self, mqtt_broker: str = "localhost", mqtt_port: int = 1883, 
                 mqtt_username: str = None, mqtt_password: str = None):
        """Initialize the solar farm simulator"""
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password
        
        # MQTT client setup
        self.mqtt_client = mqtt.Client()
        if mqtt_username and mqtt_password:
            self.mqtt_client.username_pw_set(mqtt_username, mqtt_password)
        
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_disconnect = self._on_disconnect
        self.mqtt_client.on_publish = self._on_publish
        
        # Solar farm data
        self.solar_farms: List[Dict[str, Any]] = []
        self.running = False
        self.publish_interval = 30  # seconds
        
        # Initialize solar farms
        self._generate_solar_farms()
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        logger.info("Disconnected from MQTT broker")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for successful message publish"""
        pass  # Can be used for debugging if needed
    
    def _generate_solar_farms(self):
        """Generate 150 solar farms with diverse global locations"""
        logger.info("Generating 150 solar farm configurations...")
        
        # Sample locations around the world with realistic solar farm data
        locations = [
            # North America
            {"country": "United States", "state": "California", "timezone": "America/Los_Angeles", "lat_range": (32, 42), "lon_range": (-124, -114)},
            {"country": "United States", "state": "Texas", "timezone": "America/Chicago", "lat_range": (25, 37), "lon_range": (-107, -93)},
            {"country": "United States", "state": "Arizona", "timezone": "America/Phoenix", "lat_range": (31, 37), "lon_range": (-115, -109)},
            {"country": "United States", "state": "Nevada", "timezone": "America/Los_Angeles", "lat_range": (35, 42), "lon_range": (-120, -114)},
            {"country": "Canada", "state": "Ontario", "timezone": "America/Toronto", "lat_range": (42, 57), "lon_range": (-95, -74)},
            {"country": "Mexico", "state": "Sonora", "timezone": "America/Hermosillo", "lat_range": (27, 32), "lon_range": (-115, -108)},
            
            # South America
            {"country": "Brazil", "state": "Minas Gerais", "timezone": "America/Sao_Paulo", "lat_range": (-22, -14), "lon_range": (-51, -39)},
            {"country": "Chile", "state": "Atacama", "timezone": "America/Santiago", "lat_range": (-29, -24), "lon_range": (-71, -68)},
            {"country": "Argentina", "state": "Mendoza", "timezone": "America/Argentina/Mendoza", "lat_range": (-37, -32), "lon_range": (-70, -66)},
            
            # Europe
            {"country": "Spain", "state": "Andalusia", "timezone": "Europe/Madrid", "lat_range": (36, 38), "lon_range": (-7, -1)},
            {"country": "Germany", "state": "Bavaria", "timezone": "Europe/Berlin", "lat_range": (47, 50), "lon_range": (9, 13)},
            {"country": "Italy", "state": "Sicily", "timezone": "Europe/Rome", "lat_range": (36, 38), "lon_range": (12, 16)},
            {"country": "France", "state": "Provence", "timezone": "Europe/Paris", "lat_range": (43, 45), "lon_range": (4, 7)},
            {"country": "Greece", "state": "Crete", "timezone": "Europe/Athens", "lat_range": (35, 36), "lon_range": (23, 26)},
            
            # Africa
            {"country": "South Africa", "state": "Northern Cape", "timezone": "Africa/Johannesburg", "lat_range": (-33, -28), "lon_range": (16, 24)},
            {"country": "Morocco", "state": "Ouarzazate", "timezone": "Africa/Casablanca", "lat_range": (30, 32), "lon_range": (-8, -6)},
            {"country": "Egypt", "state": "Aswan", "timezone": "Africa/Cairo", "lat_range": (24, 26), "lon_range": (32, 34)},
            
            # Asia
            {"country": "India", "state": "Rajasthan", "timezone": "Asia/Kolkata", "lat_range": (24, 30), "lon_range": (69, 78)},
            {"country": "China", "state": "Xinjiang", "timezone": "Asia/Shanghai", "lat_range": (35, 49), "lon_range": (73, 96)},
            {"country": "Japan", "state": "Kyushu", "timezone": "Asia/Tokyo", "lat_range": (31, 34), "lon_range": (129, 132)},
            {"country": "Australia", "state": "Queensland", "timezone": "Australia/Brisbane", "lat_range": (-29, -10), "lon_range": (138, 154)},
            
            # Middle East
            {"country": "United Arab Emirates", "state": "Abu Dhabi", "timezone": "Asia/Dubai", "lat_range": (22, 26), "lon_range": (51, 56)},
            {"country": "Saudi Arabia", "state": "Riyadh", "timezone": "Asia/Riyadh", "lat_range": (24, 27), "lon_range": (46, 48)},
        ]
        
        farm_names = [
            "Solar Park", "Energy Farm", "Power Station", "Solar Plant", "Green Energy Hub",
            "Renewable Center", "Solar Complex", "Energy Station", "Power Farm", "Solar Field",
            "Clean Energy Park", "Photovoltaic Plant", "Solar Installation", "Energy Complex"
        ]
        
        for i in range(150):
            location = random.choice(locations)
            
            # Generate realistic coordinates within the region
            latitude = round(random.uniform(location["lat_range"][0], location["lat_range"][1]), 6)
            longitude = round(random.uniform(location["lon_range"][0], location["lon_range"][1]), 6)
            
            # Generate installation date (last 10 years)
            start_year = 2014
            end_year = 2024
            year = random.randint(start_year, end_year)
            month = random.randint(1, 12)
            day = random.randint(1, 28)  # Safe day range
            
            # Generate system capacity (realistic range for solar farms)
            capacity_ranges = [
                (1000, 5000),    # Small farms
                (5000, 25000),   # Medium farms  
                (25000, 100000), # Large farms
                (100000, 500000) # Utility scale
            ]
            capacity_range = random.choice(capacity_ranges)
            system_capacity = random.randint(capacity_range[0], capacity_range[1])
            
            farm_name = f"{location['state']} {random.choice(farm_names)} {i+1:03d}"
            
            solar_farm = {
                "site_id": f"site_{i+1:03d}",
                "site_name": farm_name,
                "latitude": latitude,
                "longitude": longitude,
                "country": location["country"],
                "state": location["state"],
                "timezone": location["timezone"],
                "installation_date": f"{year:04d}-{month:02d}-{day:02d}",
                "system_capacity_kw": system_capacity,
                # Runtime state for simulation
                "_last_energy_generated": random.uniform(0, system_capacity * 8),  # Daily accumulation
                "_fault_probability": random.uniform(0.001, 0.01),  # 0.1% to 1% chance
                "_maintenance_mode": False,
                "_maintenance_end": None
            }
            
            self.solar_farms.append(solar_farm)
        
        logger.info(f"Generated {len(self.solar_farms)} solar farms")
    
    def _calculate_sun_factor(self, latitude: float, longitude: float, timezone_str: str) -> float:
        """Calculate a sun factor based on time of day and location (simplified)"""
        import math

        now = datetime.now(timezone.utc)
        
        # Simple day/night calculation (very basic solar model)
        # In reality, you'd use proper solar position algorithms
        hour = now.hour
        
        # Adjust for longitude (rough approximation)
        local_hour = (hour + longitude / 15) % 24
        
        # Basic sun intensity curve (0 at night, peak at noon)
        if 6 <= local_hour <= 18:
            # Sine curve for daylight hours
            sun_angle = (local_hour - 6) / 12 * 3.14159
            sun_factor = max(0, (0.8 * (1 + 0.5 * random.random())) * abs(math.sin(sun_angle)))
        else:
            sun_factor = 0
        
        # Add some seasonal variation (simplified)
        day_of_year = now.timetuple().tm_yday
        seasonal_factor = 0.8 + 0.4 * math.sin((day_of_year - 80) / 365 * 2 * 3.14159)
        
        return sun_factor * seasonal_factor
    
    def _generate_telemetry(self, farm: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic telemetry data for a solar farm"""
        import math
        
        now = datetime.now(timezone.utc)
        
        # Calculate sun factor for realistic power generation
        sun_factor = self._calculate_sun_factor(farm["latitude"], farm["longitude"], farm["timezone"])
        
        # Base environmental conditions
        base_temp = 25 + random.uniform(-10, 15)  # Seasonal variation
        ambient_temp = base_temp + random.uniform(-5, 5)
        
        # Module temperature is typically higher than ambient when sun is shining
        module_temp = ambient_temp + (sun_factor * random.uniform(5, 15))
        
        # Irradiance based on sun factor
        max_irradiance = 1200  # W/m²
        irradiance = sun_factor * max_irradiance * random.uniform(0.8, 1.0)
        
        # Power output based on capacity, irradiance, and efficiency
        efficiency = random.uniform(0.15, 0.22)  # 15-22% efficiency
        theoretical_power = farm["system_capacity_kw"] * (irradiance / 1000) * efficiency
        
        # Add realistic losses and variations
        power_output = max(0, theoretical_power * random.uniform(0.85, 0.98))
        
        # Energy calculations
        time_delta = self.publish_interval / 3600  # Convert seconds to hours
        energy_increment = power_output * time_delta
        farm["_last_energy_generated"] += energy_increment
        
        # Energy utilization (some used locally, some exported)
        utilization_factor = random.uniform(0.1, 0.3)
        energy_utilised = energy_increment * utilization_factor
        energy_exported = energy_increment * (1 - utilization_factor)
        
        # System status logic
        system_status = "online"
        inverter_status = "healthy"
        string_faults = 0
        
        # Random fault simulation
        if random.random() < farm["_fault_probability"]:
            if random.random() < 0.3:  # 30% chance of system fault
                system_status = "fault"
                power_output *= 0.1  # Significant power reduction
            elif random.random() < 0.5:  # 50% chance of inverter issue
                inverter_status = "fault"
                power_output *= 0.7  # Moderate power reduction
            else:  # String faults
                string_faults = random.randint(1, 5)
                power_output *= random.uniform(0.8, 0.95)
        
        # Maintenance mode
        if farm["_maintenance_mode"]:
            if farm["_maintenance_end"] and now > farm["_maintenance_end"]:
                farm["_maintenance_mode"] = False
                farm["_maintenance_end"] = None
            else:
                system_status = "offline"
                inverter_status = "maintenance"
                power_output = 0
                irradiance = 0
        elif random.random() < 0.0001:  # Very small chance to enter maintenance
            farm["_maintenance_mode"] = True
            # Maintenance lasts 1-6 hours
            maintenance_duration = random.randint(3600, 21600)
            from datetime import timedelta
            farm["_maintenance_end"] = now + timedelta(seconds=maintenance_duration)
        
        # Voltage calculations (simplified)
        dc_voltage = 600 + random.uniform(-50, 50) if power_output > 0 else 0
        ac_voltage = 400 + random.uniform(-20, 20) if power_output > 0 else 0
        
        return {
            "timestamp": now.isoformat(),
            "site_id": farm["site_id"],
            "ambient_temperature_c": round(ambient_temp, 1),
            "module_temperature_c": round(module_temp, 1),
            "irradiance_wm2": round(irradiance, 0),
            "energy_generated_kwh": round(farm["_last_energy_generated"], 1),
            "power_output_kw": round(power_output, 1),
            "energy_utilised_kwh": round(energy_utilised, 1),
            "energy_exported_kwh": round(energy_exported, 1),
            "system_status": system_status,
            "inverter_status": inverter_status,
            "string_faults": string_faults,
            "dc_voltage_v": round(dc_voltage, 1),
            "ac_voltage_v": round(ac_voltage, 1)
        }
    
    def _publish_farm_data(self, farm: Dict[str, Any]):
        """Publish static and telemetry data for a single farm"""
        try:
            # Publish static data (less frequently)
            static_topic = f"solar_farms/{farm['site_id']}/static"
            static_data = {
                "site_id": farm["site_id"],
                "site_name": farm["site_name"],
                "latitude": farm["latitude"],
                "longitude": farm["longitude"],
                "country": farm["country"],
                "timezone": farm["timezone"],
                "installation_date": farm["installation_date"],
                "system_capacity_kw": farm["system_capacity_kw"]
            }
            
            # Publish telemetry data
            telemetry_topic = f"solar_farms/{farm['site_id']}/telemetry"
            telemetry_data = self._generate_telemetry(farm)
            
            # Convert to JSON and publish
            static_json = json.dumps(static_data, indent=2)
            telemetry_json = json.dumps(telemetry_data, indent=2)
            
            self.mqtt_client.publish(static_topic, static_json, qos=1, retain=True)
            self.mqtt_client.publish(telemetry_topic, telemetry_json, qos=1)
            
            logger.debug(f"Published data for {farm['site_id']}")
            
        except Exception as e:
            logger.error(f"Error publishing data for {farm['site_id']}: {e}")
    
    def _publish_all_farms(self):
        """Publish data for all solar farms"""
        logger.info(f"Publishing data for {len(self.solar_farms)} solar farms...")
        
        for farm in self.solar_farms:
            if not self.running:
                break
            self._publish_farm_data(farm)
            # Small delay to avoid overwhelming the broker
            time.sleep(0.1)
        
        logger.info("Completed publishing cycle")
    
    def start_simulation(self):
        """Start the MQTT simulation"""
        logger.info("Starting solar farm simulation...")
        
        try:
            # Connect to MQTT broker
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            self.running = True
            
            # Main simulation loop
            while self.running:
                self._publish_all_farms()
                
                # Wait for next cycle
                for _ in range(self.publish_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
        except Exception as e:
            logger.error(f"Simulation error: {e}")
        finally:
            self.stop_simulation()
    
    def stop_simulation(self):
        """Stop the simulation"""
        logger.info("Stopping simulation...")
        self.running = False
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
    
    def get_farm_summary(self):
        """Get a summary of all solar farms"""
        total_capacity = sum(farm["system_capacity_kw"] for farm in self.solar_farms)
        countries = set(farm["country"] for farm in self.solar_farms)
        
        return {
            "total_farms": len(self.solar_farms),
            "total_capacity_kw": total_capacity,
            "countries": list(countries),
            "average_capacity_kw": total_capacity / len(self.solar_farms)
        }


def main():
    """Main function to run the simulator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Solar Farm MQTT Simulator")
    parser.add_argument("--broker", default="localhost", help="MQTT broker hostname")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--username", help="MQTT username")
    parser.add_argument("--password", help="MQTT password")
    parser.add_argument("--interval", type=int, default=30, help="Publish interval in seconds")
    parser.add_argument("--summary", action="store_true", help="Show farm summary and exit")
    
    args = parser.parse_args()
    
    # Create simulator
    simulator = SolarFarmSimulator(
        mqtt_broker=args.broker,
        mqtt_port=args.port,
        mqtt_username=args.username,
        mqtt_password=args.password
    )
    
    simulator.publish_interval = args.interval
    
    if args.summary:
        summary = simulator.get_farm_summary()
        print("\n=== Solar Farm Summary ===")
        print(f"Total Farms: {summary['total_farms']}")
        print(f"Total Capacity: {summary['total_capacity_kw']:,} kW")
        print(f"Average Capacity: {summary['average_capacity_kw']:,.0f} kW")
        print(f"Countries: {', '.join(summary['countries'])}")
        return
    
    # Start simulation
    try:
        simulator.start_simulation()
    except KeyboardInterrupt:
        print("\nShutting down...")
        simulator.stop_simulation()


if __name__ == "__main__":
    main()