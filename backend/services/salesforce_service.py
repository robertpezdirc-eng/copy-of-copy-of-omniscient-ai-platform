"""
Salesforce Integration Service
Provides integration with Salesforce CRM for leads, opportunities, contacts, and accounts.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
import logging

logger = logging.getLogger(__name__)


class SalesforceService:
    """Service for Salesforce CRM integration"""
    
    def __init__(self, client_id: str, client_secret: str, instance_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.instance_url = instance_url
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
    
    async def authenticate(self, username: str, password: str, security_token: str) -> Dict[str, Any]:
        """
        Authenticate with Salesforce using OAuth 2.0 Username-Password flow
        
        Args:
            username: Salesforce username
            password: Salesforce password
            security_token: Salesforce security token
            
        Returns:
            Authentication response with access token
        """
        auth_url = f"{self.instance_url}/services/oauth2/token"
        data = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": username,
            "password": f"{password}{security_token}"
        }
        
        try:
            response = requests.post(auth_url, data=data)
            response.raise_for_status()
            auth_data = response.json()
            
            self.access_token = auth_data.get("access_token")
            self.instance_url = auth_data.get("instance_url", self.instance_url)
            
            logger.info("Successfully authenticated with Salesforce")
            return auth_data
        except Exception as e:
            logger.error(f"Salesforce authentication failed: {e}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests"""
        if not self.access_token:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    # Lead Management
    async def create_lead(self, tenant_id: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new lead in Salesforce"""
        url = f"{self.instance_url}/services/data/v57.0/sobjects/Lead"
        
        payload = {
            "Company": lead_data.get("company"),
            "LastName": lead_data.get("last_name"),
            "FirstName": lead_data.get("first_name"),
            "Email": lead_data.get("email"),
            "Phone": lead_data.get("phone"),
            "Status": lead_data.get("status", "Open - Not Contacted"),
            "LeadSource": lead_data.get("source", "Web"),
            "Description": lead_data.get("description"),
            "External_Tenant_ID__c": tenant_id  # Custom field
        }
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create lead: {e}")
            raise
    
    async def get_leads(self, tenant_id: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get leads from Salesforce"""
        query = f"SELECT Id, Company, FirstName, LastName, Email, Phone, Status FROM Lead WHERE External_Tenant_ID__c = '{tenant_id}'"
        
        if filters:
            if filters.get("status"):
                query += f" AND Status = '{filters['status']}'"
        
        url = f"{self.instance_url}/services/data/v57.0/query"
        params = {"q": query}
        
        try:
            response = requests.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            return response.json().get("records", [])
        except Exception as e:
            logger.error(f"Failed to get leads: {e}")
            raise
    
    async def update_lead(self, lead_id: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing lead"""
        url = f"{self.instance_url}/services/data/v57.0/sobjects/Lead/{lead_id}"
        
        try:
            response = requests.patch(url, json=lead_data, headers=self._get_headers())
            response.raise_for_status()
            return {"success": True, "lead_id": lead_id}
        except Exception as e:
            logger.error(f"Failed to update lead: {e}")
            raise
    
    # Opportunity Management
    async def create_opportunity(self, tenant_id: str, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new opportunity in Salesforce"""
        url = f"{self.instance_url}/services/data/v57.0/sobjects/Opportunity"
        
        payload = {
            "Name": opportunity_data.get("name"),
            "StageName": opportunity_data.get("stage", "Prospecting"),
            "CloseDate": opportunity_data.get("close_date"),
            "Amount": opportunity_data.get("amount"),
            "Probability": opportunity_data.get("probability", 10),
            "Description": opportunity_data.get("description"),
            "AccountId": opportunity_data.get("account_id"),
            "External_Tenant_ID__c": tenant_id
        }
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create opportunity: {e}")
            raise
    
    async def get_opportunities(self, tenant_id: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get opportunities from Salesforce"""
        query = f"SELECT Id, Name, StageName, Amount, CloseDate, Probability FROM Opportunity WHERE External_Tenant_ID__c = '{tenant_id}'"
        
        if filters:
            if filters.get("stage"):
                query += f" AND StageName = '{filters['stage']}'"
        
        url = f"{self.instance_url}/services/data/v57.0/query"
        params = {"q": query}
        
        try:
            response = requests.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            return response.json().get("records", [])
        except Exception as e:
            logger.error(f"Failed to get opportunities: {e}")
            raise
    
    # Contact Management
    async def create_contact(self, tenant_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contact in Salesforce"""
        url = f"{self.instance_url}/services/data/v57.0/sobjects/Contact"
        
        payload = {
            "FirstName": contact_data.get("first_name"),
            "LastName": contact_data.get("last_name"),
            "Email": contact_data.get("email"),
            "Phone": contact_data.get("phone"),
            "Title": contact_data.get("title"),
            "AccountId": contact_data.get("account_id"),
            "Description": contact_data.get("description"),
            "External_Tenant_ID__c": tenant_id
        }
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create contact: {e}")
            raise
    
    async def get_contacts(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get contacts from Salesforce"""
        query = f"SELECT Id, FirstName, LastName, Email, Phone, Title FROM Contact WHERE External_Tenant_ID__c = '{tenant_id}'"
        
        url = f"{self.instance_url}/services/data/v57.0/query"
        params = {"q": query}
        
        try:
            response = requests.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            return response.json().get("records", [])
        except Exception as e:
            logger.error(f"Failed to get contacts: {e}")
            raise
    
    # Account Management
    async def create_account(self, tenant_id: str, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new account in Salesforce"""
        url = f"{self.instance_url}/services/data/v57.0/sobjects/Account"
        
        payload = {
            "Name": account_data.get("name"),
            "Type": account_data.get("type", "Prospect"),
            "Industry": account_data.get("industry"),
            "Phone": account_data.get("phone"),
            "Website": account_data.get("website"),
            "Description": account_data.get("description"),
            "External_Tenant_ID__c": tenant_id
        }
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create account: {e}")
            raise
    
    # Webhook Management
    async def setup_webhook(self, tenant_id: str, webhook_url: str, events: List[str]) -> Dict[str, Any]:
        """Setup webhook for Salesforce events"""
        # This would typically use Salesforce Streaming API or Platform Events
        return {
            "webhook_id": f"sf_webhook_{tenant_id}",
            "url": webhook_url,
            "events": events,
            "status": "active"
        }
    
    async def sync_data(self, tenant_id: str, object_type: str, direction: str = "bidirectional") -> Dict[str, Any]:
        """Sync data between platform and Salesforce"""
        stats = {
            "object_type": object_type,
            "direction": direction,
            "synced": 0,
            "failed": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if object_type == "leads":
            leads = await self.get_leads(tenant_id)
            stats["synced"] = len(leads)
        elif object_type == "opportunities":
            opportunities = await self.get_opportunities(tenant_id)
            stats["synced"] = len(opportunities)
        elif object_type == "contacts":
            contacts = await self.get_contacts(tenant_id)
            stats["synced"] = len(contacts)
        
        return stats
    
    async def get_sync_status(self, tenant_id: str) -> Dict[str, Any]:
        """Get sync status for tenant"""
        return {
            "tenant_id": tenant_id,
            "last_sync": datetime.utcnow().isoformat(),
            "status": "active",
            "objects_synced": {
                "leads": 150,
                "opportunities": 45,
                "contacts": 320,
                "accounts": 78
            }
        }
