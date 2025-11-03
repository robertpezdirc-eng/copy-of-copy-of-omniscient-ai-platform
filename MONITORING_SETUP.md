# Monitoring and Observability Setup Guide

## Overview

Omni Enterprise Ultra Max uses a comprehensive monitoring stack:
- **Prometheus** - Metrics collection and storage
- **Grafana** - Metrics visualization and dashboards
- **OpenTelemetry** - Distributed tracing
- **Jaeger** - Trace visualization
- **Sentry** - Error tracking (Gateway)

## Architecture

```
┌─────────────────┐
│  Applications   │ (Backend + Gateway)
│                 │
│  Prometheus     │ ← Scrapes /metrics endpoints
│  Exporters      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Prometheus    │ ← Stores metrics
│    Server       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Grafana      │ ← Visualizes metrics
│   Dashboards    │
└─────────────────┘

┌─────────────────┐
│  Applications   │
│                 │
│  OpenTelemetry  │ ← Traces requests
│  Instrumentation│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Jaeger      │ ← Stores & visualizes traces
└─────────────────┘
```

## Quick Start

### 1. Enable Tracing

Set environment variables:

```bash
# Backend
export ENABLE_TRACING=1
export OTEL_SERVICE_NAME=omni-backend
export JAEGER_HOST=localhost
export JAEGER_PORT=6831

# Gateway
export ENABLE_TRACING=true
export JAEGER_HOST=localhost
export JAEGER_PORT=6831
```

### 2. Run Jaeger (Local Development)

```bash
docker run -d --name jaeger \
  -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
  -p 5775:5775/udp \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 14250:14250 \
  -p 9411:9411 \
  jaegertracing/all-in-one:latest
```

Access Jaeger UI: http://localhost:16686

### 3. Run Prometheus

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'omni-backend'
    static_configs:
      - targets: ['backend:8080']
    metrics_path: '/metrics'
  
  - job_name: 'omni-gateway'
    static_configs:
      - targets: ['gateway:8080']
    metrics_path: '/metrics'
```

Run Prometheus:

```bash
docker run -d --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

Access Prometheus: http://localhost:9090

### 4. Run Grafana

```bash
docker run -d --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

Access Grafana: http://localhost:3000 (admin/admin)

### 5. Import Dashboards

1. Login to Grafana
2. Go to Configuration → Data Sources
3. Add Prometheus data source (http://prometheus:9090)
4. Go to Dashboards → Import
5. Upload JSON files from `monitoring/grafana-dashboards/`:
   - `business-metrics.json`
   - `system-performance.json`
   - `tenant-saas-metrics.json`

## Available Metrics

### Backend Metrics (`/metrics`)

**HTTP Metrics:**
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_in_progress` - Current active requests

**Business Metrics:**
- `payment_completed_total` - Completed payments
- `subscription_mrr` - Monthly recurring revenue
- `customer_ltv` - Customer lifetime value
- `conversion_completed_total` - Successful conversions
- `customer_churned_total` - Churned customers

**System Metrics:**
- `active_connections` - Active connections
- `db_connection_pool_active` - Active DB connections
- `db_connection_pool_idle` - Idle DB connections
- `task_queue_depth` - Background task queue size

**Cache Metrics:**
- `redis_keyspace_hits_total` - Cache hits
- `redis_keyspace_misses_total` - Cache misses

**Tenant Metrics:**
- `tenant_active` - Active tenants by tier
- `tenant_created_total` - New tenants
- `tenant_converted_total` - Trial to paid conversions
- `tenant_usage_percentage` - Resource usage percentage

### Gateway Metrics (`/metrics`)

**Request Metrics:**
- `gateway_requests_total` - Total requests through gateway
- `gateway_request_duration_seconds` - Request latency
- `gateway_errors_total` - Error count by type

**Rate Limiting:**
- `rate_limit_exceeded_total` - Rate limit violations
- `rate_limit_remaining` - Remaining quota

**Upstream:**
- `upstream_request_duration_seconds` - Backend latency
- `upstream_errors_total` - Backend errors

## Grafana Dashboards

### 1. Business Metrics Dashboard

Tracks revenue, users, conversions, and key business KPIs.

**Panels:**
- Revenue (24h rolling)
- Active Users
- API Calls per Second
- Conversion Rate
- Monthly Recurring Revenue (MRR)
- Customer Lifetime Value
- Churn Rate

**Use Cases:**
- Executive reporting
- Business performance monitoring
- Revenue tracking

### 2. System Performance & SLA Dashboard

Monitors system health and SLA compliance.

**Panels:**
- Request Latency (p50, p95, p99)
- Error Rate
- Uptime (SLA: 99.9%)
- Request Throughput
- Cache Hit Rate
- CPU Usage
- Memory Usage
- Database Connection Pool

**Use Cases:**
- Performance troubleshooting
- SLA monitoring
- Capacity planning

### 3. Multi-Tenant SaaS Metrics Dashboard

Tracks tenant-specific metrics and usage.

