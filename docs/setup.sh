#!/bin/bash
# PuertoCho Assistant - Quick Setup Script
# =========================================

set -e

echo "🚀 PuertoCho Assistant - Quick Setup"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the project root."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    
    # Prompt for Porcupine access key
    echo ""
    echo "🔑 IMPORTANT: You need to set your Porcupine access key"
    echo "   1. Go to https://console.picovoice.ai/"
    echo "   2. Get your access key"
    echo "   3. Edit .env file and set PORCUPINE_ACCESS_KEY"
    echo ""
    read -p "Do you want to set the access key now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your Porcupine access key: " access_key
        if [ ! -z "$access_key" ]; then
            sed -i "s/your_access_key_here/$access_key/" .env
            echo "✅ Access key set successfully"
        else
            echo "⚠️  No access key provided. Please edit .env file manually."
        fi
    fi
else
    echo "✅ .env file already exists"
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build all images
echo "🏗️  Building Docker images..."
docker-compose build

# Start all services
echo "🚀 Starting PuertoCho Assistant services..."
docker-compose up -d

# Wait a bit for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
docker-compose ps

# Health check
echo ""
echo "🏥 Health check:"
if curl -f http://localhost:8765/health &>/dev/null; then
    echo "✅ Backend API: OK"
else
    echo "❌ Backend API: Not responding"
fi

if curl -f http://localhost:3000 &>/dev/null; then
    echo "✅ Web Dashboard: OK"
else
    echo "❌ Web Dashboard: Not responding"
fi

echo ""
echo "🎉 Setup complete!"
echo "================================"
echo "🌐 Web Dashboard: http://localhost:3000"
echo "🔌 Backend API: http://localhost:8765"
echo "📊 Check status: make status"
echo "📝 View logs: make logs"
echo "🛑 Stop services: make down"
echo ""
echo "If you need to configure your Porcupine access key:"
echo "  1. Edit .env file"
echo "  2. Run: make restart"
