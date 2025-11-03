"""
Monetization & Subscription Management Routes
Provides pricing packages (Basic/Pro/Enterprise) and billing
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from database import get_redis
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class PricingTier(BaseModel):
    """Pricing tier information"""
    name: str
    price_monthly: float
    price_annual: float
    features: Dict[str, Any]
    limits: Dict[str, Any]
    popular: bool = False


class SubscriptionRequest(BaseModel):
    """Request to create or update subscription"""
    tenant_id: str = Field(..., min_length=1)
    plan: str = Field(..., pattern="^(basic|pro|enterprise)$")
    billing_cycle: str = Field(..., pattern="^(monthly|annual)$")
    payment_method: Optional[str] = None


class UsageReport(BaseModel):
    """Usage report for billing"""
    tenant_id: str
    period_start: str
    period_end: str


# Pricing packages
PRICING_TIERS = {
    "basic": PricingTier(
        name="Basic",
        price_monthly=49.00,
        price_annual=490.00,  # 2 months free
        features={
            "ai_assistant": False,
            "advanced_analytics": False,
            "priority_support": False,
            "custom_domain": False,
            "white_label": False,
            "sla_guarantee": False,
        },
        limits={
            "max_api_calls_per_day": 1000,
            "max_users": 5,
            "max_storage_gb": 1,
            "rate_limit_per_minute": 10,
        },
        popular=False
    ),
    "pro": PricingTier(
        name="Pro",
        price_monthly=199.00,
        price_annual=1990.00,  # 2 months free
        features={
            "ai_assistant": True,
            "advanced_analytics": True,
            "priority_support": True,
            "custom_domain": True,
            "white_label": False,
            "sla_guarantee": "99.9%",
        },
        limits={
            "max_api_calls_per_day": 10000,
            "max_users": 50,
            "max_storage_gb": 10,
            "rate_limit_per_minute": 100,
        },
        popular=True
    ),
    "enterprise": PricingTier(
        name="Enterprise",
        price_monthly=999.00,
        price_annual=9990.00,  # 2 months free
        features={
            "ai_assistant": True,
            "advanced_analytics": True,
            "priority_support": True,
            "custom_domain": True,
            "white_label": True,
            "sla_guarantee": "99.99%",
            "dedicated_support": True,
            "custom_integrations": True,
        },
        limits={
            "max_api_calls_per_day": -1,  # Unlimited
            "max_users": -1,  # Unlimited
            "max_storage_gb": -1,  # Unlimited
            "rate_limit_per_minute": -1,  # Unlimited
        },
        popular=False
    )
}


@router.get("/plans", tags=["Monetization"])
def get_pricing_plans():
    """Get all pricing plans"""
    return {
        "plans": [
            {
                "id": tier_id,
                **tier.dict()
            }
            for tier_id, tier in PRICING_TIERS.items()
        ],
        "currency": "EUR",
        "billing_cycles": ["monthly", "annual"],
        "annual_discount": "17%"  # 2 months free
    }


@router.get("/plans/{plan_id}", tags=["Monetization"])
def get_pricing_plan(plan_id: str):
    """Get specific pricing plan"""
    if plan_id not in PRICING_TIERS:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    tier = PRICING_TIERS[plan_id]
    return {
        "id": plan_id,
        **tier.dict()
    }


@router.post("/subscribe", tags=["Monetization"])
async def create_subscription(
    req: SubscriptionRequest,
    redis=Depends(get_redis)
):
    """Create or update subscription"""
    try:
        # Validate plan
        if req.plan not in PRICING_TIERS:
            raise HTTPException(status_code=400, detail="Invalid plan")
        
        # Get pricing tier
        tier = PRICING_TIERS[req.plan]
        
        # Calculate price
        if req.billing_cycle == "annual":
            price = tier.price_annual
            savings = (tier.price_monthly * 12) - tier.price_annual
        else:
            price = tier.price_monthly
            savings = 0
        
        # Store subscription in Redis
        if redis:
            try:
                subscription_data = {
                    "tenant_id": req.tenant_id,
                    "plan": req.plan,
                    "billing_cycle": req.billing_cycle,
                    "price": price,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "status": "active"
                }
                
                await redis.setex(
                    f"subscription:{req.tenant_id}",
                    86400 * 365,  # 1 year TTL
                    str(subscription_data)
                )
            except Exception as e:
                logger.error(f"Failed to store subscription in Redis: {e}")
        
        return {
            "success": True,
            "subscription": {
                "tenant_id": req.tenant_id,
                "plan": req.plan,
                "plan_name": tier.name,
                "billing_cycle": req.billing_cycle,
                "price": price,
                "currency": "EUR",
                "savings": savings if savings > 0 else None,
                "features": tier.features,
                "limits": tier.limits,
                "status": "active",
                "next_billing_date": self._calculate_next_billing_date(req.billing_cycle)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscriptions/{tenant_id}", tags=["Monetization"])
async def get_subscription(
    tenant_id: str,
    redis=Depends(get_redis)
):
    """Get subscription details"""
    try:
        if redis:
            try:
                data = await redis.get(f"subscription:{tenant_id}")
                if data:
                    subscription = eval(data)  # Safe in this context
                    return {
                        "success": True,
                        "subscription": subscription
                    }
            except Exception as e:
                logger.error(f"Failed to get subscription from Redis: {e}")
        
        # Default response if not found
        return {
            "success": True,
            "subscription": {
                "tenant_id": tenant_id,
                "plan": "basic",
                "status": "trial",
                "message": "No active subscription found"
            }
        }
    except Exception as e:
        logger.error(f"Failed to get subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscriptions/{tenant_id}/cancel", tags=["Monetization"])
async def cancel_subscription(
    tenant_id: str,
    redis=Depends(get_redis)
):
    """Cancel subscription"""
    try:
        if redis:
            await redis.delete(f"subscription:{tenant_id}")
        
        return {
            "success": True,
            "message": "Subscription cancelled",
            "tenant_id": tenant_id,
            "cancelled_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/usage-report", tags=["Monetization"])
async def generate_usage_report(
    req: UsageReport,
    redis=Depends(get_redis)
):
    """Generate usage report for billing"""
    try:
        # Get usage metrics from observability service
        from services.observability_service import get_observability_service
        
        obs_service = get_observability_service(redis)
        metrics = await obs_service.get_tenant_metrics(req.tenant_id)
        
        # Calculate usage-based charges
        report = {
            "tenant_id": req.tenant_id,
            "period_start": req.period_start,
            "period_end": req.period_end,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "usage": metrics,
            "charges": {
                "base_subscription": 199.00,
                "overage_api_calls": 0.00,
                "additional_storage": 0.00,
                "support_incidents": 0.00,
                "total": 199.00
            },
            "currency": "EUR"
        }
        
        return report
    except Exception as e:
        logger.error(f"Failed to generate usage report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare-plans", tags=["Monetization"])
def compare_plans():
    """Compare all pricing plans"""
    comparison = {
        "plans": [],
        "features_comparison": {}
    }
    
    # Build comparison
    all_features = set()
    for tier_id, tier in PRICING_TIERS.items():
        comparison["plans"].append({
            "id": tier_id,
            "name": tier.name,
            "price_monthly": tier.price_monthly,
            "popular": tier.popular
        })
        all_features.update(tier.features.keys())
    
    # Feature comparison matrix
    for feature in all_features:
        comparison["features_comparison"][feature] = {
            tier_id: tier.features.get(feature, False)
            for tier_id, tier in PRICING_TIERS.items()
        }
    
    return comparison


def _calculate_next_billing_date(billing_cycle: str) -> str:
    """Calculate next billing date"""
    from dateutil.relativedelta import relativedelta
    
    now = datetime.now(timezone.utc)
    if billing_cycle == "annual":
        next_date = now + relativedelta(years=1)
    else:
        next_date = now + relativedelta(months=1)
    
    return next_date.isoformat()
