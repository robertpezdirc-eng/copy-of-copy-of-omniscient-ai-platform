"""
Advanced business metrics for monitoring.
Track revenue, model performance, user engagement.
"""
from __future__ import annotations

import logging
from typing import Dict, Any

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# Business Metrics
revenue_total = Counter(
    "business_revenue_total_cents",
    "Total revenue in cents",
    ["tier", "feature"]
)

active_users_gauge = Gauge(
    "business_active_users",
    "Number of active users",
    ["tier"]
)

user_engagement_score = Gauge(
    "business_user_engagement_score",
    "Average user engagement score (0-100)",
    ["tier"]
)

# Model Performance Metrics
model_accuracy_gauge = Gauge(
    "ml_model_accuracy_percent",
    "Model prediction accuracy percentage",
    ["model_name", "model_version"]
)

model_inference_total = Counter(
    "ml_model_inference_total",
    "Total model inference requests",
    ["model_name", "status"]
)

model_prediction_latency = Histogram(
    "ml_model_prediction_seconds",
    "Model prediction latency in seconds",
    ["model_name"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# API Usage Metrics
api_calls_by_tenant = Counter(
    "api_calls_tenant_total",
    "API calls per tenant",
    ["tenant_id", "endpoint", "tier"]
)

api_data_processed_bytes = Counter(
    "api_data_processed_bytes_total",
    "Total bytes processed",
    ["direction", "endpoint"]  # direction: inbound/outbound
)

# Feature Usage
feature_usage_counter = Counter(
    "feature_usage_total",
    "Feature usage count",
    ["feature_name", "tier"]
)

# Error Tracking
business_errors_total = Counter(
    "business_errors_total",
    "Business logic errors",
    ["error_type", "severity"]
)

# Cost Tracking
compute_cost_estimate = Gauge(
    "infrastructure_cost_estimate_usd_hour",
    "Estimated hourly infrastructure cost in USD",
    ["resource_type"]
)


class BusinessMetricsCollector:
    """Helper class for collecting business metrics."""
    
    @staticmethod
    def track_revenue(amount_cents: int, tier: str, feature: str):
        """Track revenue from API usage."""
        revenue_total.labels(tier=tier, feature=feature).inc(amount_cents)
    
    @staticmethod
    def update_active_users(count: int, tier: str):
        """Update active user count for a tier."""
        active_users_gauge.labels(tier=tier).set(count)
    
    @staticmethod
    def track_model_inference(
        model_name: str, 
        status: str, 
        duration: float,
        accuracy: float = None
    ):
        """Track model inference metrics."""
        model_inference_total.labels(model_name=model_name, status=status).inc()
        model_prediction_latency.labels(model_name=model_name).observe(duration)
        
        if accuracy is not None:
            # Assume version from environment or config
            model_accuracy_gauge.labels(
                model_name=model_name, 
                model_version="v1"
            ).set(accuracy * 100)
    
    @staticmethod
    def track_api_call(tenant_id: str, endpoint: str, tier: str, bytes_in: int, bytes_out: int):
        """Track API call metrics."""
        api_calls_by_tenant.labels(
            tenant_id=tenant_id,
            endpoint=endpoint,
            tier=tier
        ).inc()
        
        api_data_processed_bytes.labels(
            direction="inbound",
            endpoint=endpoint
        ).inc(bytes_in)
        
        api_data_processed_bytes.labels(
            direction="outbound",
            endpoint=endpoint
        ).inc(bytes_out)
    
    @staticmethod
    def track_feature_usage(feature_name: str, tier: str):
        """Track feature usage."""
        feature_usage_counter.labels(
            feature_name=feature_name,
            tier=tier
        ).inc()
    
    @staticmethod
    def track_business_error(error_type: str, severity: str):
        """Track business logic errors."""
        business_errors_total.labels(
            error_type=error_type,
            severity=severity
        ).inc()
    
    @staticmethod
    def update_cost_estimate(resource_type: str, cost_usd_hour: float):
        """Update infrastructure cost estimate."""
        compute_cost_estimate.labels(resource_type=resource_type).set(cost_usd_hour)


# Export instance
business_metrics = BusinessMetricsCollector()
