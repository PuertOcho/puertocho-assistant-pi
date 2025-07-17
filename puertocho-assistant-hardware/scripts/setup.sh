#!/bin/bash
"""
Setup script for PuertoCho Assistant Hardware Service
"""

set -e

echo "🚀 Setting up PuertoCho Assistant Hardware Service..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    print_warning "This script is designed for Raspberry Pi"
    print_warning "Some hardware features may not work on other platforms"
fi

# Create necessary directories
print_status "Creating directories..."
mkdir -p logs config data temp

# Set up permissions for hardware access
print_status "Setting up hardware permissions..."
sudo usermod -a -G gpio,i2c,spi,audio $USER

# Enable I2C and SPI if not already enabled
print_status "Enabling I2C and SPI..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# Check if audio device is available
print_status "Checking audio devices..."
if aplay -l | grep -q "seeed-voicecard"; then
    print_status "ReSpeaker audio device found"
else
    print_warning "ReSpeaker audio device not found"
    print_warning "Make sure the ReSpeaker driver is installed"
fi

# Test I2C
print_status "Testing I2C..."
if i2cdetect -y 1 &>/dev/null; then
    print_status "I2C is working"
else
    print_error "I2C test failed"
fi

# Test SPI
print_status "Testing SPI..."
if ls /dev/spidev* &>/dev/null; then
    print_status "SPI devices found"
else
    print_error "No SPI devices found"
fi

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file..."
    cp .env.example .env 2>/dev/null || true
fi

print_status "Setup completed!"
print_status "You may need to reboot for all changes to take effect"
print_status "Run 'sudo reboot' to restart the system"

echo "=================================================="
echo "🎉 Setup complete! Next steps:"
echo "1. Review and update the .env file with your settings"
echo "2. Build the Docker container: docker-compose build puertocho-assistant-hardware"
echo "3. Start the service: docker-compose up puertocho-assistant-hardware"
