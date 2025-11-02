from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request, status
from .settings import settings


def verify_api_key(request: Request, x_api_key: str | None = Header(default=None)) -> None:
    keys = settings.api_keys_list
    if not keys:
        # No keys configured, treat as open (useful for internal dev)
        request.state.tenant_id = "default"
        request.state.tier = "free"
        return
    if not x_api_key or x_api_key not in keys:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
    
    # Extract tenant info from API key (format: {plan}-key-{tenant}-{year})
    # Example: prod-key-omni-2025 -> plan=prod, tenant=omni
    parts = x_api_key.split("-")
    if len(parts) >= 3:
        plan = parts[0].lower()
        # Map plan -> rate limit tier
        plan_to_tier = {
            "free": "free",
            "basic": "basic",
            "premium": "premium",
            "prod": "premium",
            "master": "master",
        }
        request.state.tier = plan_to_tier.get(plan, "free")
        request.state.tenant_id = parts[2] if len(parts) > 2 else "unknown"
    else:
        request.state.tier = "free"
        request.state.tenant_id = "unknown"
