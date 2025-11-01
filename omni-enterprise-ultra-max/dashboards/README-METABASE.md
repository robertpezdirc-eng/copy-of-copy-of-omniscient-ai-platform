# Metabase Dashboard Setup Guide

## Overview
This directory contains Metabase dashboard templates for the OMNI Enterprise Ultra Max platform. These dashboards provide comprehensive analytics across revenue, users, and AI performance.

## Available Dashboards

### 1. Revenue Analytics Dashboard (`metabase-revenue-analytics.json`)
**Purpose:** Track revenue, forecasting, and growth metrics

**Key Metrics:**
- Total Revenue (30 Days)
- MRR (Monthly Recurring Revenue)
- ARR (Annual Recurring Revenue)
- Revenue trends and forecasts
- Payment method breakdown
- Top revenue sources
- Churn impact analysis

**Database Tables Required:**
- `transactions`
- `subscriptions`
- `users`
- `ai_revenue_forecasts`

---

### 2. User Analytics & Engagement Dashboard (`metabase-user-analytics.json`)
**Purpose:** Monitor user behavior, engagement, and churn predictions

**Key Metrics:**
- Active users and new signups
- User engagement scores
- Churn risk distribution
- Feature usage heatmaps
- Retention cohort analysis
- Lifetime value predictions

**Database Tables Required:**
- `users`
- `user_events`
- `user_metrics`
- `ai_churn_predictions`

---

### 3. AI Performance & Model Insights Dashboard (`metabase-ai-performance.json`)
**Purpose:** Track AI model performance, predictions, and infrastructure metrics

**Key Metrics:**
- AI prediction volume
- Model accuracy and performance
- FAISS vector search stats
- Sentiment analysis distribution
- Anomaly detections
- Model training history
- GCS storage usage

**Database Tables Required:**
- `ai_prediction_logs`
- `ai_model_metrics`
- `ai_revenue_forecasts`
- `sentiment_analysis_results`
- `anomaly_detections`
- `ai_model_training_logs`
- `faiss_query_logs`
- `gcs_model_artifacts`

---

## Installation Steps

### 1. Import Dashboards to Metabase

```bash
# Using Metabase API
curl -X POST "https://your-metabase-url/api/dashboard" \
  -H "Content-Type: application/json" \
  -H "X-Metabase-Session: YOUR_SESSION_TOKEN" \
  -d @metabase-revenue-analytics.json

curl -X POST "https://your-metabase-url/api/dashboard" \
  -H "Content-Type: application/json" \
  -H "X-Metabase-Session: YOUR_SESSION_TOKEN" \
  -d @metabase-user-analytics.json

curl -X POST "https://your-metabase-url/api/dashboard" \
  -H "Content-Type: application/json" \
  -H "X-Metabase-Session: YOUR_SESSION_TOKEN" \
  -d @metabase-ai-performance.json
```

### 2. Configure Database Connection

In Metabase Admin:
1. Go to **Admin > Databases**
2. Add new database: `omni_db`
3. Configure connection:
   - **Type:** PostgreSQL (or your database type)
   - **Host:** Your database host
   - **Port:** 5432 (or your port)
   - **Database name:** `omni_production`
   - **Username/Password:** Your credentials

### 3. Create Required Database Tables

If tables don't exist yet, create them:

```sql
-- AI Prediction Logs
CREATE TABLE ai_prediction_logs (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(255),
  prediction_type VARCHAR(100),
  response_time_ms INTEGER,
  model_name VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);

-- AI Model Metrics
CREATE TABLE ai_model_metrics (
  id SERIAL PRIMARY KEY,
  model_name VARCHAR(100),
  accuracy_score DECIMAL(5,4),
  precision_score DECIMAL(5,4),
  recall_score DECIMAL(5,4),
  measured_at TIMESTAMP DEFAULT NOW()
);

-- AI Revenue Forecasts
CREATE TABLE ai_revenue_forecasts (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(255),
  prediction_date DATE,
  predicted_revenue DECIMAL(12,2),
  lower_bound DECIMAL(12,2),
  upper_bound DECIMAL(12,2),
  created_at TIMESTAMP DEFAULT NOW()
);

-- AI Churn Predictions
CREATE TABLE ai_churn_predictions (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255),
  churn_probability DECIMAL(5,4),
  churn_risk_level VARCHAR(50),
  engagement_score DECIMAL(5,2),
  lifetime_value_prediction DECIMAL(12,2),
  recommended_actions TEXT[],
  prediction_date TIMESTAMP DEFAULT NOW()
);

-- Sentiment Analysis Results
CREATE TABLE sentiment_analysis_results (
  id SERIAL PRIMARY KEY,
  text TEXT,
  sentiment VARCHAR(50),
  confidence DECIMAL(5,4),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Anomaly Detections
CREATE TABLE anomaly_detections (
  id SERIAL PRIMARY KEY,
  metric_name VARCHAR(100),
  anomaly_value DECIMAL(12,2),
  expected_range VARCHAR(100),
  severity VARCHAR(50),
  affected_entities TEXT[],
  detected_at TIMESTAMP DEFAULT NOW()
);

-- AI Model Training Logs
CREATE TABLE ai_model_training_logs (
  id SERIAL PRIMARY KEY,
  model_name VARCHAR(100),
  model_version VARCHAR(50),
  training_started_at TIMESTAMP,
  training_completed_at TIMESTAMP,
  dataset_size INTEGER,
  final_accuracy DECIMAL(5,4),
  deployment_status VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

-- FAISS Query Logs
CREATE TABLE faiss_query_logs (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(255),
  query_text TEXT,
  response_time_ms INTEGER,
  result_count INTEGER,
  index_size BIGINT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- GCS Model Artifacts
CREATE TABLE gcs_model_artifacts (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(255),
  model_name VARCHAR(100),
  artifact_path VARCHAR(500),
  model_size_bytes BIGINT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Daily Revenue Actuals (for forecast comparison)
CREATE TABLE daily_revenue_actuals (
  id SERIAL PRIMARY KEY,
  date DATE UNIQUE,
  actual_revenue DECIMAL(12,2),
  created_at TIMESTAMP DEFAULT NOW()
);

-- User Metrics
CREATE TABLE user_metrics (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255),
  engagement_score DECIMAL(5,2),
  calculated_at TIMESTAMP DEFAULT NOW()
);
```

