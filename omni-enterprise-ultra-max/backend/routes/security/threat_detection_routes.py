"""
Threat Detection and Security Monitoring System

Features:
- IP Blacklisting (automatic and manual)
- Brute Force Protection (rate limiting, account lockout)
- Anomaly Detection (unusual login patterns, geographic anomalies)
- Real-time threat monitoring
"""

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel, Field, IPvAnyAddress
from typing import Optional, List, Dict, Set
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import logging
import ipaddress

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/security/threat-detection", tags=["Threat Detection"])


# Enums
class ThreatLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BlacklistReason(str, Enum):
    BRUTE_FORCE = "brute_force"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    KNOWN_MALICIOUS = "known_malicious"
    MANUAL = "manual"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


class ThreatType(str, Enum):
    BRUTE_FORCE = "brute_force"
    CREDENTIAL_STUFFING = "credential_stuffing"
    ACCOUNT_TAKEOVER = "account_takeover"
    ABNORMAL_LOCATION = "abnormal_location"
    IMPOSSIBLE_TRAVEL = "impossible_travel"
    SUSPICIOUS_IP = "suspicious_ip"


# Request/Response Models
class IPBlacklistRequest(BaseModel):
    ip_address: str
    reason: BlacklistReason
    duration_hours: Optional[int] = Field(None, description="Duration in hours, None for permanent")
    notes: Optional[str] = None


class IPBlacklistResponse(BaseModel):
    ip_address: str
    blacklisted: bool
    reason: BlacklistReason
    blacklisted_at: datetime
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class ThreatEvent(BaseModel):
    event_id: str
    timestamp: datetime
    threat_type: ThreatType
    threat_level: ThreatLevel
    ip_address: str
    user_id: Optional[str] = None
    details: Dict
    action_taken: str


class LoginAttempt(BaseModel):
    user_id: str
    ip_address: str
    user_agent: Optional[str] = None
    success: bool
    location: Optional[Dict] = None


class AnomalyDetectionResult(BaseModel):
    is_anomalous: bool
    anomaly_score: float
    reasons: List[str]
    recommended_action: str


# In-memory storage (replace with Redis/database in production)
_blacklisted_ips: Dict[str, Dict] = {}  # ip -> {reason, blacklisted_at, expires_at, notes}
_failed_login_attempts: Dict[str, List[Dict]] = defaultdict(list)  # ip -> [attempts]
_user_login_history: Dict[str, List[Dict]] = defaultdict(list)  # user_id -> [login_records]
_threat_events: List[Dict] = []
_rate_limit_counters: Dict[str, Dict] = defaultdict(dict)  # ip -> {endpoint: {count, reset_time}}

# Configuration
BRUTE_FORCE_THRESHOLD = 5  # Failed attempts before blocking
BRUTE_FORCE_WINDOW_MINUTES = 15  # Time window for failed attempts
RATE_LIMIT_REQUESTS = 100  # Max requests per window
RATE_LIMIT_WINDOW_MINUTES = 1  # Rate limit window
ACCOUNT_LOCKOUT_DURATION_MINUTES = 30  # How long to lock account after brute force
IP_BLACKLIST_DURATION_HOURS = 24  # Default blacklist duration


def _is_ip_blacklisted(ip_address: str) -> tuple[bool, Optional[Dict]]:
    """Check if IP is blacklisted"""
    if ip_address in _blacklisted_ips:
        entry = _blacklisted_ips[ip_address]
        
        # Check if temporary blacklist has expired
        if entry.get("expires_at"):
            if datetime.utcnow() > entry["expires_at"]:
                del _blacklisted_ips[ip_address]
                return False, None
        
        return True, entry
    return False, None


def _add_threat_event(threat_type: ThreatType, threat_level: ThreatLevel, 
                      ip_address: str, details: Dict, user_id: Optional[str] = None,
                      action_taken: str = "logged"):
    """Log a threat event"""
    event = {
        "event_id": f"threat_{datetime.utcnow().timestamp()}",
        "timestamp": datetime.utcnow(),
        "threat_type": threat_type,
        "threat_level": threat_level,
        "ip_address": ip_address,
        "user_id": user_id,
        "details": details,
        "action_taken": action_taken
    }
    _threat_events.append(event)
    logger.warning(f"Threat detected: {threat_type} from {ip_address} - {action_taken}")
    return event


