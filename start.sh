#!/bin/bash

# Solar Farm Simulator Startup Script

echo "🌞 Solar Farm MQTT Simulator"
echo "=============================="

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed or not in PATH"
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed or not in PATH"
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Check if Docker is available for MQTT broker
if command -v docker &> /dev/null && command -v docker compose &> /dev/null; then
    echo "🐳 Starting MQTT broker with Docker..."
    docker compose up -d
    if [ $? -eq 0 ]; then
        echo "✅ MQTT broker started successfully"
        echo "   - MQTT broker: localhost:1883"
        echo "   - MQTT Explorer: http://localhost:4000"
    else
        echo "⚠️  Failed to start Docker services, continuing with external broker"
    fi
else
    echo "⚠️  Docker not found. Please ensure MQTT broker is running on localhost:1883"
fi

echo ""
echo "🚀 Starting Solar Farm Simulator..."
echo "   Press Ctrl+C to stop"
echo ""

# Start the simulator
python solar_farm_simulator.py "$@"