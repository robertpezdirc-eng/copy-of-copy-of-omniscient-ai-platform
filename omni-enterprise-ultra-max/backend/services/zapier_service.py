"""
Zapier Integration Service
Provides Zapier webhook integration for connecting to 2000+ apps.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import requests
import hmac
import hashlib

logger = logging.getLogger(__name__)


class ZapierService:
    """Zapier Integration Service"""
    
    def __init__(self, webhook_secret: Optional[str] = None):
        self.webhook_secret = webhook_secret
        self.zaps: Dict[str, Dict[str, Any]] = {}
    
    async def create_webhook(self, name: str, url: str, events: List[str]) -> Dict[str, Any]:
        """Create a new Zapier webhook"""
        webhook_id = f"webhook_{datetime.utcnow().timestamp()}"
        
        webhook = {
            'id': webhook_id,
            'name': name,
            'url': url,
            'events': events,
            'created_at': datetime.utcnow().isoformat(),
            'active': True
        }
        
        self.zaps[webhook_id] = webhook
        logger.info(f"Zapier webhook created: {webhook_id}")
        
        return webhook
    
    async def trigger_webhook(self, webhook_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a Zapier webhook"""
        if webhook_id not in self.zaps:
            raise ValueError(f"Webhook not found: {webhook_id}")
        
        webhook = self.zaps[webhook_id]
        
        if not webhook['active']:
            raise ValueError(f"Webhook is inactive: {webhook_id}")
        
        # Add signature if secret is configured
        headers = {'Content-Type': 'application/json'}
        if self.webhook_secret:
            signature = self._generate_signature(data)
            headers['X-Zapier-Signature'] = signature
        
        try:
            response = requests.post(webhook['url'], json=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Zapier webhook triggered: {webhook_id}")
            return {
                'success': True,
                'webhook_id': webhook_id,
                'status_code': response.status_code,
                'response': response.json() if response.content else None
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Zapier webhook failed: {e}")
            return {
                'success': False,
                'webhook_id': webhook_id,
                'error': str(e)
            }
    
    async def send_data(self, webhook_url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send data to a Zapier webhook URL"""
        try:
            response = requests.post(webhook_url, json=data, timeout=30)
            response.raise_for_status()
            
            logger.info("Data sent to Zapier successfully")
            return {
                'success': True,
                'status_code': response.status_code
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send data to Zapier: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_multi_step_zap(self, zap_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a multi-step Zap configuration"""
        zap_id = f"zap_{datetime.utcnow().timestamp()}"
        
        zap = {
            'id': zap_id,
            'name': zap_config.get('name', 'Unnamed Zap'),
            'trigger': zap_config.get('trigger'),
            'actions': zap_config.get('actions', []),
            'filters': zap_config.get('filters', []),
            'created_at': datetime.utcnow().isoformat(),
            'active': True
        }
        
        self.zaps[zap_id] = zap
        logger.info(f"Multi-step Zap created: {zap_id}")
        
        return zap
    
    async def execute_zap(self, zap_id: str, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a multi-step Zap"""
        if zap_id not in self.zaps:
            raise ValueError(f"Zap not found: {zap_id}")
        
        zap = self.zaps[zap_id]
        
        if not zap['active']:
            raise ValueError(f"Zap is inactive: {zap_id}")
        
        # Apply filters
        if not self._apply_filters(trigger_data, zap.get('filters', [])):
            logger.info(f"Zap filters not met: {zap_id}")
            return {'success': False, 'reason': 'Filters not met'}
        
        # Execute actions
        results = []
        for action in zap.get('actions', []):
            try:
                result = await self._execute_action(action, trigger_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Action failed: {e}")
                results.append({'success': False, 'error': str(e)})
        
        return {
            'success': True,
            'zap_id': zap_id,
            'results': results
        }
    
    async def get_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Get webhook details"""
        if webhook_id not in self.zaps:
            raise ValueError(f"Webhook not found: {webhook_id}")
        
        return self.zaps[webhook_id]
    
    async def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all webhooks"""
        return list(self.zaps.values())
    
    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        if webhook_id not in self.zaps:
            raise ValueError(f"Webhook not found: {webhook_id}")
        
        del self.zaps[webhook_id]
        logger.info(f"Webhook deleted: {webhook_id}")
        return True
    
    def _generate_signature(self, data: Dict[str, Any]) -> str:
        """Generate HMAC signature for webhook"""
        import json
        message = json.dumps(data, sort_keys=True)
        signature = hmac.new(
            self.webhook_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _apply_filters(self, data: Dict[str, Any], filters: List[Dict[str, Any]]) -> bool:
        """Apply filters to data"""
        for filter_rule in filters:
            field = filter_rule.get('field')
            operator = filter_rule.get('operator')
            value = filter_rule.get('value')
            
            if field not in data:
                return False
            
            data_value = data[field]
            
            if operator == 'equals' and data_value != value:
                return False
            elif operator == 'contains' and value not in str(data_value):
                return False
            elif operator == 'greater_than' and data_value <= value:
                return False
        
        return True
    
    async def _execute_action(self, action: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action"""
        action_type = action.get('type')
        
        if action_type == 'webhook':
            url = action.get('url')
            return await self.send_data(url, data)
        elif action_type == 'email':
            # Placeholder for email action
            return {'success': True, 'action': 'email'}
        else:
            return {'success': False, 'error': f'Unknown action type: {action_type}'}
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get Zapier integration statistics"""
        return {
            'total_webhooks': len(self.zaps),
            'active_webhooks': sum(1 for z in self.zaps.values() if z.get('active', False)),
            'timestamp': datetime.utcnow().isoformat()
        }
