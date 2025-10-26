# 🚀 OMNI Platform - Google Cloud Deployment Guide

This guide provides comprehensive instructions for deploying the complete OMNI platform to Google Cloud services.

## 📋 Prerequisites

### 1. Google Cloud Setup
- **Google Cloud Project**: `refined-graph-471712-n9`
- **Google Cloud CLI**: Installed and authenticated
- **Billing**: Enabled on your Google Cloud project

### 2. Required APIs
The following APIs must be enabled in your project:
- Cloud Build API
- Cloud Run API
- Container Registry API
- Cloud Storage API
- Cloud Logging API
- Cloud Monitoring API
- Secret Manager API
- IAM API

### 3. Authentication
```bash
# Login to Google Cloud
gcloud auth login

# Set project
gcloud config set project refined-graph-471712-n9
```

## 🏗️ Deployment Architecture

The OMNI platform will be deployed with the following services:

### **Cloud Run Services**
- **omni-platform-api**: Main Python API service (Port 8080)
- **omni-platform-web**: Node.js web interface (Port 3000)

### **Cloud Storage Buckets**
- **omni-platform-{PROJECT_ID}-assets**: Static web assets
- **omni-platform-{PROJECT_ID}-backups**: Database and configuration backups
- **omni-platform-{PROJECT_ID}-logs**: Application logs

### **Monitoring & Alerting**
- CPU usage monitoring (threshold: 80%)
- Memory usage monitoring (threshold: 85%)
- Error rate monitoring (threshold: 10%)

## 🚀 Quick Deployment

### Option 1: Automated Deployment (Recommended)

```bash
# Make deployment script executable
chmod +x deploy-to-google-cloud.sh

# Run deployment script
./deploy-to-google-cloud.sh
```

### Option 2: Manual Deployment

```bash
# 1. Enable required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com storage.googleapis.com

# 2. Create secrets
gcloud secrets create openai-api-key --data-file="openai key.txt"
gcloud secrets create service-account-key --data-file="service_account.json"

# 3. Create storage buckets
gsutil mb -l europe-west1 gs://omni-platform-refined-graph-471712-n9-assets
gsutil mb -l europe-west1 gs://omni-platform-refined-graph-471712-n9-backups
gsutil mb -l europe-west1 gs://omni-platform-refined-graph-471712-n9-logs

# 4. Build and deploy with Cloud Build
gcloud builds submit --config cloudbuild.yaml .
```

## 📁 File Structure

```
omni-platform/
├── Dockerfile                    # Python API service container
├── Dockerfile.nodejs            # Node.js web service container
├── cloudbuild.yaml              # Cloud Build configuration
├── deploy-to-google-cloud.sh    # Automated deployment script
├── monitoring-policy-*.json     # Monitoring and alerting policies
├── requirements.txt             # Python dependencies
└── GOOGLE_CLOUD_DEPLOYMENT_README.md
```

## 🔧 Configuration Files

### **Environment Variables**
The following environment variables are configured for Cloud Run services:

```bash
OPENAI_API_KEY=${_OPENAI_API_KEY}  # Your OpenAI API key
ENVIRONMENT=production             # Environment setting
PROJECT_ID=$PROJECT_ID            # Google Cloud project ID
```

### **Service Configuration**

#### **API Service (omni-platform-api)**
- **Memory**: 2GB
- **CPU**: 2 cores
- **Max Instances**: 10
- **Concurrency**: 1000

#### **Web Service (omni-platform-web)**
- **Memory**: 1GB
- **CPU**: 1 core
- **Max Instances**: 5
- **Concurrency**: 80

## 🔍 Monitoring & Logging

### **Accessing Logs**
```bash
# View all platform logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# View specific service logs
gcloud logging read "resource.labels.service_name=omni-platform-api" --limit 20

# View logs in Cloud Console
open https://console.cloud.google.com/logs/query
```

### **Monitoring Dashboard**
Access the monitoring dashboard at:
```
https://console.cloud.google.com/monitoring/dashboards
```

### **Alerting Policies**
Three alerting policies are automatically created:
1. **High CPU Usage**: Alerts when CPU > 80% for 5+ minutes
2. **High Memory Usage**: Alerts when Memory > 85% for 5+ minutes
3. **High Error Rate**: Alerts when error rate > 10% for 10+ minutes

