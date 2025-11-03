"""
GDPR Persistence Health Monitoring

Provides health checks and metrics for GDPR data persistence layer:
- Database availability monitoring
- Fallback detection and alerting
- Persistence failure tracking
- Repository type reporting
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class RepositoryHealth(str, Enum):
    """Repository health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"  # Using fallback repository
    UNHEALTHY = "unhealthy"  # Complete failure


class PersistenceMetrics:
    """Track GDPR persistence metrics"""
    
    def __init__(self):
        self.consent_save_failures = 0
        self.consent_save_successes = 0
        self.audit_log_failures = 0
        self.audit_log_successes = 0
        self.repository_fallback_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_failure_reason: Optional[str] = None
        self.current_repository_type: Optional[str] = None
        
    def record_consent_save(self, success: bool, error: Optional[str] = None):
        """Record consent save attempt"""
        if success:
            self.consent_save_successes += 1
        else:
            self.consent_save_failures += 1
            self.last_failure_time = datetime.utcnow()
            self.last_failure_reason = error
            logger.warning(f"Consent save failed: {error}")
    
    def record_audit_log(self, success: bool, error: Optional[str] = None):
        """Record audit log attempt"""
        if success:
            self.audit_log_successes += 1
        else:
            self.audit_log_failures += 1
            self.last_failure_time = datetime.utcnow()
            self.last_failure_reason = error
            logger.warning(f"Audit log failed: {error}")
    
    def record_repository_fallback(self, from_type: str, to_type: str, reason: str):
        """Record repository fallback event"""
        self.repository_fallback_count += 1
        self.current_repository_type = to_type
        self.last_failure_time = datetime.utcnow()
        self.last_failure_reason = reason
        
        # Log as warning if falling back to in-memory (data loss risk)
        if to_type == "InMemoryGDPRRepository":
            logger.error(
                f"GDPR persistence degraded: Falling back from {from_type} to {to_type}. "
                f"Reason: {reason}. Data will NOT persist across restarts!"
            )
        else:
            logger.warning(
                f"GDPR persistence fallback: {from_type} → {to_type}. Reason: {reason}"
            )
    
    def get_health_status(self) -> RepositoryHealth:
        """Determine current health status"""
        # If using in-memory, degraded
        if self.current_repository_type == "InMemoryGDPRRepository":
            return RepositoryHealth.DEGRADED
        
        # If high failure rate, unhealthy
        total_attempts = (
            self.consent_save_successes + 
            self.consent_save_failures + 
            self.audit_log_successes + 
            self.audit_log_failures
        )
        
        if total_attempts > 100:  # After warmup period
            failure_rate = (
                (self.consent_save_failures + self.audit_log_failures) / 
                total_attempts
            )
            if failure_rate > 0.1:  # >10% failure rate
                return RepositoryHealth.UNHEALTHY
        
        return RepositoryHealth.HEALTHY
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics as dict"""
        return {
            "consent_saves": {
                "successes": self.consent_save_successes,
                "failures": self.consent_save_failures,
                "total": self.consent_save_successes + self.consent_save_failures,
            },
            "audit_logs": {
                "successes": self.audit_log_successes,
                "failures": self.audit_log_failures,
                "total": self.audit_log_successes + self.audit_log_failures,
            },
            "fallback_count": self.repository_fallback_count,
            "current_repository_type": self.current_repository_type,
            "health_status": self.get_health_status().value,
            "last_failure": {
                "time": self.last_failure_time.isoformat() if self.last_failure_time else None,
                "reason": self.last_failure_reason,
            }
        }


# Global metrics instance
_persistence_metrics = PersistenceMetrics()


def get_persistence_metrics() -> PersistenceMetrics:
    """Get global persistence metrics instance"""
    return _persistence_metrics


def check_database_health() -> Dict[str, Any]:
    """
    Check database health for GDPR persistence
    
    Returns comprehensive health status including:
    - Repository type (Postgres/Mongo/InMemory)
    - Connection status
    - Recent failures
    - Recommendations
    """
    metrics = get_persistence_metrics()
    health_status = metrics.get_health_status()
    
    # Determine recommendations based on status
    recommendations = []
    
    if health_status == RepositoryHealth.DEGRADED:
        recommendations.append(
            "CRITICAL: Using in-memory storage. Data will be lost on restart. "
            "Check DATABASE_URL and MONGODB_URL configuration."
        )
        recommendations.append(
            "Verify PostgreSQL or MongoDB service is running and accessible."
        )
    
    if health_status == RepositoryHealth.UNHEALTHY:
        recommendations.append(
            "High failure rate detected. Check database connectivity and logs."
        )
    
    if metrics.consent_save_failures > 0:
        recommendations.append(
            f"Consent save failures detected: {metrics.consent_save_failures}. "
            f"Last failure: {metrics.last_failure_reason}"
        )
    
    return {
        "status": health_status.value,
        "repository_type": metrics.current_repository_type or "Unknown",
        "metrics": metrics.get_metrics(),
        "recommendations": recommendations,
        "timestamp": datetime.utcnow().isoformat(),
    }


def alert_on_degraded_persistence():
    """
    Check if persistence is degraded and log alerts
    
    Should be called periodically (e.g., every 5 minutes)
    to alert operators if GDPR data is at risk
    """
    metrics = get_persistence_metrics()
    health = metrics.get_health_status()
    
    if health == RepositoryHealth.DEGRADED:
        logger.critical(
            "⚠️  GDPR DATA LOSS RISK: Using in-memory storage. "
            f"Repository type: {metrics.current_repository_type}. "
            "User consents and audit logs will NOT persist across restarts. "
            "Check database configuration immediately!"
        )
    elif health == RepositoryHealth.UNHEALTHY:
        logger.error(
            f"GDPR persistence unhealthy: High failure rate. "
            f"Failures: {metrics.consent_save_failures + metrics.audit_log_failures}. "
            f"Last error: {metrics.last_failure_reason}"
        )


def export_prometheus_metrics() -> str:
    """
    Export metrics in Prometheus format
    
    Example usage with prometheus_client:
    ```python
    from prometheus_client import Gauge, Counter
    
    gdpr_consent_saves_total = Counter(
        'gdpr_consent_saves_total',
        'Total GDPR consent save attempts',
        ['status']
    )
    ```
    """
    metrics = get_persistence_metrics()
    health = metrics.get_health_status()
    
    # Map repository type to numeric value for gauges
    repo_type_map = {
        "PostgresGDPRRepository": 2,
        "MongoGDPRRepository": 1,
        "InMemoryGDPRRepository": 0,
    }
    
    health_map = {
        RepositoryHealth.HEALTHY: 2,
        RepositoryHealth.DEGRADED: 1,
        RepositoryHealth.UNHEALTHY: 0,
    }
    
    repo_value = repo_type_map.get(metrics.current_repository_type or "", -1)
    health_value = health_map.get(health, -1)
    
    return f"""# HELP gdpr_consent_saves_total Total GDPR consent save attempts