**Panels:**
- Active Tenants by Tier
- Total MRR by Tier
- Tenant Growth (New vs Churned)
- API Usage by Tenant (Top 10)
- Storage Usage by Tenant
- Tenants Approaching Limits
- Conversion Rate (Trial to Paid)
- Average Revenue Per Tenant

**Use Cases:**
- Tenant health monitoring
- Usage-based billing
- Capacity planning per tenant

## Alerting Rules

### High Priority Alerts

Create these alerts in Prometheus:

```yaml
groups:
  - name: omni_critical
    interval: 1m
    rules:
      # SLA Violation
      - alert: UptimeBelowSLA
        expr: |
          (1 - (sum(rate(http_requests_total{status="500"}[5m])) 
          / sum(rate(http_requests_total[5m])))) * 100 < 99.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Uptime below 99.9% SLA"
      
      # High Error Rate
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) 
          / sum(rate(http_requests_total[5m])) * 100 > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate above 5%"
      
      # High Latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, 
          rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency above 1 second"
      
      # Memory Pressure
      - alert: HighMemoryUsage
        expr: |
          (container_memory_usage_bytes 
          / container_memory_limit_bytes) * 100 > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memory usage above 90%"
```

### Business Alerts

```yaml
  - name: omni_business
    interval: 5m
    rules:
      # High Churn Rate
      - alert: HighChurnRate
        expr: |
          (sum(rate(customer_churned_total[30d])) 
          / sum(customer_total)) * 100 > 10
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Churn rate above 10%"
      
      # Low Conversion Rate
      - alert: LowConversionRate
        expr: |
          (sum(rate(conversion_completed_total[1d])) 
          / sum(rate(http_requests_total[1d]))) * 100 < 1
        for: 6h
        labels:
          severity: warning
        annotations:
          summary: "Conversion rate below 1%"
```

## Production Deployment

### Google Cloud Run

Metrics and traces are automatically collected when deployed to Cloud Run.

**Enable Cloud Trace:**
```bash
gcloud run services update omni-backend \
  --set-env-vars ENABLE_TRACING=1,OTEL_SERVICE_NAME=omni-backend
```

**Enable Cloud Monitoring:**
Metrics at `/metrics` are automatically scraped by Google Cloud Monitoring.

### Kubernetes (GKE)

1. **Install Prometheus Operator:**
```bash
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml
```

2. **Deploy ServiceMonitor:**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: omni-backend
spec:
  selector:
    matchLabels:
      app: omni-backend
  endpoints:
    - port: metrics
      path: /metrics
```

3. **Deploy Jaeger:**
```bash
kubectl apply -f https://github.com/jaegertracing/jaeger-operator/releases/latest/download/jaeger-operator.yaml
```

## Monitoring Best Practices

### 1. Golden Signals

Monitor these four key metrics (Google SRE methodology):

- **Latency** - Request duration (p50, p95, p99)
- **Traffic** - Requests per second
- **Errors** - Error rate percentage
- **Saturation** - Resource usage (CPU, memory, connections)

### 2. SLIs and SLOs

**Service Level Indicators (SLIs):**
- Request success rate
- Request latency (p95)
- System availability

**Service Level Objectives (SLOs):**
- 99.9% uptime (43.2 min downtime/month)
- P95 latency < 500ms
- Error rate < 0.1%

### 3. Alert Fatigue Prevention

- Set appropriate thresholds
- Use `for` duration to avoid flapping
- Group related alerts
- Use severity levels (critical, warning, info)

### 4. Dashboard Design

- Group related metrics
- Use appropriate visualization types
- Include time ranges and refresh intervals
- Add annotations for deploys and incidents

## Troubleshooting

### Metrics Not Appearing

1. Check `/metrics` endpoint is accessible:
   ```bash
   curl http://localhost:8080/metrics
   ```

2. Verify Prometheus is scraping:
   ```
   Check Prometheus UI → Status → Targets
   ```

3. Check application logs for errors

### Traces Not Appearing

1. Verify Jaeger is running:
   ```bash
   curl http://localhost:16686
   ```

2. Check `ENABLE_TRACING` environment variable

3. Verify Jaeger host/port configuration

4. Check application logs for tracing errors

### High Memory Usage

1. Check Redis cache size
2. Review database connection pool
3. Check for memory leaks
4. Review background task queue

## Advanced Features

### Custom Metrics

Add custom business metrics:

```python
from prometheus_client import Counter, Histogram

# Define metric
custom_metric = Counter(
    'custom_events_total',
    'Description of custom event',
    ['label1', 'label2']
)

# Increment metric
custom_metric.labels(label1='value1', label2='value2').inc()
```

### Distributed Tracing Context

Propagate trace context across services:

```python
from opentelemetry.propagate import inject

headers = {}
inject(headers)  # Add trace context to headers

# Include headers in downstream requests
response = httpx.get(url, headers=headers)
```

## Support

For monitoring issues:
1. Check service logs
2. Review Grafana dashboards
3. Check Prometheus targets
4. Verify Jaeger traces
5. Contact DevOps team

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
