# TIER 2 Infrastructure Setup

## Overview
This document outlines the GCP infrastructure needed for TIER 2 features.

## 1. Redis (Memorystore)

### Option A: Cloud Memorystore (Production)
```bash
# Create Redis instance
gcloud redis instances create omni-redis \
    --size=1 \
    --region=europe-west1 \
    --redis-version=redis_7_0 \
    --tier=basic

# Get connection info
gcloud redis instances describe omni-redis \
    --region=europe-west1 \
    --format="get(host,port)"
```

Connection string: `redis://{HOST}:{PORT}`

### Option B: Cloud Run Redis (Serverless)
Use Redis Labs or Upstash serverless Redis for Cloud Run compatibility:
```bash
# Create Upstash Redis via console or CLI
# Get connection URL (format: rediss://default:password@host:port)
```

### Environment Variable
```bash
REDIS_URL=redis://10.x.x.x:6379  # Memorystore internal IP
# OR
REDIS_URL=rediss://default:password@upstash-host:6379  # Upstash
```

## 2. Secret Manager

### Create Secrets
```bash
# API Gateway Keys (JSON array)
echo '["prod-key-omni-2025", "dev-key-test-2025"]' | \
gcloud secrets create api-gateway-keys \
    --data-file=- \
    --replication-policy=automatic

# Redis URL
echo 'redis://10.x.x.x:6379' | \
gcloud secrets create redis-url \
    --data-file=- \
    --replication-policy=automatic

# Sentry DSN (if using Sentry)
echo 'https://your-sentry-dsn@sentry.io/project' | \
gcloud secrets create sentry-dsn \
    --data-file=- \
    --replication-policy=automatic
```

### Grant Access to Cloud Run Service Account
```bash
# Get service account
gcloud run services describe ai-gateway \
    --region=europe-west1 \
    --format="value(spec.template.spec.serviceAccountName)"

# Grant access (replace SERVICE_ACCOUNT)
gcloud secrets add-iam-policy-binding api-gateway-keys \
    --member="serviceAccount:661612368188-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding redis-url \
    --member="serviceAccount:661612368188-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding sentry-dsn \
    --member="serviceAccount:661612368188-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Enable Secret Manager in Gateway
Update gateway environment:
```bash
gcloud run services update ai-gateway \
    --region=europe-west1 \
    --set-env-vars="SECRET_MANAGER_ENABLED=true,GCP_PROJECT_ID=omni-platform-prod-2025"
```

## 3. Distributed Tracing (Jaeger)

### Option A: Cloud Run Jaeger
```bash
# Deploy Jaeger all-in-one to Cloud Run
gcloud run deploy jaeger \
    --image=jaegertracing/all-in-one:latest \
    --region=europe-west1 \
    --port=16686 \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1

# Get Jaeger URL
gcloud run services describe jaeger \
    --region=europe-west1 \
    --format="value(status.url)"
```

Jaeger collector endpoint: `http://jaeger-url:14268/api/traces`

### Option B: Cloud Trace (Managed)
Use Google Cloud Trace instead of Jaeger:
```python
# Update gateway/app/tracing.py to use Cloud Trace exporter
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
```

### Environment Variables
```bash
# For Jaeger
JAEGER_HOST=jaeger-661612368188.europe-west1.run.app
JAEGER_PORT=14268
ENABLE_TRACING=true

# For Cloud Trace
ENABLE_TRACING=true
# No host/port needed - uses Application Default Credentials
```

## 4. Cloud Monitoring Alerts

### Error Rate Alert
```bash
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="High Error Rate - Gateway" \
    --condition-display-name="Error rate > 5%" \
    --condition-threshold-value=0.05 \
    --condition-threshold-duration=300s \
    --condition-filter='
      resource.type="cloud_run_revision"
      AND resource.labels.service_name="ai-gateway"
      AND metric.type="run.googleapis.com/request_count"
      AND metric.labels.response_code_class="5xx"
    '
```

### Latency Alert
```bash
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="High Latency - Gateway" \
    --condition-display-name="P95 latency > 2s" \
    --condition-threshold-value=2000 \
    --condition-threshold-duration=300s \
    --condition-filter='
      resource.type="cloud_run_revision"
      AND resource.labels.service_name="ai-gateway"
      AND metric.type="run.googleapis.com/request_latencies"
    '
```

### Rate Limit Alert
```bash
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="Rate Limit Violations - Gateway" \
    --condition-display-name="Rate limit hits > 100/min" \
    --condition-threshold-value=100 \
    --condition-threshold-duration=60s \
    --condition-filter='
      resource.type="prometheus_target"
      AND metric.type="workload.googleapis.com/http_requests_total"
      AND metric.labels.status="429"
    '
```

### Business Metrics Alert
```bash
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="Revenue Tracking Alert" \
    --condition-display-name="Revenue dropped significantly" \
    --condition-threshold-value=1000 \
    --condition-threshold-duration=3600s \
    --condition-filter='
      resource.type="prometheus_target"
      AND metric.type="workload.googleapis.com/revenue_total"
    '
```

## 5. Deployment Sequence

1. **Create Redis** (Option A or B)
2. **Create Secrets** in Secret Manager
3. **Grant IAM permissions** to service account
4. **Deploy Jaeger** (optional, or use Cloud Trace)
5. **Update Gateway** with new env vars
6. **Deploy Gateway** with TIER 2 code
7. **Create Alert Policies** in Cloud Monitoring
8. **Test end-to-end**

## 6. Environment Variables Summary

### Gateway (with TIER 2)
```bash
ENVIRONMENT=production
UPSTREAM_URL=https://omni-ultra-backend-prod-661612368188.europe-west1.run.app
API_KEYS=["prod-key-omni-2025"]  # Will be loaded from Secret Manager if enabled
REDIS_URL=redis://10.x.x.x:6379
JAEGER_HOST=jaeger-host
JAEGER_PORT=14268
ENABLE_TRACING=true
GCP_PROJECT_ID=omni-platform-prod-2025
SECRET_MANAGER_ENABLED=true
SENTRY_DSN=  # Optional, loaded from Secret Manager
ENABLE_METRICS=true
```

## 7. Testing Commands

### Test Rate Limiting
```bash
# Should return 429 after 10 requests
for i in {1..15}; do
  curl -H "x-api-key: test-key-free-2025" \
    https://ai-gateway-url/api/health
done
```

### Check Metrics
```bash
curl https://ai-gateway-url/metrics | grep business_
```

### View Traces in Jaeger
Open: `https://jaeger-url:16686`
Search for: service="ai-gateway"

### View Secrets
```bash
gcloud secrets versions access latest --secret=api-gateway-keys
```

## 8. Cost Estimates

- **Redis Memorystore Basic (1GB)**: ~$35/month
- **Upstash Redis (Pay-as-you-go)**: ~$0.20/100K requests
- **Secret Manager**: $0.06 per 10K accesses (negligible)
- **Cloud Trace**: First 2.5M spans free, then $0.20/million
- **Jaeger on Cloud Run**: ~$10/month (512Mi, minimal traffic)
- **Cloud Monitoring Alerts**: Free up to 100 rules

**Total**: ~$45-60/month for TIER 2 infrastructure
