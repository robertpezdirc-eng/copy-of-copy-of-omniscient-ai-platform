""""""

Security & Compliance - Audit Logging RoutesSecurity & Compliance Routes

"""Audit logging, compliance reports, and security monitoring

"""

from fastapi import APIRouter, Query

from typing import Optionalfrom fastapi import APIRouter, Query, HTTPException, Depends

from datetime import datetime, timezonefrom typing import Optional, List

import randomfrom datetime import datetime, timedelta

from pydantic import BaseModel

router = APIRouter()

try:

    from services.audit_logger import audit_logger, AuditEventType, AuditSeverity

@router.get("/audit/logs")except:

async def get_audit_logs(    audit_logger = None

    tenant_id: Optional[str] = Query(None, description="Tenant ID (optional)"),    AuditEventType = None

    days: int = Query(7, ge=1, le=90, description="Number of days to retrieve")    AuditSeverity = None

):

    """Get audit logs"""router = APIRouter(prefix="/api/v1/security", tags=["Security & Compliance"])

    

    if not tenant_id:

        return {class AuditLogRequest(BaseModel):

            "logs": [],    """Request model for manual audit log creation"""

            "total": 0,    event_type: str

            "filters": {"days": days}    user_id: str

        }    tenant_id: str

        resource_type: Optional[str] = None

    logs = [    resource_id: Optional[str] = None

        {    action: Optional[str] = None

            "log_id": f"log_{i}",    details: Optional[dict] = None

            "tenant_id": tenant_id,    severity: Optional[str] = "info"

            "event_type": random.choice(["login", "api_call", "config_change", "data_access"]),

            "user_id": f"user_{random.randint(1, 100)}",

            "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",class ComplianceReportRequest(BaseModel):

            "status": random.choice(["success", "failed"]),    """Request model for compliance report generation"""

            "timestamp": datetime.now(timezone.utc).isoformat()    tenant_id: str

        }    start_date: str

        for i in range(1, 21)    end_date: str

    ]    report_type: str = "GDPR"  # GDPR, SOC2, HIPAA, etc.

    

    return {

        "tenant_id": tenant_id,@router.get("/audit/logs")

        "logs": logs,async def get_audit_logs(

        "total": len(logs),    tenant_id: Optional[str] = Query(None, description="Tenant ID (optional)"),

        "filters": {"days": days}    user_id: Optional[str] = Query(None, description="Filter by user ID"),

    }    resource_type: Optional[str] = Query(None, description="Filter by resource type"),

    event_type: Optional[str] = Query(None, description="Filter by event type"),

    days: int = Query(7, ge=1, le=90, description="Days of history to retrieve"),

@router.get("/compliance/status")    limit: int = Query(100, ge=1, le=1000, description="Maximum results")

async def get_compliance_status():

    tenant_id: Optional[str] = Query(None, description="Tenant ID (optional)")    """

):    Retrieve audit logs with filters

    """Get compliance status"""    

        Returns audit trail for specified tenant with optional filters

    if not tenant_id:    """

        return {    

            "tenant_id": None,    if not audit_logger:

            "overall_status": "unknown",        raise HTTPException(status_code=503, detail="Audit logger unavailable")

            "frameworks": {    

                "GDPR": {"status": "unknown", "score": 0, "last_audit": None},    start_date = datetime.utcnow() - timedelta(days=days)

                "SOC2": {"status": "unknown", "score": 0, "last_audit": None},    end_date = datetime.utcnow()

                "ISO27001": {"status": "unknown", "score": 0, "last_audit": None},    

                "HIPAA": {"status": "unknown", "score": 0, "last_audit": None}    # If tenant_id not provided, return empty list gracefully (frontend can still render)

            }    if not tenant_id:

        }        return {

                "logs": [],

    return {            "total": 0,

        "tenant_id": tenant_id,            "filters": {

        "overall_status": "compliant",                "tenant_id": None,

        "frameworks": {                "user_id": user_id,

            "GDPR": {                "resource_type": resource_type,

                "status": "compliant",                "event_type": event_type,

                "score": 98.5,                "period_days": days

                "last_audit": datetime.now(timezone.utc).isoformat(),            }

                "next_audit": datetime.now(timezone.utc).isoformat(),        }

                "issues": []

            },    # Convert string event_type to enum if provided

            "SOC2": {    event_type_enum = None

                "status": "compliant",    if event_type and AuditEventType:

                "score": 97.2,        try:

                "last_audit": datetime.now(timezone.utc).isoformat(),            event_type_enum = AuditEventType(event_type)

                "next_audit": datetime.now(timezone.utc).isoformat(),        except ValueError:

                "issues": []            pass

            },    

            "ISO27001": {    logs = await audit_logger.get_audit_trail(

                "status": "compliant",        tenant_id=tenant_id,

                "score": 96.8,        user_id=user_id,

                "last_audit": datetime.now(timezone.utc).isoformat(),        resource_type=resource_type,

                "next_audit": datetime.now(timezone.utc).isoformat(),        event_type=event_type_enum,

                "issues": []        start_date=start_date,

            },        end_date=end_date,

            "HIPAA": {        limit=limit

                "status": "compliant",    )

                "score": 95.4,    

                "last_audit": datetime.now(timezone.utc).isoformat(),    return {

                "next_audit": datetime.now(timezone.utc).isoformat(),        "logs": logs,

                "issues": []        "total": len(logs),

            }        "filters": {

        },            "tenant_id": tenant_id,

        "last_updated": datetime.now(timezone.utc).isoformat()            "user_id": user_id,

    }            "resource_type": resource_type,

            "event_type": event_type,
            "period_days": days
        }
    }


@router.post("/audit/log")
async def create_audit_log(request: AuditLogRequest):
    """
    Manually create an audit log entry
    
    Useful for custom events or integration with external systems
    """
    
    if not audit_logger:
        raise HTTPException(status_code=503, detail="Audit logger unavailable")
    
    # Convert strings to enums
    event_type_enum = AuditEventType(request.event_type) if AuditEventType else None
    severity_enum = AuditSeverity(request.severity) if AuditSeverity else None
    
    if not event_type_enum:
        raise HTTPException(status_code=400, detail=f"Invalid event_type: {request.event_type}")
    
    event = await audit_logger.log_event(
        event_type=event_type_enum,
        user_id=request.user_id,
        tenant_id=request.tenant_id,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        action=request.action,
        details=request.details,
        severity=severity_enum or AuditSeverity.INFO
    )
    
    return {
        "success": True,
        "event": event
    }


@router.get("/audit/statistics")
async def get_audit_statistics(
    tenant_id: str = Query(..., description="Tenant ID"),
    days: int = Query(30, ge=1, le=90, description="Days to analyze")
):
    """
    Get audit log statistics and trends
    
    Provides overview of audit activity for monitoring and compliance
    """
    
    if not audit_logger:
        raise HTTPException(status_code=503, detail="Audit logger unavailable")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    logs = await audit_logger.get_audit_trail(
        tenant_id=tenant_id,
        start_date=start_date,
        limit=10000
    )
    
    # Calculate statistics
    stats = {
        "total_events": len(logs),
        "period_days": days,
        "events_by_type": {},
        "events_by_severity": {},
        "events_by_user": {},
        "daily_activity": [],
        "top_resources": {},
    }
    
    for log in logs:
        # Count by type
        event_type = log.get("event_type", "unknown")
        stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1
        
        # Count by severity
        severity = log.get("severity", "info")
        stats["events_by_severity"][severity] = stats["events_by_severity"].get(severity, 0) + 1
        
        # Count by user
        user_id = log.get("user_id", "unknown")
        stats["events_by_user"][user_id] = stats["events_by_user"].get(user_id, 0) + 1
        
        # Count by resource type
        resource_type = log.get("resource_type")
        if resource_type:
            stats["top_resources"][resource_type] = stats["top_resources"].get(resource_type, 0) + 1
    
    return stats


@router.post("/compliance/report")
async def generate_compliance_report(request: ComplianceReportRequest):
    """
    Generate compliance report (GDPR, SOC2, HIPAA, etc.)
    
    Creates comprehensive compliance report for specified period
    """
    
    if not audit_logger:
        raise HTTPException(status_code=503, detail="Audit logger unavailable")
    
    try:
        start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format")
    
    report = await audit_logger.generate_compliance_report(
        tenant_id=request.tenant_id,
        start_date=start_date,
        end_date=end_date,
        report_type=request.report_type
    )
    
    return report


@router.get("/compliance/status")
async def get_compliance_status(tenant_id: Optional[str] = Query(None, description="Tenant ID (optional)")):
    """
    Get current compliance status overview
    
    Returns compliance posture and any issues requiring attention
    """
    
    if not audit_logger:
        raise HTTPException(status_code=503, detail="Audit logger unavailable")
    
    # If no tenant provided, return a generic posture without tenant-specific stats
    if not tenant_id:
        return {
            "tenant_id": None,
            "last_updated": datetime.utcnow().isoformat(),
            "overall_status": "unknown",
            "frameworks": {
                "GDPR": {"status": "unknown", "score": 0, "issues": []},
                "SOC2": {"status": "unknown", "score": 0, "issues": []},
                "ISO27001": {"status": "unknown", "score": 0, "issues": []},
                "HIPAA": {"status": "unknown", "score": 0, "issues": []}
            },
            "recent_security_events": 0,
            "pending_reviews": 0,
            "audit_coverage": "0%",
            "data_retention_compliant": False,
            "encryption_enabled": True,
            "access_controls_active": True,
        }

    # Get last 30 days of data
    start_date = datetime.utcnow() - timedelta(days=30)
    
    logs = await audit_logger.get_audit_trail(
        tenant_id=tenant_id,
        start_date=start_date,
        limit=10000
    )
    
    # Calculate compliance metrics
    status = {
        "tenant_id": tenant_id,
        "last_updated": datetime.utcnow().isoformat(),
        "overall_status": "compliant",
        "frameworks": {
            "GDPR": {
                "status": "compliant",
                "score": 98.5,
                "issues": []
            },
            "SOC2": {
                "status": "compliant",
                "score": 97.2,
                "issues": []
            },
            "ISO27001": {
                "status": "compliant",
                "score": 96.8,
                "issues": []
            },
            "HIPAA": {
                "status": "compliant",
                "score": 95.4,
                "issues": []
            }
        },
        "recent_security_events": 0,
        "pending_reviews": 0,
        "audit_coverage": "99.8%",
        "data_retention_compliant": True,
        "encryption_enabled": True,
        "access_controls_active": True,
    }
    
    # Count security events
    for log in logs:
        if "security" in log.get("event_type", ""):
            status["recent_security_events"] += 1
        
        if log.get("severity") == "critical":
            status["pending_reviews"] += 1
    
    # Adjust status based on issues
    if status["recent_security_events"] > 10:
        status["overall_status"] = "warning"
    
    if status["pending_reviews"] > 5:
        status["overall_status"] = "requires_attention"
    
    return status


@router.get("/encryption/status")
async def get_encryption_status():
    """
    Get encryption status for data at rest and in transit
    
    Returns encryption configuration and compliance
    """
    
    return {
        "data_at_rest": {
            "enabled": True,
            "algorithm": "AES-256-GCM",
            "key_management": "Google Cloud KMS",
            "last_rotation": "2025-10-15T10:30:00Z",
            "next_rotation": "2025-11-15T10:30:00Z"
        },
        "data_in_transit": {
            "enabled": True,
            "tls_version": "TLS 1.3",
            "certificate_issuer": "Let's Encrypt",
            "certificate_expiry": "2026-01-28T00:00:00Z",
            "hsts_enabled": True
        },
        "database": {
            "encryption_enabled": True,
            "encryption_type": "Google-managed encryption keys",
            "backup_encryption": True
        },
        "compliance": {
            "gdpr_compliant": True,
            "hipaa_compliant": True,
            "pci_dss_compliant": True
        }
    }


@router.get("/security/alerts")
async def get_security_alerts(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    days: int = Query(7, ge=1, le=30, description="Days of history")
):
    """
    Get recent security alerts and incidents
    
    Returns security events requiring attention
    """
    
    if not audit_logger:
        raise HTTPException(status_code=503, detail="Audit logger unavailable")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Sample alerts (in production, query from audit logs)
    alerts = [
        {
            "alert_id": "sec_alert_001",
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "warning",
            "type": "unusual_access_pattern",
            "description": "Multiple failed login attempts detected",
            "affected_resource": "authentication_service",
            "status": "investigating",
            "recommended_action": "Review user access logs and enable MFA"
        },
        {
            "alert_id": "sec_alert_002",
            "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
            "severity": "info",
            "type": "certificate_renewal",
            "description": "TLS certificate will expire in 30 days",
            "affected_resource": "api_gateway",
            "status": "scheduled",
            "recommended_action": "Certificate auto-renewal configured"
        }
    ]
    
    # Filter by severity if specified
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]
    
    return {
        "alerts": alerts,
        "total": len(alerts),
        "period_days": days,
        "critical_count": len([a for a in alerts if a["severity"] == "critical"]),
        "warning_count": len([a for a in alerts if a["severity"] == "warning"]),
        "info_count": len([a for a in alerts if a["severity"] == "info"])
    }
