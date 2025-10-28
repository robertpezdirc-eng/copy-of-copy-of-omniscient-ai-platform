"""
API Monetization System
Handles pay-per-use billing, API rate limiting, and tiered pricing
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os
import logging
import hashlib
import time
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-monetization", tags=["API Monetization"])

# Data storage paths
API_DATA_DIR = "data/api_monetization"
API_KEYS_FILE = os.path.join(API_DATA_DIR, "api_keys.json")
USAGE_LOGS_FILE = os.path.join(API_DATA_DIR, "api_usage_logs.json")
PRICING_CONFIG_FILE = os.path.join(API_DATA_DIR, "pricing_config.json")
RATE_LIMITS_FILE = os.path.join(API_DATA_DIR, "rate_limits.json")

# Ensure data directory exists
os.makedirs(API_DATA_DIR, exist_ok=True)

security = HTTPBearer()

class APITier(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class APIService(str, Enum):
    AI_AGENT = "ai_agent"
    QUANTUM_COMPUTE = "quantum_compute"
    MONITORING = "monitoring"
    ANALYTICS = "analytics"
    BILLING = "billing"
    ADVERTISING = "advertising"

class PricingModel(str, Enum):
    PAY_PER_USE = "pay_per_use"
    TIERED = "tiered"
    FLAT_RATE = "flat_rate"

class APIKey(BaseModel):
    key_id: str
    user_id: str
    api_key: str
    tier: APITier
    name: str
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True
    monthly_quota: int  # -1 for unlimited
    current_usage: int = 0
    allowed_services: List[APIService]
    rate_limit_per_minute: int
    rate_limit_per_hour: int
    metadata: Optional[Dict[str, Any]] = None

class APIUsageLog(BaseModel):
    log_id: str
    api_key: str
    user_id: str
    service: APIService
    endpoint: str
    method: str
    timestamp: datetime
    response_time_ms: int
    status_code: int
    request_size_bytes: int = 0
    response_size_bytes: int = 0
    cost: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

class ServicePricing(BaseModel):
    service: APIService
    pricing_model: PricingModel
    base_price: float
    per_request_price: float
    per_mb_price: float = 0.0
    per_minute_price: float = 0.0
    tier_multipliers: Dict[APITier, float] = Field(default_factory=dict)
    free_tier_quota: int = 1000

class RateLimit(BaseModel):
    api_key: str
    service: APIService
    requests_per_minute: List[datetime] = Field(default_factory=list)
    requests_per_hour: List[datetime] = Field(default_factory=list)
    last_reset: datetime = Field(default_factory=datetime.now)

# Default pricing configuration
DEFAULT_PRICING = {
    APIService.AI_AGENT: ServicePricing(
        service=APIService.AI_AGENT,
        pricing_model=PricingModel.PAY_PER_USE,
        base_price=0.0,
        per_request_price=0.01,
        tier_multipliers={
            APITier.FREE: 0.0,
            APITier.BASIC: 0.5,
            APITier.PRO: 0.8,
            APITier.ENTERPRISE: 1.0
        },
        free_tier_quota=100
    ),
    APIService.QUANTUM_COMPUTE: ServicePricing(
        service=APIService.QUANTUM_COMPUTE,
        pricing_model=PricingModel.PAY_PER_USE,
        base_price=0.0,
        per_request_price=0.50,
        per_minute_price=1.00,
        tier_multipliers={
            APITier.FREE: 0.0,
            APITier.BASIC: 0.3,
            APITier.PRO: 0.7,
            APITier.ENTERPRISE: 1.0
        },
        free_tier_quota=10
    ),
    APIService.MONITORING: ServicePricing(
        service=APIService.MONITORING,
        pricing_model=PricingModel.TIERED,
        base_price=0.0,
        per_request_price=0.001,
        tier_multipliers={
            APITier.FREE: 0.0,
            APITier.BASIC: 0.5,
            APITier.PRO: 0.8,
            APITier.ENTERPRISE: 1.0
        },
        free_tier_quota=1000
    ),
    APIService.ANALYTICS: ServicePricing(
        service=APIService.ANALYTICS,
        pricing_model=PricingModel.PAY_PER_USE,
        base_price=0.0,
        per_request_price=0.005,
        per_mb_price=0.10,
        tier_multipliers={
            APITier.FREE: 0.0,
            APITier.BASIC: 0.6,
            APITier.PRO: 0.8,
            APITier.ENTERPRISE: 1.0
        },
        free_tier_quota=500
    )
}

def load_api_keys() -> List[APIKey]:
    """Load API keys from file"""
    try:
        if os.path.exists(API_KEYS_FILE):
            with open(API_KEYS_FILE, 'r') as f:
                data = json.load(f)
                return [APIKey(**key) for key in data]
    except Exception as e:
        logger.error(f"Error loading API keys: {e}")
    return []

def save_api_keys(keys: List[APIKey]):
    """Save API keys to file"""
    try:
        data = [key.dict() for key in keys]
        with open(API_KEYS_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving API keys: {e}")

def load_usage_logs() -> List[APIUsageLog]:
    """Load API usage logs from file"""
    try:
        if os.path.exists(USAGE_LOGS_FILE):
            with open(USAGE_LOGS_FILE, 'r') as f:
                data = json.load(f)
                return [APIUsageLog(**log) for log in data]
    except Exception as e:
        logger.error(f"Error loading usage logs: {e}")
    return []

def save_usage_logs(logs: List[APIUsageLog]):
    """Save API usage logs to file"""
    try:
        data = [log.dict() for log in logs]
        with open(USAGE_LOGS_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving usage logs: {e}")

def load_pricing_config() -> Dict[APIService, ServicePricing]:
    """Load pricing configuration"""
    try:
        if os.path.exists(PRICING_CONFIG_FILE):
            with open(PRICING_CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return {APIService(k): ServicePricing(**v) for k, v in data.items()}
    except Exception as e:
        logger.error(f"Error loading pricing config: {e}")
    
    # Save defaults if file doesn't exist
    save_pricing_config(DEFAULT_PRICING)
    return DEFAULT_PRICING

def save_pricing_config(pricing: Dict[APIService, ServicePricing]):
    """Save pricing configuration"""
    try:
        data = {k.value: v.dict() for k, v in pricing.items()}
        with open(PRICING_CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving pricing config: {e}")

def generate_api_key() -> str:
    """Generate secure API key"""
    timestamp = str(int(time.time()))
    random_data = os.urandom(32)
    key_data = f"{timestamp}{random_data.hex()}"
    return f"omni_{hashlib.sha256(key_data.encode()).hexdigest()[:32]}"

def calculate_request_cost(
    service: APIService,
    tier: APITier,
    request_size_mb: float = 0.0,
    processing_minutes: float = 0.0
) -> float:
    """Calculate cost for API request based on service and tier"""
    pricing_config = load_pricing_config()
    
    if service not in pricing_config:
        return 0.0
    
    pricing = pricing_config[service]
    tier_multiplier = pricing.tier_multipliers.get(tier, 1.0)
    
    cost = pricing.base_price
    cost += pricing.per_request_price
    cost += pricing.per_mb_price * request_size_mb
    cost += pricing.per_minute_price * processing_minutes
    
    return cost * tier_multiplier

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> APIKey:
    """Verify API key and return key details"""
    api_key = credentials.credentials
    keys = load_api_keys()
    
    for key in keys:
        if key.api_key == api_key and key.is_active:
            # Update last used timestamp
            key.last_used = datetime.now()
            save_api_keys(keys)
            return key
    
    raise HTTPException(status_code=401, detail="Invalid or inactive API key")

async def check_rate_limit(api_key: APIKey, service: APIService) -> bool:
    """Check if request is within rate limits"""
    try:
        if os.path.exists(RATE_LIMITS_FILE):
            with open(RATE_LIMITS_FILE, 'r') as f:
                rate_limits_data = json.load(f)
        else:
            rate_limits_data = {}
        
        key_id = f"{api_key.api_key}_{service.value}"
        now = datetime.now()
        
        if key_id not in rate_limits_data:
            rate_limits_data[key_id] = {
                "requests_per_minute": [],
                "requests_per_hour": [],
                "last_reset": now.isoformat()
            }
        
        rate_limit = rate_limits_data[key_id]
        
        # Clean old requests
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        rate_limit["requests_per_minute"] = [
            req for req in rate_limit["requests_per_minute"]
            if datetime.fromisoformat(req) > minute_ago
        ]
        rate_limit["requests_per_hour"] = [
            req for req in rate_limit["requests_per_hour"]
            if datetime.fromisoformat(req) > hour_ago
        ]
        
        # Check limits
        if len(rate_limit["requests_per_minute"]) >= api_key.rate_limit_per_minute:
            return False
        if len(rate_limit["requests_per_hour"]) >= api_key.rate_limit_per_hour:
            return False
        
        # Add current request
        rate_limit["requests_per_minute"].append(now.isoformat())
        rate_limit["requests_per_hour"].append(now.isoformat())
        
        # Save updated rate limits
        with open(RATE_LIMITS_FILE, 'w') as f:
            json.dump(rate_limits_data, f, indent=2, default=str)
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        return True  # Allow request if rate limit check fails

@router.post("/keys/create")
async def create_api_key(
    user_id: str,
    tier: APITier,
    name: str,
    allowed_services: List[APIService]
):
    """Create new API key for user"""
    keys = load_api_keys()
    
    # Set quotas and rate limits based on tier
    tier_config = {
        APITier.FREE: {
            "monthly_quota": 1000,
            "rate_limit_per_minute": 10,
            "rate_limit_per_hour": 100
        },
        APITier.BASIC: {
            "monthly_quota": 10000,
            "rate_limit_per_minute": 50,
            "rate_limit_per_hour": 1000
        },
        APITier.PRO: {
            "monthly_quota": 100000,
            "rate_limit_per_minute": 200,
            "rate_limit_per_hour": 5000
        },
        APITier.ENTERPRISE: {
            "monthly_quota": -1,  # Unlimited
            "rate_limit_per_minute": 1000,
            "rate_limit_per_hour": 20000
        }
    }
    
    config = tier_config[tier]
    
    new_key = APIKey(
        key_id=f"key_{len(keys) + 1}",
        user_id=user_id,
        api_key=generate_api_key(),
        tier=tier,
        name=name,
        created_at=datetime.now(),
        monthly_quota=config["monthly_quota"],
        allowed_services=allowed_services,
        rate_limit_per_minute=config["rate_limit_per_minute"],
        rate_limit_per_hour=config["rate_limit_per_hour"]
    )
    
    keys.append(new_key)
    save_api_keys(keys)
    
    logger.info(f"Created API key for user {user_id}: {tier.value}")
    
    return {
        "message": "API key created successfully",
        "api_key": new_key.api_key,
        "key_details": new_key
    }

@router.get("/keys/{user_id}")
async def get_user_api_keys(user_id: str):
    """Get all API keys for user"""
    keys = load_api_keys()
    user_keys = [key for key in keys if key.user_id == user_id]
    
    # Hide actual API key in response
    for key in user_keys:
        key.api_key = f"{key.api_key[:8]}...{key.api_key[-4:]}"
    
    return {"api_keys": user_keys}

@router.delete("/keys/{key_id}")
async def revoke_api_key(key_id: str, user_id: str):
    """Revoke API key"""
    keys = load_api_keys()
    
    for i, key in enumerate(keys):
        if key.key_id == key_id and key.user_id == user_id:
            keys[i].is_active = False
            save_api_keys(keys)
            return {"message": "API key revoked successfully"}
    
    raise HTTPException(status_code=404, detail="API key not found")

@router.post("/usage/log")
async def log_api_usage(
    service: APIService,
    endpoint: str,
    method: str,
    response_time_ms: int,
    status_code: int,
    request_size_bytes: int = 0,
    response_size_bytes: int = 0,
    processing_minutes: float = 0.0,
    api_key: APIKey = Depends(verify_api_key)
):
    """Log API usage for billing purposes"""
    
    # Check if service is allowed for this API key
    if service not in api_key.allowed_services:
        raise HTTPException(status_code=403, detail="Service not allowed for this API key")
    
    # Check rate limits
    if not await check_rate_limit(api_key, service):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Calculate cost
    request_size_mb = request_size_bytes / (1024 * 1024)
    cost = calculate_request_cost(
        service=service,
        tier=api_key.tier,
        request_size_mb=request_size_mb,
        processing_minutes=processing_minutes
    )
    
    # Create usage log
    usage_log = APIUsageLog(
        log_id=f"log_{int(time.time())}_{api_key.key_id}",
        api_key=api_key.api_key,
        user_id=api_key.user_id,
        service=service,
        endpoint=endpoint,
        method=method,
        timestamp=datetime.now(),
        response_time_ms=response_time_ms,
        status_code=status_code,
        request_size_bytes=request_size_bytes,
        response_size_bytes=response_size_bytes,
        cost=cost
    )
    
    # Save usage log
    logs = load_usage_logs()
    logs.append(usage_log)
    save_usage_logs(logs)
    
    # Update API key usage
    keys = load_api_keys()
    for i, key in enumerate(keys):
        if key.api_key == api_key.api_key:
            keys[i].current_usage += 1
            break
    save_api_keys(keys)
    
    return {
        "message": "Usage logged successfully",
        "cost": cost,
        "remaining_quota": api_key.monthly_quota - api_key.current_usage if api_key.monthly_quota > 0 else -1
    }

@router.get("/usage/{user_id}")
async def get_user_usage(user_id: str, days: int = 30):
    """Get user's API usage statistics"""
    logs = load_usage_logs()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    user_logs = [
        log for log in logs
        if log.user_id == user_id and start_date <= log.timestamp <= end_date
    ]
    
    usage_stats = {
        "total_requests": len(user_logs),
        "total_cost": sum(log.cost for log in user_logs),
        "usage_by_service": {},
        "usage_by_day": {},
        "average_response_time": 0.0,
        "error_rate": 0.0
    }
    
    # Calculate usage by service
    for service in APIService:
        service_logs = [log for log in user_logs if log.service == service]
        usage_stats["usage_by_service"][service.value] = {
            "requests": len(service_logs),
            "cost": sum(log.cost for log in service_logs),
            "avg_response_time": sum(log.response_time_ms for log in service_logs) / len(service_logs) if service_logs else 0
        }
    
    # Calculate usage by day
    for log in user_logs:
        day_key = log.timestamp.strftime("%Y-%m-%d")
        if day_key not in usage_stats["usage_by_day"]:
            usage_stats["usage_by_day"][day_key] = {"requests": 0, "cost": 0.0}
        usage_stats["usage_by_day"][day_key]["requests"] += 1
        usage_stats["usage_by_day"][day_key]["cost"] += log.cost
    
    # Calculate averages
    if user_logs:
        usage_stats["average_response_time"] = sum(log.response_time_ms for log in user_logs) / len(user_logs)
        error_logs = [log for log in user_logs if log.status_code >= 400]
        usage_stats["error_rate"] = len(error_logs) / len(user_logs) * 100
    
    return usage_stats

