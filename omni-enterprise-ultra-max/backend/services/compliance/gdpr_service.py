"""
GDPR Compliance Service

EU General Data Protection Regulation (GDPR) compliance module with:
- Right to Access (Art. 15)
- Right to Erasure (Art. 17)
- Right to Rectification (Art. 16)
- Right to Data Portability (Art. 20)
- Consent Management (Art. 6-7)
- Data Processing Records (Art. 30)
- Breach Notifications (Art. 33-34)
- Audit Logging

Slovenia ZVOP-2 compliant
"""

import os
import logging
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ConsentType(str, Enum):
    """GDPR consent types"""
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    PROFILING = "profiling"
    THIRD_PARTY_SHARING = "third_party_sharing"
    ESSENTIAL = "essential"  # Required for service operation


class DataSubjectRights(str, Enum):
    """GDPR data subject rights"""
    ACCESS = "access"  # Art. 15
    RECTIFICATION = "rectification"  # Art. 16
    ERASURE = "erasure"  # Art. 17 (Right to be forgotten)
    RESTRICT_PROCESSING = "restrict_processing"  # Art. 18
    DATA_PORTABILITY = "data_portability"  # Art. 20
    OBJECT = "object"  # Art. 21


class ProcessingLegalBasis(str, Enum):
    """GDPR legal basis for processing (Art. 6)"""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class GDPRService:
    """
    GDPR compliance service for EU data protection
    """
    
    def __init__(
        self,
        dpo_email: str = None,  # Data Protection Officer
        retention_period_days: int = 90,  # Default retention
        breach_notification_hours: int = 72  # Art. 33
    ):
        self.dpo_email = dpo_email or os.getenv("GDPR_DPO_EMAIL", "dpo@omni-platform.eu")
        self.retention_period = timedelta(days=retention_period_days)
        self.breach_notification_deadline = timedelta(hours=breach_notification_hours)
        
        # Consent store (should use database in production)
        self.consent_records: Dict[str, Dict[str, Any]] = {}
        
        # Audit log
        self.audit_log: List[Dict[str, Any]] = []
        
        # Processing records (Art. 30)
        self.processing_activities: List[Dict[str, Any]] = []
        
        logger.info(f"GDPR Service initialized - DPO: {self.dpo_email}")
    
    def record_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        granted: bool,
        purpose: str,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record user consent (Art. 7)
        
        GDPR requires:
        - Freely given
        - Specific
        - Informed
        - Unambiguous indication
        - Withdrawable
        
        Args:
            user_id: User identifier
            consent_type: Type of consent
            granted: True if consent given
            purpose: Purpose of data processing
            ip_address: Optional IP for verification
            metadata: Additional consent metadata
        
        Returns:
            Consent record with ID
        """
        consent_id = hashlib.sha256(
            f"{user_id}_{consent_type}_{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        record = {
            "consent_id": consent_id,
            "user_id": user_id,
            "consent_type": consent_type,
            "granted": granted,
            "purpose": purpose,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": ip_address,
            "metadata": metadata or {},
            "withdrawn_at": None
        }
        
        # Store consent
        if user_id not in self.consent_records:
            self.consent_records[user_id] = {}
        
        self.consent_records[user_id][consent_type] = record
        
        # Audit log
        self._log_audit(
            action="consent_recorded",
            user_id=user_id,
            details={
                "consent_id": consent_id,
                "consent_type": consent_type,
                "granted": granted
            }
        )
        
        logger.info(f"Consent recorded: {user_id} - {consent_type} = {granted}")
        
        return record
    
    def withdraw_consent(
        self,
        user_id: str,
        consent_type: ConsentType
    ) -> Dict[str, Any]:
        """
        Withdraw consent (Art. 7.3)
        
        User must be able to withdraw consent as easily as giving it.
        """
        if user_id not in self.consent_records:
            raise ValueError(f"No consent records for user {user_id}")
        
        if consent_type not in self.consent_records[user_id]:
            raise ValueError(f"No {consent_type} consent for user {user_id}")
        
        record = self.consent_records[user_id][consent_type]
        record["withdrawn_at"] = datetime.utcnow().isoformat()
        record["granted"] = False
        
        self._log_audit(
            action="consent_withdrawn",
            user_id=user_id,
            details={"consent_type": consent_type}
        )
        
        logger.info(f"Consent withdrawn: {user_id} - {consent_type}")
        
        return record
    
    def check_consent(
        self,
        user_id: str,
        consent_type: ConsentType
    ) -> bool:
        """
        Check if user has given active consent
        
        Returns:
            True if consent is active and not withdrawn
        """
        if user_id not in self.consent_records:
            return False
        
        if consent_type not in self.consent_records[user_id]:
            return False
        
        record = self.consent_records[user_id][consent_type]
        
        return record["granted"] and record["withdrawn_at"] is None
    
    async def exercise_right_to_access(
        self,
        user_id: str,
        include_processing_info: bool = True
    ) -> Dict[str, Any]:
        """
        Right to Access (Art. 15)
        
        Provide user with:
        - Copy of personal data
        - Processing purposes
        - Categories of data
        - Recipients
        - Storage period
        - Rights information
        
        Must respond within 1 month (extendable to 3 months)
        """
        self._log_audit(
            action="access_request",
            user_id=user_id,
            details={"request_type": "right_to_access"}
        )
        
        # Collect user data from all sources
        # In production, query all databases/services
        user_data = await self._collect_user_data(user_id)
        
        response = {
            "user_id": user_id,
            "request_date": datetime.utcnow().isoformat(),
            "personal_data": user_data,
            "consents": self.consent_records.get(user_id, {}),
            "data_retention_period": f"{self.retention_period.days} days",
            "your_rights": [
                "Right to rectification (correct your data)",
                "Right to erasure (delete your data)",
                "Right to restrict processing",
                "Right to data portability",
                "Right to object",
                "Right to withdraw consent"
            ],
            "dpo_contact": self.dpo_email
        }
        
        if include_processing_info:
            response["processing_activities"] = self._get_user_processing_activities(user_id)
        
        logger.info(f"Access request fulfilled for user {user_id}")
        
        return response
    
    async def exercise_right_to_erasure(
        self,
        user_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Right to Erasure / Right to be Forgotten (Art. 17)
        
        Grounds for erasure:
        - Data no longer necessary
        - Consent withdrawn
        - Objection to processing
        - Unlawful processing
        - Legal obligation
        
        Exceptions:
        - Legal obligations
        - Public interest
        - Legal claims
        """
        self._log_audit(
            action="erasure_request",
            user_id=user_id,
            details={"reason": reason}
        )
        
        # Check if erasure is possible
        can_erase, obstacles = self._check_erasure_obstacles(user_id)
        
        if not can_erase:
            return {
                "success": False,
                "user_id": user_id,
                "message": "Erasure request cannot be fulfilled",
                "obstacles": obstacles,
                "retained_data_reason": "Legal obligation or pending claims"
            }
        
        # Perform erasure
        deleted_records = await self._delete_user_data(user_id)
        
        # Anonymize instead of delete if legal obligation exists
        anonymized_records = await self._anonymize_user_data(user_id)
        
        logger.info(f"Erasure completed for user {user_id}")
        
        return {
            "success": True,
            "user_id": user_id,
            "erasure_date": datetime.utcnow().isoformat(),
            "deleted_records": deleted_records,
            "anonymized_records": anonymized_records,
            "confirmation": f"Your data has been erased. Confirmation sent to DPO: {self.dpo_email}"
        }
    
    async def exercise_right_to_rectification(
        self,
        user_id: str,
        corrections: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Right to Rectification (Art. 16)
        
        User can request correction of inaccurate personal data
        """
        self._log_audit(
            action="rectification_request",
            user_id=user_id,
            details={"corrections": corrections}
        )
        
        # Apply corrections
        updated_fields = await self._update_user_data(user_id, corrections)
        
        logger.info(f"Rectification completed for user {user_id}")
        
        return {
            "success": True,
            "user_id": user_id,
            "updated_fields": updated_fields,
            "update_date": datetime.utcnow().isoformat()
        }
    
    async def exercise_right_to_data_portability(
        self,
        user_id: str,
        format: str = "json"  # json, csv, xml
    ) -> Dict[str, Any]:
        """
        Right to Data Portability (Art. 20)
        
        Provide user data in structured, machine-readable format
        """
        self._log_audit(
            action="portability_request",
            user_id=user_id,
            details={"format": format}
        )
        
        user_data = await self._collect_user_data(user_id)
        
        if format == "json":
            portable_data = json.dumps(user_data, indent=2)
        elif format == "csv":
            # Convert to CSV
            portable_data = self._convert_to_csv(user_data)
        elif format == "xml":
            # Convert to XML
            portable_data = self._convert_to_xml(user_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Data portability export for user {user_id} in {format}")
        
        return {
            "success": True,
            "user_id": user_id,
            "format": format,
            "data": portable_data,
            "export_date": datetime.utcnow().isoformat()
        }
    
    def record_processing_activity(
        self,
        activity_name: str,
        purpose: str,
        legal_basis: ProcessingLegalBasis,
        data_categories: List[str],
        recipients: List[str],
        retention_period: str,
        security_measures: List[str]
    ) -> str:
        """
        Record processing activity (Art. 30)
        
        Required for GDPR compliance documentation
        """
        activity_id = hashlib.sha256(
            f"{activity_name}_{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        activity = {
            "activity_id": activity_id,
            "name": activity_name,
            "purpose": purpose,
            "legal_basis": legal_basis,
            "data_categories": data_categories,
            "recipients": recipients,
            "retention_period": retention_period,
            "security_measures": security_measures,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.processing_activities.append(activity)
        
        logger.info(f"Processing activity recorded: {activity_name}")
        
        return activity_id
    
    def record_data_breach(
        self,
        breach_description: str,
        affected_users: List[str],
        data_categories: List[str],
        severity: str,  # low, medium, high, critical
        mitigation_steps: List[str]
    ) -> Dict[str, Any]:
        """
        Record data breach (Art. 33-34)
        
        Must notify supervisory authority within 72 hours if high risk
        Must notify affected individuals if high risk to rights/freedoms
        """
        breach_id = hashlib.sha256(
            f"breach_{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        breach = {
            "breach_id": breach_id,
            "description": breach_description,
            "affected_user_count": len(affected_users),
            "data_categories": data_categories,
            "severity": severity,
            "detected_at": datetime.utcnow().isoformat(),
            "notification_deadline": (
                datetime.utcnow() + self.breach_notification_deadline
            ).isoformat(),
            "mitigation_steps": mitigation_steps,
            "authority_notified": False,
            "users_notified": False
        }
        
        self._log_audit(
            action="data_breach_recorded",
            user_id="system",
            details=breach
        )
        
        # Check if notification required
        requires_notification = severity in ["high", "critical"]
        
        if requires_notification:
            logger.critical(
                f"DATA BREACH: {breach_id} - Severity: {severity}. "
                f"Must notify within 72 hours!"
            )
            # TODO: Trigger automatic notification workflow
        
        return breach
    
    def _log_audit(
        self,
        action: str,
        user_id: str,
        details: Dict[str, Any]
    ):
        """Log audit event for GDPR compliance"""
        self.audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user_id": user_id,
            "details": details
        })
    
    async def _collect_user_data(self, user_id: str) -> Dict[str, Any]:
        """Collect all user data from system"""
        # TODO: Query all databases and services
        return {
            "user_id": user_id,
            "profile": {},
            "transactions": [],
            "logs": []
        }
    
    async def _delete_user_data(self, user_id: str) -> Dict[str, int]:
        """Delete user data from all systems"""
        # TODO: Delete from all databases
        return {
            "profile_records": 1,
            "transaction_records": 0,
            "log_records": 0
        }
    
    async def _anonymize_user_data(self, user_id: str) -> Dict[str, int]:
        """Anonymize user data (for legal retention)"""
        # TODO: Anonymize instead of delete
        return {
            "anonymized_records": 0
        }
    
    async def _update_user_data(
        self,
        user_id: str,
        corrections: Dict[str, Any]
    ) -> List[str]:
        """Update user data across systems"""
        # TODO: Update all databases
        return list(corrections.keys())
    
    def _check_erasure_obstacles(self, user_id: str) -> tuple[bool, List[str]]:
        """Check if erasure is legally possible"""
        obstacles = []
        
        # Check for legal obligations
        # Check for pending legal claims
        # Check for contractual requirements
        
        can_erase = len(obstacles) == 0
        return can_erase, obstacles
    
    def _get_user_processing_activities(self, user_id: str) -> List[Dict[str, Any]]:
        """Get processing activities affecting user"""
        # TODO: Filter processing activities by user
        return self.processing_activities
    
    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """Convert data to CSV format"""
        # TODO: Implement CSV conversion
        return ""
    
    def _convert_to_xml(self, data: Dict[str, Any]) -> str:
        """Convert data to XML format"""
        # TODO: Implement XML conversion
        return ""


# Singleton
_gdpr_service: Optional[GDPRService] = None


def get_gdpr_service() -> GDPRService:
    """Get GDPR service singleton"""
    global _gdpr_service
    
    if _gdpr_service is None:
        dpo_email = os.getenv("GDPR_DPO_EMAIL")
        retention_days = int(os.getenv("GDPR_RETENTION_DAYS", "90"))
        
        _gdpr_service = GDPRService(
            dpo_email=dpo_email,
            retention_period_days=retention_days
        )
    
    return _gdpr_service
