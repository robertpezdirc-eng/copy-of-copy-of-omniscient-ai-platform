# Multi-Region Deployment Configuration
# GCP Multi-Region Setup for Omni Enterprise Ultra Max

## Architecture Overview

```
                         ┌─────────────────┐
                         │  Global CDN     │
                         │  Cloud CDN      │
                         └────────┬────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                │
          ┌──────▼──────┐  ┌─────▼──────┐  ┌─────▼──────┐
          │   US Region │  │  EU Region │  │ Asia Region│
          │ us-central1 │  │europe-west1│  │asia-ne1    │
          └──────┬──────┘  └─────┬──────┘  └─────┬──────┘
                 │                │                │
          ┌──────▼──────┐  ┌─────▼──────┐  ┌─────▼──────┐
          │  Cloud Run  │  │ Cloud Run  │  │ Cloud Run  │
          │  + GKE      │  │ + GKE      │  │ + GKE      │
          └──────┬──────┘  └─────┬──────┘  └─────┬──────┘
                 │                │                │
          ┌──────▼──────┐  ┌─────▼──────┐  ┌─────▼──────┘
          │  Cloud SQL  │  │ Cloud SQL  │  │ Cloud SQL  │
          │  + Spanner  │  │ + Spanner  │  │ + Spanner  │
          │  Replica    │  │  Primary   │  │  Replica   │
          └─────────────┘  └────────────┘  └────────────┘
```

## Deployment Regions

### Primary Regions

**US - us-central1 (Iowa)**
- Primary for North America
- Low CO2 region
- 4 zones (a, b, c, f)
- Full service availability

**EU - europe-west1 (Belgium)**
- Primary for Europe
- GDPR compliant
- Low CO2 region
- 3 zones (b, c, d)

**Asia - asia-northeast1 (Tokyo)**
- Primary for Asia-Pacific
- Low latency for Japan/Korea
- 3 zones (a, b, c)

### Secondary Regions

**US East - us-east1 (South Carolina)**
- Backup for US traffic
- Cross-region redundancy

**EU West - europe-west4 (Netherlands)**
- Backup for EU traffic
- Additional GDPR compliance

**Asia South - asia-south1 (Mumbai)**
- Backup for Asia traffic
- Coverage for India

## Quick Deployment Commands

### 1. Deploy Backend to Multiple Regions

```bash
# US Region
gcloud run deploy omni-backend-us \
  --image=europe-west1-docker.pkg.dev/${PROJECT_ID}/omni/omni-ultra-backend:${TAG} \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars="REGION=us-central1,DATABASE_REGION=us-central1"

# EU Region
gcloud run deploy omni-backend-eu \
  --image=europe-west1-docker.pkg.dev/${PROJECT_ID}/omni/omni-ultra-backend:${TAG} \
  --region=europe-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars="REGION=europe-west1,DATABASE_REGION=europe-west1"

# Asia Region
gcloud run deploy omni-backend-asia \
  --image=europe-west1-docker.pkg.dev/${PROJECT_ID}/omni/omni-ultra-backend:${TAG} \
  --region=asia-northeast1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars="REGION=asia-northeast1,DATABASE_REGION=asia-northeast1"
```

### 2. Setup Global Load Balancer

```bash
# Create backend services for each region
gcloud compute backend-services create omni-backend-global \
  --global \
  --load-balancing-scheme=EXTERNAL \
  --protocol=HTTP

# Add backends from each region
gcloud compute backend-services add-backend omni-backend-global \
  --global \
  --network-endpoint-group=omni-neg-us \
  --network-endpoint-group-region=us-central1 \
  --balancing-mode=RATE \
  --max-rate-per-endpoint=100

# Create URL map
gcloud compute url-maps create omni-global-lb \
  --default-service=omni-backend-global

# Create HTTPS proxy
gcloud compute target-https-proxies create omni-https-proxy \
  --url-map=omni-global-lb \
  --ssl-certificates=omni-ssl-cert

# Create forwarding rule
gcloud compute forwarding-rules create omni-https-forwarding-rule \
  --global \
  --target-https-proxy=omni-https-proxy \
  --ports=443
```

### 3. Setup Cloud CDN

```bash
# Enable Cloud CDN on backend service
gcloud compute backend-services update omni-backend-global \
  --global \
  --enable-cdn \
  --cache-mode=CACHE_ALL_STATIC \
  --default-ttl=3600 \
  --max-ttl=86400 \
  --client-ttl=3600

# Configure cache key policy
gcloud compute backend-services update omni-backend-global \
  --global \
  --cache-key-include-protocol \
  --cache-key-include-host \
  --cache-key-include-query-string
```

### 4. Setup Cloud Spanner (Multi-Region Database)

```bash
# Create multi-region Spanner instance
gcloud spanner instances create omni-global-db \
  --config=nam-eur-asia1 \
  --description="Omni multi-region database" \
  --nodes=3

# Create database
gcloud spanner databases create omni-production \
  --instance=omni-global-db

# Create tables with geographic replication
gcloud spanner databases ddl update omni-production \
  --instance=omni-global-db \
  --ddl='CREATE TABLE tenants (
    tenant_id STRING(36) NOT NULL,
    name STRING(255),
    region STRING(50),
    created_at TIMESTAMP,
  ) PRIMARY KEY (tenant_id)'
```

### 5. Setup Redis with Memory Store

```bash
# Create Redis instances in each region
# US Region
gcloud redis instances create omni-redis-us \
  --region=us-central1 \
  --tier=standard \
  --size=5 \
  --redis-version=redis_6_x

# EU Region
gcloud redis instances create omni-redis-eu \
  --region=europe-west1 \
  --tier=standard \
  --size=5 \
  --redis-version=redis_6_x

# Asia Region
gcloud redis instances create omni-redis-asia \
  --region=asia-northeast1 \
  --tier=standard \
  --size=5 \
  --redis-version=redis_6_x
```

