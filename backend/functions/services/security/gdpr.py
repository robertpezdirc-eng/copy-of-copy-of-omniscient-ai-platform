from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class GDPRService:
    """Best-effort GDPR operations.

    Real implementations must enumerate all data sources and models. This
    service clears cache-like layers and provides placeholders for datastore
    erasure/export so the integration surface exists now.
    """

    def __init__(self) -> None:
        self._consents: Dict[str, Dict[str, Any]] = {}

    async def _optional_get_redis(self):
        try:
            from ...database import get_redis as _get_redis  # type: ignore
        except Exception:
            try:
                from backend.database import get_redis as _get_redis  # type: ignore
            except Exception:
                return None
        try:
            return await _get_redis()
        except Exception:
            return None

    async def _optional_get_mongo(self):
        try:
            from ...database import get_mongodb as _get_mongodb  # type: ignore
        except Exception:
            try:
                from backend.database import get_mongodb as _get_mongodb  # type: ignore
            except Exception:
                return None
        try:
            return await _get_mongodb()
        except Exception:
            return None

    async def record_consent(self, user_id: str, consent: Dict[str, Any]) -> Dict[str, Any]:
        self._consents[user_id] = consent
        # If Redis available, persist simple record
        try:
            redis = await self._optional_get_redis()
            if redis:
                await redis.hset(f"consent:{user_id}", mapping={k: str(v) for k, v in consent.items()})
        except Exception as exc:  # pragma: no cover - non-critical
            logger.warning("Consent Redis persist failed: %s", exc)
        return {"ok": True, "consent": consent}

    async def get_consent(self, user_id: str) -> Dict[str, Any]:
        if user_id in self._consents:
            return {"ok": True, "consent": self._consents[user_id]}
        try:
            redis = await self._optional_get_redis()
            if redis:
                data = await redis.hgetall(f"consent:{user_id}")
                if data:
                    return {"ok": True, "consent": data}
        except Exception:
            pass
        return {"ok": False, "consent": None}

    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        # Placeholder: attempt to fetch some data from Mongo if available
        export: Dict[str, Any] = {"user_id": user_id, "sources": {}}
        try:
            mongo = await self._optional_get_mongo()
            if mongo is not None:
                # Example: pretend there is a users collection
                doc = await mongo["users"].find_one({"user_id": user_id})
                if doc:
                    export["sources"]["mongodb.users"] = doc
        except Exception as exc:  # pragma: no cover - optional
            logger.warning("Mongo export failed: %s", exc)
        # Include consent snapshot
        export["consent"] = (await self.get_consent(user_id)).get("consent")
        return export

    async def erase_user_data(self, user_id: str) -> Dict[str, Any]:
        """Best-effort erasure.
        Clears caches and deletes example records in Mongo if present.
        Returns a report of actions taken.
        """
        report: Dict[str, Any] = {"user_id": user_id, "actions": []}
        # Clear Redis keys
        try:
            redis = await self._optional_get_redis()
            if redis:
                deleted = 0
                for pattern in [f"sess:{user_id}:*", f"cache:user:{user_id}:*", f"consent:{user_id}"]:
                    keys = await redis.keys(pattern)
                    if keys:
                        deleted += await redis.delete(*keys)
                report["actions"].append({"redis_deleted": deleted})
        except Exception as exc:  # pragma: no cover - optional
            report["actions"].append({"redis_error": str(exc)})
        # Delete example docs in Mongo
        try:
            mongo = await self._optional_get_mongo()
            if mongo is not None:
                res = await mongo["users"].delete_many({"user_id": user_id})
                report["actions"].append({"mongodb_users_deleted": res.deleted_count})
        except Exception as exc:  # pragma: no cover - optional
            report["actions"].append({"mongodb_error": str(exc)})
        # Remove in-memory consent
        self._consents.pop(user_id, None)
        return report


_gdpr_singleton: Optional[GDPRService] = None


def get_gdpr_service() -> GDPRService:
    global _gdpr_singleton
    if _gdpr_singleton is None:
        _gdpr_singleton = GDPRService()
        
    return _gdpr_singleton