# TYPE gdpr_consent_saves_total counter
gdpr_consent_saves_total{{status="success"}} {metrics.consent_save_successes}
gdpr_consent_saves_total{{status="failure"}} {metrics.consent_save_failures}

# HELP gdpr_audit_logs_total Total GDPR audit log attempts
# TYPE gdpr_audit_logs_total counter
gdpr_audit_logs_total{{status="success"}} {metrics.audit_log_successes}
gdpr_audit_logs_total{{status="failure"}} {metrics.audit_log_failures}

# HELP gdpr_repository_fallback_total Total repository fallback events
# TYPE gdpr_repository_fallback_total counter
gdpr_repository_fallback_total {metrics.repository_fallback_count}

# HELP gdpr_repository_type Current repository type (2=Postgres, 1=Mongo, 0=InMemory)
# TYPE gdpr_repository_type gauge
gdpr_repository_type {repo_value}

# HELP gdpr_health_status Health status (2=Healthy, 1=Degraded, 0=Unhealthy)
# TYPE gdpr_health_status gauge
gdpr_health_status {health_value}
"""


# Integration point for scheduled health checks
async def periodic_health_check():
    """
    Periodic health check to run every 5 minutes
    
    Add to FastAPI background tasks or Celery beat schedule:
    ```python
    from fastapi import BackgroundTasks
    
    @app.on_event("startup")
    async def schedule_health_checks():
        # Schedule periodic check
        pass
    ```
    """
    try:
        alert_on_degraded_persistence()
        health_report = check_database_health()
        
        # If degraded, also check if we can recover
        if health_report["status"] == RepositoryHealth.DEGRADED.value:
            # Attempt to reconnect to primary database
            logger.info("Attempting to recover primary database connection...")
            # This would trigger repository re-initialization logic
    except Exception as e:
        logger.error(f"Health check failed: {e}")
