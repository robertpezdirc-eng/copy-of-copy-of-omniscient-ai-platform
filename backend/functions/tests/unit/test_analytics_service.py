"""
Unit tests for Analytics Service
"""

import pytest
from datetime import datetime, timedelta
from backend.services.analytics_service import AnalyticsService, ReportType, ReportFormat


@pytest.fixture
def analytics_service():
    return AnalyticsService()


@pytest.mark.asyncio
async def test_generate_usage_report(analytics_service):
    """Test usage report generation"""
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    report = await analytics_service.generate_report(
        tenant_id="tenant_123",
        report_type=ReportType.USAGE,
        start_date=start_date,
        end_date=end_date,
        format=ReportFormat.JSON
    )
    
    assert report["report_type"] == "usage"
    assert report["tenant_id"] == "tenant_123"
    assert "metrics" in report
    assert report["metrics"]["total_api_calls"] > 0


@pytest.mark.asyncio
async def test_generate_revenue_report(analytics_service):
    """Test revenue report generation"""
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    report = await analytics_service.generate_report(
        tenant_id="tenant_123",
        report_type=ReportType.REVENUE,
        start_date=start_date,
        end_date=end_date
    )
    
    assert report["report_type"] == "revenue"
    assert "metrics" in report
    assert "mrr" in report["metrics"]
    assert "arr" in report["metrics"]


@pytest.mark.asyncio
async def test_schedule_report(analytics_service):
    """Test report scheduling"""
    schedule = await analytics_service.schedule_report(
        tenant_id="tenant_123",
        report_type=ReportType.USAGE,
        schedule_cron="0 0 * * *",  # Daily at midnight
        format=ReportFormat.PDF,
        recipients=["admin@example.com"]
    )
    
    assert "schedule_id" in schedule
    assert schedule["status"] == "active"
    assert schedule["report_type"] == ReportType.USAGE


@pytest.mark.asyncio
async def test_get_analytics_dashboard(analytics_service):
    """Test analytics dashboard data"""
    dashboard = await analytics_service.get_analytics_dashboard("tenant_123")
    
    assert "overview" in dashboard
    assert "charts" in dashboard
    assert dashboard["overview"]["total_users"] > 0
