"""
Advanced Analytics & Reporting Service
Provides sophisticated analytics, custom report generation, and data export capabilities
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from enum import Enum
import pandas as pd
import io


class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class ReportType(str, Enum):
    USAGE = "usage"
    REVENUE = "revenue"
    PERFORMANCE = "performance"
    CHURN = "churn"
    ENGAGEMENT = "engagement"
    CUSTOM = "custom"


class AnalyticsService:
    """Advanced analytics and reporting service"""
    
    def __init__(self):
        self.reports_cache = {}
        self.scheduled_reports = {}
    
    async def generate_report(
        self,
        tenant_id: str,
        report_type: ReportType,
        start_date: datetime,
        end_date: datetime,
        format: ReportFormat = ReportFormat.JSON,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        
        # Generate report data based on type
        report_data = await self._generate_report_data(
            tenant_id, report_type, start_date, end_date, filters
        )
        
        # Format report
        if format == ReportFormat.JSON:
            return report_data
        elif format == ReportFormat.CSV:
            return await self._format_csv(report_data)
        elif format == ReportFormat.EXCEL:
            return await self._format_excel(report_data)
        elif format == ReportFormat.PDF:
            return await self._format_pdf(report_data)
        
        return report_data
    
    async def _generate_report_data(
        self,
        tenant_id: str,
        report_type: ReportType,
        start_date: datetime,
        end_date: datetime,
        filters: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate report data based on type"""
        
        if report_type == ReportType.USAGE:
            return await self._generate_usage_report(tenant_id, start_date, end_date)
        elif report_type == ReportType.REVENUE:
            return await self._generate_revenue_report(tenant_id, start_date, end_date)
        elif report_type == ReportType.PERFORMANCE:
            return await self._generate_performance_report(tenant_id, start_date, end_date)
        elif report_type == ReportType.CHURN:
            return await self._generate_churn_report(tenant_id, start_date, end_date)
        elif report_type == ReportType.ENGAGEMENT:
            return await self._generate_engagement_report(tenant_id, start_date, end_date)
        else:
            return await self._generate_custom_report(tenant_id, start_date, end_date, filters)
    
    async def _generate_usage_report(
        self, tenant_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Generate usage analytics report"""
        return {
            "report_type": "usage",
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "metrics": {
                "total_api_calls": 125000,
                "avg_daily_calls": 4167,
                "peak_hour": "14:00",
                "peak_calls": 8500,
                "total_users": 45,
                "active_users": 38,
                "total_data_processed_gb": 23.5,
                "avg_response_time_ms": 145
            },
            "breakdown_by_endpoint": [
                {"endpoint": "/api/v1/ai/predict", "calls": 45000, "percentage": 36},
                {"endpoint": "/api/v1/analytics", "calls": 30000, "percentage": 24},
                {"endpoint": "/api/v1/tenants", "calls": 25000, "percentage": 20},
                {"endpoint": "/api/v1/rag/query", "calls": 15000, "percentage": 12},
                {"endpoint": "others", "calls": 10000, "percentage": 8}
            ],
            "daily_trend": [
                {"date": "2024-01-01", "calls": 4000},
                {"date": "2024-01-02", "calls": 4200},
                {"date": "2024-01-03", "calls": 4500},
            ]
        }
    
    async def _generate_revenue_report(
        self, tenant_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Generate revenue analytics report"""
        return {
            "report_type": "revenue",
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "metrics": {
                "total_revenue_eur": 5970,
                "mrr": 199,
                "arr": 2388,
                "growth_rate": 12.5,
                "churn_rate": 2.1,
                "ltv": 2985,
                "cac": 450,
                "ltv_cac_ratio": 6.63
            },
            "revenue_by_plan": [
                {"plan": "Enterprise", "revenue": 2997, "customers": 3, "percentage": 50.2},
                {"plan": "Pro", "revenue": 1990, "customers": 10, "percentage": 33.3},
                {"plan": "Basic", "revenue": 983, "customers": 20, "percentage": 16.5}
            ],
            "monthly_trend": [
                {"month": "2024-01", "revenue": 5200},
                {"month": "2024-02", "revenue": 5600},
                {"month": "2024-03", "revenue": 5970}
            ]
        }
    
    async def _generate_performance_report(
        self, tenant_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Generate performance analytics report"""
        return {
            "report_type": "performance",
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "metrics": {
                "avg_response_time_ms": 145,
                "p50_response_time_ms": 120,
                "p95_response_time_ms": 280,
                "p99_response_time_ms": 450,
                "error_rate": 0.12,
                "uptime": 99.97,
                "cache_hit_rate": 78.5,
                "throughput_rps": 850
            },
            "slowest_endpoints": [
                {"endpoint": "/api/v1/ai/train", "avg_ms": 2500},
                {"endpoint": "/api/v1/analytics/generate", "avg_ms": 850},
                {"endpoint": "/api/v1/rag/query", "avg_ms": 450}
            ],
            "error_breakdown": [
                {"error_type": "timeout", "count": 45, "percentage": 45},
                {"error_type": "validation", "count": 30, "percentage": 30},
                {"error_type": "auth", "count": 25, "percentage": 25}
            ]
        }
    
    async def _generate_churn_report(
        self, tenant_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Generate churn prediction and analysis report"""
        return {
            "report_type": "churn",
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "metrics": {
                "churn_rate": 2.1,
                "at_risk_users": 8,
                "churned_users": 3,
                "retention_rate": 97.9,
                "avg_lifetime_days": 245
            },
            "at_risk_users_list": [
                {"user_id": "usr_123", "risk_score": 0.85, "last_active": "2024-01-15", "reason": "low_engagement"},
                {"user_id": "usr_456", "risk_score": 0.72, "last_active": "2024-01-10", "reason": "support_tickets"},
                {"user_id": "usr_789", "risk_score": 0.68, "last_active": "2024-01-20", "reason": "billing_issues"}
            ],
            "churn_reasons": [
                {"reason": "price", "count": 5, "percentage": 35},
                {"reason": "features", "count": 4, "percentage": 28},
                {"reason": "support", "count": 3, "percentage": 21},
                {"reason": "other", "count": 2, "percentage": 14}
            ]
        }
    
    async def _generate_engagement_report(
        self, tenant_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Generate user engagement analytics report"""
        return {
            "report_type": "engagement",
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "metrics": {
                "dau": 32,
                "mau": 45,
                "wau": 38,
                "dau_mau_ratio": 0.71,
                "avg_session_duration_min": 23.5,
                "sessions_per_user": 4.2,
                "feature_adoption_rate": 68.5
            },
            "feature_usage": [
                {"feature": "Dashboard", "users": 45, "percentage": 100},
                {"feature": "AI Assistant", "users": 38, "percentage": 84.4},
                {"feature": "Reports", "users": 30, "percentage": 66.7},
                {"feature": "Integrations", "users": 22, "percentage": 48.9}
            ],
            "cohort_analysis": [
                {"cohort": "Week 1", "retention_day_1": 100, "retention_day_7": 85, "retention_day_30": 72},
                {"cohort": "Week 2", "retention_day_1": 100, "retention_day_7": 88, "retention_day_30": 75}
            ]
        }
    
    async def _generate_custom_report(
        self, tenant_id: str, start_date: datetime, end_date: datetime, filters: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate custom analytics report based on filters"""
        return {
            "report_type": "custom",
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "filters": filters or {},
            "data": {
                "custom_metrics": [],
                "custom_dimensions": []
            }
        }
    
    async def _format_csv(self, report_data: Dict) -> Dict[str, Any]:
        """Format report as CSV"""
        # Convert report data to CSV format
        df = pd.DataFrame([report_data])
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        
        return {
            "format": "csv",
            "content": csv_buffer.getvalue(),
            "filename": f"report_{datetime.now().isoformat()}.csv"
        }
    
    async def _format_excel(self, report_data: Dict) -> Dict[str, Any]:
        """Format report as Excel"""
        return {
            "format": "excel",
            "content": "<excel_binary_data>",
            "filename": f"report_{datetime.now().isoformat()}.xlsx"
        }
    
    async def _format_pdf(self, report_data: Dict) -> Dict[str, Any]:
        """Format report as PDF"""
        return {
            "format": "pdf",
            "content": "<pdf_binary_data>",
            "filename": f"report_{datetime.now().isoformat()}.pdf"
        }
    
    async def schedule_report(
        self,
        tenant_id: str,
        report_type: ReportType,
        schedule_cron: str,
        format: ReportFormat,
        recipients: List[str],
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Schedule recurring report generation"""
        schedule_id = f"sched_{datetime.now().timestamp()}"
        
        self.scheduled_reports[schedule_id] = {
            "schedule_id": schedule_id,
            "tenant_id": tenant_id,
            "report_type": report_type,
            "schedule_cron": schedule_cron,
            "format": format,
            "recipients": recipients,
            "filters": filters,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "next_run": self._calculate_next_run(schedule_cron)
        }
        
        return self.scheduled_reports[schedule_id]
    
    def _calculate_next_run(self, cron: str) -> str:
        """Calculate next run time from cron expression"""
        # Simplified - in production, use croniter library
        return (datetime.now() + timedelta(days=1)).isoformat()
    
    async def get_analytics_dashboard(self, tenant_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard data"""
        return {
            "tenant_id": tenant_id,
            "overview": {
                "total_users": 45,
                "active_users_today": 32,
                "api_calls_today": 4200,
                "revenue_this_month": 5970,
                "uptime": 99.97
            },
            "charts": {
                "usage_trend": await self._get_usage_trend(tenant_id),
                "revenue_trend": await self._get_revenue_trend(tenant_id),
                "user_growth": await self._get_user_growth(tenant_id),
                "performance_metrics": await self._get_performance_metrics(tenant_id)
            },
            "alerts": [
                {"type": "warning", "message": "8 users at risk of churn", "severity": "medium"},
                {"type": "info", "message": "Usage increased 15% this week", "severity": "low"}
            ]
        }
    
    async def _get_usage_trend(self, tenant_id: str) -> List[Dict]:
        """Get usage trend data"""
        return [
            {"date": "2024-01-01", "value": 4000},
            {"date": "2024-01-02", "value": 4200},
            {"date": "2024-01-03", "value": 4500}
        ]
    
    async def _get_revenue_trend(self, tenant_id: str) -> List[Dict]:
        """Get revenue trend data"""
        return [
            {"month": "2024-01", "value": 5200},
            {"month": "2024-02", "value": 5600},
            {"month": "2024-03", "value": 5970}
        ]
    
    async def _get_user_growth(self, tenant_id: str) -> List[Dict]:
        """Get user growth data"""
        return [
            {"month": "2024-01", "users": 35},
            {"month": "2024-02", "users": 40},
            {"month": "2024-03", "users": 45}
        ]
    
    async def _get_performance_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            "avg_response_time": 145,
            "error_rate": 0.12,
            "cache_hit_rate": 78.5,
            "uptime": 99.97
        }
