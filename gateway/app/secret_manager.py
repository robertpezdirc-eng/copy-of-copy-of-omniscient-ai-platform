"""
GCP Secret Manager integration for secure API key storage.
Fetches secrets at startup and caches them.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from cachetools import TTLCache
from google.cloud import secretmanager

from .settings import settings

logger = logging.getLogger(__name__)

# Cache secrets for 5 minutes to avoid excessive API calls
secret_cache = TTLCache(maxsize=100, ttl=300)


class SecretManagerClient:
    """Client for fetching secrets from GCP Secret Manager."""
    
    def __init__(self):
        self.client: Optional[secretmanager.SecretManagerServiceClient] = None
        self.project_id = settings.gcp_project_id
        self.enabled = settings.secret_manager_enabled and self.project_id
        
        if self.enabled:
            try:
                self.client = secretmanager.SecretManagerServiceClient()
                logger.info(f"Secret Manager client initialized for project {self.project_id}")
            except Exception as e:
                logger.error(f"Failed to initialize Secret Manager client: {e}")
                self.enabled = False
    
    def get_secret(self, secret_id: str, version: str = "latest") -> Optional[str]:
        """
        Get secret value from Secret Manager.
        
        Args:
            secret_id: Name of the secret (e.g., "api-gateway-keys")
            version: Version to fetch (default: "latest")
            
        Returns:
            Secret value as string, or None if not found/error
        """
        if not self.enabled or not self.client:
            return None
        
        # Check cache first
        cache_key = f"{secret_id}:{version}"
        if cache_key in secret_cache:
            logger.debug(f"Secret {secret_id} retrieved from cache")
            return secret_cache[cache_key]
        
        try:
            # Build the resource name
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
            
            # Access the secret version
            response = self.client.access_secret_version(request={"name": name})
            
            # Decode the secret payload
            secret_value = response.payload.data.decode("UTF-8")
            
            # Cache the secret
            secret_cache[cache_key] = secret_value
            
            logger.info(f"Secret {secret_id} fetched from Secret Manager")
            return secret_value
            
        except Exception as e:
            logger.error(f"Error fetching secret {secret_id}: {e}")
            return None
    
    def get_api_keys(self) -> List[str]:
        """
        Get API keys from Secret Manager.
        
        Expected secret format: comma-separated API keys
        Secret name: "api-gateway-keys"
        
        Returns:
            List of API keys
        """
        if not self.enabled:
            # Fallback to environment variable
            return settings.api_keys_list
        
        secret_value = self.get_secret("api-gateway-keys")
        
        if not secret_value:
            logger.warning("Failed to fetch API keys from Secret Manager, using env vars")
            return settings.api_keys_list
        
        # Parse comma-separated keys
        keys = [k.strip() for k in secret_value.split(",") if k.strip()]
        logger.info(f"Loaded {len(keys)} API keys from Secret Manager")
        return keys
    
    def get_redis_url(self) -> Optional[str]:
        """
        Get Redis connection URL from Secret Manager.
        
        Secret name: "redis-url"
        
        Returns:
            Redis URL or None
        """
        if not self.enabled:
            return settings.redis_url
        
        redis_url = self.get_secret("redis-url")
        
        if redis_url:
            logger.info("Redis URL loaded from Secret Manager")
            return redis_url
        else:
            logger.info("Redis URL not found in Secret Manager, using env var")
            return settings.redis_url
    
    def get_sentry_dsn(self) -> Optional[str]:
        """
        Get Sentry DSN from Secret Manager.
        
        Secret name: "sentry-dsn"
        
        Returns:
            Sentry DSN or None
        """
        if not self.enabled:
            return settings.sentry_dsn
        
        dsn = self.get_secret("sentry-dsn")
        
        if dsn:
            logger.info("Sentry DSN loaded from Secret Manager")
            return dsn
        else:
            return settings.sentry_dsn


# Global instance
secret_manager = SecretManagerClient()


def load_secrets_from_manager():
    """
    Load all secrets from Secret Manager at startup.
    Updates settings with fetched values.
    """
    if not secret_manager.enabled:
        logger.info("Secret Manager disabled, using environment variables")
        return
    
    logger.info("Loading secrets from GCP Secret Manager...")
    
    # Load API keys
    api_keys = secret_manager.get_api_keys()
    if api_keys:
        # Override settings
        settings.api_keys = ",".join(api_keys)
    
    # Load Redis URL
    redis_url = secret_manager.get_redis_url()
    if redis_url:
        settings.redis_url = redis_url
    
    # Load Sentry DSN
    sentry_dsn = secret_manager.get_sentry_dsn()
    if sentry_dsn:
        settings.sentry_dsn = sentry_dsn
    
    logger.info("Secrets loaded successfully")
