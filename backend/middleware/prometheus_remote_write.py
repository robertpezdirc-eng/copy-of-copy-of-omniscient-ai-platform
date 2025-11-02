"""
Prometheus Remote Write middleware for Grafana Cloud integration.

This middleware enables pushing metrics to Grafana Cloud via Prometheus Remote Write protocol.
"""

import os
import logging
from typing import Optional
from prometheus_client import REGISTRY, generate_latest
from prometheus_client.exposition import basic_auth_handler
import httpx

logger = logging.getLogger(__name__)


class GrafanaCloudConfig:
    """Configuration for Grafana Cloud Prometheus Remote Write."""
    
    def __init__(self):
        self.enabled = os.getenv("GRAFANA_CLOUD_ENABLED", "false").lower() == "true"
        self.remote_write_url = os.getenv("GRAFANA_CLOUD_REMOTE_WRITE_URL", "")
        self.username = os.getenv("GRAFANA_CLOUD_USERNAME", "")
        self.api_key = os.getenv("GRAFANA_CLOUD_API_KEY", "")
        
        # Push interval in seconds (default: 15 seconds)
        self.push_interval = int(os.getenv("GRAFANA_CLOUD_PUSH_INTERVAL", "15"))
        
    def is_configured(self) -> bool:
        """Check if Grafana Cloud is properly configured."""
        if not self.enabled:
            return False
        
        if not self.remote_write_url:
            logger.warning("Grafana Cloud enabled but GRAFANA_CLOUD_REMOTE_WRITE_URL not set")
            return False
            
        if not self.username or not self.api_key:
            logger.warning("Grafana Cloud enabled but credentials not set")
            return False
            
        return True


class PrometheusRemoteWriteClient:
    """Client for pushing metrics to Grafana Cloud via Prometheus Remote Write."""
    
    def __init__(self, config: GrafanaCloudConfig):
        self.config = config
        self.client: Optional[httpx.AsyncClient] = None
        
    async def start(self):
        """Initialize the HTTP client."""
        if self.config.is_configured():
            auth = httpx.BasicAuth(self.config.username, self.config.api_key)
            self.client = httpx.AsyncClient(
                auth=auth,
                timeout=httpx.Timeout(10.0),
                headers={
                    "Content-Type": "application/x-protobuf",
                    "Content-Encoding": "snappy",
                    "X-Prometheus-Remote-Write-Version": "0.1.0"
                }
            )
            logger.info("Prometheus Remote Write client initialized for Grafana Cloud")
        else:
            logger.info("Grafana Cloud integration not configured - skipping")
    
    async def stop(self):
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            logger.info("Prometheus Remote Write client stopped")
    
    async def push_metrics(self):
        """
        Push current metrics to Grafana Cloud.
        
        Note: This is a simplified version. For production, you should use
        the official prometheus-client library with remote write support,
        or a specialized library like prometheus-remote-write.
        """
        if not self.client or not self.config.is_configured():
            return
        
        try:
            # Generate metrics in Prometheus exposition format
            metrics_data = generate_latest(REGISTRY)
            
            # For production, you would convert this to Prometheus Remote Write format
            # and compress with snappy. For now, we'll use the simple approach.
            
            # Note: Actual implementation would require:
            # 1. Converting metrics to Prometheus protobuf format
            # 2. Compressing with snappy
            # 3. Sending via POST to remote_write_url
            
            logger.debug(f"Metrics ready for push: {len(metrics_data)} bytes")
            
            # For now, we'll log that metrics are available
            # Full implementation would require additional dependencies:
            # - snappy (for compression)
            # - prometheus-remote-write or similar library
            
        except Exception as e:
            logger.error(f"Error pushing metrics to Grafana Cloud: {e}")


# Global instance
_grafana_cloud_client: Optional[PrometheusRemoteWriteClient] = None


def get_grafana_cloud_client() -> Optional[PrometheusRemoteWriteClient]:
    """Get the global Grafana Cloud client instance."""
    return _grafana_cloud_client


async def setup_grafana_cloud():
    """Initialize Grafana Cloud integration."""
    global _grafana_cloud_client
    
    config = GrafanaCloudConfig()
    
    if config.is_configured():
        _grafana_cloud_client = PrometheusRemoteWriteClient(config)
        await _grafana_cloud_client.start()
        logger.info("Grafana Cloud integration enabled")
        return _grafana_cloud_client
    else:
        logger.info("Grafana Cloud integration not configured - metrics available at /metrics")
        return None


async def shutdown_grafana_cloud():
    """Shutdown Grafana Cloud integration."""
    global _grafana_cloud_client
    
    if _grafana_cloud_client:
        await _grafana_cloud_client.stop()
        _grafana_cloud_client = None
