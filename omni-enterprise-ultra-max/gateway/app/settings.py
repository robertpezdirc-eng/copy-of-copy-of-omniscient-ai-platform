from __future__ import annotations

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter=None)

    # Core
    service_name: str = "ai-gateway"
    environment: str = "dev"

    # Upstream ML Worker
    upstream_url: str = "http://localhost:9000"  # default for local dev; override via env UPSTREAM_URL

    # Security
    api_keys: str = ""  # Comma-separated string; env var API_KEYS
    
    # OpenAI API Key (for AI services)
    openai_api_key: Optional[str] = None  # OpenAI API key; env var OPENAI_API_KEY

    # Redis (for rate limiting and caching)
    redis_url: Optional[str] = None  # redis://host:port/db or redis://host:port

    # Networking
    connect_timeout: float = 5.0
    request_timeout: float = 60.0

    # Observability
    enable_metrics: bool = True
    sentry_dsn: Optional[str] = None
    
    # Tracing
    jaeger_host: Optional[str] = None
    jaeger_port: int = 6831
    enable_tracing: bool = False
    
    # GCP
    gcp_project_id: Optional[str] = None
    secret_manager_enabled: bool = False

    @property
    def api_keys_list(self) -> List[str]:
        """Return API keys as a list, split from comma-separated string."""
        if not self.api_keys:
            return []
        return [s.strip() for s in self.api_keys.split(",") if s.strip()]


settings = Settings()  # loaded at import time; lightweight
