# 📊 Grafana Monitoring Setup Guide

**Pozdravljen!** This guide will help you set up comprehensive monitoring for your Omni Enterprise Ultra Max Platform with Grafana, Prometheus, and Redis metrics.

## 🎯 Overview

This monitoring solution provides:

1. **Cache Monitoring** - Redis cache hit rates, memory usage, connection status
2. **FastAPI Application Monitoring** - Endpoint latency, request rates, error rates
3. **Business Metrics** - ML predictions, revenue tracking, user engagement
4. **Alerting** - Automated alerts for low cache hit rate, high latency, errors, and service availability

## 📦 What's Included

### Dashboards

- `grafana-cache-monitoring.json` - Redis cache performance and metrics
- `grafana-fastapi-monitoring.json` - API performance and endpoint analytics
- `grafana-business-metrics.json` - Business KPIs and ML model performance
- `grafana-ai-overview.json` - High-level AI metrics overview

### Alerts

- `monitoring/prometheus-alerts.yml` - Comprehensive alert rules for all components

### Metrics Endpoints

- Gateway: `http://localhost:8081/metrics`
- Backend: `http://localhost:8080/metrics`

## 🚀 Quick Start

### Option 1: Local Setup with Docker Compose

Create a `docker-compose.monitoring.yml` file (see below), then:

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access services
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# Gateway: http://localhost:8081/metrics
# Backend: http://localhost:8080/metrics
```

### Option 2: Existing Prometheus/Grafana

1. **Configure Prometheus** to scrape metrics from your services
2. **Import Grafana dashboards** from the `dashboards/` directory
3. **Configure alerts** using `monitoring/prometheus-alerts.yml`

## 📋 Prerequisites

- Docker and Docker Compose (for local setup)
- Or existing Prometheus + Grafana infrastructure
- Redis instance (for cache metrics)
- FastAPI services running (gateway + backend)

## 🔧 Detailed Setup

### Step 1: Configure Prometheus

Create or update your `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

# Load alert rules
rule_files:
  - "alerts/*.yml"

