# Business Intelligence Deployment Guide

## Overview
Real-time BI analytics with WebSocket streaming for live dashboard updates.

## Architecture
- **RealtimeAnalyticsService**: In-memory metric aggregation with pub/sub pattern
- **WebSocket `/dashboard`**: Live streaming updates to connected clients
- **REST `/record`**: Record new metrics
- **REST `/metrics`**: Get current snapshot

## Endpoints

### WebSocket Dashboard
```
ws://localhost:8080/dashboard
```

**Protocol**:
1. Client connects → receives full metrics snapshot
2. Server sends updates whenever metrics change
3. Server sends keepalive ping every 30s
4. Client disconnects → unsubscribed automatically

**Message Format**:
```json
{
  "event": "snapshot",
  "data": {
    "api_calls": {"count": 42, "sum": 42.0, "metadata": []},
    "revenue": {"count": 10, "sum": 999.99, "metadata": [{"currency": "USD"}]}
  }
}
```

```json
{
  "event": "metric_update",
  "metric": "api_calls",
  "value": 1.0,
  "metadata": null
}
```

### REST Record Metric
```http
POST /record
Content-Type: application/json

{
  "metric": "revenue",
  "value": 49.99,
  "metadata": {"plan": "pro", "currency": "EUR"}
}
```

**Response**:
```json
{"status": "recorded"}
```

### REST Get Metrics
```http
GET /metrics
```

**Response**:
```json
{
  "api_calls": {"count": 142, "sum": 142.0, "metadata": []},
  "revenue": {"count": 25, "sum": 1249.75, "metadata": [...]}
}
```

## Client Example (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8080/dashboard');

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  if (msg.event === 'snapshot') {
    // Initial full state
    console.log('Metrics:', msg.data);
  } else if (msg.event === 'metric_update') {
    // Incremental update
    console.log(`${msg.metric} += ${msg.value}`);
  } else if (msg.event === 'keepalive') {
    console.log('Keepalive ping');
  }
};

ws.onerror = (err) => console.error('WebSocket error:', err);
ws.onclose = () => console.log('Disconnected');
```

## Python Client Example
```python
import asyncio
import websockets
import json

async def connect_dashboard():
    async with websockets.connect('ws://localhost:8080/dashboard') as ws:
        async for message in ws:
            data = json.loads(message)
            if data['event'] == 'snapshot':
                print('Full metrics:', data['data'])
            elif data['event'] == 'metric_update':
                print(f"{data['metric']}: +{data['value']}")

asyncio.run(connect_dashboard())
```

## Deployment Checklist
- [ ] Set `OMNI_ENCRYPTION_KEY` for security features
- [ ] Configure Redis for GDPR consent storage (optional)
- [ ] Configure MongoDB for GDPR export/erase (optional)
- [ ] Verify WebSocket support in reverse proxy (nginx: `proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade;`)
- [ ] Enable Prometheus scraping on `/metrics`
- [ ] Configure CSP header if needed (currently report-only)

## Testing
```bash
# Run BI tests
pytest backend/tests/test_bi_analytics.py -v

# Record a metric via REST
curl -X POST http://localhost:8080/record \
  -H "Content-Type: application/json" \
  -d '{"metric":"test","value":1.0}'

# Get metrics snapshot
curl http://localhost:8080/metrics

# Connect WebSocket (requires wscat or similar)
wscat -c ws://localhost:8080/dashboard
```

## Observability
- **Prometheus metrics**: `gdpr_consent_total`, `gdpr_export_total`, `gdpr_erase_total` track GDPR operations
- **CSP Report-Only**: Security headers include CSP in report-only mode for gradual rollout
- **PII Redaction**: Logs automatically redact emails and bearer tokens

## Production Notes
- In-memory metrics are ephemeral (restart = data loss); persist to TimescaleDB or Prometheus if durability needed
- WebSocket keepalive prevents idle connection drops through load balancers
- Subscriber cleanup happens on disconnect (context manager ensures unsubscribe)
- Concurrency safety: asyncio.Lock protects metrics dict during updates
