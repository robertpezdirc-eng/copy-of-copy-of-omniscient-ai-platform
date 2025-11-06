"""
Real-time Dashboard API Routes
Endpoints for serving real-time metrics for the new dashboard.
"""
from fastapi import APIRouter, HTTPException
from prometheus_client import REGISTRY, Counter, Histogram
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/dashboards", tags=["Real-time Dashboard"])

# --- Helper Functions to Parse Metrics ---

def parse_counter(counter: Counter):
    """Parses a Prometheus Counter into a list of dictionaries."""
    samples = []
    for sample in counter.collect()[0].samples:
        samples.append({
            "value": sample.value,
            "labels": sample.labels,
        })
    return samples

def parse_histogram(histogram: Histogram):
    """Parses a Prometheus Histogram into a structured dictionary."""
    samples = []
    # Buckets and sums are the most important for latency analysis
    for sample in histogram.collect()[0].samples:
        # We are interested in buckets and sum/count for avg calculations
        if '_bucket' in sample.name or '_sum' in sample.name or '_count' in sample.name:
            samples.append({
                "name": sample.name,
                "value": sample.value,
                "labels": sample.labels,
            })
    return samples

# --- API Endpoints ---

@router.get("/realtime-metrics")
async def get_realtime_metrics():
    """
    Provides real-time metrics for the dashboard, parsed from the Prometheus registry.
    """
    try:
        data = {
            "requests_total": [],
            "requests_latency": [],
        }

        # Find the metrics in the registry
        request_counter = REGISTRY._names_to_collectors.get('http_requests_total')
        request_latency_histogram = REGISTRY._names_to_collectors.get('http_request_duration_seconds')

        if request_counter:
            data["requests_total"] = parse_counter(request_counter)

        if request_latency_histogram:
            data["requests_latency"] = parse_histogram(request_latency_histogram)
            
        return data

    except Exception as e:
        logger.error(f"Could not fetch real-time metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch real-time metrics")

