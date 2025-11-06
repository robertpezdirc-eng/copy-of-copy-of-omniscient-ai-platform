"""
Enhanced Observability Service for SLA Monitoring
Provides metrics, tracing, and health monitoring with SLA guarantees
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from enum import Enum
import logging
import time

logger = logging.getLogger(__name__)


class SLALevel(str, Enum):
    """SLA guarantee levels"""
    NONE = "none"
    STANDARD = "99.9%"  # Basic & Pro
    PREMIUM = "99.99%"  # Enterprise


class HealthStatus(str, Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServiceMetrics:
    """Metrics for a service"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.request_count = 0
        self.error_count = 0
        self.total_latency_ms = 0.0
        self.last_request_time: Optional[datetime] = None
        self.start_time = datetime.now(timezone.utc)
        
    def record_request(self, latency_ms: float, is_error: bool = False):
        """Record a request"""
        self.request_count += 1
        self.total_latency_ms += latency_ms
        self.last_request_time = datetime.now(timezone.utc)
        
        if is_error:
            self.error_count += 1
    
    def get_average_latency(self) -> float:
        """Get average latency in milliseconds"""
        if self.request_count == 0:
            return 0.0
        return self.total_latency_ms / self.request_count
    
    def get_error_rate(self) -> float:
        """Get error rate as percentage"""
        if self.request_count == 0:
            return 0.0
        return (self.error_count / self.request_count) * 100
    
    def get_uptime_seconds(self) -> float:
        """Get uptime in seconds"""
        return (datetime.now(timezone.utc) - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "service_name": self.service_name,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "average_latency_ms": round(self.get_average_latency(), 2),
            "error_rate_percent": round(self.get_error_rate(), 2),
            "uptime_seconds": round(self.get_uptime_seconds(), 2),
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None
        }