### 4. Set Up Data Collection

Wire your application to log AI metrics:

```python
# Example: Log AI predictions
async def log_prediction(prediction_type: str, response_time: int, model: str):
    await db.execute(
        "INSERT INTO ai_prediction_logs (prediction_type, response_time_ms, model_name) VALUES ($1, $2, $3)",
        prediction_type, response_time, model
    )

# Example: Log model metrics
async def log_model_metrics(model: str, accuracy: float, precision: float, recall: float):
    await db.execute(
        "INSERT INTO ai_model_metrics (model_name, accuracy_score, precision_score, recall_score) VALUES ($1, $2, $3, $4)",
        model, accuracy, precision, recall
    )
```

---

## Dashboard Features

### Filters
All dashboards support:
- **Date Range:** Past 7 days, 30 days, 90 days, custom
- **Tenant Filter:** Multi-tenant support
- **Category Filters:** Payment methods, user segments, model types

### Auto-Refresh
Set dashboards to auto-refresh:
1. Open dashboard
2. Click gear icon
3. Set refresh interval (e.g., 5 minutes)

### Alerts
Configure alerts for critical metrics:
- Revenue drops below threshold
- High churn risk users detected
- Model accuracy falls below 85%
- Anomalies detected

---

## Customization

### Modify Queries
Edit SQL queries in Metabase:
1. Open dashboard
2. Click on card
3. Edit → Modify query
4. Save changes

### Add New Cards
1. Click "+" in dashboard
2. Select "Question" or "SQL query"
3. Build visualization
4. Add to dashboard

### Change Colors/Themes
1. Dashboard settings
2. Appearance
3. Customize colors, fonts, layout

---

## Integration with OMNI Platform

### Backend Logging
Add to `backend/utils/metrics_logger.py`:

```python
import asyncpg
from datetime import datetime

class MetricsLogger:
    def __init__(self, db_pool):
        self.db = db_pool
    
    async def log_ai_prediction(self, data: dict):
        await self.db.execute("""
            INSERT INTO ai_prediction_logs 
            (tenant_id, prediction_type, response_time_ms, model_name)
            VALUES ($1, $2, $3, $4)
        """, data['tenant_id'], data['type'], data['time'], data['model'])
    
    async def log_churn_prediction(self, user_id: str, prediction: dict):
        await self.db.execute("""
            INSERT INTO ai_churn_predictions
            (user_id, churn_probability, churn_risk_level, engagement_score, lifetime_value_prediction, recommended_actions)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, user_id, prediction['probability'], prediction['risk'], 
            prediction['engagement'], prediction['ltv'], prediction['actions'])
```

### AI Worker Integration
Modify `ai-worker/main.py` to log metrics:

```python
from utils.metrics import log_prediction_metric

@app.post("/predict/revenue")
async def predict_revenue(payload: RevenueForecastRequest):
    start_time = time.time()
    result = await _predictive.predict_revenue(...)
    
    # Log metrics
    await log_prediction_metric(
        prediction_type="revenue_forecast",
        response_time_ms=int((time.time() - start_time) * 1000),
        model_name="Prophet"
    )
    
    # Store forecast
    await store_revenue_forecast(result)
    
    return result
```

---

## Maintenance

### Regular Tasks
- **Weekly:** Review dashboard performance
- **Monthly:** Update SQL queries if schema changes
- **Quarterly:** Add new metrics based on business needs

### Backup Dashboards
Export regularly:
```bash
curl "https://your-metabase-url/api/dashboard/1" \
  -H "X-Metabase-Session: YOUR_TOKEN" > backup-$(date +%Y%m%d).json
```

---

## Troubleshooting

### Dashboard Not Loading
1. Check database connection
2. Verify table permissions
3. Review query syntax

### Slow Queries
1. Add indexes on frequently queried columns
2. Reduce date ranges
3. Use materialized views for complex queries

### Missing Data
1. Verify data collection is running
2. Check application logs
3. Ensure database writes are successful

---

## Support

For issues or questions:
- Check Metabase documentation: https://www.metabase.com/docs
- Review application logs
- Contact: support@omni-ultra.com

---

**Version:** 1.0.0  
**Last Updated:** November 1, 2025  
**Compatible with:** Metabase v0.46+
