# Multi-Region Deployment Configuration

This configuration enables global deployment across multiple regions with CDN and geo-routing.

## Architecture

```
                     [Global Load Balancer]
                              |
        +---------------------+---------------------+
        |                     |                     |
   [US Region]          [EU Region]           [ASIA Region]
   us-central1          europe-west1          asia-southeast1
        |                     |                     |
   Cloud Run            Cloud Run             Cloud Run
   Backend              Backend               Backend
        |                     |                     |
   Regional DB          Regional DB           Regional DB
```

## Regions

### 1. US Region (Primary)
- **Location:** us-central1 (Iowa)
- **Services:**
  - Cloud Run Backend
  - Cloud SQL (PostgreSQL)
  - Redis (Memorystore)
- **Capacity:** 1000 req/s

### 2. EU Region
- **Location:** europe-west1 (Belgium)
- **Services:**
  - Cloud Run Backend
  - Cloud SQL (PostgreSQL replica)
  - Redis (Memorystore)
- **Capacity:** 500 req/s

### 3. ASIA Region
- **Location:** asia-southeast1 (Singapore)
- **Services:**
  - Cloud Run Backend
  - Cloud SQL (PostgreSQL replica)
  - Redis (Memorystore)
- **Capacity:** 500 req/s

## Deployment Commands

### Deploy to US Region
```bash
gcloud run deploy omni-backend-us \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars REGION=us,PRIMARY_DB=us-central1 \
  --min-instances 3 \
  --max-instances 100
```

### Deploy to EU Region
```bash
gcloud run deploy omni-backend-eu \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars REGION=eu,PRIMARY_DB=us-central1 \
  --min-instances 2 \
  --max-instances 50
```

### Deploy to ASIA Region
```bash
gcloud run deploy omni-backend-asia \
  --source . \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --set-env-vars REGION=asia,PRIMARY_DB=us-central1 \
  --min-instances 2 \
  --max-instances 50
```

## Global Load Balancer Configuration

### Create Backend Services
```bash
# US Backend
gcloud compute backend-services create omni-backend-us \
  --global \
  --load-balancing-scheme=EXTERNAL \
  --protocol=HTTPS

# EU Backend
gcloud compute backend-services create omni-backend-eu \
  --global \
  --load-balancing-scheme=EXTERNAL \
  --protocol=HTTPS

# ASIA Backend
gcloud compute backend-services create omni-backend-asia \
  --global \
  --load-balancing-scheme=EXTERNAL \
  --protocol=HTTPS
```

### Create URL Map with Geo-routing
```bash
gcloud compute url-maps create omni-global-lb \
  --default-service omni-backend-us
```

### Configure Cloud CDN
```bash
gcloud compute backend-services update omni-backend-us \
  --enable-cdn \
  --cache-mode=CACHE_ALL_STATIC

gcloud compute backend-services update omni-backend-eu \
  --enable-cdn \
  --cache-mode=CACHE_ALL_STATIC

gcloud compute backend-services update omni-backend-asia \
  --enable-cdn \
  --cache-mode=CACHE_ALL_STATIC
```

## Database Replication

### Primary Database (US)
```sql
-- Configure for replication
ALTER SYSTEM SET wal_level = logical;
ALTER SYSTEM SET max_replication_slots = 10;
```

### Read Replicas
```bash
# EU Replica
gcloud sql instances create omni-db-eu-replica \
  --master-instance-name=omni-db-us \
  --region=europe-west1

# ASIA Replica
gcloud sql instances create omni-db-asia-replica \
  --master-instance-name=omni-db-us \
  --region=asia-southeast1
```

## Monitoring

### Health Checks
```bash
gcloud compute health-checks create https omni-health-check \
  --request-path=/api/health \
  --port=443
```

### Uptime Monitoring
- US: https://omni-us.omniscient.ai/api/health
- EU: https://omni-eu.omniscient.ai/api/health
- ASIA: https://omni-asia.omniscient.ai/api/health

## Failover Strategy

### Automatic Failover
1. Health check fails in primary region
2. Load balancer redirects traffic to nearest healthy region
3. Automatic notification to ops team
4. RTO: < 5 minutes

### Manual Failover
```bash
# Redirect all traffic to EU
gcloud compute url-maps set-default-service omni-global-lb \
  --default-service omni-backend-eu
```

## Performance Metrics

### Target Latencies
- **Same Region:** < 50ms
- **Cross Region:** < 150ms
- **Global Average:** < 100ms

### Availability Targets
- **Per Region:** 99.95%
- **Global:** 99.99%

## Cost Optimization

### Auto-scaling Configuration
- **Min instances:** Region-specific (2-3)
- **Max instances:** Based on capacity (50-100)
- **Scale-up threshold:** 70% CPU
- **Scale-down threshold:** 30% CPU

### CDN Caching
- **Static assets:** 1 year cache
- **API responses:** 60s cache (configurable)
- **Cache hit ratio target:** > 80%

## Security

### SSL/TLS
- All regions use Google-managed SSL certificates
- Minimum TLS 1.2
- HSTS enabled

### DDoS Protection
- Cloud Armor enabled
- Rate limiting: 1000 req/minute per IP
- Geo-blocking for high-risk regions

## Disaster Recovery

### Backup Strategy
- **Database:** Daily automated backups
- **Redis:** AOF persistence enabled
- **Cross-region backup:** Weekly

### Recovery Procedures
See `/infrastructure/disaster-recovery/` for detailed procedures.
