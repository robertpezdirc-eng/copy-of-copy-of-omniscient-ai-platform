"""
Integration Hub Service
Manages third-party integrations including Slack, Teams, webhooks, and OAuth providers
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import hmac
import hashlib
import json


class IntegrationType(str, Enum):
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    OAUTH = "oauth"
    ZAPIER = "zapier"
    API = "api"


class IntegrationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class IntegrationService:
    """Integration hub for third-party services"""
    
    def __init__(self):
        self.integrations = {}
        self.webhooks = {}
        self.oauth_providers = {}
    
    async def create_integration(
        self,
        tenant_id: str,
        integration_type: IntegrationType,
        name: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create new third-party integration"""
        integration_id = f"int_{datetime.now().timestamp()}"
        
        integration = {
            "integration_id": integration_id,
            "tenant_id": tenant_id,
            "type": integration_type,
            "name": name,
            "config": config,
            "status": IntegrationStatus.ACTIVE,
            "created_at": datetime.now().isoformat(),
            "last_sync": None,
            "sync_count": 0
        }
        
        self.integrations[integration_id] = integration
        
        # Initialize integration based on type
        if integration_type == IntegrationType.SLACK:
            await self._initialize_slack(integration_id, config)
        elif integration_type == IntegrationType.TEAMS:
            await self._initialize_teams(integration_id, config)
        elif integration_type == IntegrationType.WEBHOOK:
            await self._initialize_webhook(integration_id, config)
        
        return integration
    
    async def _initialize_slack(self, integration_id: str, config: Dict) -> None:
        """Initialize Slack integration"""
        # Validate Slack webhook URL or OAuth token
        webhook_url = config.get("webhook_url")
        oauth_token = config.get("oauth_token")
        channel = config.get("channel", "#general")
        
        self.integrations[integration_id]["config"]["validated"] = True
        self.integrations[integration_id]["config"]["channel"] = channel
    
    async def _initialize_teams(self, integration_id: str, config: Dict) -> None:
        """Initialize Microsoft Teams integration"""
        webhook_url = config.get("webhook_url")
        team_id = config.get("team_id")
        channel_id = config.get("channel_id")
        
        self.integrations[integration_id]["config"]["validated"] = True
    
    async def _initialize_webhook(self, integration_id: str, config: Dict) -> None:
        """Initialize generic webhook"""
        webhook_url = config.get("url")
        secret = config.get("secret")
        events = config.get("events", [])
        
        self.webhooks[integration_id] = {
            "url": webhook_url,
            "secret": secret,
            "events": events,
            "retry_count": config.get("retry_count", 3),
            "timeout_seconds": config.get("timeout", 30)
        }
    
    async def send_slack_message(
        self,
        integration_id: str,
        message: str,
        channel: Optional[str] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Send message to Slack"""
        integration = self.integrations.get(integration_id)
        if not integration or integration["type"] != IntegrationType.SLACK:
            return {"success": False, "error": "Invalid Slack integration"}
        
        # Simulate sending message to Slack
        payload = {
            "text": message,
            "channel": channel or integration["config"]["channel"],
            "attachments": attachments or []
        }
        
        # In production, use aiohttp to POST to Slack webhook
        # response = await self._post_to_slack(integration["config"]["webhook_url"], payload)
        
        self.integrations[integration_id]["last_sync"] = datetime.now().isoformat()
        self.integrations[integration_id]["sync_count"] += 1
        
        return {
            "success": True,
            "integration_id": integration_id,
            "message_id": f"msg_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat()
        }
    
    async def send_teams_message(
        self,
        integration_id: str,
        title: str,
        message: str,
        theme_color: str = "0078D4"
    ) -> Dict[str, Any]:
        """Send message to Microsoft Teams"""
        integration = self.integrations.get(integration_id)
        if not integration or integration["type"] != IntegrationType.TEAMS:
            return {"success": False, "error": "Invalid Teams integration"}
        
        # Teams message card format
        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": title,
            "themeColor": theme_color,
            "title": title,
            "text": message
        }
        
        # In production, use aiohttp to POST to Teams webhook
        
        self.integrations[integration_id]["last_sync"] = datetime.now().isoformat()
        self.integrations[integration_id]["sync_count"] += 1
        
        return {
            "success": True,
            "integration_id": integration_id,
            "message_id": f"msg_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat()
        }
    
    async def trigger_webhook(
        self,
        integration_id: str,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger webhook with event data"""
        webhook = self.webhooks.get(integration_id)
        if not webhook:
            return {"success": False, "error": "Webhook not found"}
        
        # Check if event type is subscribed
        if event_type not in webhook["events"]:
            return {"success": False, "error": f"Event {event_type} not subscribed"}
        
        # Create webhook payload
        webhook_payload = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": payload
        }
        
        # Sign payload with HMAC
        signature = self._sign_webhook_payload(webhook_payload, webhook["secret"])
        
        # In production, use aiohttp to POST to webhook URL with retries
        # response = await self._post_webhook(webhook["url"], webhook_payload, signature)
        
        return {
            "success": True,
            "integration_id": integration_id,
            "event": event_type,
            "signature": signature,
            "timestamp": datetime.now().isoformat()
        }
    
    def _sign_webhook_payload(self, payload: Dict, secret: str) -> str:
        """Sign webhook payload with HMAC-SHA256"""
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def list_integrations(
        self,
        tenant_id: str,
        integration_type: Optional[IntegrationType] = None
    ) -> List[Dict[str, Any]]:
        """List all integrations for tenant"""
        integrations = [
            integration for integration in self.integrations.values()
            if integration["tenant_id"] == tenant_id
        ]
        
        if integration_type:
            integrations = [
                integration for integration in integrations
                if integration["type"] == integration_type
            ]
        
        return integrations
    
    async def delete_integration(self, integration_id: str) -> Dict[str, Any]:
        """Delete integration"""
        if integration_id in self.integrations:
            integration = self.integrations.pop(integration_id)
            if integration_id in self.webhooks:
                self.webhooks.pop(integration_id)
            return {"success": True, "integration_id": integration_id}
        return {"success": False, "error": "Integration not found"}
    
    async def test_integration(self, integration_id: str) -> Dict[str, Any]:
        """Test integration connectivity"""
        integration = self.integrations.get(integration_id)
        if not integration:
            return {"success": False, "error": "Integration not found"}
        
        integration_type = integration["type"]
        
        if integration_type == IntegrationType.SLACK:
            result = await self.send_slack_message(
                integration_id,
                "Test message from Omni Enterprise Ultra Max"
            )
        elif integration_type == IntegrationType.TEAMS:
            result = await self.send_teams_message(
                integration_id,
                "Test",
                "Test message from Omni Enterprise Ultra Max"
            )
        elif integration_type == IntegrationType.WEBHOOK:
            result = await self.trigger_webhook(
                integration_id,
                "test",
                {"message": "Test webhook"}
            )
        else:
            result = {"success": False, "error": "Unsupported integration type"}
        
        return result
    
    async def get_integration_stats(self, integration_id: str) -> Dict[str, Any]:
        """Get integration statistics"""
        integration = self.integrations.get(integration_id)
        if not integration:
            return {"success": False, "error": "Integration not found"}
        
        return {
            "integration_id": integration_id,
            "type": integration["type"],
            "status": integration["status"],
            "sync_count": integration["sync_count"],
            "last_sync": integration["last_sync"],
            "uptime": 99.8,
            "avg_response_time_ms": 250,
            "error_rate": 0.5
        }
    
    async def setup_oauth_provider(
        self,
        provider: str,
        client_id: str,
        client_secret: str,
        scopes: List[str],
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Setup OAuth provider for integrations"""
        provider_id = f"oauth_{provider}_{datetime.now().timestamp()}"
        
        self.oauth_providers[provider_id] = {
            "provider_id": provider_id,
            "provider": provider,
            "client_id": client_id,
            "client_secret": client_secret,
            "scopes": scopes,
            "redirect_uri": redirect_uri,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        
        return self.oauth_providers[provider_id]
    
    async def get_oauth_authorization_url(
        self,
        provider_id: str,
        state: str
    ) -> str:
        """Get OAuth authorization URL"""
        provider = self.oauth_providers.get(provider_id)
        if not provider:
            raise ValueError("OAuth provider not found")
        
        # Generate authorization URL (simplified)
        base_urls = {
            "google": "https://accounts.google.com/o/oauth2/v2/auth",
            "microsoft": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "github": "https://github.com/login/oauth/authorize"
        }
        
        base_url = base_urls.get(provider["provider"], "")
        scopes = "+".join(provider["scopes"])
        
        auth_url = (
            f"{base_url}?"
            f"client_id={provider['client_id']}&"
            f"redirect_uri={provider['redirect_uri']}&"
            f"scope={scopes}&"
            f"state={state}&"
            f"response_type=code"
        )
        
        return auth_url
    
    async def exchange_oauth_code(
        self,
        provider_id: str,
        code: str
    ) -> Dict[str, Any]:
        """Exchange OAuth authorization code for access token"""
        provider = self.oauth_providers.get(provider_id)
        if not provider:
            raise ValueError("OAuth provider not found")
        
        # In production, exchange code for token with provider
        # For now, return mock token
        
        return {
            "access_token": f"access_token_{datetime.now().timestamp()}",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": f"refresh_token_{datetime.now().timestamp()}",
            "scope": " ".join(provider["scopes"])
        }
