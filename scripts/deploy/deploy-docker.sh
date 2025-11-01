#!/bin/bash
#
# Deploy OMNI Platform using Docker Compose
# For local development and testing
#

set -e

echo "🐳 OMNI Platform - Docker Deployment"
echo "===================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose not installed"
    exit 1
fi

echo -e "${YELLOW}🛑 Step 1: Stopping existing containers${NC}"
docker-compose down || true

echo -e "${YELLOW}🏗️  Step 2: Building images${NC}"
docker-compose build --no-cache

echo -e "${YELLOW}🚀 Step 3: Starting services${NC}"
docker-compose up -d

echo -e "${YELLOW}⏳ Step 4: Waiting for services to be ready${NC}"
sleep 10

# Health checks
echo -e "${YELLOW}🔍 Step 5: Running health checks${NC}"

check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service is healthy${NC}"
            return 0
        fi
        echo "   Waiting for $service... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done

    echo -e "❌ $service failed to start"
    return 1
}

check_service "Backend" "http://localhost:8080/health"
check_service "Frontend" "http://localhost:8000"

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "📡 Service URLs:"
echo "   Frontend:  http://localhost:8000"
echo "   Dashboard: http://localhost:8000/omni-dashboard.html"
echo "   Backend:   http://localhost:8080"
echo "   API Docs:  http://localhost:8080/docs"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
