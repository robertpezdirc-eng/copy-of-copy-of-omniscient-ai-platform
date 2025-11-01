#!/bin/bash
#
# Health check script for OMNI Platform
# Verifies all services are running correctly
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🏥 OMNI Platform - Health Check"
echo "==============================="
echo ""

# Function to check endpoint
check_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}

    printf "Checking %-20s " "$name..."
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✅ OK ($response)${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL ($response)${NC}"
        return 1
    fi
}

# Local Docker deployment
echo "🐳 Docker Services:"
if docker-compose ps | grep -q "Up"; then
    check_endpoint "Frontend" "http://localhost:8000"
    check_endpoint "Backend Health" "http://localhost:8080/health"
    check_endpoint "Backend API" "http://localhost:8080/api/modules"
else
    echo -e "${YELLOW}⚠️  Docker services not running${NC}"
fi

echo ""

# Cloud Run deployment
echo "☁️  Cloud Run Services:"
if command -v gcloud &> /dev/null; then
    FRONTEND_URL=$(gcloud run services describe omni-frontend --region europe-west1 --format 'value(status.url)' 2>/dev/null || echo "")
    BACKEND_URL=$(gcloud run services describe omni-backend --region europe-west1 --format 'value(status.url)' 2>/dev/null || echo "")
    
    if [ -n "$FRONTEND_URL" ]; then
        check_endpoint "Frontend" "$FRONTEND_URL"
    else
        echo -e "${YELLOW}⚠️  Frontend not deployed${NC}"
    fi
    
    if [ -n "$BACKEND_URL" ]; then
        check_endpoint "Backend Health" "$BACKEND_URL/health"
        check_endpoint "Backend API" "$BACKEND_URL/api/modules"
    else
        echo -e "${YELLOW}⚠️  Backend not deployed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  gcloud CLI not installed${NC}"
fi

echo ""

# Module pages
echo "📄 Module Pages:"
for module in sales customers finance; do
    if [ -f "frontend/modules/$module.html" ]; then
        echo -e "   $module.html ${GREEN}✅${NC}"
    else
        echo -e "   $module.html ${RED}❌${NC}"
    fi
done

echo ""
echo "📊 Summary complete!"
