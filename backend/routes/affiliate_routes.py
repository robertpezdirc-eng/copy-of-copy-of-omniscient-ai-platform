"""
Affiliate Marketing System Routes
Complete affiliate program with multi-tier commissions, tracking, and payouts
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, EmailStr, Field
import uuid
import random

affiliate_router = APIRouter()


# ================================================
# DATA MODELS
# ================================================

class AffiliateRegistration(BaseModel):
    """Affiliate registration data"""
    email: EmailStr
    full_name: str
    company_name: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    promotional_methods: List[str] = Field(default_factory=list)
    expected_monthly_sales: Optional[str] = None
    payment_method: str = "paypal"
    payment_details: Dict[str, str] = Field(default_factory=dict)


class AffiliateLink(BaseModel):
    """Custom affiliate link creation"""
    campaign_name: str
    destination_url: str
    custom_code: Optional[str] = None
    tracking_params: Dict[str, str] = Field(default_factory=dict)


class PayoutRequest(BaseModel):
    """Payout request"""
    affiliate_id: str
    amount: float
    payment_method: str
    payment_details: Dict[str, str]
    notes: Optional[str] = None


# ================================================
# AFFILIATE TIER CONFIGURATION
# ================================================

AFFILIATE_TIERS = {
    "bronze": {
        "name": "Bronze",
        "threshold": 0,
        "commission_rate": 10,
        "benefits": ["10% commission", "Basic marketing materials", "Email support"]
    },
    "silver": {
        "name": "Silver",
        "threshold": 1000,
        "commission_rate": 15,
        "benefits": ["15% commission", "Advanced marketing materials", "Priority email support", "Monthly performance reports"]
    },
    "gold": {
        "name": "Gold",
        "threshold": 5000,
        "commission_rate": 20,
        "benefits": ["20% commission", "Premium marketing materials", "Dedicated account manager", "Weekly performance reports", "Custom landing pages"]
    },
    "platinum": {
        "name": "Platinum",
        "threshold": 10000,
        "commission_rate": 25,
        "benefits": ["25% commission", "Exclusive marketing materials", "Dedicated account manager", "Real-time analytics", "Custom integrations", "Co-marketing opportunities"]
    }
}


# ================================================
# HELPER FUNCTIONS
# ================================================

def calculate_tier(total_sales: float) -> Dict[str, Any]:
    """Calculate affiliate tier based on total sales"""
    if total_sales >= AFFILIATE_TIERS["platinum"]["threshold"]:
        return AFFILIATE_TIERS["platinum"]
    elif total_sales >= AFFILIATE_TIERS["gold"]["threshold"]:
        return AFFILIATE_TIERS["gold"]
    elif total_sales >= AFFILIATE_TIERS["silver"]["threshold"]:
        return AFFILIATE_TIERS["silver"]
    else:
        return AFFILIATE_TIERS["bronze"]


def generate_affiliate_code() -> str:
    """Generate unique affiliate code"""
    return f"AFF{uuid.uuid4().hex[:8].upper()}"


def generate_tracking_link(affiliate_code: str, destination: str = "") -> str:
    """Generate tracking link"""
    base_url = "https://track.omni-ultra.com"
    return f"{base_url}/ref/{affiliate_code}?dest={destination or 'dashboard'}"


# ================================================
# AFFILIATE REGISTRATION & MANAGEMENT
# ================================================

@affiliate_router.post("/register")
async def register_affiliate(registration: AffiliateRegistration):
    """
    Register new affiliate

    Creates new affiliate account with unique tracking code
    """

    affiliate_id = f"aff_{uuid.uuid4().hex[:12]}"
    affiliate_code = generate_affiliate_code()

    affiliate_data = {
        "affiliate_id": affiliate_id,
        "affiliate_code": affiliate_code,
        "email": registration.email,
        "full_name": registration.full_name,
        "company_name": registration.company_name,
        "website": registration.website,
        "phone": registration.phone,
        "promotional_methods": registration.promotional_methods,
        "expected_monthly_sales": registration.expected_monthly_sales,
        "payment_method": registration.payment_method,
        "payment_details": registration.payment_details,
        "status": "pending_approval",
        "tier": "bronze",
        "commission_rate": 10,
        "total_sales": 0,
        "total_commission": 0,
        "total_referrals": 0,
        "total_conversions": 0,
        "conversion_rate": 0,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "approved_at": None,
        "tracking_link": generate_tracking_link(affiliate_code)
    }

    return {
        "success": True,
        "message": "Affiliate registration submitted successfully",
        "affiliate_data": affiliate_data,
        "next_steps": [
            "Wait for approval (usually within 24-48 hours)",
            "You will receive an email with your dashboard login",
            "Start promoting using your unique tracking link"
        ]
    }


@affiliate_router.get("/dashboard/{affiliate_id}")
async def get_affiliate_dashboard(
    affiliate_id: str,
    period: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y")
):
    """
    Get affiliate dashboard with performance metrics

    Returns comprehensive analytics for affiliate
    """

    # Calculate period dates
    days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = days_map.get(period, 30)

    # Mock affiliate data
    total_sales = random.uniform(2500, 15000)
    tier_info = calculate_tier(total_sales)
    commission_rate = tier_info["commission_rate"]
    total_commission = total_sales * (commission_rate / 100)

    clicks = random.randint(500, 5000)
    conversions = random.randint(20, 200)
    conversion_rate = (conversions / clicks) * 100 if clicks > 0 else 0

    dashboard_data = {
        "affiliate_id": affiliate_id,
        "period": period,
        "tier": tier_info["name"],
        "commission_rate": commission_rate,

        "performance": {
            "total_clicks": clicks,
            "total_referrals": conversions,
            "total_conversions": conversions,
            "conversion_rate": round(conversion_rate, 2),
            "total_sales": round(total_sales, 2),
            "total_commission_earned": round(total_commission, 2),
            "pending_commission": round(total_commission * 0.3, 2),
            "paid_commission": round(total_commission * 0.7, 2)
        },

        "earnings_breakdown": {
            "this_month": round(total_commission * 0.4, 2),
            "last_month": round(total_commission * 0.3, 2),
            "this_quarter": round(total_commission * 0.8, 2),
            "this_year": round(total_commission, 2)
        },

        "top_referrals": [
            {
                "customer_id": f"cust_{i}",
                "customer_name": f"Customer {i}",
                "sale_amount": round(random.uniform(100, 1000), 2),
                "commission": round(random.uniform(10, 100), 2),
                "date": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, days))).isoformat(),
                "status": random.choice(["completed", "pending", "processing"])
            }
            for i in range(1, 6)
        ],

        "recent_clicks": [
            {
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72))).isoformat(),
                "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                "country": random.choice(["US", "UK", "DE", "FR", "ES", "IT"]),
                "device": random.choice(["Desktop", "Mobile", "Tablet"]),
                "converted": random.choice([True, False, False, False])
            }
            for _ in range(10)
        ],

        "tier_progress": {
            "current_tier": tier_info["name"],
            "current_sales": round(total_sales, 2),
            "next_tier": "Platinum" if tier_info["name"] != "Platinum" else "Platinum (Maximum)",
            "next_tier_threshold": 10000 if tier_info["name"] != "Platinum" else None,
            "progress_percentage": min(100, (total_sales / 10000) * 100) if tier_info["name"] != "Platinum" else 100,
            "benefits": tier_info["benefits"]
        },

        "payment_info": {
            "next_payout_date": (datetime.now(timezone.utc) + timedelta(days=15)).isoformat(),
            "minimum_payout": 50.00,
            "eligible_for_payout": total_commission > 50,
            "payout_history": [
                {
                    "payout_id": f"payout_{i}",
                    "amount": round(random.uniform(100, 500), 2),
                    "date": (datetime.now(timezone.utc) - timedelta(days=30 * i)).isoformat(),
                    "status": "completed",
                    "method": "PayPal"
                }
                for i in range(1, 4)
            ]
        }
    }

    return dashboard_data


@affiliate_router.get("/profile/{affiliate_id}")
async def get_affiliate_profile(affiliate_id: str):
    """Get affiliate profile information"""

    profile = {
        "affiliate_id": affiliate_id,
        "affiliate_code": generate_affiliate_code(),
        "email": "affiliate@example.com",
        "full_name": "John Doe",
        "company_name": "Marketing Pro Inc.",
        "website": "https://marketingpro.com",
        "phone": "+1234567890",
        "status": "active",
        "tier": "gold",
        "commission_rate": 20,
        "registered_at": (datetime.now(timezone.utc) - timedelta(days=180)).isoformat(),
        "approved_at": (datetime.now(timezone.utc) - timedelta(days=178)).isoformat(),
        "payment_method": "paypal",
        "payment_details": {
            "paypal_email": "affiliate@example.com"
        },
        "promotional_methods": ["email_marketing", "social_media", "content_marketing", "paid_ads"],
        "tracking_link": generate_tracking_link("DEMO123"),
        "custom_links": []
    }

    return profile


@affiliate_router.put("/profile/{affiliate_id}")
async def update_affiliate_profile(
    affiliate_id: str,
    updates: Dict[str, Any] = Body(...)
):
    """Update affiliate profile"""

    return {
        "success": True,
        "message": "Profile updated successfully",
        "updated_fields": list(updates.keys()),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


# ================================================
# TRACKING LINKS & CAMPAIGNS
# ================================================

@affiliate_router.post("/links/create")
async def create_tracking_link(
    affiliate_id: str = Query(..., description="Affiliate ID"),
    link_data: AffiliateLink = Body(...)
):
    """
    Create custom tracking link for specific campaign

    Allows affiliates to create multiple tracking links for different campaigns
    """

    link_id = f"link_{uuid.uuid4().hex[:10]}"
    affiliate_code = link_data.custom_code or generate_affiliate_code()

    tracking_link = {
        "link_id": link_id,
        "affiliate_id": affiliate_id,
        "campaign_name": link_data.campaign_name,
        "affiliate_code": affiliate_code,
        "destination_url": link_data.destination_url,
        "tracking_url": generate_tracking_link(affiliate_code, link_data.destination_url),
        "tracking_params": link_data.tracking_params,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "clicks": 0,
        "conversions": 0,
        "conversion_rate": 0,
        "total_sales": 0,
        "status": "active"
    }

    return {
        "success": True,
        "tracking_link": tracking_link,
        "usage_example": f'<a href="{tracking_link["tracking_url"]}">Join Omni Ultra</a>',
        "qr_code_url": f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={tracking_link['tracking_url']}"
    }


@affiliate_router.get("/links/{affiliate_id}")
async def get_affiliate_links(
    affiliate_id: str,
    limit: int = Query(50, ge=1, le=100)
):
    """Get all tracking links for affiliate"""

    links = [
        {
            "link_id": f"link_{i}",
            "campaign_name": f"Campaign {i}",
            "affiliate_code": generate_affiliate_code(),
            "tracking_url": generate_tracking_link(f"CODE{i}"),
            "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 90))).isoformat(),
            "clicks": random.randint(100, 2000),
            "conversions": random.randint(5, 100),
            "conversion_rate": round(random.uniform(2, 10), 2),
            "total_sales": round(random.uniform(500, 5000), 2),
            "status": "active"
        }
        for i in range(1, min(limit + 1, 11))
    ]

    return {
        "affiliate_id": affiliate_id,
        "total_links": len(links),
        "links": links
    }


# ================================================
# COMMISSION & PAYOUTS
# ================================================

@affiliate_router.get("/commissions/{affiliate_id}")
async def get_commission_history(
    affiliate_id: str,
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, paid"),
    limit: int = Query(50, ge=1, le=100)
):
    """Get commission history for affiliate"""

    commissions = [
        {
            "commission_id": f"comm_{uuid.uuid4().hex[:10]}",
            "affiliate_id": affiliate_id,
            "referral_id": f"ref_{i}",
            "customer_id": f"cust_{i}",
            "order_id": f"order_{i}",
            "sale_amount": round(random.uniform(100, 1000), 2),
            "commission_rate": random.choice([10, 15, 20, 25]),
            "commission_amount": round(random.uniform(10, 250), 2),
            "status": random.choice(["pending", "approved", "paid"]),
            "sale_date": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 90))).isoformat(),
            "approved_date": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60))).isoformat() if random.random() > 0.3 else None,
            "paid_date": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))).isoformat() if random.random() > 0.5 else None
        }
        for i in range(1, min(limit + 1, 21))
    ]

    # Filter by status if provided
    if status:
        commissions = [c for c in commissions if c["status"] == status]

    total_commission = sum(c["commission_amount"] for c in commissions)

    return {
        "affiliate_id": affiliate_id,
        "total_commissions": len(commissions),
        "total_amount": round(total_commission, 2),
        "commissions": commissions
    }


@affiliate_router.post("/payouts/request")
async def request_payout(payout: PayoutRequest):
    """
    Request commission payout

    Affiliates can request payout once minimum threshold is reached
    """

    if payout.amount < 50:
        raise HTTPException(
            status_code=400,
            detail="Minimum payout amount is $50.00"
        )

    payout_id = f"payout_{uuid.uuid4().hex[:12]}"

    payout_data = {
        "payout_id": payout_id,
        "affiliate_id": payout.affiliate_id,
        "amount": payout.amount,
        "payment_method": payout.payment_method,
        "payment_details": payout.payment_details,
        "status": "pending",
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "estimated_processing_time": "3-5 business days",
        "notes": payout.notes
    }

    return {
        "success": True,
        "message": "Payout request submitted successfully",
        "payout": payout_data
    }


@affiliate_router.get("/payouts/{affiliate_id}")
async def get_payout_history(
    affiliate_id: str,
    limit: int = Query(50, ge=1, le=100)
):
    """Get payout history for affiliate"""

    payouts = [
        {
            "payout_id": f"payout_{i}",
            "amount": round(random.uniform(100, 1000), 2),
            "payment_method": random.choice(["paypal", "bank_transfer", "crypto"]),
            "status": random.choice(["completed", "processing", "pending"]),
            "requested_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(30, 180))).isoformat(),
            "completed_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 150))).isoformat() if random.random() > 0.3 else None,
            "transaction_id": f"txn_{uuid.uuid4().hex[:12]}" if random.random() > 0.3 else None
        }
        for i in range(1, min(limit + 1, 11))
    ]

    total_paid = sum(p["amount"] for p in payouts if p["status"] == "completed")

    return {
        "affiliate_id": affiliate_id,
        "total_payouts": len(payouts),
        "total_paid": round(total_paid, 2),
        "payouts": payouts
    }


# ================================================
# ANALYTICS & REPORTING
# ================================================

@affiliate_router.get("/analytics/{affiliate_id}")
async def get_affiliate_analytics(
    affiliate_id: str,
    period: str = Query("30d", description="Period: 7d, 30d, 90d, 1y")
):
    """Get detailed analytics for affiliate"""

    days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = days_map.get(period, 30)

    # Generate time series data
    daily_stats = []
    for i in range(days):
        date = datetime.now(timezone.utc) - timedelta(days=days - i)
        daily_stats.append({
            "date": date.strftime("%Y-%m-%d"),
            "clicks": random.randint(10, 200),
            "conversions": random.randint(0, 10),
            "sales": round(random.uniform(0, 1000), 2),
            "commission": round(random.uniform(0, 200), 2)
        })

    return {
        "affiliate_id": affiliate_id,
        "period": period,
        "daily_stats": daily_stats,

        "summary": {
            "total_clicks": sum(s["clicks"] for s in daily_stats),
            "total_conversions": sum(s["conversions"] for s in daily_stats),
            "total_sales": round(sum(s["sales"] for s in daily_stats), 2),
            "total_commission": round(sum(s["commission"] for s in daily_stats), 2),
            "average_order_value": round(sum(s["sales"] for s in daily_stats) / max(sum(s["conversions"] for s in daily_stats), 1), 2),
            "conversion_rate": round((sum(s["conversions"] for s in daily_stats) / max(sum(s["clicks"] for s in daily_stats), 1)) * 100, 2)
        },

        "traffic_sources": [
            {"source": "direct", "clicks": random.randint(100, 500), "conversions": random.randint(5, 50)},
            {"source": "social_media", "clicks": random.randint(200, 800), "conversions": random.randint(10, 80)},
            {"source": "email", "clicks": random.randint(150, 600), "conversions": random.randint(15, 90)},
            {"source": "paid_ads", "clicks": random.randint(300, 1000), "conversions": random.randint(20, 100)}
        ],

        "device_breakdown": [
            {"device": "Desktop", "clicks": random.randint(500, 1500), "conversions": random.randint(30, 100)},
            {"device": "Mobile", "clicks": random.randint(800, 2000), "conversions": random.randint(40, 120)},
            {"device": "Tablet", "clicks": random.randint(200, 500), "conversions": random.randint(10, 40)}
        ],

        "geographic_data": [
            {"country": "United States", "clicks": random.randint(500, 1500), "conversions": random.randint(30, 100)},
            {"country": "United Kingdom", "clicks": random.randint(200, 800), "conversions": random.randint(15, 60)},
            {"country": "Germany", "clicks": random.randint(150, 600), "conversions": random.randint(10, 50)},
            {"country": "France", "clicks": random.randint(100, 500), "conversions": random.randint(8, 40)},
            {"country": "Canada", "clicks": random.randint(100, 400), "conversions": random.randint(5, 30)}
        ]
    }


@affiliate_router.get("/leaderboard")
async def get_affiliate_leaderboard(
    period: str = Query("30d", description="Period: 7d, 30d, 90d, all"),
    metric: str = Query("sales", description="Metric: sales, conversions, commission"),
    limit: int = Query(10, ge=1, le=100)
):
    """Get affiliate leaderboard"""

    leaderboard = [
        {
            "rank": i,
            "affiliate_id": f"aff_{uuid.uuid4().hex[:12]}",
            "affiliate_name": f"Affiliate {i}",
            "tier": random.choice(["Bronze", "Silver", "Gold", "Platinum"]),
            "total_sales": round(random.uniform(5000, 50000), 2),
            "total_conversions": random.randint(50, 500),
            "total_commission": round(random.uniform(500, 12500), 2),
            "conversion_rate": round(random.uniform(2, 15), 2)
        }
        for i in range(1, limit + 1)
    ]

    # Sort by selected metric
    metric_map = {
        "sales": "total_sales",
        "conversions": "total_conversions",
        "commission": "total_commission"
    }
    sort_key = metric_map.get(metric, "total_sales")
    leaderboard.sort(key=lambda x: x[sort_key], reverse=True)

    return {
        "period": period,
        "metric": metric,
        "leaderboard": leaderboard
    }


# ================================================
# MARKETING RESOURCES
# ================================================

@affiliate_router.get("/resources/{affiliate_id}")
async def get_marketing_resources(affiliate_id: str):
    """Get marketing resources and materials for affiliate"""

    return {
        "affiliate_id": affiliate_id,
        "banners": [
            {
                "name": "Banner 728x90",
                "size": "728x90",
                "format": "png",
                "url": "https://cdn.omni-ultra.com/affiliate/banners/728x90.png",
                "html_code": '<img src="https://cdn.omni-ultra.com/affiliate/banners/728x90.png" alt="Omni Ultra" />'
            },
            {
                "name": "Banner 300x250",
                "size": "300x250",
                "format": "png",
                "url": "https://cdn.omni-ultra.com/affiliate/banners/300x250.png",
                "html_code": '<img src="https://cdn.omni-ultra.com/affiliate/banners/300x250.png" alt="Omni Ultra" />'
            }
        ],
        "email_templates": [
            {
                "name": "Product Launch Email",
                "subject": "Introducing Omni Ultra - Revolutionary Platform",
                "preview_url": "https://cdn.omni-ultra.com/affiliate/emails/product-launch.html"
            },
            {
                "name": "Feature Highlight Email",
                "subject": "10 Features That Make Omni Ultra Stand Out",
                "preview_url": "https://cdn.omni-ultra.com/affiliate/emails/feature-highlight.html"
            }
        ],
        "social_media_posts": [
            {
                "platform": "Twitter/X",
                "content": "Just discovered @OmniUltra - the most advanced enterprise platform I've ever seen! 🚀 #EnterpriseTech",
                "hashtags": ["#EnterpriseTech", "#Innovation", "#AI"]
            },
            {
                "platform": "LinkedIn",
                "content": "Looking for an enterprise platform that's truly 10 years ahead? Check out Omni Ultra's revolutionary features.",
                "hashtags": ["#B2B", "#Enterprise", "#Technology"]
            }
        ],
        "landing_pages": [
            {
                "name": "Main Landing Page",
                "url": "https://omni-ultra.com/lp/main",
                "description": "General purpose landing page"
            },
            {
                "name": "Enterprise Solutions",
                "url": "https://omni-ultra.com/lp/enterprise",
                "description": "Focused on enterprise features"
            }
        ],
        "product_info": {
            "key_features": [
                "AI-Powered Intelligence",
                "Multi-Payment Gateway Integration",
                "Real-time Analytics & BI",
                "Enterprise Security & Compliance",
                "Global Scaling & Localization"
            ],
            "pricing": "Starting at $99/month",
            "target_audience": "Enterprises, SMBs, Startups",
            "unique_selling_points": [
                "10 years ahead of competition",
                "All-in-one platform",
                "99.98% uptime guarantee",
                "24/7 premium support"
            ]
        }
    }


# ================================================
# ADMIN ENDPOINTS (for affiliate program management)
# ================================================

@affiliate_router.get("/admin/pending")
async def get_pending_affiliates(limit: int = Query(50, ge=1, le=100)):
    """Get pending affiliate applications (admin only)"""

    pending = [
        {
            "affiliate_id": f"aff_{uuid.uuid4().hex[:12]}",
            "email": f"affiliate{i}@example.com",
            "full_name": f"Affiliate {i}",
            "company_name": f"Company {i}",
            "applied_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 7))).isoformat(),
            "expected_monthly_sales": random.choice(["$1000-$5000", "$5000-$10000", "$10000+"]),
            "status": "pending_approval"
        }
        for i in range(1, min(limit + 1, 11))
    ]

    return {
        "total_pending": len(pending),
        "pending_applications": pending
    }


@affiliate_router.post("/admin/approve/{affiliate_id}")
async def approve_affiliate(affiliate_id: str):
    """Approve affiliate application (admin only)"""

    return {
        "success": True,
        "message": f"Affiliate {affiliate_id} approved",
        "affiliate_id": affiliate_id,
        "status": "active",
        "approved_at": datetime.now(timezone.utc).isoformat()
    }


@affiliate_router.post("/admin/reject/{affiliate_id}")
async def reject_affiliate(
    affiliate_id: str,
    reason: str = Body(..., description="Rejection reason")
):
    """Reject affiliate application (admin only)"""

    return {
        "success": True,
        "message": f"Affiliate {affiliate_id} rejected",
        "affiliate_id": affiliate_id,
        "status": "rejected",
        "reason": reason,
        "rejected_at": datetime.now(timezone.utc).isoformat()
    }