# Scrape configurations
scrape_configs:
  # Gateway service
  - job_name: 'gateway'
    static_configs:
      - targets: ['gateway:8081']  # or 'localhost:8081' for local
    metrics_path: '/metrics'
    scrape_interval: 30s

  # Backend service
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8080']  # or 'localhost:8080' for local
    metrics_path: '/metrics'
    scrape_interval: 30s

  # Redis exporter (optional, for detailed Redis metrics)
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s
```

### Step 2: Start Services with Metrics Enabled

Ensure your services have metrics enabled:

**Gateway (.env or environment):**
```bash
ENABLE_METRICS=true
REDIS_URL=redis://redis:6379
```

**Backend (.env or environment):**
```bash
# Metrics are enabled by default
```

### Step 3: Import Grafana Dashboards

1. Open Grafana (http://localhost:3000)
2. Login with admin credentials (default: admin/admin)
3. Go to **Dashboards → Import**
4. Upload each JSON file from `dashboards/` directory:
   - `grafana-cache-monitoring.json`
   - `grafana-fastapi-monitoring.json`
   - `grafana-business-metrics.json`
   - `grafana-ai-overview.json`
5. Select your Prometheus data source
6. Click **Import**

### Step 4: Configure Alerting

1. Copy `monitoring/prometheus-alerts.yml` to your Prometheus alerts directory
2. Reload Prometheus configuration:
   ```bash
   curl -X POST http://localhost:9090/-/reload
   ```
3. Verify alerts are loaded: http://localhost:9090/alerts

### Step 5: Set Up Alert Notifications (Optional)

Configure Grafana alert notifications:

1. Go to **Alerting → Contact points**
2. Add notification channels (Email, Slack, PagerDuty, etc.)
3. Create notification policies for different severity levels

## 📊 Dashboard Overview

### 1. Cache Monitoring Dashboard

**Key Metrics:**
- Cache hit rate (overall and by cache type: Redis/memory)
- Cache operations rate (hits/misses per second)
- Cache size (number of items)
- Redis memory usage and peak
- Redis connection status
- Request latency: cached vs uncached

**Use Cases:**
- Monitor cache effectiveness
- Identify cache performance issues
- Track Redis resource usage
- Optimize cache TTL settings

### 2. FastAPI Application Monitoring

**Key Metrics:**
- Request rate (requests/second)
- Error rate (4xx, 5xx)
- Latency percentiles (p50, p95, p99)
- Top slowest endpoints
- Request rate by endpoint
- Status code distribution

**Use Cases:**
- Identify slow endpoints
- Track error patterns
- Monitor API health
- Capacity planning

### 3. Business & ML Metrics

**Key Metrics:**
- Total revenue (by tier, by feature)
- Active users (by tier)
- ML model inference rate and accuracy
- ML prediction latency
- Feature usage statistics
- API calls by tenant
- Business error tracking

**Use Cases:**
- Track business KPIs
- Monitor ML model performance
- Identify revenue trends
- User engagement analysis

## 🚨 Alert Rules

### Cache Alerts

| Alert | Threshold | Severity | Description |
|-------|-----------|----------|-------------|
| LowCacheHitRate | < 50% for 10m | Warning | Cache hit rate below optimal |
| CriticallyLowCacheHitRate | < 20% for 5m | Critical | Cache nearly ineffective |
| RedisDown | Connection lost for 1m | Critical | Redis unavailable |
| RedisHighMemoryUsage | > 90% for 5m | Warning | Redis memory pressure |

### API Alerts

| Alert | Threshold | Severity | Description |
|-------|-----------|----------|-------------|
| HighErrorRate | > 5% for 5m | Critical | High server error rate |
| ElevatedErrorRate | > 1% for 10m | Warning | Elevated error rate |
| HighLatency | p95 > 5s for 10m | Warning | High response latency |
| CriticalLatency | p95 > 10s for 5m | Critical | Critical response latency |
| HighRequestRate | > 1000 req/s for 10m | Warning | Unusual traffic spike |

### Availability Alerts

| Alert | Threshold | Severity | Description |
|-------|-----------|----------|-------------|
| ServiceDown | No response for 2m | Critical | Service unavailable |
| LowRequestVolume | < 0.1 req/s for 15m | Warning | Unusually low traffic |

### ML Alerts

| Alert | Threshold | Severity | Description |
|-------|-----------|----------|-------------|
| MLModelHighLatency | p95 > 2s for 10m | Warning | Slow model predictions |
| MLModelLowAccuracy | < 70% for 15m | Warning | Model accuracy degraded |
| MLModelHighFailureRate | > 10% for 5m | Critical | High model error rate |

### Business Alerts

| Alert | Threshold | Severity | Description |
|-------|-----------|----------|-------------|
| LowUserEngagement | Avg < 30 for 30m | Warning | Poor user engagement |
| HighBusinessErrorRate | > 0.1 errors/s for 5m | Critical | Business logic failures |
| RevenueDropDetected | -30% vs 1h ago for 15m | Warning | Significant revenue drop |

## 🔍 Monitoring Best Practices

### 1. Set Appropriate Baselines

- Review metrics over 7 days to establish normal patterns
- Adjust alert thresholds based on your traffic patterns
- Consider different thresholds for different times (peak vs off-peak)

### 2. Cache Optimization

- **Target hit rate**: > 80% for production workloads
- Monitor cache size to prevent memory issues
- Adjust TTL based on data freshness requirements
- Use cache warming for predictable access patterns

### 3. Performance Monitoring

- Track p95/p99 latency, not just averages
- Set up latency budgets per endpoint
- Monitor error rates by endpoint to identify problem areas
- Use slow query logs for debugging

### 4. Capacity Planning

- Monitor request rate trends
- Track resource utilization (CPU, memory, connections)
- Set up alerts before hitting capacity limits
- Plan scaling based on growth trends

### 5. Alert Fatigue Prevention

- Start with conservative thresholds
- Use appropriate "for" durations to avoid flapping
- Route different severities to different channels
- Regularly review and tune alert rules

## 🛠️ Troubleshooting

### No Metrics Appearing

**Check Prometheus targets:**
```bash
curl http://localhost:9090/api/v1/targets
```

**Verify metrics endpoints:**
```bash
# Gateway metrics
curl http://localhost:8081/metrics

