#!/usr/bin/env python3
"""
OMNI Platform API Client
Client for communicating with OMNI platform Google Cloud Functions
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio
import aiohttp
import requests
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class OmniPlatformError(Exception):
    """Custom exception for OMNI platform API errors"""
    pass

@dataclass
class ConversationMetrics:
    """Conversation metrics from OMNI platform"""
    total_conversations: int
    today_conversations: int
    avg_response_time: float
    success_rate: float
    error_count: int
    last_activity: datetime

@dataclass
class PlatformStatus:
    """OMNI platform status information"""
    status: str
    platform: str
    provider: str
    deployment: str
    project_id: str
    gemini_model: str
    services: Dict[str, str]
    features: List[str]
    timestamp: datetime

@dataclass
class Conversation:
    """Individual conversation data"""
    query: str
    response: str
    timestamp: datetime
    user_id: str
    success: bool

class OmniPlatformClient:
    """
    Client for communicating with OMNI platform Google Cloud Functions
    """

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.project_id = os.environ.get('PROJECT_ID', 'gen-lang-client-0885737339')
        self.region = os.environ.get('REGION', 'europe-west1')

        if base_url:
            self.base_url = base_url
        else:
            self.base_url = f"https://{self.region}-{self.project_id}.cloudfunctions.net"

        self.api_key = api_key or os.environ.get('OMNI_API_KEY')
        self.session = None

        # API endpoints
        self.endpoints = {
            'chat': f'{self.base_url}/omni-chat',
            'status': f'{self.base_url}/omni-status',
            'health': f'{self.base_url}/omni-health'
        }

        logger.info(f"OMNI Platform Client initialized for {self.base_url}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()

    async def create_session(self):
        """Create aiohttp session for async requests"""
        if not self.session:
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for requests"""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

    # Synchronous methods for simple operations
    def get_platform_status(self) -> PlatformStatus:
        """Get current platform status"""
        try:
            response = requests.get(
                self.endpoints['status'],
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            return PlatformStatus(
                status=data.get('status', 'unknown'),
                platform=data.get('platform', 'unknown'),
                provider=data.get('provider', 'unknown'),
                deployment=data.get('deployment', 'unknown'),
                project_id=data.get('project_id', self.project_id),
                gemini_model=data.get('gemini_model', 'unknown'),
                services=data.get('services', {}),
                features=data.get('features', []),
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.utcnow().isoformat()))
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting platform status: {e}")
            raise OmniPlatformError(f"Failed to get platform status: {e}")

    def get_health_status(self) -> Dict[str, Any]:
        """Get health check status"""
        try:
            response = requests.get(
                self.endpoints['health'],
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting health status: {e}")
            raise OmniPlatformError(f"Failed to get health status: {e}")

    def send_chat_message(self, message: str, user_id: str = 'dashboard') -> Dict[str, Any]:
        """Send a chat message to OMNI platform"""
        try:
            payload = {
                'message': message,
                'user_id': user_id
            }

            response = requests.post(
                self.endpoints['chat'],
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending chat message: {e}")
            raise OmniPlatformError(f"Failed to send chat message: {e}")

    # Async methods for better performance
    async def get_platform_status_async(self) -> PlatformStatus:
        """Get current platform status (async)"""
        if not self.session:
            await self.create_session()

        try:
            async with self.session.get(self.endpoints['status']) as response:
                response.raise_for_status()
                data = await response.json()

                return PlatformStatus(
                    status=data.get('status', 'unknown'),
                    platform=data.get('platform', 'unknown'),
                    provider=data.get('provider', 'unknown'),
                    deployment=data.get('deployment', 'unknown'),
                    project_id=data.get('project_id', self.project_id),
                    gemini_model=data.get('gemini_model', 'unknown'),
                    services=data.get('services', {}),
                    features=data.get('features', []),
                    timestamp=datetime.fromisoformat(data.get('timestamp', datetime.utcnow().isoformat()))
                )

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Error getting platform status: {e}")
            raise OmniPlatformError(f"Failed to get platform status: {e}")

    async def send_chat_message_async(self, message: str, user_id: str = 'dashboard') -> Dict[str, Any]:
        """Send a chat message to OMNI platform (async)"""
        if not self.session:
            await self.create_session()

        try:
            payload = {
                'message': message,
                'user_id': user_id
            }

            async with self.session.post(
                self.endpoints['chat'],
                json=payload
            ) as response:
                response.raise_for_status()
                return await response.json()

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Error sending chat message: {e}")
            raise OmniPlatformError(f"Failed to send chat message: {e}")

    def get_conversation_metrics(self, days: int = 7) -> ConversationMetrics:
        """Get conversation metrics for the specified number of days"""
        try:
            # This would typically come from a metrics endpoint
            # For now, we'll simulate based on available data
            status = self.get_platform_status()

            # Simulate metrics based on platform status
            return ConversationMetrics(
                total_conversations=0,  # Would come from actual metrics
                today_conversations=0,  # Would come from actual metrics
                avg_response_time=0.0,  # Would come from actual metrics
                success_rate=100.0 if status.status == 'active' else 0.0,
                error_count=0,  # Would come from actual metrics
                last_activity=status.timestamp
            )

        except Exception as e:
            logger.error(f"Error getting conversation metrics: {e}")
            raise OmniPlatformError(f"Failed to get conversation metrics: {e}")

    def test_connection(self) -> bool:
        """Test connection to OMNI platform"""
        try:
            status = self.get_platform_status()
            return status.status == 'active'
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

# Global client instance
omni_client = None

def get_omni_client() -> OmniPlatformClient:
    """Get or create global OMNI platform client"""
    global omni_client
    if omni_client is None:
        omni_client = OmniPlatformClient()
    return omni_client

def initialize_omni_client(base_url: Optional[str] = None, api_key: Optional[str] = None) -> OmniPlatformClient:
    """Initialize OMNI platform client with custom settings"""
    global omni_client
    omni_client = OmniPlatformClient(base_url=base_url, api_key=api_key)
    return omni_client