@router.get("/pricing")
async def get_pricing_config():
    """Get current API pricing configuration"""
    pricing = load_pricing_config()
    return {service.value: config.dict() for service, config in pricing.items()}

@router.put("/pricing/{service}")
async def update_service_pricing(service: APIService, pricing: ServicePricing):
    """Update pricing for specific service (admin only)"""
    pricing_config = load_pricing_config()
    pricing_config[service] = pricing
    save_pricing_config(pricing_config)
    
    return {"message": f"Pricing updated for {service.value}", "pricing": pricing}

@router.get("/analytics/revenue")
async def get_api_revenue_analytics():
    """Get API revenue analytics"""
    logs = load_usage_logs()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    recent_logs = [
        log for log in logs
        if start_date <= log.timestamp <= end_date
    ]
    
    analytics = {
        "total_revenue": sum(log.cost for log in recent_logs),
        "total_requests": len(recent_logs),
        "revenue_by_service": {},
        "revenue_by_tier": {},
        "top_users": {},
        "daily_revenue": {}
    }
    
    # Revenue by service
    for service in APIService:
        service_logs = [log for log in recent_logs if log.service == service]
        analytics["revenue_by_service"][service.value] = sum(log.cost for log in service_logs)
    
    # Revenue by tier (need to get tier from API keys)
    keys = load_api_keys()
    key_tiers = {key.api_key: key.tier for key in keys}
    
    for tier in APITier:
        tier_logs = [log for log in recent_logs if key_tiers.get(log.api_key) == tier]
        analytics["revenue_by_tier"][tier.value] = sum(log.cost for log in tier_logs)
    
    # Top users by revenue
    user_revenue = {}
    for log in recent_logs:
        if log.user_id not in user_revenue:
            user_revenue[log.user_id] = 0.0
        user_revenue[log.user_id] += log.cost
    
    analytics["top_users"] = dict(sorted(user_revenue.items(), key=lambda x: x[1], reverse=True)[:10])
    
    # Daily revenue
    for log in recent_logs:
        day_key = log.timestamp.strftime("%Y-%m-%d")
        if day_key not in analytics["daily_revenue"]:
            analytics["daily_revenue"][day_key] = 0.0
        analytics["daily_revenue"][day_key] += log.cost
    
    return analytics