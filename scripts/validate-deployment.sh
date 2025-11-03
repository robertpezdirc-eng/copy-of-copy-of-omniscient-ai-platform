#!/bin/bash

# Production Deployment Validation Script
# Preverja da so vsi features pravilno deployi-ani in delujejo

set -e

echo "🚀 Omni Platform - Production Deployment Validation"
echo "=================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8080}"
TENANT_A_KEY="${TENANT_A_KEY:-demo-key-tenant-a}"
TENANT_B_KEY="${TENANT_B_KEY:-demo-key-tenant-b}"

PASSED=0
FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}!${NC} $1"
}

test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    local headers=$4
    
    echo -n "Testing $name... "
    
    if [ -n "$headers" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -H "$headers" "$url")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    fi
    
    if [ "$response" -eq "$expected_code" ]; then
        pass "$name (HTTP $response)"
    else
        fail "$name (Expected $expected_code, got $response)"
    fi
}

echo "📊 1. Testing Core Endpoints"
echo "----------------------------"

# Health check
test_endpoint "Health endpoint" "$BACKEND_URL/health"

# API docs
test_endpoint "API documentation" "$BACKEND_URL/docs"

# Metrics endpoint
test_endpoint "Prometheus metrics" "$BACKEND_URL/metrics"

echo ""
echo "💾 2. Testing Caching"
echo "---------------------"

# Cache stats endpoint
test_endpoint "Cache stats endpoint" "$BACKEND_URL/api/v1/cache/stats"

# Test cache hit (make 2 requests, second should be faster)
echo -n "Testing cache performance... "
START1=$(date +%s%N)
curl -s "$BACKEND_URL/api/intelligence/predictions/revenue" > /dev/null
END1=$(date +%s%N)
TIME1=$((($END1 - $START1) / 1000000))

sleep 1

START2=$(date +%s%N)
curl -s "$BACKEND_URL/api/intelligence/predictions/revenue" > /dev/null
END2=$(date +%s%N)
TIME2=$((($END2 - $START2) / 1000000))

if [ $TIME2 -lt $((TIME1 / 2)) ]; then
    pass "Cache hit detected (${TIME1}ms -> ${TIME2}ms)"
else
    warn "Cache may not be working optimally (${TIME1}ms -> ${TIME2}ms)"
fi

echo ""
echo "🔐 3. Testing Multi-Tenancy"
echo "---------------------------"

# Test tenant A
test_endpoint "Tenant A usage endpoint" "$BACKEND_URL/api/v1/tenant/usage" 200 "Authorization: Bearer $TENANT_A_KEY"

# Test tenant B
test_endpoint "Tenant B usage endpoint" "$BACKEND_URL/api/v1/tenant/usage" 200 "Authorization: Bearer $TENANT_B_KEY"

# Test without auth (should fail)
test_endpoint "Unauthorized access (expected)" "$BACKEND_URL/api/v1/tenant/usage" 401

# Test tenant isolation
echo -n "Testing tenant isolation... "
RESPONSE_A=$(curl -s -H "Authorization: Bearer $TENANT_A_KEY" "$BACKEND_URL/api/v1/tenant/usage" | grep -o '"tenant_id":"[^"]*"' | cut -d'"' -f4)
RESPONSE_B=$(curl -s -H "Authorization: Bearer $TENANT_B_KEY" "$BACKEND_URL/api/v1/tenant/usage" | grep -o '"tenant_id":"[^"]*"' | cut -d'"' -f4)

if [ "$RESPONSE_A" != "$RESPONSE_B" ]; then
    pass "Tenants are isolated (A=$RESPONSE_A, B=$RESPONSE_B)"
else
    fail "Tenant isolation not working properly"
fi

echo ""
echo "📈 4. Testing Observability"
echo "---------------------------"

# Check Prometheus metrics format
echo -n "Validating Prometheus metrics format... "
METRICS=$(curl -s "$BACKEND_URL/metrics")
if echo "$METRICS" | grep -q "# HELP"; then
    pass "Metrics in Prometheus format"
else
    fail "Metrics not in Prometheus format"
fi

# Check for key metrics
echo -n "Checking cache hit rate metric... "
if echo "$METRICS" | grep -q "cache_hit_rate"; then
    pass "Cache hit rate metric exists"
else
    fail "Cache hit rate metric missing"
fi

echo -n "Checking request latency metric... "
if echo "$METRICS" | grep -q "http_request_duration"; then
    pass "Request latency metric exists"
else
    fail "Request latency metric missing"
fi

echo ""
echo "🧪 5. Testing Cached Endpoints"
echo "-------------------------------"

# Test all 10 cached endpoints
test_endpoint "Revenue predictions" "$BACKEND_URL/api/intelligence/predictions/revenue"
test_endpoint "Business insights" "$BACKEND_URL/api/intelligence/insights/business"
test_endpoint "Anomaly detection" "$BACKEND_URL/api/intelligence/anomaly-detection"
test_endpoint "Text analysis" "$BACKEND_URL/api/ai/analyze/text" 405 # POST endpoint, GET returns 405
test_endpoint "Analytics dashboard" "$BACKEND_URL/api/analytics/dashboard"
test_endpoint "Analytics metrics" "$BACKEND_URL/api/analytics/metrics"
test_endpoint "Dashboard types" "$BACKEND_URL/api/v1/dashboards/types"
test_endpoint "AI models list" "$BACKEND_URL/api/advanced-ai/models"

echo ""
echo "⚡ 6. Performance Check"
echo "------------------------"

# Test response times
echo -n "Measuring average response time... "
TOTAL=0
SAMPLES=5
for i in $(seq 1 $SAMPLES); do
    START=$(date +%s%N)
    curl -s "$BACKEND_URL/api/intelligence/predictions/revenue" > /dev/null
    END=$(date +%s%N)
    TIME=$((($END - $START) / 1000000))
    TOTAL=$((TOTAL + TIME))
done
AVG=$((TOTAL / SAMPLES))

if [ $AVG -lt 500 ]; then
    pass "Average response time: ${AVG}ms (target: <500ms)"
elif [ $AVG -lt 1000 ]; then
    warn "Average response time: ${AVG}ms (acceptable, target: <500ms)"
else
    fail "Average response time: ${AVG}ms (too slow, target: <500ms)"
fi

echo ""
echo "=================================================="
echo "📊 Validation Summary"
echo "=================================================="
echo ""
echo -e "${GREEN}Passed:${NC} $PASSED tests"
echo -e "${RED}Failed:${NC} $FAILED tests"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Platform is production-ready.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Review output above.${NC}"
    exit 1
fi
