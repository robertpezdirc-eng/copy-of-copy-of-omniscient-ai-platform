"""
SaaS Billing Tiers Management
Handles subscription plans, usage tracking, and billing for the Omni Platform
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["Billing & Subscriptions"])

# Data storage paths
BILLING_DATA_DIR = "data/billing"
SUBSCRIPTIONS_FILE = os.path.join(BILLING_DATA_DIR, "subscriptions.json")
USAGE_TRACKING_FILE = os.path.join(BILLING_DATA_DIR, "usage_tracking.json")
BILLING_PLANS_FILE = os.path.join(BILLING_DATA_DIR, "billing_plans.json")

# Ensure data directory exists
os.makedirs(BILLING_DATA_DIR, exist_ok=True)

class PlanTier(str, Enum):
    FREEMIUM = "freemium"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class BillingPlan(BaseModel):
    tier: PlanTier
    name: str
    price_monthly: float
    price_yearly: float
    api_calls_limit: int  # -1 for unlimited
    users_limit: int      # -1 for unlimited
    features: List[str]
    support_level: str
    sla_uptime: float
    custom_integrations: bool
    white_label: bool
    priority_support: bool

class Subscription(BaseModel):
    user_id: str
    plan_tier: PlanTier
    billing_cycle: str  # "monthly" or "yearly"
    start_date: datetime
    end_date: datetime
    status: str  # "active", "cancelled", "expired", "trial"
    auto_renew: bool = True
    stripe_subscription_id: Optional[str] = None
    usage_current_period: Dict[str, int] = Field(default_factory=dict)

class UsageRecord(BaseModel):
    user_id: str
    service: str  # "ai_agent", "quantum_compute", "api_call", "monitoring"
    usage_type: str  # "api_call", "compute_minutes", "storage_gb", "users"
    amount: int
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class BillingUsage(BaseModel):
    user_id: str
    period_start: datetime
    period_end: datetime
    api_calls: int = 0
    ai_agent_calls: int = 0
    quantum_compute_minutes: int = 0
    storage_gb: float = 0.0
    active_users: int = 0
    total_cost: float = 0.0

# Default billing plans configuration
DEFAULT_BILLING_PLANS = {
    PlanTier.FREEMIUM: BillingPlan(
        tier=PlanTier.FREEMIUM,
        name="Freemium",
        price_monthly=0.0,
        price_yearly=0.0,
        api_calls_limit=1000,
        users_limit=1,
        features=[
            "Basic AI Agents",
            "Standard API Access",
            "Community Support",
            "Basic Monitoring"
        ],
        support_level="Community",
        sla_uptime=99.0,
        custom_integrations=False,
        white_label=False,
        priority_support=False
    ),
    PlanTier.BASIC: BillingPlan(
        tier=PlanTier.BASIC,
        name="Basic",
        price_monthly=29.99,
        price_yearly=299.99,
        api_calls_limit=10000,
        users_limit=5,
        features=[
            "All Freemium Features",
            "Advanced AI Agents",
            "Quantum Computing (10 min/month)",
            "Email Support",
            "Advanced Analytics",
            "Custom Dashboards"
        ],
        support_level="Email",
        sla_uptime=99.5,
        custom_integrations=True,
        white_label=False,
        priority_support=False
    ),
    PlanTier.PRO: BillingPlan(
        tier=PlanTier.PRO,
        name="Professional",
        price_monthly=99.99,
        price_yearly=999.99,
        api_calls_limit=100000,
        users_limit=25,
        features=[
            "All Basic Features",
            "Unlimited Quantum Computing",
            "Priority Support",
            "Advanced Integrations",
            "Custom AI Agent Training",
            "White-label Options",
            "Advanced Security"
        ],
        support_level="Priority",
        sla_uptime=99.9,
        custom_integrations=True,
        white_label=True,
        priority_support=True
    ),
    PlanTier.ENTERPRISE: BillingPlan(
        tier=PlanTier.ENTERPRISE,
        name="Enterprise",
        price_monthly=499.99,
        price_yearly=4999.99,
        api_calls_limit=-1,  # Unlimited
        users_limit=-1,     # Unlimited
        features=[
            "All Pro Features",
            "Unlimited Everything",
            "Dedicated Support Manager",
            "Custom Development",
            "On-premise Deployment",
            "Advanced Security & Compliance",
            "Custom SLA",
            "24/7 Phone Support"
        ],
        support_level="Dedicated",
        sla_uptime=99.99,
        custom_integrations=True,
        white_label=True,
        priority_support=True
    )
}

def load_billing_plans() -> Dict[PlanTier, BillingPlan]:
    """Load billing plans from file or return defaults"""
    try:
        if os.path.exists(BILLING_PLANS_FILE):
            with open(BILLING_PLANS_FILE, 'r') as f:
                data = json.load(f)
                return {PlanTier(k): BillingPlan(**v) for k, v in data.items()}
    except Exception as e:
        logger.error(f"Error loading billing plans: {e}")
    
    # Save defaults if file doesn't exist
    save_billing_plans(DEFAULT_BILLING_PLANS)
    return DEFAULT_BILLING_PLANS

def save_billing_plans(plans: Dict[PlanTier, BillingPlan]):
    """Save billing plans to file"""
    try:
        data = {k.value: v.dict() for k, v in plans.items()}
        with open(BILLING_PLANS_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving billing plans: {e}")

def load_subscriptions() -> List[Subscription]:
    """Load subscriptions from file"""
    try:
        if os.path.exists(SUBSCRIPTIONS_FILE):
            with open(SUBSCRIPTIONS_FILE, 'r') as f:
                data = json.load(f)
                return [Subscription(**sub) for sub in data]
    except Exception as e:
        logger.error(f"Error loading subscriptions: {e}")
    return []

def save_subscriptions(subscriptions: List[Subscription]):
    """Save subscriptions to file"""
    try:
        data = [sub.dict() for sub in subscriptions]
        with open(SUBSCRIPTIONS_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving subscriptions: {e}")

def load_usage_records() -> List[UsageRecord]:
    """Load usage records from file"""
    try:
        if os.path.exists(USAGE_TRACKING_FILE):
            with open(USAGE_TRACKING_FILE, 'r') as f:
                data = json.load(f)
                return [UsageRecord(**record) for record in data]
    except Exception as e:
        logger.error(f"Error loading usage records: {e}")
    return []

def save_usage_records(records: List[UsageRecord]):
    """Save usage records to file"""
    try:
        data = [record.dict() for record in records]
        with open(USAGE_TRACKING_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving usage records: {e}")

@router.get("/plans", response_model=Dict[str, BillingPlan])
async def get_billing_plans():
    """Get all available billing plans"""
    plans = load_billing_plans()
    return {tier.value: plan for tier, plan in plans.items()}

@router.get("/plans/{tier}", response_model=BillingPlan)
async def get_billing_plan(tier: PlanTier):
    """Get specific billing plan details"""
    plans = load_billing_plans()
    if tier not in plans:
        raise HTTPException(status_code=404, detail="Billing plan not found")
    return plans[tier]

@router.post("/subscribe")
async def create_subscription(
    user_id: str,
    plan_tier: PlanTier,
    billing_cycle: str = "monthly"
):
    """Create new subscription for user"""
    if billing_cycle not in ["monthly", "yearly"]:
        raise HTTPException(status_code=400, detail="Invalid billing cycle")
    
    plans = load_billing_plans()
    if plan_tier not in plans:
        raise HTTPException(status_code=404, detail="Billing plan not found")
    
    subscriptions = load_subscriptions()
    
    # Check if user already has active subscription
    for sub in subscriptions:
        if sub.user_id == user_id and sub.status == "active":
            raise HTTPException(status_code=400, detail="User already has active subscription")
    
    # Create new subscription
    start_date = datetime.now()
    end_date = start_date + (timedelta(days=365) if billing_cycle == "yearly" else timedelta(days=30))
    
    new_subscription = Subscription(
        user_id=user_id,
        plan_tier=plan_tier,
        billing_cycle=billing_cycle,
        start_date=start_date,
        end_date=end_date,
        status="active" if plan_tier == PlanTier.FREEMIUM else "trial",
        usage_current_period={}
    )
    
    subscriptions.append(new_subscription)
    save_subscriptions(subscriptions)
    
    logger.info(f"Created subscription for user {user_id}: {plan_tier.value} ({billing_cycle})")
    
    return {
        "message": "Subscription created successfully",
        "subscription": new_subscription,
        "plan_details": plans[plan_tier]
    }

@router.get("/subscription/{user_id}", response_model=Subscription)
async def get_user_subscription(user_id: str):
    """Get user's current subscription"""
    subscriptions = load_subscriptions()
    
    for sub in subscriptions:
        if sub.user_id == user_id and sub.status in ["active", "trial"]:
            return sub
    
    raise HTTPException(status_code=404, detail="No active subscription found")

