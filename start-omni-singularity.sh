#!/bin/bash

# OMNI Singularity Quantum Dashboard v10.0 - Startup Script
# Quick start script for Docker deployment with Google Cloud integration

echo "🧠 OMNI Singularity Quantum Dashboard v10.0"
echo "============================================="
echo ""
echo "🚀 Starting OMNI Singularity in Docker with Google Cloud..."
echo ""

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Setup Google Cloud integration
echo "☁️ Setting up Google Cloud integration..."
if [ -f setup-google-cloud.sh ]; then
    chmod +x setup-google-cloud.sh
    ./setup-google-cloud.sh
else
    echo "⚠️ Google Cloud setup script not found, continuing without Google Cloud integration"
fi

# Build and start OMNI Singularity
echo ""
echo "🔨 Building OMNI Singularity Docker image..."
docker build -f Dockerfile.omni-singularity -t omni-singularity:v10.0 .

echo ""
echo "🚀 Starting OMNI Singularity services..."
docker-compose -f docker-compose.omni.yml up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 30

# Check if services are healthy
echo ""
echo "❤️ Checking service health..."

if curl -f http://localhost:8093/health &> /dev/null; then
    echo "✅ OMNI Singularity is healthy"
else
    echo "⚠️ OMNI Singularity health check failed - services may still be starting"
fi

if curl -f http://localhost:8081/health &> /dev/null; then
    echo "✅ Dashboard is healthy"
else
    echo "⚠️ Dashboard health check failed"
fi

if curl -f http://localhost:8082/api/v1/health &> /dev/null; then
    echo "✅ API Gateway is healthy"
else
    echo "⚠️ API Gateway health check failed"
fi

# Test Google Cloud integration
echo ""
echo "☁️ Testing Google Cloud integration..."
if curl -f "http://localhost:8093/google-cloud/status" &> /dev/null; then
    echo "✅ Google Cloud integration is working"
else
    echo "⚠️ Google Cloud integration test failed"
fi

echo ""
echo "🎉 OMNI Singularity with Google Cloud is now running!"
echo ""
echo "🌐 Access Points:"
echo "   🧠 Main Interface:    http://localhost:8093"
echo "   📊 Dashboard:         http://localhost:8081"
echo "   🔌 API Gateway:       http://localhost:8082"
echo "   📈 Grafana:           http://localhost:3000"
echo "   📊 Prometheus:        http://localhost:9090"
echo "   ☁️ Google Cloud:      Integrated with API key"
echo ""
echo "🎯 Quick Test Commands:"
echo "   Health:              curl http://localhost:8093/health"
echo "   Status:              curl http://localhost:8093/status"
echo "   BCI Status:          curl http://localhost:8093/bci/status"
echo "   Google Cloud:        curl http://localhost:8093/google-cloud/status"
echo ""
echo "🛑 To stop: docker-compose -f docker-compose.omni.yml down"
echo ""
echo "🚀 Welcome to OMNI Singularity v10.0 with Google Cloud!"