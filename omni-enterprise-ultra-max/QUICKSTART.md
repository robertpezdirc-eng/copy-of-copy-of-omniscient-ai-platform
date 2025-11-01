# Quick Start Guide - Omni Unified Platform

## 🚀 Local Development

### 1. Start Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

Access at: http://localhost:8080

### 2. Access API Documentation
http://localhost:8080/api/docs

### 3. Test New Routes

#### Adapters
```bash
curl http://localhost:8080/api/v1/adapters/list
```

#### Machine Learning
```bash
curl http://localhost:8080/api/v1/learning/models
```

#### Data Ingestion
```bash
curl http://localhost:8080/api/v1/ingestion/jobs
```

## ☁️ Google Cloud Storage Backup

### Manual Backup
```bash
# On Linux/Mac
chmod +x scripts/gcs-backup.sh
./scripts/gcs-backup.sh

# On Windows (using Git Bash or WSL)
bash scripts/gcs-backup.sh
```

### View Backups
```bash
gsutil ls gs://omni-unified-backups/omni-unified-platform/
```

### Setup Cloud Scheduler (30-minute backups)
```bash
gcloud scheduler jobs create http omni-backup-trigger \
  --location=europe-west1 \
  --schedule="*/30 * * * *" \
  --uri="https://YOUR-CLOUD-RUN-URL/api/v1/admin/trigger-backup" \
  --http-method=POST \
  --project=refined-graph-471712-n9
```

## 🏗️ Deploy to Cloud Run

```bash
gcloud run deploy omni-unified-platform \
  --source . \
  --platform managed \
  --region europe-west1 \
  --project refined-graph-471712-n9 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 4 \
  --min-instances 1 \
  --max-instances 50
```

## 📊 Verify Deployment

```bash
# Get service URL
gcloud run services describe omni-unified-platform \
  --region europe-west1 \
  --format 'value(status.url)'

# Health check
curl https://YOUR-URL/api/health

# System summary
curl https://YOUR-URL/api/v1/omni/summary
```

## 🔧 Environment Setup

Copy `.env` and configure:
- GCP_PROJECT_ID=refined-graph-471712-n9
- GCP_REGION=europe-west1
- STRIPE_SECRET_KEY=...
- PAYPAL_CLIENT_SECRET=...
- Other API keys

## 📦 Total Routes: 28+

1. Stripe Payments
2. PayPal Payments
3. Crypto Payments
4. Affiliate System
5. Marketplace
6. AI Services
7. Analytics
8. AI Intelligence
9. Growth Engine
10. Security & Compliance
11. Global Scaling
12. Developer Ecosystem
13. Support & Community
14. Performance Monitoring
15. Billing
16. Feedback
17. Auth
18. Tenant Management
19. IoT & Telemetry
20. Monetization
21. Analytics & Usage
22. WebSocket
23. Capacity Planning
24. Security Audit
25. **Adapters** ⭐ NEW
26. **Learning & ML** ⭐ NEW
27. **Data Ingestion** ⭐ NEW
28. Health & System

## 🎉 Success!

Platform merged successfully with continuous Google Cloud backup!

See `MERGE_SUMMARY.md` for complete documentation.