@router.post("/usage/track")
async def track_usage(usage: UsageRecord):
    """Track usage for billing purposes"""
    records = load_usage_records()
    usage.timestamp = datetime.now()
    records.append(usage)
    save_usage_records(records)
    
    # Update current period usage in subscription
    subscriptions = load_subscriptions()
    for sub in subscriptions:
        if sub.user_id == usage.user_id and sub.status in ["active", "trial"]:
            if usage.usage_type not in sub.usage_current_period:
                sub.usage_current_period[usage.usage_type] = 0
            sub.usage_current_period[usage.usage_type] += usage.amount
            break
    
    save_subscriptions(subscriptions)
    
    return {"message": "Usage tracked successfully", "usage": usage}

@router.get("/usage/{user_id}", response_model=BillingUsage)
async def get_user_usage(user_id: str, days: int = 30):
    """Get user's usage statistics for billing period"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    records = load_usage_records()
    user_records = [
        r for r in records 
        if r.user_id == user_id and start_date <= r.timestamp <= end_date
    ]
    
    usage = BillingUsage(
        user_id=user_id,
        period_start=start_date,
        period_end=end_date
    )
    
    for record in user_records:
        if record.usage_type == "api_call":
            usage.api_calls += record.amount
        elif record.usage_type == "ai_agent_call":
            usage.ai_agent_calls += record.amount
        elif record.usage_type == "quantum_compute_minutes":
            usage.quantum_compute_minutes += record.amount
        elif record.usage_type == "storage_gb":
            usage.storage_gb += record.amount
        elif record.usage_type == "active_users":
            usage.active_users = max(usage.active_users, record.amount)
    
    # Calculate total cost based on usage and plan
    try:
        subscription = await get_user_subscription(user_id)
        plans = load_billing_plans()
        plan = plans[subscription.plan_tier]
        
        if subscription.billing_cycle == "yearly":
            usage.total_cost = plan.price_yearly
        else:
            usage.total_cost = plan.price_monthly
            
    except HTTPException:
        usage.total_cost = 0.0
    
    return usage

@router.post("/upgrade")
async def upgrade_subscription(user_id: str, new_tier: PlanTier):
    """Upgrade user's subscription to higher tier"""
    subscriptions = load_subscriptions()
    
    for i, sub in enumerate(subscriptions):
        if sub.user_id == user_id and sub.status in ["active", "trial"]:
            # Validate upgrade path
            tier_order = [PlanTier.FREEMIUM, PlanTier.BASIC, PlanTier.PRO, PlanTier.ENTERPRISE]
            current_index = tier_order.index(sub.plan_tier)
            new_index = tier_order.index(new_tier)
            
            if new_index <= current_index:
                raise HTTPException(status_code=400, detail="Can only upgrade to higher tier")
            
            # Update subscription
            subscriptions[i].plan_tier = new_tier
            subscriptions[i].usage_current_period = {}  # Reset usage for new tier
            
            save_subscriptions(subscriptions)
            
            plans = load_billing_plans()
            return {
                "message": f"Successfully upgraded to {new_tier.value}",
                "subscription": subscriptions[i],
                "new_plan": plans[new_tier]
            }
    
    raise HTTPException(status_code=404, detail="No active subscription found")

