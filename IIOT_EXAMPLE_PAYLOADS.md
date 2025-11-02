# Example IoT Data Payloads

This file contains example JSON payloads for testing the IIoT-Ollama integration.

## Normal Operation - Vibration Sensor

```json
{
  "device_id": "vibration-sensor-001",
  "sensor_type": "vibration",
  "timestamp": "2024-01-15T10:30:00Z",
  "measurements": {
    "vibration": 65.5,
    "temperature": 68.2,
    "pressure": 101.3,
    "humidity": 45.0
  }
}
```

## Warning Level - High Vibration

```json
{
  "device_id": "vibration-sensor-001",
  "sensor_type": "vibration",
  "timestamp": "2024-01-15T10:35:00Z",
  "measurements": {
    "vibration": 87.3,
    "temperature": 78.5,
    "pressure": 101.3,
    "humidity": 48.0
  }
}
```

## Critical Level - Machine Fault

```json
{
  "device_id": "vibration-sensor-001",
  "sensor_type": "vibration",
  "timestamp": "2024-01-15T10:40:00Z",
  "measurements": {
    "vibration": 95.8,
    "temperature": 89.7,
    "pressure": 103.2,
    "humidity": 55.0
  }
}
```

## Pressure Sensor - Normal

```json
{
  "device_id": "pressure-sensor-002",
  "sensor_type": "pressure",
  "timestamp": "2024-01-15T10:30:00Z",
  "measurements": {
    "pressure": 100.2,
    "temperature": 70.5,
    "flow_rate": 125.3
  }
}
```

## Temperature Sensor - Warning

```json
{
  "device_id": "temperature-sensor-003",
  "sensor_type": "temperature",
  "timestamp": "2024-01-15T10:30:00Z",
  "measurements": {
    "temperature": 82.5,
    "humidity": 68.0,
    "heat_index": 88.3
  }
}
```

## Multi-Sensor Device

```json
{
  "device_id": "multi-sensor-004",
  "sensor_type": "environmental",
  "timestamp": "2024-01-15T10:30:00Z",
  "measurements": {
    "temperature": 72.0,
    "humidity": 50.0,
    "pressure": 101.3,
    "co2": 450,
    "voc": 125,
    "pm2_5": 12.5,
    "pm10": 18.3
  }
}
```

## Batch Testing - Multiple Devices

For testing with multiple devices simultaneously:

```bash
# Device 1 - Normal
gcloud pubsub topics publish iot-data-topic --message='{"device_id":"sensor-001","sensor_type":"vibration","timestamp":"2024-01-15T10:30:00Z","measurements":{"vibration":65.5,"temperature":68.2}}'

# Device 2 - Warning
gcloud pubsub topics publish iot-data-topic --message='{"device_id":"sensor-002","sensor_type":"pressure","timestamp":"2024-01-15T10:30:05Z","measurements":{"pressure":96.5,"temperature":80.2}}'

# Device 3 - Critical
gcloud pubsub topics publish iot-data-topic --message='{"device_id":"sensor-003","sensor_type":"temperature","timestamp":"2024-01-15T10:30:10Z","measurements":{"temperature":92.5,"humidity":75.0}}'
```

## Using curl for Direct Testing

```bash
export SERVICE_URL=$(gcloud run services describe iiot-ollama-processor \
  --region=europe-west1 \
  --format='value(status.url)')

curl -X POST "${SERVICE_URL}/analyze" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test-sensor-001",
    "sensor_type": "vibration",
    "timestamp": "2024-01-15T10:30:00Z",
    "measurements": {
      "vibration": 92.0,
      "temperature": 85.0
    }
  }'
```

## Expected LLM Analysis Response

When a critical vibration reading is detected, the Ollama LLM should provide analysis similar to:

```json
{
  "device_id": "vibration-sensor-001",
  "sensor_type": "vibration",
  "timestamp": "2024-01-15T10:40:00Z",
  "original_data": { ... },
  "analysis": "Analysis of the IIoT sensor data:\n\n1. **Sensor Readings Analysis**:\n   - Vibration: 95.8% - CRITICAL level, significantly above normal operational range\n   - Temperature: 89.7°F - Elevated, concerning in combination with high vibration\n   - Pressure: 103.2 kPa - Slightly elevated\n\n2. **Anomalies Identified**:\n   - CRITICAL: Vibration levels at 95.8% indicate severe mechanical stress\n   - WARNING: Temperature elevation suggests potential bearing failure or insufficient lubrication\n   - Pattern suggests imminent equipment failure\n\n3. **Recommended Actions**:\n   - IMMEDIATE: Shut down equipment for inspection\n   - Check bearing condition and lubrication\n   - Inspect for misalignment or imbalance\n   - Schedule emergency maintenance\n   - Do not restart until issue is resolved\n\n4. **Health Assessment**: CRITICAL - Immediate action required",
  "model": "llama3",
  "processed_at": "2024-01-15T10:40:05.123Z"
}
```

## Data Generation Script

Use the included generator for realistic test data:

```bash
# Generate 50 messages with mixed status
python3 iot_data_generator.py \
  --project refined-graph-471712-n9 \
  --count 50 \
  --interval 1 \
  --status mixed

# Generate only critical alerts
python3 iot_data_generator.py \
  --project refined-graph-471712-n9 \
  --count 10 \
  --interval 2 \
  --status critical
```