class ObservabilityService:
    """Enhanced observability service for SLA monitoring"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.metrics: Dict[str, ServiceMetrics] = {}
        self.health_checks: Dict[str, HealthStatus] = {}
        self.sla_config: Dict[str, SLALevel] = {}
        
    def register_service(self, service_name: str, sla_level: SLALevel = SLALevel.STANDARD):
        """Register a service for monitoring"""
        if service_name not in self.metrics:
            self.metrics[service_name] = ServiceMetrics(service_name)
            self.health_checks[service_name] = HealthStatus.UNKNOWN
            self.sla_config[service_name] = sla_level
            logger.info(f"Registered service for monitoring: {service_name} (SLA: {sla_level.value})")
    
    async def record_request(
        self,
        service_name: str,
        latency_ms: float,
        is_error: bool = False,
        tenant_id: Optional[str] = None
    ):
        """Record a service request"""
        if service_name not in self.metrics:
            self.register_service(service_name)
        
        self.metrics[service_name].record_request(latency_ms, is_error)
        
        # Store in Redis for persistence
        if self.redis and tenant_id:
            try:
                key = f"metrics:{tenant_id}:{service_name}"
                await self.redis.hincrby(key, "requests", 1)
                if is_error:
                    await self.redis.hincrby(key, "errors", 1)
                await self.redis.hincrbyfloat(key, "total_latency", latency_ms)
                await self.redis.expire(key, 86400)  # 24 hour retention
            except Exception as e:
                logger.error(f"Failed to store metrics in Redis: {e}")
    
    async def check_health(self, service_name: str) -> HealthStatus:
        """Check health status of a service"""
        if service_name not in self.metrics:
            return HealthStatus.UNKNOWN
        
        metrics = self.metrics[service_name]
        error_rate = metrics.get_error_rate()
        avg_latency = metrics.get_average_latency()
        
        # Health criteria
        if error_rate > 10:  # More than 10% errors
            status = HealthStatus.UNHEALTHY
        elif error_rate > 5 or avg_latency > 1000:  # 5% errors or >1s latency
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY
        
        self.health_checks[service_name] = status
        return status
    
    async def get_sla_status(self, service_name: str) -> Dict[str, Any]:
        """Get SLA status for a service"""
        if service_name not in self.metrics:
            return {
                "service": service_name,
                "sla_target": "N/A",
                "current_uptime": "N/A",
                "meeting_sla": False
            }
        
        metrics = self.metrics[service_name]
        sla_level = self.sla_config.get(service_name, SLALevel.NONE)
        
        # Calculate uptime percentage
        error_rate = metrics.get_error_rate()
        uptime_percent = 100 - error_rate
        
        # Parse SLA target
        sla_target_value = 0.0
        if sla_level != SLALevel.NONE:
            sla_target_value = float(sla_level.value.rstrip('%'))
        
        meeting_sla = uptime_percent >= sla_target_value
        
        return {
            "service": service_name,
            "sla_target": sla_level.value,
            "current_uptime": f"{uptime_percent:.2f}%",
            "uptime_numeric": uptime_percent,
            "meeting_sla": meeting_sla,
            "error_rate": f"{error_rate:.2f}%",
            "average_latency_ms": round(metrics.get_average_latency(), 2),
            "total_requests": metrics.request_count
        }
    
    async def get_all_metrics(self) -> List[Dict[str, Any]]:
        """Get metrics for all services"""
        result = []
        for service_name, metrics in self.metrics.items():
            health = await self.check_health(service_name)
            sla = await self.get_sla_status(service_name)
            
            result.append({
                **metrics.to_dict(),
                "health_status": health.value,
                "sla_status": sla
            })
        
        return result
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        services = []
        overall_healthy = True
        
        for service_name in self.metrics.keys():
            health = await self.check_health(service_name)
            sla = await self.get_sla_status(service_name)
            
            services.append({
                "name": service_name,
                "status": health.value,
                "meeting_sla": sla["meeting_sla"]
            })
            
            if health != HealthStatus.HEALTHY:
                overall_healthy = False
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": services,
            "total_services": len(services),
            "healthy_services": sum(1 for s in services if s["status"] == "healthy")
        }
    
    async def get_tenant_metrics(
        self,
        tenant_id: str,
        service_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get metrics for a specific tenant"""
        if not self.redis:
            return {"error": "Redis not available"}
        
        try:
            if service_name:
                key = f"metrics:{tenant_id}:{service_name}"
                data = await self.redis.hgetall(key)
                
                if not data:
                    return {"error": "No metrics found"}
                
                requests = int(data.get(b"requests", 0))
                errors = int(data.get(b"errors", 0))
                total_latency = float(data.get(b"total_latency", 0))
                
                return {
                    "tenant_id": tenant_id,
                    "service": service_name,
                    "requests": requests,
                    "errors": errors,
                    "error_rate": (errors / requests * 100) if requests > 0 else 0,
                    "average_latency_ms": (total_latency / requests) if requests > 0 else 0
                }
            else:
                # Get all services for tenant
                pattern = f"metrics:{tenant_id}:*"
                metrics = []
                
                async for key in self.redis.scan_iter(match=pattern):
                    service = key.decode().split(":")[-1]
                    data = await self.redis.hgetall(key)
                    
                    requests = int(data.get(b"requests", 0))
                    errors = int(data.get(b"errors", 0))
                    total_latency = float(data.get(b"total_latency", 0))
                    
                    metrics.append({
                        "service": service,
                        "requests": requests,
                        "errors": errors,
                        "average_latency_ms": (total_latency / requests) if requests > 0 else 0
                    })
                
                return {
                    "tenant_id": tenant_id,
                    "services": metrics
                }
        except Exception as e:
            logger.error(f"Failed to get tenant metrics: {e}")
            return {"error": str(e)}
    
    async def generate_sla_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate SLA compliance report"""
        if start_date is None:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        
        report = {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "services": []
        }
        
        for service_name in self.metrics.keys():
            sla_status = await self.get_sla_status(service_name)
            metrics = self.metrics[service_name]
            
            report["services"].append({
                "service": service_name,
                "sla_target": sla_status["sla_target"],
                "achieved_uptime": sla_status["current_uptime"],
                "meeting_sla": sla_status["meeting_sla"],
                "total_requests": metrics.request_count,
                "total_errors": metrics.error_count,
                "average_latency_ms": round(metrics.get_average_latency(), 2)
            })
        
        total_services = len(report["services"])
        compliant_services = sum(1 for s in report["services"] if s["meeting_sla"])
        
        report["summary"] = {
            "total_services": total_services,
            "compliant_services": compliant_services,
            "compliance_rate": f"{(compliant_services / total_services * 100):.2f}%" if total_services > 0 else "N/A"
        }
        
        return report


# Global observability service instance
_observability_service: Optional[ObservabilityService] = None


def get_observability_service(redis_client=None) -> ObservabilityService:
    """Get or create observability service instance"""
    global _observability_service
    if _observability_service is None:
        _observability_service = ObservabilityService(redis_client)
    return _observability_service
