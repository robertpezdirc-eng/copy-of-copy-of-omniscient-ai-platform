"""
Integration Hub API Routes
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel

from backend.services.integration_service import IntegrationService, IntegrationType

router = APIRouter(prefix="/api/v1/integrations", tags=["Integration Hub"])
integration_service = IntegrationService()


class CreateIntegrationRequest(BaseModel):
    tenant_id: str
    integration_type: IntegrationType
    name: str
    config: dict


class SlackMessageRequest(BaseModel):
    message: str
    channel: Optional[str] = None
    attachments: Optional[List[dict]] = None


class TeamsMessageRequest(BaseModel):
    title: str
    message: str
    theme_color: str = "0078D4"


class WebhookTriggerRequest(BaseModel):
    event_type: str
    payload: dict


@router.post("/create")
async def create_integration(request: CreateIntegrationRequest):
    """Create new third-party integration"""
    try:
        integration = await integration_service.create_integration(
            tenant_id=request.tenant_id,
            integration_type=request.integration_type,
            name=request.name,
            config=request.config
        )
        return integration
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/{tenant_id}")
async def list_integrations(
    tenant_id: str,
    integration_type: Optional[IntegrationType] = None
):
    """List all integrations for tenant"""
    try:
        integrations = await integration_service.list_integrations(
            tenant_id=tenant_id,
            integration_type=integration_type
        )
        return integrations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/slack/{integration_id}/send")
async def send_slack_message(integration_id: str, request: SlackMessageRequest):
    """Send message to Slack"""
    try:
        result = await integration_service.send_slack_message(
            integration_id=integration_id,
            message=request.message,
            channel=request.channel,
            attachments=request.attachments
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teams/{integration_id}/send")
async def send_teams_message(integration_id: str, request: TeamsMessageRequest):
    """Send message to Microsoft Teams"""
    try:
        result = await integration_service.send_teams_message(
            integration_id=integration_id,
            title=request.title,
            message=request.message,
            theme_color=request.theme_color
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/{integration_id}/trigger")
async def trigger_webhook(integration_id: str, request: WebhookTriggerRequest):
    """Trigger webhook with event data"""
    try:
        result = await integration_service.trigger_webhook(
            integration_id=integration_id,
            event_type=request.event_type,
            payload=request.payload
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{integration_id}/test")
async def test_integration(integration_id: str):
    """Test integration connectivity"""
    try:
        result = await integration_service.test_integration(integration_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{integration_id}/stats")
async def get_integration_stats(integration_id: str):
    """Get integration statistics"""
    try:
        stats = await integration_service.get_integration_stats(integration_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{integration_id}")
async def delete_integration(integration_id: str):
    """Delete integration"""
    try:
        result = await integration_service.delete_integration(integration_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
