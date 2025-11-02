#!/bin/bash
# Test script for IIoT-Ollama integration
# Tests health checks and sends sample IoT data

set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"refined-graph-471712-n9"}
REGION=${REGION:-"europe-west1"}

echo "================================================"
echo "IIoT-Ollama Integration - Test Suite"
echo "================================================"
echo ""

# Get service URLs
echo "Fetching service URLs..."
IIOT_URL=$(gcloud run services describe iiot-ollama-processor \
  --region=${REGION} \
  --format='value(status.url)' 2>/dev/null || echo "")

OLLAMA_URL=$(gcloud run services describe ollama-ai-inference \
  --region=${REGION} \
  --format='value(status.url)' 2>/dev/null || echo "")

if [ -z "$IIOT_URL" ]; then
    echo "❌ IIoT Processing Service not deployed"
    exit 1
fi

if [ -z "$OLLAMA_URL" ]; then
    echo "⚠️  Ollama Service not deployed (optional for testing)"
fi

echo "✓ IIoT Service: ${IIOT_URL}"
echo "✓ Ollama Service: ${OLLAMA_URL}"
echo ""

# Test 1: Health check
echo "Test 1: Health Check"
echo "--------------------"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${IIOT_URL}/health" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)")

HEALTH_HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

if [ "$HEALTH_HTTP_CODE" = "200" ]; then
    echo "$HEALTH_BODY" | jq .
    echo ""
    echo "✓ Health check passed"
else
    echo "❌ Health check failed with code: $HEALTH_HTTP_CODE"
    echo "$HEALTH_BODY"
    exit 1
fi

echo ""

# Test 2: Direct analysis endpoint
echo "Test 2: Direct Analysis (bypassing Pub/Sub)"
echo "--------------------------------------------"
cat > /tmp/test_iot_data.json <<EOF
{
  "device_id": "test-sensor-001",
  "sensor_type": "vibration",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "measurements": {
    "vibration": 92,
    "temperature": 75,
    "pressure": 101.3,
    "humidity": 45
  }
}
EOF

echo "Sending IoT data for analysis..."
RESPONSE=$(curl -s -w "\n%{http_code}" "${IIOT_URL}/analyze" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d @/tmp/test_iot_data.json)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Direct analysis successful"
    echo ""
    echo "Response:"
    echo "$BODY" | jq .
else
    echo "❌ Direct analysis failed with code: $HTTP_CODE"
    echo "$BODY"
    exit 1
fi

echo ""

# Test 3: Pub/Sub message
echo "Test 3: Pub/Sub Message (end-to-end)"
echo "-------------------------------------"
echo "Publishing message to iot-data-topic..."

# Create a test message with high vibration (should trigger warning)
TEST_MESSAGE='{
  "device_id": "sensor-critical-001",
  "sensor_type": "vibration",
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
  "measurements": {
    "vibration": 95,
    "temperature": 85,
    "pressure": 102.5,
    "humidity": 60
  }
}'

gcloud pubsub topics publish iot-data-topic --message="${TEST_MESSAGE}"

echo "✓ Message published"
echo ""
echo "Waiting 10 seconds for processing..."
sleep 10

echo ""
echo "Checking recent logs for processing confirmation..."
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=iiot-ollama-processor" \
  --limit=5 \
  --format="table(timestamp,textPayload)" \
  --freshness=1m

echo ""

# Test 4: List subscriptions
echo "Test 4: Verify Pub/Sub Configuration"
echo "-------------------------------------"
echo "Subscriptions:"
gcloud pubsub subscriptions list --format="table(name,topic,pushConfig.pushEndpoint)" | grep iot

echo ""
echo "================================================"
echo "Test Suite Complete!"
echo "================================================"
echo ""
echo "Summary:"
echo "- IIoT Processing Service: ✓ Running"
echo "- Health Check: ✓ Passed"
echo "- Direct Analysis: ✓ Working"
echo "- Pub/Sub Integration: ✓ Configured"
echo ""
echo "To monitor ongoing activity:"
echo "  gcloud logging tail 'resource.type=cloud_run_revision AND resource.labels.service_name=iiot-ollama-processor'"
echo ""
