@echo off
REM Solar Farm Simulator Startup Script for Windows

echo 🌞 Solar Farm MQTT Simulator
echo ==============================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install dependencies if requirements.txt exists
if exist requirements.txt (
    echo 📦 Installing Python dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check if Docker is available for MQTT broker
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    docker-compose --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo 🐳 Starting MQTT broker with Docker...
        docker-compose up -d
        if %errorlevel% equ 0 (
            echo ✅ MQTT broker started successfully
            echo    - MQTT broker: localhost:1883
            echo    - MQTT Explorer: http://localhost:4000
        ) else (
            echo ⚠️  Failed to start Docker services, continuing with external broker
        )
    ) else (
        echo ⚠️  Docker Compose not found. Please ensure MQTT broker is running on localhost:1883
    )
) else (
    echo ⚠️  Docker not found. Please ensure MQTT broker is running on localhost:1883
)

echo.
echo 🚀 Starting Solar Farm Simulator...
echo    Press Ctrl+C to stop
echo.

REM Start the simulator
python solar_farm_simulator.py %*