## 🌐 Accessing Your Services

After deployment, your services will be available at:

### **API Service**
```
https://omni-platform-api-{hash}-europe-west1.run.app
```

### **Web Interface**
```
https://omni-platform-web-{hash}-europe-west1.run.app
```

### **Health Check Endpoints**
- API Health: `https://your-api-url/api/health`
- Web Health: `https://your-web-url/api/health`

## 🔒 Security Configuration

### **Service Account Permissions**
The deployment creates a service account with the following roles:
- `roles/cloudtranslate.user`
- `roles/secretmanager.secretAccessor`
- `roles/storage.objectAdmin`

### **VPC Configuration**
Services are deployed to the default VPC with public access enabled.

### **Authentication**
- Services use service account for Google Cloud API access
- OpenAI API key stored securely in Secret Manager
- No authentication required for public endpoints

## 🛠️ Troubleshooting

### **Common Issues**

#### **Build Failures**
```bash
# Check build logs
gcloud builds list
gcloud builds log $(gcloud builds list --format='value(id)' --limit 1)

# Common fixes:
# 1. Ensure all dependencies are in requirements.txt
# 2. Check that Dockerfile copies all necessary files
# 3. Verify API keys and secrets exist
```

#### **Service Startup Issues**
```bash
# Check service logs
gcloud logging read "resource.labels.service_name=omni-platform-api" --limit 50

# Check service status
gcloud run services describe omni-platform-api --region=europe-west1

# Common fixes:
# 1. Verify environment variables are set correctly
# 2. Check that ports match Dockerfile EXPOSE directive
# 3. Ensure health check endpoints are working
```

#### **Permission Issues**
```bash
# Check IAM permissions
gcloud projects get-iam-policy refined-graph-471712-n9 --format=json

# Grant additional permissions if needed
gcloud projects add-iam-policy-binding refined-graph-471712-n9 \
    --member="serviceAccount:omni-platform@refined-graph-471712-n9.iam.gserviceaccount.com" \
    --role="roles/storage.admin"
```

## 📊 Cost Optimization

### **Current Configuration Costs**
- **Cloud Run**: ~$0.40/hour (2 services)
- **Cloud Storage**: ~$0.02/GB/month
- **Cloud Build**: ~$0.003/build minute
- **Monitoring**: Free tier included

### **Cost Optimization Tips**
1. **Set CPU allocation**: Use appropriate CPU/memory ratios
2. **Configure concurrency**: Adjust based on traffic patterns
3. **Use cold starts**: Set min instances to 0 for infrequent usage
4. **Storage lifecycle**: Set retention policies for old logs

## 🔄 Updates and Maintenance

### **Deploying Updates**
```bash
# Automatic deployment via Cloud Build
gcloud builds submit --config cloudbuild.yaml .

# Or use the deployment script
./deploy-to-google-cloud.sh
```

### **Rolling Back**
```bash
# List service revisions
gcloud run revisions list --service omni-platform-api --region=europe-west1

# Roll back to previous revision
gcloud run services update-traffic omni-platform-api \
    --platform managed \
    --region europe-west1 \
    --to-revisions omni-platform-api-00001=100
```

### **Scaling Services**
```bash
# Update service configuration
gcloud run services update omni-platform-api \
    --platform managed \
    --region europe-west1 \
    --memory 4Gi \
    --cpu 4 \
    --max-instances 20
```

## 📞 Support

### **Getting Help**
1. **Cloud Console**: https://console.cloud.google.com/
2. **Documentation**: https://cloud.google.com/run/docs
3. **Community**: https://cloud.google.com/community

### **Emergency Contacts**
- **Google Cloud Support**: https://cloud.google.com/support
- **Platform Issues**: Check service logs and monitoring dashboard

---

## 🎯 Next Steps

1. **Deploy the platform** using the automated script
2. **Test all endpoints** to ensure services are working
3. **Configure monitoring alerts** with your notification channels
4. **Set up domain mapping** (optional) for custom URLs
5. **Configure CDN** for static assets (optional)

**Happy deploying! 🚀**