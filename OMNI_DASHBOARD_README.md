# OMNI Platform - Integrated Operational Dashboard

## Overview

This professional operational dashboard provides comprehensive monitoring and management capabilities for your entire OMNI AI platform. The dashboard integrates seamlessly with your Google Cloud Functions and provides real-time insights into both system performance and OMNI platform metrics.

## Features

### 🔧 System Monitoring
- **Real-time CPU, Memory, and Disk Usage** - Live system metrics with historical trends
- **Service Health Monitoring** - Track status of all critical services
- **Cloud Resource Management** - Monitor Google Cloud instances and costs
- **Alert System** - Automated alerts for critical issues

### 🤖 OMNI Platform Integration
- **Platform Status Monitoring** - Real-time OMNI platform health
- **AI Model Tracking** - Monitor Gemini AI model performance
- **Success Rate Analytics** - Track platform success metrics
- **Response Time Monitoring** - Performance optimization insights
- **Feature Overview** - Display available OMNI platform features

### 🌐 Real-time Updates
- **WebSocket Support** - Live data streaming to dashboard
- **Auto-refresh** - Fallback polling mechanism
- **Interactive Charts** - Beautiful visualizations with Plotly
- **Responsive Design** - Works on desktop and mobile devices

### 🔐 Security & Authentication
- **API Key Authentication** - Secure communication with OMNI platform
- **HMAC Signature Support** - Advanced security for production use
- **Configurable Auth Methods** - Support for multiple authentication strategies

## Quick Start

### Prerequisites

1. **Google Cloud Account** with billing enabled
2. **OMNI Platform Cloud Functions** deployed and running
3. **Python 3.11+** installed
4. **Docker** (for containerized deployment)

### Local Development

1. **Install Dependencies**
   ```bash
   pip install -r requirements-dashboard.txt
   ```

2. **Set Environment Variables**
   ```bash
   export PROJECT_ID="your-project-id"
   export OMNI_API_KEY="your-omni-api-key"
   export OMNI_AUTH_METHOD="api_key"
   ```

3. **Run Dashboard**
   ```bash
   python omni_operational_dashboard.py
   ```

4. **Access Dashboard**
   Open http://localhost:8080 in your browser

### Google Cloud Run Deployment

1. **Build and Push Image**
   ```bash
   # Build Docker image
   docker build -f Dockerfile.dashboard -t gcr.io/YOUR_PROJECT_ID/omni-dashboard:latest .

   # Push to Google Container Registry
   gcloud auth configure-docker
   docker push gcr.io/YOUR_PROJECT_ID/omni-dashboard:latest
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy omni-dashboard \
     --image gcr.io/YOUR_PROJECT_ID/omni-dashboard:latest \
     --platform managed \
     --region europe-west1 \
     --allow-unauthenticated \
     --port 8080 \
     --memory 1Gi \
     --cpu 1 \
     --max-instances 3 \
     --set-env-vars PROJECT_ID=YOUR_PROJECT_ID \
     --set-env-vars OMNI_API_KEY=your-api-key
   ```

3. **Get Service URL**
   ```bash
   gcloud run services describe omni-dashboard --platform managed --region europe-west1 --format="value(status.url)"
   ```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PROJECT_ID` | Google Cloud Project ID | - | Yes |
| `REGION` | Google Cloud Region | `europe-west1` | No |
| `OMNI_API_KEY` | API key for OMNI platform | - | Yes |
| `OMNI_AUTH_METHOD` | Authentication method (`api_key`, `hmac`, `jwt`) | `api_key` | No |
| `OMNI_SECRET_KEY` | Secret key for HMAC authentication | - | For HMAC |
| `OMNI_JWT_SECRET` | JWT secret for token authentication | - | For JWT |
| `OMNI_DEBUG_AUTH` | Enable debug authentication | `false` | No |

### Authentication Methods

#### API Key (Recommended for development)
```bash
export OMNI_AUTH_METHOD="api_key"
export OMNI_API_KEY="your-api-key-here"
```

#### HMAC (Recommended for production)
```bash
export OMNI_AUTH_METHOD="hmac"
export OMNI_SECRET_KEY="your-secret-key-here"
```

#### JWT
```bash
export OMNI_AUTH_METHOD="jwt"
export OMNI_JWT_SECRET="your-jwt-secret-here"
```

## API Endpoints

### Dashboard Interface
- `GET /` - Main dashboard HTML interface
- `GET /api/metrics` - Current system metrics
- `GET /api/services` - Service status information
- `GET /api/cloud` - Google Cloud resources
- `GET /api/alerts` - Active alerts
- `GET /api/analytics` - Platform analytics
- `GET /api/omni` - OMNI platform data
- `GET /api/omni/status` - OMNI platform status
- `POST /api/omni/chat` - Send chat message to OMNI platform

### Real-time Updates
- `WebSocket /ws` - Real-time data streaming

## Dashboard Sections

### System Health Overview
- **Overall Health Score** - Calculated based on resource usage
- **Monthly Cost Estimate** - Google Cloud cost projections
- **Active Services** - Service availability status
- **Average Response Time** - System performance metrics

### OMNI Platform Status
- **Platform Health** - Real-time OMNI platform status
- **AI Model Information** - Currently active Gemini model
- **Success Rate** - Platform operation success percentage
- **Response Time** - OMNI platform response performance

### Interactive Charts
- **CPU & Memory Usage** - Historical performance trends
- **Disk Usage** - Storage utilization over time
- **Service Status Grid** - Visual service health indicators
- **Alert Timeline** - Recent system alerts

## Security Best Practices

1. **Use Strong API Keys** - Generate keys with sufficient entropy
2. **Enable Authentication** - Use HMAC or JWT for production
3. **Network Security** - Deploy behind Google Cloud Load Balancer
4. **Access Control** - Configure appropriate IAM permissions
5. **HTTPS Only** - Always use SSL/TLS in production

## Troubleshooting

### Common Issues

**Dashboard won't start**
- Check Python version (requires 3.11+)
- Verify all dependencies are installed
- Check environment variables

**OMNI platform not connecting**
- Verify OMNI platform Cloud Functions are deployed
- Check API key configuration
- Confirm network connectivity

**WebSocket connection fails**
- Check browser compatibility
- Verify WebSocket support in deployment environment
- Check firewall settings

**High resource usage**
- Monitor dashboard performance
- Adjust update intervals if needed
- Consider using Cloud Run concurrency settings

### Logs and Monitoring

**View Dashboard Logs**
```bash
# Local development
tail -f logs/omni_dashboard.log

# Google Cloud Run
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=omni-dashboard" --limit 50
```

**Monitor Performance**
```bash
# Check Cloud Run metrics
gcloud run services describe omni-dashboard --region europe-west1

# View resource utilization
gcloud monitoring dashboards create
```

## Advanced Configuration

### Custom Monitoring Intervals
```python
# In omni_operational_dashboard.py
self.check_interval = 15  # Update every 15 seconds
self.websocket_update_interval = 3  # WebSocket updates every 3 seconds
```

### Custom Alert Thresholds
```python
# Customize alert conditions in _generate_alerts() method
if latest.cpu_percent > 85:  # Lower threshold
    self._add_alert("warning", "High CPU usage", f"CPU at {latest.cpu_percent}%")
```

### Additional Data Sources
```python
# Add custom monitoring in _check_services_status()
services_to_check = [
    "custom-service",
    "api-gateway",
    "message-queue"
]
```

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review Cloud Run logs for error details
3. Verify OMNI platform Cloud Functions are operational
4. Check network connectivity and firewall settings

## License

This dashboard is part of the OMNI Platform and follows the same licensing terms.