# Backend metrics  
curl http://localhost:8080/metrics
```

**Check service logs:**
```bash
# Gateway
docker-compose logs gateway

# Backend
docker-compose logs backend
```

### Low Cache Hit Rate

1. Check if Redis is connected: Look at `redis_connected` metric
2. Verify cache TTL settings are appropriate
3. Review cache key generation logic
4. Check if cache is being bypassed for certain requests
5. Monitor cache memory usage

### High Latency

1. Identify slow endpoints in "Top 10 Slowest Endpoints" panel
2. Check if cache is working (compare cached vs uncached latency)
3. Review database query performance
4. Check external API call latencies
5. Look for resource contention (CPU, memory)

### Alerts Not Firing

1. Verify alert rules are loaded in Prometheus
2. Check alert expressions are valid
3. Confirm data is available for alert queries
4. Review alert state in Prometheus UI
5. Check Alertmanager configuration

## 📚 Metrics Reference

### Cache Metrics

```
# Cache operations
cache_hits_total{cache_type="redis|memory"}     # Counter
cache_misses_total                              # Counter
cache_size_items{cache_type="redis|memory"}     # Gauge

# Redis metrics
redis_connected                                  # Gauge (0/1)
redis_memory_used_bytes                         # Gauge
redis_memory_peak_bytes                         # Gauge
redis_keys_total                                # Gauge
redis_connected_clients                         # Gauge
```

### HTTP Metrics

```
# Request metrics
http_requests_total{method,path,status}         # Counter
http_request_duration_seconds{method,path,status} # Histogram

# Error metrics
http_errors_total{method,path}                  # Counter
```

### Business Metrics

```
# Revenue
business_revenue_total_cents{tier,feature}      # Counter

# Users
business_active_users{tier}                     # Gauge
business_user_engagement_score{tier}            # Gauge

# ML Models
ml_model_inference_total{model_name,status}     # Counter
ml_model_accuracy_percent{model_name,model_version} # Gauge
ml_model_prediction_seconds{model_name}         # Histogram

# API Usage
api_calls_tenant_total{tenant_id,endpoint,tier} # Counter
api_data_processed_bytes_total{direction,endpoint} # Counter

# Features & Errors
feature_usage_total{feature_name,tier}          # Counter
business_errors_total{error_type,severity}      # Counter
```

## 🔗 Useful PromQL Queries

### Cache Performance

```promql
# Cache hit rate
rate(cache_hits_total[5m]) / 
(rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) * 100

# Cache operations per second
rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])

# Redis memory usage percentage
(redis_memory_used_bytes / redis_memory_peak_bytes) * 100
```

### API Performance

```promql
# Request rate
sum(rate(http_requests_total[5m]))

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / 
sum(rate(http_requests_total[5m])) * 100

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Top 10 endpoints by traffic
topk(10, sum by (path) (rate(http_requests_total[5m])))
```

### Business Metrics

```promql
# Revenue per hour
sum(increase(business_revenue_total_cents[1h])) / 100

# Active users by tier
sum by (tier) (business_active_users)

# ML inference rate
sum(rate(ml_model_inference_total[5m]))

# Model success rate
sum(rate(ml_model_inference_total{status="success"}[5m])) /
sum(rate(ml_model_inference_total[5m])) * 100
```

## 🎓 Next Steps

1. **Customize dashboards** - Adjust panels and queries for your specific needs
2. **Set up alerting** - Configure notification channels and policies
3. **Create runbooks** - Document response procedures for each alert
4. **Implement SLOs** - Define service level objectives based on metrics
5. **Regular reviews** - Weekly/monthly reviews of trends and patterns

## 📞 Support

For questions or issues:
1. Check the [main README](../README.md)
2. Review service logs
3. Verify Prometheus targets are healthy
4. Check Grafana data source configuration

## 🔄 Maintenance

- **Weekly**: Review alert frequencies, adjust thresholds
- **Monthly**: Update dashboards based on new features
- **Quarterly**: Review capacity and scaling needs
- **Annually**: Audit metrics collection and storage costs

---

**Happy Monitoring! 🎉**

For more information, see:
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Project README](../README.md)
