"""
Customer Success & Engagement Routes
Provides health scoring, churn prediction, engagement tracking, onboarding, and customer journey management
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

router = APIRouter(prefix="/api/v1/customer-success", tags=["Customer Success"])


class HealthStatus(str, Enum):
    CRITICAL = "critical"
    AT_RISK = "at_risk"
    MODERATE = "moderate"
    HEALTHY = "healthy"
    EXCELLENT = "excellent"


class ChurnRisk(str, Enum):
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class OnboardingStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    STUCK = "stuck"


class PlaybookType(str, Enum):
    ONBOARDING = "onboarding"
    RENEWAL = "renewal"
    EXPANSION = "expansion"
    CHURN_PREVENTION = "churn_prevention"
    ESCALATION = "escalation"


# ==================== Customer Health Score ====================

@router.get("/health/{customer_id}")
async def get_customer_health(customer_id: str):
    """
    Get comprehensive customer health score
    Based on product usage, engagement, support tickets, payment history
    """
    return {
        "customer_id": customer_id,
        "company_name": "Acme Corporation",
        "overall_health_score": 78.5,
        "health_status": "healthy",
        "last_calculated": datetime.utcnow().isoformat(),
        "trend": "+5.2 points (30 days)",
        "components": {
            "product_usage": {
                "score": 85.0,
                "weight": 0.35,
                "metrics": {
                    "daily_active_users": 45,
                    "feature_adoption": 72.0,
                    "api_usage_trend": "increasing",
                    "login_frequency": "daily"
                }
            },
            "engagement": {
                "score": 75.0,
                "weight": 0.25,
                "metrics": {
                    "email_open_rate": 45.0,
                    "training_completed": 80.0,
                    "community_participation": "moderate",
                    "last_contact": "3 days ago"
                }
            },
            "support": {
                "score": 82.0,
                "weight": 0.20,
                "metrics": {
                    "open_tickets": 2,
                    "avg_resolution_time_hours": 12,
                    "satisfaction_score": 4.5,
                    "escalations": 0
                }
            },
            "financial": {
                "score": 70.0,
                "weight": 0.20,
                "metrics": {
                    "payment_status": "current",
                    "days_until_renewal": 45,
                    "expansion_potential": "high",
                    "payment_history": "good"
                }
            }
        },
        "risk_factors": [
            {
                "factor": "Declining feature usage",
                "impact": -3.5,
                "severity": "medium",
                "detected": "7 days ago"
            },
            {
                "factor": "Renewal approaching",
                "impact": -2.0,
                "severity": "low",
                "detected": "today"
            }
        ],
        "recommendations": [
            "Schedule business review meeting",
            "Showcase new features relevant to their use case",
            "Offer expansion discount before renewal"
        ]
    }


@router.get("/health/dashboard")
async def get_health_dashboard(
    status: Optional[HealthStatus] = None,
    segment: Optional[str] = None
):
    """
    Get health dashboard for all customers
    """
    return {
        "summary": {
            "total_customers": 1250,
            "average_health_score": 76.8,
            "by_status": {
                "excellent": 285,
                "healthy": 625,
                "moderate": 220,
                "at_risk": 95,
                "critical": 25
            }
        },
        "at_risk_customers": [
            {
                "customer_id": "cust-12345",
                "company_name": "TechStart Inc",
                "health_score": 45.0,
                "status": "at_risk",
                "churn_probability": 0.68,
                "arr": 48000,
                "days_until_renewal": 30,
                "csm_assigned": "Sarah Johnson"
            },
            {
                "customer_id": "cust-67890",
                "company_name": "DataFlow Systems",
                "health_score": 32.0,
                "status": "critical",
                "churn_probability": 0.85,
                "arr": 120000,
                "days_until_renewal": 15,
                "csm_assigned": "Mike Chen"
            }
        ],
        "trending_down": 45,
        "intervention_needed": 32,
        "success_stories": 18
    }


# ==================== Churn Prediction ====================

@router.get("/churn/prediction/{customer_id}")
async def predict_churn(customer_id: str):
    """
    Predict churn probability using ML model
    Identifies contributing factors and provides intervention recommendations
    """
    return {
        "customer_id": customer_id,
        "churn_probability": 0.68,
        "churn_risk": "high",
        "confidence": 0.92,
        "predicted_churn_date": (datetime.utcnow() + timedelta(days=45)).isoformat(),
        "model_version": "v2.5",
        "last_updated": datetime.utcnow().isoformat(),
        "contributing_factors": [
            {
                "factor": "Product usage declined 40%",
                "impact_score": 8.5,
                "weight": 0.35,
                "trend": "declining"
            },
            {
                "factor": "No login in 14 days",
                "impact_score": 7.2,
                "weight": 0.25,
                "trend": "static"
            },
            {
                "factor": "Support tickets increased",
                "impact_score": 6.5,
                "weight": 0.20,
                "trend": "increasing"
            },
            {
                "factor": "Renewal approaching (30 days)",
                "impact_score": 5.0,
                "weight": 0.15,
                "trend": "time-based"
            },
            {
                "factor": "No expansion in 12 months",
                "impact_score": 3.8,
                "weight": 0.05,
                "trend": "static"
            }
        ],
        "similar_customers_churned": 12,
        "similar_customers_retained": 8,
        "intervention_recommendations": [
            {
                "action": "Schedule executive check-in",
                "priority": "high",
                "expected_impact": "+15% retention",
                "effort": "medium"
            },
            {
                "action": "Provide personalized training",
                "priority": "high",
                "expected_impact": "+12% retention",
                "effort": "low"
            },
            {
                "action": "Offer renewal incentive",
                "priority": "medium",
                "expected_impact": "+8% retention",
                "effort": "low"
            }
        ],
        "estimated_recovery_probability": 0.72
    }


@router.get("/churn/risk-cohorts")
async def get_churn_risk_cohorts():
    """
    Get customers grouped by churn risk
    """
    return {
        "cohorts": [
            {
                "risk_level": "very_high",
                "count": 25,
                "total_arr": 2400000,
                "avg_churn_probability": 0.85,
                "avg_days_to_churn": 20,
                "csm_capacity": "overloaded"
            },
            {
                "risk_level": "high",
                "count": 70,
                "total_arr": 4200000,
                "avg_churn_probability": 0.65,
                "avg_days_to_churn": 45,
                "csm_capacity": "adequate"
            },
            {
                "risk_level": "medium",
                "count": 220,
                "total_arr": 8800000,
                "avg_churn_probability": 0.35,
                "avg_days_to_churn": 90,
                "csm_capacity": "good"
            },
            {
                "risk_level": "low",
                "count": 625,
                "total_arr": 31250000,
                "avg_churn_probability": 0.12,
                "avg_days_to_churn": 180,
                "csm_capacity": "good"
            },
            {
                "risk_level": "very_low",
                "count": 310,
                "total_arr": 18600000,
                "avg_churn_probability": 0.05,
                "avg_days_to_churn": 365,
                "csm_capacity": "excellent"
            }
        ],
        "total_at_risk_arr": 6600000,
        "intervention_pipeline": {
            "planned": 45,
            "in_progress": 28,
            "completed": 12
        }
    }


# ==================== Onboarding & Adoption ====================

@router.get("/onboarding/{customer_id}")
async def get_onboarding_status(customer_id: str):
    """
    Get onboarding progress and milestones
    """
    return {
        "customer_id": customer_id,
        "company_name": "Acme Corporation",
        "status": "in_progress",
        "overall_completion": 72.0,
        "started_at": "2024-01-10T00:00:00Z",
        "target_completion": "2024-02-10T00:00:00Z",
        "days_elapsed": 10,
        "days_remaining": 20,
        "on_track": True,
        "milestones": [
            {
                "milestone_id": "m1",
                "name": "Account Setup",
                "status": "completed",
                "completion_date": "2024-01-11T00:00:00Z",
                "tasks_completed": 5,
                "tasks_total": 5
            },
            {
                "milestone_id": "m2",
                "name": "Team Training",
                "status": "completed",
                "completion_date": "2024-01-15T00:00:00Z",
                "tasks_completed": 3,
                "tasks_total": 3
            },
            {
                "milestone_id": "m3",
                "name": "Integration Setup",
                "status": "in_progress",
                "completion_date": None,
                "tasks_completed": 4,
                "tasks_total": 6,
                "blocked": False
            },
            {
                "milestone_id": "m4",
                "name": "First Value Achievement",
                "status": "not_started",
                "completion_date": None,
                "tasks_completed": 0,
                "tasks_total": 4,
                "blocked": False
            },
            {
                "milestone_id": "m5",
                "name": "Full Adoption",
                "status": "not_started",
                "completion_date": None,
                "tasks_completed": 0,
                "tasks_total": 5,
                "blocked": False
            }
        ],
        "engagement_metrics": {
            "login_count": 45,
            "feature_adoption_rate": 65.0,
            "support_tickets": 3,
            "training_completion": 80.0
        },
        "blockers": [],
        "csm_notes": "Customer progressing well. Integration taking longer due to their internal IT review process."
    }


@router.post("/onboarding/{customer_id}/milestone/{milestone_id}/complete")
async def complete_milestone(customer_id: str, milestone_id: str):
    """
    Mark onboarding milestone as complete
    """
    return {
        "customer_id": customer_id,
        "milestone_id": milestone_id,
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat(),
        "completed_by": "csm-sarah@company.com",
        "next_milestone": "m4",
        "overall_completion": 80.0,
        "celebration_sent": True
    }


# ==================== Customer Journey ====================

@router.get("/journey/{customer_id}")
async def get_customer_journey(customer_id: str):
    """
    Get complete customer journey timeline
    """
    return {
        "customer_id": customer_id,
        "journey_start": "2024-01-01T00:00:00Z",
        "current_stage": "expansion",
        "days_as_customer": 20,
        "lifetime_value": 48000,
        "timeline": [
            {
                "date": "2024-01-01",
                "stage": "prospect",
                "event": "Signed up for trial",
                "type": "milestone",
                "details": {"source": "website", "campaign": "Q1-2024"}
            },
            {
                "date": "2024-01-05",
                "stage": "trial",
                "event": "Completed product demo",
                "type": "engagement",
                "details": {"demo_type": "personalized", "attendees": 3}
            },
            {
                "date": "2024-01-10",
                "stage": "customer",
                "event": "Converted to paid (Professional plan)",
                "type": "milestone",
                "details": {"plan": "professional", "arr": 36000}
            },
            {
                "date": "2024-01-12",
                "stage": "onboarding",
                "event": "Onboarding kickoff call",
                "type": "engagement",
                "details": {"csm": "Sarah Johnson", "attendees": 5}
            },
            {
                "date": "2024-01-18",
                "stage": "adoption",
                "event": "First integration completed",
                "type": "milestone",
                "details": {"integration": "Slack", "users": 25}
            },
            {
                "date": "2024-01-20",
                "stage": "expansion",
                "event": "Added 15 more users",
                "type": "milestone",
                "details": {"expansion_arr": 12000, "new_total_arr": 48000}
            }
        ],
        "upcoming_milestones": [
            {
                "milestone": "Quarterly Business Review",
                "due_date": "2024-02-01",
                "owner": "Sarah Johnson"
            },
            {
                "milestone": "Contract Renewal",
                "due_date": "2024-12-31",
                "owner": "Renewal Team"
            }
        ],
        "touchpoint_summary": {
            "total_touchpoints": 24,
            "calls": 6,
            "emails": 12,
            "product_usage_sessions": 145,
            "support_tickets": 3
        }
    }


# ==================== Engagement Tracking ====================

@router.post("/engagement/track")
async def track_engagement(
    customer_id: str,
    engagement_type: str,
    details: Dict[str, Any]
):
    """
    Track customer engagement event
    """
    return {
        "engagement_id": f"eng-{hash(customer_id) % 1000000}",
        "customer_id": customer_id,
        "engagement_type": engagement_type,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details,
        "recorded_by": "system",
        "health_score_impact": "+0.5"
    }


@router.get("/engagement/{customer_id}/metrics")
async def get_engagement_metrics(
    customer_id: str,
    days: int = Query(30, ge=1, le=365)
):
    """
    Get detailed engagement metrics
    """
    return {
        "customer_id": customer_id,
        "period_days": days,
        "engagement_score": 78.5,
        "trend": "+8.2%",
        "metrics": {
            "product_usage": {
                "daily_active_users": 45,
                "weekly_active_users": 67,
                "monthly_active_users": 85,
                "dau_mau_ratio": 0.53,
                "sessions_per_user": 4.2,
                "avg_session_duration_minutes": 35
            },
            "feature_adoption": {
                "features_available": 50,
                "features_used": 32,
                "adoption_rate": 64.0,
                "power_users": 8,
                "core_features_adoption": 95.0
            },
            "communication": {
                "emails_sent": 15,
                "emails_opened": 9,
                "open_rate": 60.0,
                "calls_completed": 3,
                "avg_call_duration_minutes": 45
            },
            "content": {
                "help_articles_viewed": 28,
                "webinars_attended": 2,
                "community_posts": 5,
                "training_completed": 80.0
            }
        },
        "engagement_events": [
            {
                "date": "2024-01-20",
                "type": "product_usage",
                "description": "High usage day - 58 active users",
                "sentiment": "positive"
            },
            {
                "date": "2024-01-18",
                "type": "training",
                "description": "Completed advanced features training",
                "sentiment": "positive"
            },
            {
                "date": "2024-01-15",
                "type": "support",
                "description": "Opened support ticket",
                "sentiment": "neutral"
            }
        ]
    }


# ==================== Success Playbooks ====================

@router.get("/playbooks")
async def list_playbooks(playbook_type: Optional[PlaybookType] = None):
    """
    List available success playbooks
    """
    return {
        "playbooks": [
            {
                "playbook_id": "pb-001",
                "name": "30-Day Onboarding",
                "type": "onboarding",
                "description": "Standard 30-day onboarding for mid-market customers",
                "steps": 15,
                "avg_completion_rate": 92.0,
                "success_rate": 88.0
            },
            {
                "playbook_id": "pb-002",
                "name": "Churn Prevention - High Risk",
                "type": "churn_prevention",
                "description": "Intensive intervention for at-risk customers",
                "steps": 8,
                "avg_completion_rate": 78.0,
                "success_rate": 65.0
            },
            {
                "playbook_id": "pb-003",
                "name": "Expansion - Upsell",
                "type": "expansion",
                "description": "Strategic upsell playbook for healthy customers",
                "steps": 10,
                "avg_completion_rate": 85.0,
                "success_rate": 72.0
            },
            {
                "playbook_id": "pb-004",
                "name": "Renewal - 90 Days Out",
                "type": "renewal",
                "description": "Proactive renewal engagement starting 90 days before",
                "steps": 12,
                "avg_completion_rate": 95.0,
                "success_rate": 94.0
            }
        ],
        "total": 4
    }


@router.post("/playbooks/{playbook_id}/execute")
async def execute_playbook(
    playbook_id: str,
    customer_id: str,
    assigned_to: str
):
    """
    Execute a playbook for a customer
    """
    return {
        "execution_id": f"exec-{hash(playbook_id + customer_id) % 1000000}",
        "playbook_id": playbook_id,
        "customer_id": customer_id,
        "assigned_to": assigned_to,
        "status": "active",
        "started_at": datetime.utcnow().isoformat(),
        "expected_completion": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "steps": [
            {"step": 1, "name": "Kickoff call", "status": "pending", "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat()},
            {"step": 2, "name": "Account setup review", "status": "pending", "due_date": (datetime.utcnow() + timedelta(days=3)).isoformat()},
            {"step": 3, "name": "Integration planning", "status": "pending", "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat()}
        ],
        "completion_percentage": 0,
        "automated_reminders": True
    }


# ==================== NPS & Feedback ====================

@router.post("/feedback/nps")
async def record_nps(
    customer_id: str,
    score: int = Query(..., ge=0, le=10),
    comment: Optional[str] = None,
    survey_id: Optional[str] = None
):
    """
    Record NPS (Net Promoter Score) response
    """
    return {
        "response_id": f"nps-{hash(customer_id) % 1000000}",
        "customer_id": customer_id,
        "score": score,
        "category": "promoter" if score >= 9 else ("passive" if score >= 7 else "detractor"),
        "comment": comment,
        "submitted_at": datetime.utcnow().isoformat(),
        "survey_id": survey_id,
        "follow_up_required": score <= 6,
        "assigned_to": "csm-team" if score <= 6 else None
    }


@router.get("/feedback/nps/analysis")
async def get_nps_analysis(days: int = Query(90, ge=1, le=365)):
    """
    Get NPS analysis and trends
    """
    return {
        "period_days": days,
        "nps_score": 42,
        "trend": "+5 points",
        "responses": 245,
        "distribution": {
            "promoters": 125,
            "passives": 75,
            "detractors": 45
        },
        "percentages": {
            "promoters": 51.0,
            "passives": 30.6,
            "detractors": 18.4
        },
        "by_segment": {
            "enterprise": {"nps": 52, "responses": 85},
            "mid_market": {"nps": 45, "responses": 120},
            "smb": {"nps": 28, "responses": 40}
        },
        "by_tenure": {
            "0_3_months": {"nps": 38, "responses": 55},
            "3_12_months": {"nps": 45, "responses": 95},
            "12_plus_months": {"nps": 48, "responses": 95}
        },
        "top_positive_themes": [
            {"theme": "Easy to use", "mentions": 45},
            {"theme": "Great support", "mentions": 38},
            {"theme": "Valuable features", "mentions": 32}
        ],
        "top_negative_themes": [
            {"theme": "Pricing concerns", "mentions": 18},
            {"theme": "Missing features", "mentions": 15},
            {"theme": "Performance issues", "mentions": 12}
        ]
    }


# ==================== CSM Workload Management ====================

@router.get("/csm/portfolio/{csm_id}")
async def get_csm_portfolio(csm_id: str):
    """
    Get CSM portfolio and workload
    """
    return {
        "csm_id": csm_id,
        "name": "Sarah Johnson",
        "email": "sarah.johnson@company.com",
        "portfolio": {
            "total_customers": 45,
            "total_arr": 2250000,
            "avg_health_score": 78.5,
            "at_risk_customers": 5,
            "at_risk_arr": 340000
        },
        "workload": {
            "capacity_utilization": 85.0,
            "recommended_capacity": 90.0,
            "status": "healthy",
            "upcoming_tasks": [
                {
                    "task": "Quarterly Business Review",
                    "customer": "Acme Corp",
                    "due_date": "2024-01-25",
                    "priority": "high"
                },
                {
                    "task": "Renewal discussion",
                    "customer": "TechStart Inc",
                    "due_date": "2024-01-28",
                    "priority": "critical"
                },
                {
                    "task": "Onboarding check-in",
                    "customer": "DataFlow Systems",
                    "due_date": "2024-01-23",
                    "priority": "medium"
                }
            ],
            "overdue_tasks": 2
        },
        "performance": {
            "customer_retention": 94.0,
            "expansion_rate": 125.0,
            "avg_health_improvement": "+6.2",
            "nps_avg": 48,
            "on_time_completion": 92.0
        }
    }


@router.get("/csm/recommendations")
async def get_csm_recommendations():
    """
    Get AI-powered recommendations for CSM team
    """
    return {
        "recommendations": [
            {
                "priority": "critical",
                "customer": "TechStart Inc",
                "issue": "High churn risk (85%) with renewal in 15 days",
                "recommended_action": "Immediate executive engagement + discount offer",
                "estimated_impact": "$120K ARR at risk",
                "csm": "Mike Chen"
            },
            {
                "priority": "high",
                "customer": "DataFlow Systems",
                "issue": "Onboarding stuck at 60% for 2 weeks",
                "recommended_action": "Technical support escalation for integration",
                "estimated_impact": "Prevent onboarding failure",
                "csm": "Sarah Johnson"
            },
            {
                "priority": "medium",
                "customer": "Acme Corp",
                "issue": "Strong expansion opportunity detected",
                "recommended_action": "Present enterprise plan upgrade",
                "estimated_impact": "+$45K ARR potential",
                "csm": "Sarah Johnson"
            }
        ],
        "team_metrics": {
            "total_at_risk_arr": 680000,
            "expansion_pipeline": 420000,
            "team_capacity": 82.0
        }
    }
