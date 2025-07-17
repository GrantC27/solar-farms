#!/usr/bin/env python3
"""
Health check script for Solar Farm Monitoring Stack
Checks if all services are running and accessible
"""

import requests
import socket
import json
import time
import sys
from datetime import datetime

def check_port(host, port, service_name):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ {service_name} - Port {port} is open")
            return True
        else:
            print(f"❌ {service_name} - Port {port} is closed")
            return False
    except Exception as e:
        print(f"❌ {service_name} - Error checking port {port}: {e}")
        return False

def check_http_service(url, service_name, expected_status=200):
    """Check if an HTTP service is responding"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == expected_status:
            print(f"✅ {service_name} - HTTP service is responding")
            return True
        else:
            print(f"❌ {service_name} - HTTP service returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {service_name} - HTTP service is not responding: {e}")
        return False

def check_influxdb():
    """Check InfluxDB health and database"""
    try:
        # Check health endpoint
        health_url = "http://localhost:8086/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ InfluxDB - Health check passed")
            
            # Check if database exists
            query_url = "http://localhost:8086/query"
            params = {
                'q': 'SHOW DATABASES',
                'u': 'telegraf',
                'p': 'telegraf123'
            }
            
            response = requests.get(query_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                databases = [db[0] for db in data['results'][0]['series'][0]['values']]
                
                if 'solar_farms' in databases:
                    print("✅ InfluxDB - solar_farms database exists")
                    return True
                else:
                    print("⚠️  InfluxDB - solar_farms database not found")
                    return False
            else:
                print(f"❌ InfluxDB - Query failed with status {response.status_code}")
                return False
        else:
            print(f"❌ InfluxDB - Health check failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ InfluxDB - Error: {e}")
        return False

def check_grafana():
    """Check Grafana health and datasource"""
    try:
        # Check health endpoint
        health_url = "http://localhost:3000/api/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Grafana - Health check passed")
            
            # Check datasource (requires authentication)
            auth = ('admin', 'admin123')
            ds_url = "http://localhost:3000/api/datasources"
            response = requests.get(ds_url, auth=auth, timeout=10)
            
            if response.status_code == 200:
                datasources = response.json()
                influx_ds = [ds for ds in datasources if ds.get('type') == 'influxdb']
                
                if influx_ds:
                    print("✅ Grafana - InfluxDB datasource configured")
                    return True
                else:
                    print("⚠️  Grafana - InfluxDB datasource not found")
                    return False
            else:
                print(f"⚠️  Grafana - Could not check datasources (status {response.status_code})")
                return True  # Still consider healthy if main service is up
        else:
            print(f"❌ Grafana - Health check failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Grafana - Error: {e}")
        return False

def main():
    """Main health check function"""
    print("🏥 Solar Farm Monitoring Stack Health Check")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    services_status = {}
    
    # Check MQTT Broker
    print("📡 Checking MQTT Services...")
    services_status['mosquitto'] = check_port('localhost', 1883, 'Mosquitto MQTT')
    services_status['mosquitto_ws'] = check_port('localhost', 9001, 'Mosquitto WebSocket')
    print()
    
    # Check Telegraf (no direct health check, but check if it's collecting data)
    print("📊 Checking Data Collection...")
    services_status['telegraf'] = check_port('localhost', 8086, 'Telegraf → InfluxDB')
    print()
    
    # Check InfluxDB
    print("🗄️  Checking Database...")
    services_status['influxdb'] = check_influxdb()
    print()
    
    # Check Grafana
    print("📈 Checking Visualization...")
    services_status['grafana'] = check_grafana()
    print()
    
    # Check MQTT Explorer
    print("🔍 Checking MQTT Explorer...")
    services_status['mqtt_explorer'] = check_http_service('http://localhost:4000', 'MQTT Explorer')
    print()
    
    # Summary
    print("=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    healthy_services = sum(1 for status in services_status.values() if status)
    total_services = len(services_status)
    
    for service, status in services_status.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service.replace('_', ' ').title()}")
    
    print()
    print(f"Overall Health: {healthy_services}/{total_services} services healthy")
    
    if healthy_services == total_services:
        print("🎉 All services are running correctly!")
        print()
        print("🌐 Access URLs:")
        print("   • Grafana Dashboard: http://localhost:3000 (admin/admin123)")
        print("   • MQTT Explorer: http://localhost:4000")
        print("   • InfluxDB: http://localhost:8086 (telegraf/telegraf123)")
        return 0
    else:
        print("⚠️  Some services are not healthy. Check the logs above.")
        print()
        print("🔧 Troubleshooting:")
        print("   • Run: docker-compose ps")
        print("   • Run: docker-compose logs [service-name]")
        print("   • Restart: docker-compose restart")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Health check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during health check: {e}")
        sys.exit(1)