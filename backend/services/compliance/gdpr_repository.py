import logging
from datetime import datetime
from typing import Any, Dict, Optional

from database import SessionLocal, mongodb_db
from models.gdpr import ConsentRecordModel, AuditEventModel, ProcessingActivityModel

logger = logging.getLogger(__name__)


# Import health monitoring
try:
    from services.compliance.gdpr_health import get_persistence_metrics
    _health_monitoring_available = True
except ImportError:
    _health_monitoring_available = False
    logger.warning("GDPR health monitoring not available")


class GDPRRepository:
    """Abstract persistence layer for GDPR operations."""

    def save_consent(self, record: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def get_consent(self, user_id: str, consent_type: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def withdraw_consent(self, user_id: str, consent_type: str) -> Dict[str, Any]:
        raise NotImplementedError

    def list_consents_for_user(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        raise NotImplementedError

    def log_audit(self, action: str, user_id: str, details: Dict[str, Any]) -> None:
        raise NotImplementedError

    def record_processing_activity(self, activity: Dict[str, Any]) -> str:
        raise NotImplementedError

    def count_unique_consent_users(self) -> int:
        """Count unique users with consent records"""
        raise NotImplementedError

    def count_audit_events(self) -> int:
        """Count total audit events"""
        raise NotImplementedError

    def count_processing_activities(self) -> int:
        """Count total processing activities"""
        raise NotImplementedError


class PostgresGDPRRepository(GDPRRepository):
    def save_consent(self, record: Dict[str, Any]) -> Dict[str, Any]:
        with SessionLocal() as session:
            # Upsert by (user_id, consent_type)
            existing = (
                session.query(ConsentRecordModel)
                .filter(
                    ConsentRecordModel.user_id == record["user_id"],
                    ConsentRecordModel.consent_type == str(record["consent_type"]),
                )
                .one_or_none()
            )
            if existing is None:
                obj = ConsentRecordModel(
                    user_id=record["user_id"],
                    consent_type=str(record["consent_type"]),
                    granted=bool(record["granted"]),
                    purpose=record.get("purpose"),
                    ip_address=record.get("ip_address"),
                    metadata=record.get("metadata") or {},
                    timestamp=datetime.fromisoformat(record["timestamp"]) if isinstance(record.get("timestamp"), str) else record.get("timestamp", datetime.utcnow()),
                    withdrawn_at=datetime.fromisoformat(record["withdrawn_at"]) if isinstance(record.get("withdrawn_at"), str) and record.get("withdrawn_at") else None,
                )
                session.add(obj)
                session.commit()
                session.refresh(obj)
                record["consent_id"] = obj.id
            else:
                existing.granted = bool(record["granted"])
                existing.purpose = record.get("purpose")
                existing.ip_address = record.get("ip_address")
                existing.metadata = record.get("metadata") or {}
                existing.timestamp = datetime.fromisoformat(record["timestamp"]) if isinstance(record.get("timestamp"), str) else datetime.utcnow()
                existing.withdrawn_at = datetime.fromisoformat(record["withdrawn_at"]) if isinstance(record.get("withdrawn_at"), str) and record.get("withdrawn_at") else None
                session.commit()
                record["consent_id"] = existing.id
        return record

    def get_consent(self, user_id: str, consent_type: str) -> Optional[Dict[str, Any]]:
        with SessionLocal() as session:
            obj = (
                session.query(ConsentRecordModel)
                .filter(
                    ConsentRecordModel.user_id == user_id,
                    ConsentRecordModel.consent_type == str(consent_type),
                )
                .one_or_none()
            )
            if not obj:
                return None
            return {
                "consent_id": obj.id,
                "user_id": obj.user_id,
                "consent_type": obj.consent_type,
                "granted": obj.granted,
                "purpose": obj.purpose,
                "timestamp": obj.timestamp.isoformat(),
                "ip_address": obj.ip_address,
                "metadata": obj.metadata or {},
                "withdrawn_at": obj.withdrawn_at.isoformat() if obj.withdrawn_at else None,
            }

    def withdraw_consent(self, user_id: str, consent_type: str) -> Dict[str, Any]:
        with SessionLocal() as session:
            obj = (
                session.query(ConsentRecordModel)
                .filter(
                    ConsentRecordModel.user_id == user_id,
                    ConsentRecordModel.consent_type == str(consent_type),
                )
                .one_or_none()
            )
            if not obj:
                raise ValueError(f"No {consent_type} consent for user {user_id}")
            obj.granted = False
            obj.withdrawn_at = datetime.utcnow()
            session.commit()
            return {
                "consent_id": obj.id,
                "user_id": obj.user_id,
                "consent_type": obj.consent_type,
                "granted": obj.granted,
                "purpose": obj.purpose,
                "timestamp": obj.timestamp.isoformat(),
                "ip_address": obj.ip_address,
                "metadata": obj.metadata or {},
                "withdrawn_at": obj.withdrawn_at.isoformat() if obj.withdrawn_at else None,
            }

    def list_consents_for_user(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        with SessionLocal() as session:
            rows = (
                session.query(ConsentRecordModel)
                .filter(ConsentRecordModel.user_id == user_id)
                .all()
            )
            out: Dict[str, Dict[str, Any]] = {}
            for r in rows:
                out[r.consent_type] = {
                    "consent_id": r.id,
                    "user_id": r.user_id,
                    "consent_type": r.consent_type,
                    "granted": r.granted,
                    "purpose": r.purpose,
                    "timestamp": r.timestamp.isoformat(),
                    "ip_address": r.ip_address,
                    "metadata": r.metadata or {},
                    "withdrawn_at": r.withdrawn_at.isoformat() if r.withdrawn_at else None,
                }
            return out

    def log_audit(self, action: str, user_id: str, details: Dict[str, Any]) -> None:
        with SessionLocal() as session:
            session.add(
                AuditEventModel(
                    action=action,
                    user_id=user_id,
                    details=details,
                )
            )
            session.commit()

    def record_processing_activity(self, activity: Dict[str, Any]) -> str:
        with SessionLocal() as session:
            obj = ProcessingActivityModel(
                name=activity["name"],
                purpose=activity["purpose"],
                legal_basis=str(activity["legal_basis"]),
                data_categories=activity.get("data_categories", []),
                recipients=activity.get("recipients", []),
                retention_period=activity.get("retention_period", ""),
                security_measures=activity.get("security_measures", []),
            )
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj.id

    def count_unique_consent_users(self) -> int:
        with SessionLocal() as session:
            from sqlalchemy import func
            return session.query(func.count(func.distinct(ConsentRecordModel.user_id))).scalar() or 0

    def count_audit_events(self) -> int:
        with SessionLocal() as session:
            return session.query(AuditEventModel).count()

    def count_processing_activities(self) -> int:
        with SessionLocal() as session:
            return session.query(ProcessingActivityModel).count()


class MongoGDPRRepository(GDPRRepository):
    def __init__(self):
        if mongodb_db is None:
            raise RuntimeError("MongoDB not initialized")
        self._consents = mongodb_db.get_collection("gdpr_consents")
        self._audits = mongodb_db.get_collection("gdpr_audits")
        self._activities = mongodb_db.get_collection("gdpr_processing_activities")
        # Indexes
        try:
            self._consents.create_index([("user_id", 1), ("consent_type", 1)], unique=True)
        except Exception as e:
            logger.warning(f"Mongo index creation warning: {e}")

    def save_consent(self, record: Dict[str, Any]) -> Dict[str, Any]:
        self._consents.update_one(
            {"user_id": record["user_id"], "consent_type": str(record["consent_type"])},
            {"$set": record},
            upsert=True,
        )
        return record

    def get_consent(self, user_id: str, consent_type: str) -> Optional[Dict[str, Any]]:
        return self._consents.find_one({"user_id": user_id, "consent_type": str(consent_type)}, {"_id": 0})

    def withdraw_consent(self, user_id: str, consent_type: str) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        res = self._consents.find_one_and_update(
            {"user_id": user_id, "consent_type": str(consent_type)},
            {"$set": {"granted": False, "withdrawn_at": now}},
            return_document=True,
        )
        if not res:
            raise ValueError(f"No {consent_type} consent for user {user_id}")
        res.pop("_id", None)
        return res

    def list_consents_for_user(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for r in self._consents.find({"user_id": user_id}, {"_id": 0}):
            out[str(r["consent_type"])]=r
        return out

    def log_audit(self, action: str, user_id: str, details: Dict[str, Any]) -> None:
        self._audits.insert_one({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user_id": user_id,
            "details": details,
        })

    def record_processing_activity(self, activity: Dict[str, Any]) -> str:
        doc = {
            **activity,
            "created_at": datetime.utcnow().isoformat(),
        }
        res = self._activities.insert_one(doc)
        return str(res.inserted_id)

    def count_unique_consent_users(self) -> int:
        return len(self._consents.distinct("user_id"))

    def count_audit_events(self) -> int:
        return self._audits.count_documents({})

    def count_processing_activities(self) -> int:
        return self._activities.count_documents({})


class InMemoryGDPRRepository(GDPRRepository):
    def __init__(self):
        self._consents: Dict[str, Dict[str, Any]] = {}
        self._audits: list[Dict[str, Any]] = []

    def save_consent(self, record: Dict[str, Any]) -> Dict[str, Any]:
        self._consents.setdefault(record["user_id"], {})[str(record["consent_type"])] = record
        return record

    def get_consent(self, user_id: str, consent_type: str) -> Optional[Dict[str, Any]]:
        return self._consents.get(user_id, {}).get(str(consent_type))

    def withdraw_consent(self, user_id: str, consent_type: str) -> Dict[str, Any]:
        rec = self.get_consent(user_id, consent_type)
        if not rec:
            raise ValueError(f"No {consent_type} consent for user {user_id}")
        rec["granted"] = False
        rec["withdrawn_at"] = datetime.utcnow().isoformat()
        return rec

    def list_consents_for_user(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        return self._consents.get(user_id, {})

    def log_audit(self, action: str, user_id: str, details: Dict[str, Any]) -> None:
        self._audits.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user_id": user_id,
            "details": details,
        })

    def record_processing_activity(self, activity: Dict[str, Any]) -> str:
        # In-memory: return synthetic id
        return f"mem-{int(datetime.utcnow().timestamp())}"

    def count_unique_consent_users(self) -> int:
        return len(self._consents)

    def count_audit_events(self) -> int:
        return len(self._audits)

    def count_processing_activities(self) -> int:
        # In-memory doesn't track processing activities separately
        return 0


def get_best_available_repository() -> GDPRRepository:
    """Pick Postgres if available, else Mongo if configured, else in-memory."""
    metrics = get_persistence_metrics() if _health_monitoring_available else None
    
    # Try PostgreSQL first
    try:
        # Try quick connection by opening/closing session
        with SessionLocal() as _:
            pass
        logger.info("GDPRRepository: using Postgres")
        if metrics:
            metrics.current_repository_type = "PostgresGDPRRepository"
        return PostgresGDPRRepository()
    except Exception as e:
        logger.warning(f"GDPRRepository Postgres unavailable: {e}")
        if metrics:
            metrics.record_repository_fallback(
                "PostgresGDPRRepository",
                "attempting MongoDB",
                str(e)
            )

    # Try MongoDB as fallback
    try:
        if mongodb_db is not None:
            logger.info("GDPRRepository: using MongoDB")
            if metrics:
                metrics.current_repository_type = "MongoGDPRRepository"
            return MongoGDPRRepository()
    except Exception as e:
        logger.warning(f"GDPRRepository Mongo unavailable: {e}")
        if metrics:
            metrics.record_repository_fallback(
                "MongoGDPRRepository",
                "InMemoryGDPRRepository",
                str(e)
            )

    # Final fallback to in-memory (data loss risk!)
    logger.error(
        "⚠️  CRITICAL: Using in-memory GDPR repository. "
        "User consents and audit logs will NOT persist across restarts!"
    )
    if metrics:
        metrics.current_repository_type = "InMemoryGDPRRepository"
        metrics.record_repository_fallback(
            "PostgresGDPRRepository/MongoGDPRRepository",
            "InMemoryGDPRRepository",
            "All persistent databases unavailable"
        )
    
    return InMemoryGDPRRepository()