## DNS Configuration

### Cloud DNS Setup

```bash
# Create DNS zone
gcloud dns managed-zones create omni-zone \
  --dns-name="omni-ultra.com." \
  --description="Omni Enterprise DNS"

# Add A records for global load balancer
gcloud dns record-sets create api.omni-ultra.com. \
  --zone=omni-zone \
  --type=A \
  --ttl=300 \
  --rrdatas="GLOBAL_LB_IP"

# Add region-specific records
gcloud dns record-sets create us.api.omni-ultra.com. \
  --zone=omni-zone \
  --type=A \
  --ttl=300 \
  --rrdatas="US_CLOUD_RUN_IP"

gcloud dns record-sets create eu.api.omni-ultra.com. \
  --zone=omni-zone \
  --type=A \
  --ttl=300 \
  --rrdatas="EU_CLOUD_RUN_IP"
```

## Monitoring & Alerting

### Cloud Monitoring Dashboards

```bash
# Create uptime check for each region
gcloud monitoring uptime-checks create http omni-us-health \
  --display-name="Omni US Health Check" \
  --resource-type=uptime-url \
  --host=us.api.omni-ultra.com \
  --path=/api/health

# Create alert policies
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=300s
```

## Geographic Routing

### Traffic Distribution Rules

```yaml
# traffic-routing.yaml
apiVersion: networking.gke.io/v1
kind: MultiClusterService
metadata:
  name: omni-service
  namespace: default
spec:
  template:
    spec:
      selector:
        app: omni-backend
      ports:
      - name: http
        protocol: TCP
        port: 8080
  clusters:
  - link: "us-central1/omni-cluster"
    weight: 40
  - link: "europe-west1/omni-cluster"
    weight: 35
  - link: "asia-northeast1/omni-cluster"
    weight: 25
```

## Data Residency & Compliance

### GDPR Compliance (EU)

```bash
# Set data location constraints
gcloud services enable cloudresourcemanager.googleapis.com

# Create organization policy for data location
gcloud resource-manager org-policies set-policy \
  --organization=ORG_ID \
  policy.yaml

# policy.yaml content:
# constraint: constraints/gcp.resourceLocations
# listPolicy:
#   allowedValues:
#   - in:eu-locations
```

### Region-Specific Storage

```python
# In backend code - route data by region
def get_storage_bucket(tenant_region: str) -> str:
    region_buckets = {
        "US": "omni-storage-us",
        "EU": "omni-storage-eu",
        "ASIA": "omni-storage-asia"
    }
    return region_buckets.get(tenant_region, "omni-storage-global")
```

## Failover Configuration

### Automatic Failover Setup

```bash
# Configure health checks
gcloud compute health-checks create http omni-health-check \
  --port=8080 \
  --request-path=/api/health \
  --check-interval=10s \
  --timeout=5s \
  --unhealthy-threshold=3 \
  --healthy-threshold=2

# Configure backend service with failover
gcloud compute backend-services update omni-backend-global \
  --global \
  --health-checks=omni-health-check \
  --enable-logging \
  --logging-sample-rate=1.0
```

## Cost Optimization

### Multi-Region Cost Estimates

**Monthly Costs (per region):**
- Cloud Run: $50-200 (based on traffic)
- Cloud SQL: $200-500 (HA setup)
- Redis (Memorystore): $150-300
- Cloud Storage: $20-100
- Network Egress: $50-200
- Cloud CDN: $10-50

**Total per region:** ~$480-1,350/month
**3 regions total:** ~$1,440-4,050/month

### Cost Reduction Strategies

1. **Use Committed Use Discounts** (30-70% savings)
2. **Enable Cloud CDN** (reduce origin traffic)
3. **Use Cloud Storage lifecycle policies**
4. **Optimize database queries** (reduce Cloud SQL load)
5. **Use preemptible VMs** for batch jobs

## Deployment Checklist

- [ ] Configure GCP project for multi-region
- [ ] Deploy backend to 3 primary regions
- [ ] Setup global load balancer
- [ ] Enable Cloud CDN
- [ ] Configure Cloud Spanner or replicated Cloud SQL
- [ ] Setup Redis in each region
- [ ] Configure DNS with geo-routing
- [ ] Setup monitoring and alerting
- [ ] Test failover scenarios
- [ ] Configure data residency policies
- [ ] Implement GDPR compliance measures
- [ ] Load test each region
- [ ] Document runbooks for incidents

## Testing

### Region Failover Test

```bash
# Test automatic failover
./scripts/test-failover.sh us-central1 europe-west1

# Expected output:
# ✓ Primary region health check failed (simulated)
# ✓ Traffic rerouted to secondary region
# ✓ DNS updated within 30 seconds
# ✓ Zero data loss verified
# ✓ All services operational in secondary region
```

### Performance Test

```bash
# Test latency from different regions
for region in us eu asia; do
  curl -w "\nTime: %{time_total}s\n" \
    https://${region}.api.omni-ultra.com/api/health
done
```

## Support

For multi-region deployment support:
- Email: devops@omni-ultra.com
- Slack: #multi-region-deployment
- On-call: Use PagerDuty escalation

## References

- [GCP Multi-Region Guide](https://cloud.google.com/architecture/deploy-multi-region)
- [Cloud Spanner Best Practices](https://cloud.google.com/spanner/docs/best-practice-list)
- [Global Load Balancing](https://cloud.google.com/load-balancing/docs/https)
- [GDPR Compliance on GCP](https://cloud.google.com/security/gdpr)
