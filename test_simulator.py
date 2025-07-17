#!/usr/bin/env python3
"""
Test script for Solar Farm Simulator
Runs basic tests to ensure the simulator works correctly
"""

import json
import sys
import os

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from solar_farm_simulator import SolarFarmSimulator

def test_simulator_initialization():
    """Test that the simulator initializes correctly"""
    print("Testing simulator initialization...")
    
    try:
        simulator = SolarFarmSimulator()
        
        # Check that 150 farms were generated
        assert len(simulator.solar_farms) == 150, f"Expected 150 farms, got {len(simulator.solar_farms)}"
        
        # Check that farms have required fields
        farm = simulator.solar_farms[0]
        required_fields = [
            'site_id', 'site_name', 'latitude', 'longitude', 
            'country', 'timezone', 'installation_date', 'system_capacity_kw'
        ]
        
        for field in required_fields:
            assert field in farm, f"Missing required field: {field}"
        
        print("✅ Simulator initialization test passed")
        return True
        
    except Exception as e:
        print(f"❌ Simulator initialization test failed: {e}")
        return False

def test_telemetry_generation():
    """Test telemetry data generation"""
    print("Testing telemetry generation...")
    
    try:
        simulator = SolarFarmSimulator()
        farm = simulator.solar_farms[0]
        
        # Generate telemetry data
        telemetry = simulator._generate_telemetry(farm)
        
        # Check required telemetry fields
        required_fields = [
            'timestamp', 'site_id', 'ambient_temperature_c', 'module_temperature_c',
            'irradiance_wm2', 'energy_generated_kwh', 'power_output_kw',
            'energy_utilised_kwh', 'energy_exported_kwh', 'system_status',
            'inverter_status', 'string_faults', 'dc_voltage_v', 'ac_voltage_v'
        ]
        
        for field in required_fields:
            assert field in telemetry, f"Missing telemetry field: {field}"
        
        # Check data types and ranges
        assert isinstance(telemetry['ambient_temperature_c'], (int, float)), "Temperature should be numeric"
        assert isinstance(telemetry['power_output_kw'], (int, float)), "Power should be numeric"
        assert telemetry['power_output_kw'] >= 0, "Power should be non-negative"
        assert telemetry['system_status'] in ['online', 'offline', 'fault'], "Invalid system status"
        assert telemetry['inverter_status'] in ['healthy', 'fault', 'maintenance'], "Invalid inverter status"
        
        print("✅ Telemetry generation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Telemetry generation test failed: {e}")
        return False

def test_json_serialization():
    """Test that generated data can be serialized to JSON"""
    print("Testing JSON serialization...")
    
    try:
        simulator = SolarFarmSimulator()
        farm = simulator.solar_farms[0]
        
        # Test static data serialization
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
        
        static_json = json.dumps(static_data, indent=2)
        assert len(static_json) > 0, "Static JSON should not be empty"
        
        # Test telemetry data serialization
        telemetry = simulator._generate_telemetry(farm)
        telemetry_json = json.dumps(telemetry, indent=2)
        assert len(telemetry_json) > 0, "Telemetry JSON should not be empty"
        
        # Test that JSON can be parsed back
        parsed_static = json.loads(static_json)
        parsed_telemetry = json.loads(telemetry_json)
        
        assert parsed_static['site_id'] == farm['site_id'], "Static data parsing failed"
        assert parsed_telemetry['site_id'] == farm['site_id'], "Telemetry data parsing failed"
        
        print("✅ JSON serialization test passed")
        return True
        
    except Exception as e:
        print(f"❌ JSON serialization test failed: {e}")
        return False

def test_farm_diversity():
    """Test that generated farms have geographic diversity"""
    print("Testing farm diversity...")
    
    try:
        simulator = SolarFarmSimulator()
        
        # Check country diversity
        countries = set(farm['country'] for farm in simulator.solar_farms)
        assert len(countries) >= 10, f"Expected at least 10 countries, got {len(countries)}"
        
        # Check capacity diversity
        capacities = [farm['system_capacity_kw'] for farm in simulator.solar_farms]
        min_capacity = min(capacities)
        max_capacity = max(capacities)
        assert max_capacity > min_capacity * 2, "Capacity range should be diverse"
        
        # Check coordinate diversity
        latitudes = [farm['latitude'] for farm in simulator.solar_farms]
        longitudes = [farm['longitude'] for farm in simulator.solar_farms]
        
        lat_range = max(latitudes) - min(latitudes)
        lon_range = max(longitudes) - min(longitudes)
        
        assert lat_range > 50, f"Latitude range too small: {lat_range}"
        assert lon_range > 100, f"Longitude range too small: {lon_range}"
        
        print("✅ Farm diversity test passed")
        print(f"   Countries: {len(countries)}")
        print(f"   Capacity range: {min_capacity:,} - {max_capacity:,} kW")
        print(f"   Geographic spread: {lat_range:.1f}° lat, {lon_range:.1f}° lon")
        return True
        
    except Exception as e:
        print(f"❌ Farm diversity test failed: {e}")
        return False

def test_summary_function():
    """Test the farm summary function"""
    print("Testing summary function...")
    
    try:
        simulator = SolarFarmSimulator()
        summary = simulator.get_farm_summary()
        
        # Check summary structure
        required_keys = ['total_farms', 'total_capacity_kw', 'countries', 'average_capacity_kw']
        for key in required_keys:
            assert key in summary, f"Missing summary key: {key}"
        
        assert summary['total_farms'] == 150, f"Expected 150 farms in summary, got {summary['total_farms']}"
        assert summary['total_capacity_kw'] > 0, "Total capacity should be positive"
        assert len(summary['countries']) > 0, "Should have at least one country"
        assert summary['average_capacity_kw'] > 0, "Average capacity should be positive"
        
        print("✅ Summary function test passed")
        print(f"   Total farms: {summary['total_farms']}")
        print(f"   Total capacity: {summary['total_capacity_kw']:,} kW")
        print(f"   Countries: {len(summary['countries'])}")
        return True
        
    except Exception as e:
        print(f"❌ Summary function test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running Solar Farm Simulator Tests\n")
    
    tests = [
        test_simulator_initialization,
        test_telemetry_generation,
        test_json_serialization,
        test_farm_diversity,
        test_summary_function
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
        print()  # Empty line between tests
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())