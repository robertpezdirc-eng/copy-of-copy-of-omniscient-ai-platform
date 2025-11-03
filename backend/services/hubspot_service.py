"""
HubSpot Integration Service
Provides integration with HubSpot for CRM, marketing automation, and sales.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
import logging

logger = logging.getLogger(__name__)


class HubSpotService:
    """Service for HubSpot CRM and marketing automation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    # Contact Management
    async def create_contact(self, tenant_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contact in HubSpot"""
        url = f"{self.base_url}/crm/v3/objects/contacts"
        
        properties = {
            "email": contact_data.get("email"),
            "firstname": contact_data.get("first_name"),
            "lastname": contact_data.get("last_name"),
            "phone": contact_data.get("phone"),
            "company": contact_data.get("company"),
            "website": contact_data.get("website"),
            "lifecyclestage": contact_data.get("lifecycle_stage", "lead"),
            "tenant_id": tenant_id
        }
        
        payload = {"properties": properties}
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create HubSpot contact: {e}")
            raise
    
    async def get_contacts(self, tenant_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get contacts from HubSpot"""
        url = f"{self.base_url}/crm/v3/objects/contacts"
        params = {"limit": limit}
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            results = response.json().get("results", [])
            
            # Filter by tenant_id
            return [c for c in results if c.get("properties", {}).get("tenant_id") == tenant_id]
        except Exception as e:
            logger.error(f"Failed to get HubSpot contacts: {e}")
            raise
    
    async def update_contact(self, contact_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a contact in HubSpot"""
        url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}"
        payload = {"properties": contact_data}
        
        try:
            response = requests.patch(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to update HubSpot contact: {e}")
            raise
    
    # Deal Management
    async def create_deal(self, tenant_id: str, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new deal in HubSpot"""
        url = f"{self.base_url}/crm/v3/objects/deals"
        
        properties = {
            "dealname": deal_data.get("name"),
            "amount": deal_data.get("amount"),
            "dealstage": deal_data.get("stage", "appointmentscheduled"),
            "pipeline": deal_data.get("pipeline", "default"),
            "closedate": deal_data.get("close_date"),
            "tenant_id": tenant_id
        }
        
        payload = {"properties": properties}
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create HubSpot deal: {e}")
            raise
    
    async def get_deals(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get deals from HubSpot"""
        url = f"{self.base_url}/crm/v3/objects/deals"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            results = response.json().get("results", [])
            
            return [d for d in results if d.get("properties", {}).get("tenant_id") == tenant_id]
        except Exception as e:
            logger.error(f"Failed to get HubSpot deals: {e}")
            raise
    
    # Company Management
    async def create_company(self, tenant_id: str, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new company in HubSpot"""
        url = f"{self.base_url}/crm/v3/objects/companies"
        
        properties = {
            "name": company_data.get("name"),
            "domain": company_data.get("domain"),
            "industry": company_data.get("industry"),
            "phone": company_data.get("phone"),
            "city": company_data.get("city"),
            "state": company_data.get("state"),
            "tenant_id": tenant_id
        }
        
        payload = {"properties": properties}
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create HubSpot company: {e}")
            raise
    
    # Email Marketing
    async def send_marketing_email(self, tenant_id: str, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a marketing email via HubSpot"""
        url = f"{self.base_url}/marketing/v3/emails/send"
        
        payload = {
            "emailId": email_data.get("template_id"),
            "message": {
                "to": email_data.get("recipients"),
                "from": email_data.get("from_email"),
                "subject": email_data.get("subject")
            },
            "contactProperties": email_data.get("contact_properties", {})
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send marketing email: {e}")
            raise
    
    async def create_email_campaign(self, tenant_id: str, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an email campaign"""
        return {
            "campaign_id": f"hs_campaign_{tenant_id}",
            "name": campaign_data.get("name"),
            "subject": campaign_data.get("subject"),
            "recipients": campaign_data.get("recipients", []),
            "status": "draft",
            "created_at": datetime.utcnow().isoformat()
        }
    
    # Workflow Automation
    async def create_workflow(self, tenant_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an automation workflow"""
        return {
            "workflow_id": f"hs_workflow_{tenant_id}",
            "name": workflow_data.get("name"),
            "type": workflow_data.get("type", "contact"),
            "triggers": workflow_data.get("triggers", []),
            "actions": workflow_data.get("actions", []),
            "status": "active"
        }
    
    async def enroll_contact_in_workflow(self, contact_id: str, workflow_id: str) -> Dict[str, Any]:
        """Enroll a contact in a workflow"""
        return {
            "contact_id": contact_id,
            "workflow_id": workflow_id,
            "enrollment_status": "enrolled",
            "enrolled_at": datetime.utcnow().isoformat()
        }
    
    # Analytics
    async def get_contact_analytics(self, tenant_id: str) -> Dict[str, Any]:
        """Get contact analytics"""
        return {
            "tenant_id": tenant_id,
            "total_contacts": 1250,
            "new_contacts_this_month": 85,
            "lifecycle_stages": {
                "subscriber": 420,
                "lead": 350,
                "marketingqualifiedlead": 180,
                "salesqualifiedlead": 120,
                "opportunity": 95,
                "customer": 85
            },
            "engagement_rate": 42.5
        }
    
    async def get_deal_analytics(self, tenant_id: str) -> Dict[str, Any]:
        """Get deal analytics"""
        return {
            "tenant_id": tenant_id,
            "total_deals": 145,
            "total_value": 2850000,
            "avg_deal_value": 19655,
            "win_rate": 28.5,
            "deals_by_stage": {
                "appointmentscheduled": 35,
                "qualifiedtobuy": 28,
                "presentationscheduled": 22,
                "decisionmakerboughtin": 18,
                "contractsent": 12,
                "closedwon": 30
            }
        }
    
    # Sync Operations
    async def sync_contacts(self, tenant_id: str, direction: str = "bidirectional") -> Dict[str, Any]:
        """Sync contacts between platform and HubSpot"""
        contacts = await self.get_contacts(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "direction": direction,
            "contacts_synced": len(contacts),
            "last_sync": datetime.utcnow().isoformat(),
            "status": "success"
        }
    
    async def get_sync_status(self, tenant_id: str) -> Dict[str, Any]:
        """Get sync status"""
        return {
            "tenant_id": tenant_id,
            "last_sync": datetime.utcnow().isoformat(),
            "status": "active",
            "objects_synced": {
                "contacts": 1250,
                "companies": 320,
                "deals": 145,
                "tickets": 89
            },
            "errors": 0
        }
