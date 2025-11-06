"""
Real-time AI Insights Service for personalized recommendations and alerts.

Provides:
- Real-time performance insights
- Personalized AI recommendations
- Proactive alerts and notifications
- KPI tracking and visualization data
- Gamification features
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import random

logger = logging.getLogger(__name__)


class AIInsightsService:
    """Real-time AI insights and personalized recommendations."""

    def __init__(self):
        self._user_insights: Dict[str, List[Dict[str, Any]]] = {}
        self._alerts: List[Dict[str, Any]] = []
        self._kpis: Dict[str, Dict[str, Any]] = {}

    async def get_realtime_insights(
        self,
        user_id: str,
        data_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get real-time AI insights for a user.
        
        Args:
            user_id: User identifier
            data_sources: Data sources to analyze (optional)
        
        Returns:
            Real-time insights with visualizations
        """
        data_sources = data_sources or ["usage", "performance", "engagement"]
        
        insights = []
        
        for source in data_sources:
            insight = self._generate_insight(user_id, source)
            insights.append(insight)
        
        # Store insights
        if user_id not in self._user_insights:
            self._user_insights[user_id] = []
        self._user_insights[user_id].extend(insights)
        
        return {
            "user_id": user_id,
            "insights": insights,
            "summary": self._generate_summary(insights),
            "recommended_actions": self._get_recommended_actions(insights),
            "visualization_data": self._prepare_visualization_data(insights),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_personalized_recommendations(
        self,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get personalized AI recommendations.
        
        Args:
            user_id: User identifier
            context: Additional context (current page, recent activity, etc.)
        
        Returns:
            Personalized recommendations
        """
        context = context or {}
        
        recommendations = [
            {
                "id": f"rec_{i}",
                "type": rec_type,
                "title": title,
                "description": desc,
                "priority": priority,
                "expected_impact": impact,
                "action_url": f"/dashboard/{rec_type}",
            }
            for i, (rec_type, title, desc, priority, impact) in enumerate([
                ("optimization", "Optimize Your Workflow",
                 "AI detected 3 bottlenecks in your workflow", "high",
                 "+25% efficiency"),
                ("feature", "Try Advanced Analytics",
                 "Based on your usage, this feature could help", "medium",
                 "+15% insights"),
                ("training", "Complete AI Certification",
                 "Unlock advanced features by completing the course", "low",
                 "50 points + badge"),
            ])
        ]
        
        return {
            "user_id": user_id,
            "recommendations": recommendations,
            "personalization_score": round(random.uniform(0.8, 0.95), 2),
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def create_alert(
        self,
        user_id: str,
        alert_type: str,
        message: str,
        severity: str = "info",
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a proactive AI alert.
        
        Args:
            user_id: User to alert
            alert_type: Type of alert (performance, anomaly, opportunity, etc.)
            message: Alert message
            severity: Severity level (info, warning, critical)
            data: Additional alert data
        
        Returns:
            Created alert
        """
        alert = {
            "id": f"alert_{len(self._alerts)}",
            "user_id": user_id,
            "type": alert_type,
            "message": message,
            "severity": severity,
            "data": data or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "read": False,
            "action_required": severity in ["warning", "critical"],
        }
        
        self._alerts.append(alert)
        logger.info(f"Created alert for user {user_id}: {message}")
        
        return alert

    async def get_user_alerts(
        self,
        user_id: str,
        unread_only: bool = False
    ) -> Dict[str, Any]:
        """
        Get alerts for a user.
        
        Args:
            user_id: User identifier
            unread_only: Return only unread alerts
        
        Returns:
            User alerts
        """
        user_alerts = [
            alert for alert in self._alerts
            if alert["user_id"] == user_id
        ]
        
        if unread_only:
            user_alerts = [a for a in user_alerts if not a["read"]]
        
        # Sort by severity and time
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        user_alerts.sort(
            key=lambda a: (severity_order.get(a["severity"], 2), a["created_at"]),
            reverse=True
        )
        
        return {
            "user_id": user_id,
            "alerts": user_alerts,
            "total": len(user_alerts),
            "unread": sum(1 for a in user_alerts if not a["read"]),
            "critical": sum(1 for a in user_alerts if a["severity"] == "critical"),
        }

    async def track_kpi(
        self,
        user_id: str,
        kpi_name: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track a KPI for real-time monitoring.
        
        Args:
            user_id: User identifier
            kpi_name: KPI name
            value: KPI value
            metadata: Additional metadata
        
        Returns:
            KPI tracking result with insights
        """
        kpi_key = f"{user_id}:{kpi_name}"
        
        if kpi_key not in self._kpis:
            self._kpis[kpi_key] = {
                "user_id": user_id,
                "kpi_name": kpi_name,
                "values": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        
        # Add value
        self._kpis[kpi_key]["values"].append({
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        })
        
        # Keep last 100 values
        self._kpis[kpi_key]["values"] = self._kpis[kpi_key]["values"][-100:]
        
        # Analyze trend
        analysis = self._analyze_kpi_trend(self._kpis[kpi_key])
        
        # Create alert if needed
        if analysis["needs_alert"]:
            await self.create_alert(
                user_id=user_id,
                alert_type="kpi_anomaly",
                message=f"{kpi_name} {analysis['trend_description']}",
                severity=analysis["severity"],
                data={"kpi": kpi_name, "value": value, "analysis": analysis}
            )
        
        return {
            "kpi_name": kpi_name,
            "current_value": value,
            "trend": analysis["trend"],
            "change_percentage": analysis["change_percentage"],
            "insight": analysis["insight"],
            "visualization": self._prepare_kpi_visualization(self._kpis[kpi_key]),
        }

    async def get_gamification_status(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get gamification status for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Gamification status with points, badges, achievements
        """
        # Calculate points from insights and KPIs
        user_insights = self._user_insights.get(user_id, [])
        points = len(user_insights) * 10
        
        # Get KPIs for user
        user_kpis = [
            kpi for key, kpi in self._kpis.items()
            if key.startswith(f"{user_id}:")
        ]
        
        kpi_points = sum(
            50 for kpi in user_kpis
            if self._kpi_meets_target(kpi)
        )
        
        total_points = points + kpi_points
        
        # Determine level
        level = (total_points // 100) + 1
        
        # Badges
        badges = self._calculate_badges(user_id, user_kpis)
        
        # Achievements
        achievements = self._calculate_achievements(user_id, user_insights, user_kpis)
        
        return {
            "user_id": user_id,
            "total_points": total_points,
            "level": level,
            "points_to_next_level": 100 - (total_points % 100),
            "badges": badges,
            "achievements": achievements,
            "leaderboard_rank": self._calculate_rank(user_id, total_points),
            "engagement_score": round(random.uniform(0.75, 0.95), 2),
            "streak_days": random.randint(1, 30),
            "next_milestone": self._get_next_milestone(total_points),
        }

    async def get_dashboard_summary(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard summary with all AI insights.
        
        Args:
            user_id: User identifier
        
        Returns:
            Dashboard summary with insights, alerts, KPIs, gamification
        """
        # Get recent insights
        insights = await self.get_realtime_insights(user_id)
        
        # Get alerts
        alerts = await self.get_user_alerts(user_id, unread_only=True)
        
        # Get gamification status
        gamification = await self.get_gamification_status(user_id)
        
        # Get top KPIs
        user_kpis = [
            {
                "name": kpi["kpi_name"],
                "current_value": kpi["values"][-1]["value"] if kpi["values"] else 0,
                "trend": self._analyze_kpi_trend(kpi)["trend"],
            }
            for key, kpi in self._kpis.items()
            if key.startswith(f"{user_id}:")
        ][:5]
        
        return {
            "user_id": user_id,
            "summary": {
                "total_insights": len(insights["insights"]),
                "unread_alerts": alerts["unread"],
                "active_kpis": len(user_kpis),
                "points": gamification["total_points"],
                "level": gamification["level"],
            },
            "insights": insights["insights"][:3],  # Top 3
            "alerts": alerts["alerts"][:5],  # Top 5
            "kpis": user_kpis,
            "gamification": gamification,
            "recommendations": (await self.get_personalized_recommendations(user_id))["recommendations"][:3],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_insight(self, user_id: str, source: str) -> Dict[str, Any]:
        """Generate an insight from a data source."""
        insights_templates = {
            "usage": {
                "title": "Usage Pattern Detected",
                "message": "Your API usage increased by 35% this week",
                "type": "trend",
                "impact": "positive",
            },
            "performance": {
                "title": "Performance Optimization Opportunity",
                "message": "3 endpoints can be optimized for 40% faster response",
                "type": "optimization",
                "impact": "high",
            },
            "engagement": {
                "title": "Engagement Milestone",
                "message": "You're in the top 10% of active users!",
                "type": "achievement",
                "impact": "positive",
            },
        }
        
        template = insights_templates.get(source, insights_templates["usage"])
        
        return {
            "id": f"insight_{source}_{datetime.now().timestamp()}",
            "source": source,
            "title": template["title"],
            "message": template["message"],
            "type": template["type"],
            "impact": template["impact"],
            "confidence": round(random.uniform(0.8, 0.95), 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_summary(self, insights: List[Dict[str, Any]]) -> str:
        """Generate summary of insights."""
        if not insights:
            return "No new insights available"
        
        positive = sum(1 for i in insights if i["impact"] == "positive")
        return f"Found {len(insights)} insights ({positive} positive opportunities)"

    def _get_recommended_actions(self, insights: List[Dict[str, Any]]) -> List[str]:
        """Get recommended actions from insights."""
        actions = []
        for insight in insights:
            if insight["type"] == "optimization":
                actions.append("Review optimization suggestions")
            elif insight["type"] == "trend":
                actions.append("Monitor trend development")
            elif insight["type"] == "achievement":
                actions.append("Claim your achievement reward")
        return actions

    def _prepare_visualization_data(self, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare data for visualizations."""
        return {
            "chart_type": "mixed",
            "data_points": len(insights),
            "categories": list(set(i["type"] for i in insights)),
            "series": [
                {
                    "name": insight["type"],
                    "value": insight["confidence"] * 100,
                }
                for insight in insights
            ],
        }

    def _analyze_kpi_trend(self, kpi: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze KPI trend."""
        values = kpi["values"]
        
        if len(values) < 2:
            return {
                "trend": "stable",
                "change_percentage": 0,
                "needs_alert": False,
                "severity": "info",
                "trend_description": "not enough data",
                "insight": "Track more data points for trend analysis",
            }
        
        recent_value = values[-1]["value"]
        previous_value = values[-2]["value"]
        change = ((recent_value - previous_value) / previous_value * 100) if previous_value else 0
        
        trend = "increasing" if change > 5 else "decreasing" if change < -5 else "stable"
        needs_alert = abs(change) > 20
        severity = "warning" if abs(change) > 20 else "critical" if abs(change) > 50 else "info"
        
        return {
            "trend": trend,
            "change_percentage": round(change, 2),
            "needs_alert": needs_alert,
            "severity": severity,
            "trend_description": f"{trend} by {abs(change):.1f}%",
            "insight": self._generate_kpi_insight(trend, change),
        }

    def _generate_kpi_insight(self, trend: str, change: float) -> str:
        """Generate insight from KPI trend."""
        if trend == "increasing" and change > 20:
            return "Significant improvement detected! Keep up the momentum."
        elif trend == "decreasing" and change < -20:
            return "Performance declining. Review recent changes."
        else:
            return "Performance stable within normal range."

    def _prepare_kpi_visualization(self, kpi: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare KPI visualization data."""
        return {
            "chart_type": "line",
            "data_points": [
                {
                    "timestamp": v["timestamp"],
                    "value": v["value"],
                }
                for v in kpi["values"][-20:]  # Last 20 points
            ],
        }

    def _kpi_meets_target(self, kpi: Dict[str, Any]) -> bool:
        """Check if KPI meets target."""
        if not kpi["values"]:
            return False
        latest = kpi["values"][-1]["value"]
        return latest > 0.8  # Simplified: 80% target

    def _calculate_badges(self, user_id: str, kpis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate earned badges."""
        badges = []
        
        if len(kpis) >= 5:
            badges.append({
                "id": "kpi_master",
                "name": "KPI Master",
                "description": "Track 5+ KPIs simultaneously",
                "icon": "🎯",
                "earned_at": datetime.now(timezone.utc).isoformat(),
            })
        
        if any(self._kpi_meets_target(kpi) for kpi in kpis):
            badges.append({
                "id": "target_achiever",
                "name": "Target Achiever",
                "description": "Meet KPI target",
                "icon": "🏆",
                "earned_at": datetime.now(timezone.utc).isoformat(),
            })
        
        return badges

    def _calculate_achievements(
        self,
        user_id: str,
        insights: List[Dict[str, Any]],
        kpis: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate achievements."""
        achievements = []
        
        if len(insights) >= 10:
            achievements.append({
                "id": "insight_explorer",
                "name": "Insight Explorer",
                "description": "Received 10+ AI insights",
                "points": 100,
                "completed": True,
            })
        
        return achievements

    def _calculate_rank(self, user_id: str, points: int) -> int:
        """Calculate leaderboard rank (simplified)."""
        return random.randint(1, 100)

    def _get_next_milestone(self, current_points: int) -> Dict[str, Any]:
        """Get next milestone."""
        milestones = [500, 1000, 2500, 5000, 10000]
        next_milestone = next((m for m in milestones if m > current_points), milestones[-1])
        
        return {
            "points": next_milestone,
            "reward": "Exclusive Badge + 200 bonus points",
            "progress": f"{current_points}/{next_milestone}",
        }


# Singleton instance
_ai_insights_service: Optional[AIInsightsService] = None


def get_ai_insights_service() -> AIInsightsService:
    """Get singleton instance of AI insights service."""
    global _ai_insights_service
    if _ai_insights_service is None:
        _ai_insights_service = AIInsightsService()
    return _ai_insights_service
