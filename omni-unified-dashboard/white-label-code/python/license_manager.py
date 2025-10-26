from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

TIERS = {
    "free": {"features": ["basic"], "requests_per_day": 100},
    "pro": {"features": ["basic", "advanced"], "requests_per_day": 1000, "price": 99},
    "enterprise": {"features": ["basic", "advanced", "enterprise"], "requests_per_day": 10000, "price": 499},
}

@dataclass
class License:
    key: str
    tier: str
    issued_at: datetime
    expires_at: datetime
    tenant_id: Optional[str] = None

class LicenseManager:
    def __init__(self):
        self._store: Dict[str, License] = {}

    def issue_demo(self, tier: str = "pro", days: int = 14, tenant_id: Optional[str] = None) -> License:
        now = datetime.utcnow()
        lic = License(key=f"DEMO-{now.timestamp()}", tier=tier, issued_at=now, expires_at=now + timedelta(days=days), tenant_id=tenant_id)
        self._store[lic.key] = lic
        return lic

    def validate(self, key: str) -> bool:
        lic = self._store.get(key)
        return bool(lic and lic.expires_at > datetime.utcnow())

    def feature_access(self, key: str, feature: str) -> bool:
        lic = self._store.get(key)
        if not lic or lic.expires_at <= datetime.utcnow():
            return False
        return feature in TIERS.get(lic.tier, {}).get("features", [])

    def remaining_days(self, key: str) -> int:
        lic = self._store.get(key)
        if not lic:
            return 0
        delta = lic.expires_at - datetime.utcnow()
        return max(0, delta.days)