# OMNI Platform Dashboard - Google Cloud Run Deployment

🚀 Professional operational dashboard for the complete Omni AI platform, deployed to Google Cloud Run.

## 📋 Overview

This deployment includes:
- **Real-time monitoring** of system metrics and services
- **Google Cloud integration** for resource monitoring
- **Interactive charts** and visualizations
- **Alert management** system
- **Professional web interface** with modern UI

## 🛠️ Deployment Configuration

### Target Environment
- **Project ID:** `refined-graph-471712-n9`
- **Region:** `europe-west1` (Belgium)
- **Service Name:** `omni-dashboard`
- **Platform:** Google Cloud Run (Fully managed)

### Resources Allocated
- **Memory:** 1 GB
- **CPU:** 1 vCPU
- **Max Instances:** 3
- **Timeout:** 300 seconds
- **Concurrency:** Default (80 requests per instance)

## 🚀 Quick Deployment

### Method 1: Automated Deployment (Recommended)

```bash
# 1. Ensure you're authenticated with Google Cloud
gcloud auth login

# 2. Set the project
gcloud config set project refined-graph-471712-n9

# 3. Run the deployment script
./deploy-dashboard-to-cloud-run.sh
```

### Method 2: Manual Deployment

```bash
# 1. Build and push Docker image
docker build -t gcr.io/refined-graph-471712-n9/omni-dashboard:latest .
gcloud auth configure-docker
docker push gcr.io/refined-graph-471712-n9/omni-dashboard:latest

# 2. Deploy to Cloud Run
gcloud run deploy omni-dashboard \
    --image gcr.io/refined-graph-471712-n9/omni-dashboard:latest \
    --platform managed \
    --region europe-west1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 3 \
    --timeout 300 \
    --set-env-vars OMNI_SYSTEM_CHECKS=false,OMNI_QUIET_CLOUDRUN=true,OMNI_CLOUDRUN_LOG_LEVEL=WARNING
```

## 🌐 Access URLs

After successful deployment, the dashboard will be available at:
```
https://omni-dashboard-[random-hash]-europe-west1.run.app
```

### API Endpoints
- **Main Dashboard:** `https://[SERVICE_URL]/`
- **Metrics API:** `https://[SERVICE_URL]/api/metrics`
- **Services Status:** `https://[SERVICE_URL]/api/services`
- **Cloud Resources:** `https://[SERVICE_URL]/api/cloud`
- **Alerts:** `https://[SERVICE_URL]/api/alerts`
- **Analytics:** `https://[SERVICE_URL]/api/analytics`

## 📊 Dashboard Features

### Real-time Monitoring
- **System Metrics:** CPU, Memory, Disk usage
- **Service Health:** Status of all platform services
- **Cloud Resources:** GCE instances, costs, utilization
- **Network I/O:** Bandwidth and connection metrics

### Visualizations
- **Interactive Charts:** Real-time CPU/Memory graphs
- **Service Status Grid:** Visual service health indicators
- **Cost Analysis:** Monthly cost estimates and trends
- **Alert Dashboard:** Active alerts and notifications

### Google Cloud Integration
- **Resource Discovery:** Automatic detection of GCE instances
- **Cost Monitoring:** Real-time cost calculation
- **Service Integration:** Status monitoring of cloud services
- **Logging Integration:** Cloud Logging for all events

## 🔧 Configuration

### Environment Variables
The following environment variables are configured:
- `PROJECT_ID`: Google Cloud project ID
- `ENVIRONMENT`: Set to 'production'
- `PORT`: Application port (8080)
- `LOG_LEVEL`: Logging level (INFO)
- `OMNI_SYSTEM_CHECKS`: Set to 'false' to minimize startup checks in Cloud Run
- `OMNI_QUIET_CLOUDRUN`: Set to 'true' to reduce logging verbosity in managed environment
- `OMNI_CLOUDRUN_LOG_LEVEL`: Logging level for Cloud Run (default: `WARNING`). Set to `INFO` or `DEBUG` for more verbose logs

### Customization Options
- **Memory/CPU:** Adjust in deployment command
- **Max Instances:** Scale based on traffic
- **Timeout:** Increase for heavy operations
- **Region:** Change to closer region if needed

## 🔍 Monitoring & Troubleshooting

### Check Service Status
```bash
gcloud run services describe omni-dashboard --region=europe-west1
```

### View Logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=omni-dashboard" --limit 50
```

### Debug Issues
```bash
# Check if service is responding
curl https://[SERVICE_URL]/api/metrics

# View detailed service information
gcloud run services logs read omni-dashboard --region=europe-west1
```

### Common Issues
1. **Service not accessible:** Check if `--allow-unauthenticated` is set
2. **High latency:** Consider increasing memory/CPU allocation
3. **Timeout errors:** Increase timeout value in deployment
4. **Import errors:** Verify all dependencies are in requirements.txt

## 💰 Cost Optimization

### Current Configuration Costs
- **Memory:** 1 GB × $0.000925/hour = ~$0.022/hour
- **CPU:** 1 vCPU × $0.042/hour = ~$0.042/hour
- **Total:** ~$0.064/hour (~$1.54/day)

### Optimization Tips
- Reduce memory to 512MB if sufficient
- Set max instances to 1 for low traffic
- Use preemptible instances (if applicable)
- Monitor usage and scale down during off-hours

## 🔒 Security Considerations

⚠️ **Important Security Notes:**
- Service is deployed with `--allow-unauthenticated` for easy access
- For production use, implement proper authentication
- Consider using Identity-Aware Proxy (IAP)
- Set up VPC networking for internal services
- Enable Cloud Armor for additional protection

## 📞 Support

For issues or questions:
1. Check the logs using commands above
2. Verify all APIs are enabled in Google Cloud Console
3. Ensure proper authentication is configured
4. Check resource quotas and limits

## 🔄 Updates

To deploy updates:
```bash
# Rebuild and push new image
docker build -t gcr.io/refined-graph-471712-n9/omni-dashboard:v2 .
docker push gcr.io/refined-graph-471712-n9/omni-dashboard:v2

# Deploy updated version
gcloud run deploy omni-dashboard --image gcr.io/refined-graph-471712-n9/omni-dashboard:v2 --region=europe-west1
```

---

🎉 **Happy Monitoring!** Your OMNI Platform Dashboard is now live on Google Cloud Run!