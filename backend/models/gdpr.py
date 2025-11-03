import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, JSON, String, UniqueConstraint

from backend.database import Base


class ConsentRecordModel(Base):
    __tablename__ = "gdpr_consent_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, index=True)
    consent_type = Column(String(64), nullable=False, index=True)
    granted = Column(Boolean, nullable=False, default=True)
    purpose = Column(String(512), nullable=True)
    ip_address = Column(String(64), nullable=True)
    metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    withdrawn_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "consent_type", name="uq_user_consent_type"),
        Index("ix_consent_user_type", "user_id", "consent_type"),
    )


class AuditEventModel(Base):
    __tablename__ = "gdpr_audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    action = Column(String(128), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    details = Column(JSON, nullable=True)


class ProcessingActivityModel(Base):
    __tablename__ = "gdpr_processing_activities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    purpose = Column(String(512), nullable=False)
    legal_basis = Column(String(64), nullable=False)
    data_categories = Column(JSON, nullable=False, default=list)
    recipients = Column(JSON, nullable=False, default=list)
    retention_period = Column(String(128), nullable=False)
    security_measures = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