def _check_brute_force(ip_address: str, user_id: Optional[str] = None) -> bool:
    """
    Check if IP or user has exceeded brute force threshold
    
    Returns True if brute force detected
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=BRUTE_FORCE_WINDOW_MINUTES)
    
    # Check IP-based attempts
    recent_attempts = [
        attempt for attempt in _failed_login_attempts[ip_address]
        if attempt["timestamp"] > cutoff_time
    ]
    
    if len(recent_attempts) >= BRUTE_FORCE_THRESHOLD:
        return True
    
    # Check user-based attempts (if user_id provided)
    if user_id:
        user_attempts = [
            attempt for attempt in _user_login_history[user_id]
            if attempt["timestamp"] > cutoff_time and not attempt.get("success")
        ]
        
        if len(user_attempts) >= BRUTE_FORCE_THRESHOLD:
            return True
    
    return False


def _check_rate_limit(ip_address: str, endpoint: str = "global") -> bool:
    """
    Check if IP has exceeded rate limit
    
    Returns True if rate limit exceeded
    """
    now = datetime.utcnow()
    
    if endpoint not in _rate_limit_counters[ip_address]:
        _rate_limit_counters[ip_address][endpoint] = {
            "count": 0,
            "reset_time": now + timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
        }
    
    counter = _rate_limit_counters[ip_address][endpoint]
    
    # Reset if window expired
    if now > counter["reset_time"]:
        counter["count"] = 0
        counter["reset_time"] = now + timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
    
    counter["count"] += 1
    
    return counter["count"] > RATE_LIMIT_REQUESTS


def _detect_anomalies(user_id: str, ip_address: str, location: Optional[Dict] = None) -> AnomalyDetectionResult:
    """
    Detect anomalous login behavior
    
    Checks for:
    - Unusual geographic location
    - Impossible travel (two logins from distant locations in short time)
    - New device/IP for user
    - Unusual time of day
    """
    anomaly_score = 0.0
    reasons = []
    
    # Get user's login history
    history = _user_login_history.get(user_id, [])
    
    if not history:
        # First login - slightly suspicious
        anomaly_score += 0.1
        reasons.append("First login for this user")
    else:
        # Check if IP is new for this user
        known_ips = set(record.get("ip_address") for record in history[-20:])  # Last 20 logins
        if ip_address not in known_ips:
            anomaly_score += 0.3
            reasons.append("New IP address for user")
        
        # Check for impossible travel if location provided
        if location and history:
            last_location = history[-1].get("location")
            if last_location:
                last_time = history[-1].get("timestamp")
                time_diff = (datetime.utcnow() - last_time).total_seconds() / 3600  # hours
                
                # Simplified distance check (in production, use proper geolocation)
                if time_diff < 2:  # Less than 2 hours
                    if location.get("country") != last_location.get("country"):
                        anomaly_score += 0.5
                        reasons.append("Impossible travel detected")
        
        # Check for unusual login time
        hour = datetime.utcnow().hour
        typical_hours = [record.get("timestamp").hour for record in history[-20:] if record.get("timestamp")]
        if typical_hours:
            avg_hour = sum(typical_hours) / len(typical_hours)
            if abs(hour - avg_hour) > 6:  # More than 6 hours difference
                anomaly_score += 0.2
                reasons.append("Unusual login time")
    
    # Determine if anomalous
    is_anomalous = anomaly_score >= 0.5
    
    # Recommended action
    if anomaly_score >= 0.8:
        recommended_action = "block_and_notify"
    elif anomaly_score >= 0.5:
        recommended_action = "require_mfa"
    elif anomaly_score >= 0.3:
        recommended_action = "log_and_monitor"
    else:
        recommended_action = "allow"
    
    return AnomalyDetectionResult(
        is_anomalous=is_anomalous,
        anomaly_score=anomaly_score,
        reasons=reasons,
        recommended_action=recommended_action
    )


@router.post("/ip/blacklist", response_model=IPBlacklistResponse)
async def blacklist_ip(request: IPBlacklistRequest):
    """
    Manually blacklist an IP address
    """
    try:
        # Validate IP address
        try:
            ipaddress.ip_address(request.ip_address)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid IP address")
        
        expires_at = None
        if request.duration_hours:
            expires_at = datetime.utcnow() + timedelta(hours=request.duration_hours)
        
        _blacklisted_ips[request.ip_address] = {
            "reason": request.reason,
            "blacklisted_at": datetime.utcnow(),
            "expires_at": expires_at,
            "notes": request.notes
        }
        
        # Log threat event
        _add_threat_event(
            threat_type=ThreatType.SUSPICIOUS_IP,
            threat_level=ThreatLevel.HIGH,
            ip_address=request.ip_address,
            details={"reason": request.reason, "notes": request.notes},
            action_taken="ip_blacklisted"
        )
        
        logger.info(f"IP {request.ip_address} blacklisted: {request.reason}")
        
        return IPBlacklistResponse(
            ip_address=request.ip_address,
            blacklisted=True,
            reason=request.reason,
            blacklisted_at=datetime.utcnow(),
            expires_at=expires_at,
            notes=request.notes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to blacklist IP: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to blacklist IP: {str(e)}")


@router.delete("/ip/blacklist/{ip_address}")
async def remove_ip_from_blacklist(ip_address: str):
    """Remove IP from blacklist"""
    if ip_address in _blacklisted_ips:
        del _blacklisted_ips[ip_address]
        logger.info(f"IP {ip_address} removed from blacklist")
        return {"success": True, "message": "IP removed from blacklist"}
    else:
        raise HTTPException(status_code=404, detail="IP not found in blacklist")


@router.get("/ip/blacklist/{ip_address}")
async def check_ip_blacklist(ip_address: str):
    """Check if IP is blacklisted"""
    is_blacklisted, entry = _is_ip_blacklisted(ip_address)
    
    if is_blacklisted:
        return {
            "ip_address": ip_address,
            "blacklisted": True,
            "reason": entry["reason"],
            "blacklisted_at": entry["blacklisted_at"],
            "expires_at": entry.get("expires_at"),
            "notes": entry.get("notes")
        }
    else:
        return {
            "ip_address": ip_address,
            "blacklisted": False
        }


@router.get("/ip/blacklist")
async def list_blacklisted_ips(active_only: bool = True):
    """List all blacklisted IPs"""
    blacklist = []
    
    for ip, entry in list(_blacklisted_ips.items()):
        # Check expiration
        if active_only and entry.get("expires_at"):
            if datetime.utcnow() > entry["expires_at"]:
                del _blacklisted_ips[ip]
                continue
        
        blacklist.append({
            "ip_address": ip,
            **entry
        })
    
    return {
        "total_count": len(blacklist),
        "blacklisted_ips": blacklist
    }


@router.post("/login/attempt")
async def record_login_attempt(
    attempt: LoginAttempt,
    request: Request,
    x_forwarded_for: Optional[str] = Header(None)
):
    """
    Record and analyze login attempt
    
    This endpoint should be called after every login attempt to:
    - Detect brute force attacks
    - Track failed login attempts
    - Detect anomalous behavior
    """
    try:
        # Get real IP (considering proxies)
        ip_address = x_forwarded_for or attempt.ip_address
        if request.client:
            ip_address = request.client.host
        
        # Check if IP is blacklisted
        is_blacklisted, blacklist_entry = _is_ip_blacklisted(ip_address)
        if is_blacklisted:
            _add_threat_event(
                threat_type=ThreatType.SUSPICIOUS_IP,
                threat_level=ThreatLevel.HIGH,
                ip_address=ip_address,
                user_id=attempt.user_id,
                details={"reason": "Attempt from blacklisted IP", "blacklist_reason": blacklist_entry["reason"]},
                action_taken="blocked"
            )
            raise HTTPException(status_code=403, detail="Access denied - IP blacklisted")
        
        # Check rate limiting
        if _check_rate_limit(ip_address, "login"):
            # Auto-blacklist for rate limit violation
            _blacklisted_ips[ip_address] = {
                "reason": BlacklistReason.RATE_LIMIT_EXCEEDED,
                "blacklisted_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=1),
                "notes": "Automatic blacklist due to rate limit violation"
            }
            
            _add_threat_event(
                threat_type=ThreatType.BRUTE_FORCE,
                threat_level=ThreatLevel.HIGH,
                ip_address=ip_address,
                user_id=attempt.user_id,
                details={"reason": "Rate limit exceeded on login endpoint"},
                action_taken="ip_blacklisted_1h"
            )
            
            raise HTTPException(status_code=429, detail="Too many requests - IP temporarily blacklisted")
        
        # Record attempt
        attempt_record = {
            "timestamp": datetime.utcnow(),
            "user_id": attempt.user_id,
            "ip_address": ip_address,
            "user_agent": attempt.user_agent,
            "success": attempt.success,
            "location": attempt.location
        }
        
        # Add to login history
        _user_login_history[attempt.user_id].append(attempt_record)
        
        # If failed, check for brute force
        if not attempt.success:
            _failed_login_attempts[ip_address].append(attempt_record)
            
            # Check brute force threshold
            if _check_brute_force(ip_address, attempt.user_id):
                # Auto-blacklist for brute force
                _blacklisted_ips[ip_address] = {
                    "reason": BlacklistReason.BRUTE_FORCE,
                    "blacklisted_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow() + timedelta(hours=IP_BLACKLIST_DURATION_HOURS),
                    "notes": f"Automatic blacklist due to {BRUTE_FORCE_THRESHOLD} failed login attempts"
                }
                
                _add_threat_event(
                    threat_type=ThreatType.BRUTE_FORCE,
                    threat_level=ThreatLevel.CRITICAL,
                    ip_address=ip_address,
                    user_id=attempt.user_id,
                    details={"failed_attempts": BRUTE_FORCE_THRESHOLD, "window_minutes": BRUTE_FORCE_WINDOW_MINUTES},
                    action_taken=f"ip_blacklisted_{IP_BLACKLIST_DURATION_HOURS}h"
                )
                
                return {
                    "status": "blocked",
                    "reason": "brute_force_detected",
                    "message": f"Too many failed attempts. IP blocked for {IP_BLACKLIST_DURATION_HOURS} hours."
                }
        
        # Detect anomalies
        anomaly_result = _detect_anomalies(attempt.user_id, ip_address, attempt.location)
        
        if anomaly_result.is_anomalous:
            _add_threat_event(
                threat_type=ThreatType.ABNORMAL_LOCATION if "travel" in str(anomaly_result.reasons) else ThreatType.SUSPICIOUS_IP,
                threat_level=ThreatLevel.MEDIUM if anomaly_result.anomaly_score < 0.7 else ThreatLevel.HIGH,
                ip_address=ip_address,
                user_id=attempt.user_id,
                details={
                    "anomaly_score": anomaly_result.anomaly_score,
                    "reasons": anomaly_result.reasons
                },
                action_taken=anomaly_result.recommended_action
            )
        
        return {
            "status": "recorded",
            "attempt_successful": attempt.success,
            "anomaly_detected": anomaly_result.is_anomalous,
            "anomaly_score": anomaly_result.anomaly_score if anomaly_result.is_anomalous else 0,
            "recommended_action": anomaly_result.recommended_action if anomaly_result.is_anomalous else "allow"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record login attempt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record attempt: {str(e)}")


@router.get("/threats")
async def get_threat_events(
    threat_type: Optional[ThreatType] = None,
    threat_level: Optional[ThreatLevel] = None,
    ip_address: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100
):
    """Get recent threat events with filtering"""
    filtered_events = _threat_events
    
    if threat_type:
        filtered_events = [e for e in filtered_events if e.get("threat_type") == threat_type]
    if threat_level:
        filtered_events = [e for e in filtered_events if e.get("threat_level") == threat_level]
    if ip_address:
        filtered_events = [e for e in filtered_events if e.get("ip_address") == ip_address]
    if user_id:
        filtered_events = [e for e in filtered_events if e.get("user_id") == user_id]
    
    # Sort by timestamp descending
    filtered_events = sorted(filtered_events, key=lambda x: x.get("timestamp", datetime.min), reverse=True)
    
    return {
        "total_count": len(filtered_events),
        "events": [ThreatEvent(**e) for e in filtered_events[:limit]]
    }


@router.get("/stats")
async def get_security_stats():
    """Get security statistics"""
    # Count events by type and level
    threat_counts = defaultdict(int)
    level_counts = defaultdict(int)
    
    for event in _threat_events:
        threat_counts[event.get("threat_type", "unknown")] += 1
        level_counts[event.get("threat_level", "unknown")] += 1
    
    # Recent threats (last 24h)
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_threats = [e for e in _threat_events if e.get("timestamp", datetime.min) > recent_cutoff]
    
    return {
        "total_threats_detected": len(_threat_events),
        "threats_last_24h": len(recent_threats),
        "blacklisted_ips": len(_blacklisted_ips),
        "threat_counts_by_type": dict(threat_counts),
        "threat_counts_by_level": dict(level_counts),
        "active_monitoring": True,
        "timestamp": datetime.utcnow()
    }


@router.post("/check-request")
async def check_request_security(
    request: Request,
    endpoint: str,
    user_id: Optional[str] = None,
    x_forwarded_for: Optional[str] = Header(None)
):
    """
    Check if a request should be allowed (middleware-style endpoint)
    
    Returns security assessment and recommended action
    """
    try:
        # Get IP address
        ip_address = x_forwarded_for or (request.client.host if request.client else "unknown")
        
        # Check blacklist
        is_blacklisted, blacklist_entry = _is_ip_blacklisted(ip_address)
        if is_blacklisted:
            return {
                "allowed": False,
                "reason": "ip_blacklisted",
                "details": blacklist_entry,
                "recommended_action": "block"
            }
        
        # Check rate limit
        if _check_rate_limit(ip_address, endpoint):
            return {
                "allowed": False,
                "reason": "rate_limit_exceeded",
                "recommended_action": "block"
            }
        
        return {
            "allowed": True,
            "ip_address": ip_address,
            "endpoint": endpoint,
            "recommended_action": "allow"
        }
        
    except Exception as e:
        logger.error(f"Security check failed: {e}")
        # Fail open (allow request) on error
        return {
            "allowed": True,
            "reason": "security_check_error",
            "error": str(e),
            "recommended_action": "allow"
        }
