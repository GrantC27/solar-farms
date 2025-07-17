#!/usr/bin/env python3
"""
MQTT Subscriber for Solar Farm Data
Simple script to subscribe to and display solar farm data
"""

import json
import paho.mqtt.client as mqtt
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SolarFarmSubscriber:
    def __init__(self, broker="localhost", port=1883, username=None, password=None):
        self.broker = broker
        self.port = port
        
        # MQTT client setup
        self.client = mqtt.Client()
        if username and password:
            self.client.username_pw_set(username, password)
        
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        self.message_count = 0
        self.farms_seen = set()
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            # Subscribe to all solar farm topics
            client.subscribe("solar_farms/+/telemetry", qos=1)
            client.subscribe("solar_farms/+/static", qos=1)
            logger.info("Subscribed to solar farm topics")
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        logger.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Callback for received messages"""
        try:
            topic_parts = msg.topic.split('/')
            site_id = topic_parts[1]
            data_type = topic_parts[2]  # 'telemetry' or 'static'
            
            # Parse JSON data
            data = json.loads(msg.payload.decode())
            
            self.message_count += 1
            self.farms_seen.add(site_id)
            
            if data_type == "telemetry":
                self._display_telemetry(site_id, data)
            elif data_type == "static":
                self._display_static(site_id, data)
                
        except Exception as e:
            logger.error(f"Error processing message from {msg.topic}: {e}")
    
    def _display_telemetry(self, site_id, data):
        """Display telemetry data"""
        print(f"\n📊 TELEMETRY - {site_id}")
        print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
        print(f"   Power Output: {data.get('power_output_kw', 0):,.1f} kW")
        print(f"   Energy Generated: {data.get('energy_generated_kwh', 0):,.1f} kWh")
        print(f"   Irradiance: {data.get('irradiance_wm2', 0):,.0f} W/m²")
        print(f"   Ambient Temp: {data.get('ambient_temperature_c', 0):.1f}°C")
        print(f"   Module Temp: {data.get('module_temperature_c', 0):.1f}°C")
        print(f"   System Status: {data.get('system_status', 'unknown')}")
        print(f"   Inverter Status: {data.get('inverter_status', 'unknown')}")
        
        if data.get('string_faults', 0) > 0:
            print(f"   ⚠️  String Faults: {data.get('string_faults', 0)}")
    
    def _display_static(self, site_id, data):
        """Display static data"""
        print(f"\n🏭 STATIC - {site_id}")
        print(f"   Name: {data.get('site_name', 'N/A')}")
        print(f"   Location: {data.get('country', 'N/A')}")
        print(f"   Coordinates: {data.get('latitude', 0):.4f}, {data.get('longitude', 0):.4f}")
        print(f"   Capacity: {data.get('system_capacity_kw', 0):,} kW")
        print(f"   Installed: {data.get('installation_date', 'N/A')}")
    
    def start_listening(self):
        """Start listening for messages"""
        logger.info("Starting MQTT subscriber...")
        
        try:
            self.client.connect(self.broker, self.port, 60)
            
            print("\n🎯 Solar Farm Data Subscriber Started")
            print("   Press Ctrl+C to stop")
            print("   Listening for solar farm data...\n")
            
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            logger.info("Subscriber interrupted by user")
        except Exception as e:
            logger.error(f"Subscriber error: {e}")
        finally:
            self.stop_listening()
    
    def stop_listening(self):
        """Stop the subscriber"""
        logger.info("Stopping subscriber...")
        self.client.loop_stop()
        self.client.disconnect()
        
        print(f"\n📈 Session Summary:")
        print(f"   Messages received: {self.message_count}")
        print(f"   Unique farms seen: {len(self.farms_seen)}")
        if self.farms_seen:
            print(f"   Farm IDs: {', '.join(sorted(self.farms_seen))}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Solar Farm MQTT Subscriber")
    parser.add_argument("--broker", default="localhost", help="MQTT broker hostname")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--username", help="MQTT username")
    parser.add_argument("--password", help="MQTT password")
    
    args = parser.parse_args()
    
    # Create subscriber
    subscriber = SolarFarmSubscriber(
        broker=args.broker,
        port=args.port,
        username=args.username,
        password=args.password
    )
    
    # Start listening
    try:
        subscriber.start_listening()
    except KeyboardInterrupt:
        print("\nShutting down...")
        subscriber.stop_listening()


if __name__ == "__main__":
    main()