@router.delete("/cancel/{user_id}")
async def cancel_subscription(user_id: str):
    """Cancel user's subscription"""
    subscriptions = load_subscriptions()
    
    for i, sub in enumerate(subscriptions):
        if sub.user_id == user_id and sub.status == "active":
            subscriptions[i].status = "cancelled"
            subscriptions[i].auto_renew = False
            save_subscriptions(subscriptions)
            
            return {"message": "Subscription cancelled successfully"}
    
    raise HTTPException(status_code=404, detail="No active subscription found")

@router.get("/analytics/revenue")
async def get_revenue_analytics():
    """Get revenue analytics for business dashboard"""
    subscriptions = load_subscriptions()
    plans = load_billing_plans()
    
    analytics = {
        "total_subscribers": len([s for s in subscriptions if s.status == "active"]),
        "monthly_recurring_revenue": 0.0,
        "annual_recurring_revenue": 0.0,
        "subscribers_by_tier": {},
        "churn_rate": 0.0,
        "average_revenue_per_user": 0.0
    }
    
    for tier in PlanTier:
        analytics["subscribers_by_tier"][tier.value] = 0
    
    total_revenue = 0.0
    for sub in subscriptions:
        if sub.status == "active":
            plan = plans[sub.plan_tier]
            analytics["subscribers_by_tier"][sub.plan_tier.value] += 1
            
            if sub.billing_cycle == "yearly":
                analytics["annual_recurring_revenue"] += plan.price_yearly
                total_revenue += plan.price_yearly
            else:
                analytics["monthly_recurring_revenue"] += plan.price_monthly
                total_revenue += plan.price_monthly * 12
    
    if analytics["total_subscribers"] > 0:
        analytics["average_revenue_per_user"] = total_revenue / analytics["total_subscribers"]
    
    return analytics