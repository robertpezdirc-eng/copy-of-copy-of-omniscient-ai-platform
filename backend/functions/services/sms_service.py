"""
SMS Service for sending SMS notifications and 2FA codes via Twilio
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass
class SMSMessage:
    """SMS message structure"""
    message_id: str
    to: str
    from_number: str
    body: str
    status: str  # pending, sent, delivered, failed
    tenant_id: Optional[str]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    error: Optional[str]
    cost: Optional[float]


@dataclass
class SMSTemplate:
    """SMS template"""
    template_id: str
    name: str
    body: str
    variables: List[str]
    category: str


class SMSService:
    """Service for sending SMS messages via Twilio"""
    
    def __init__(self):
        self.templates = self._init_templates()
        self.sent_messages: List[SMSMessage] = []
        
        # Twilio configuration (should come from environment)
        self.config = {
            "account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "auth_token": "your_auth_token",
            "from_number": "+1234567890"
        }
    
    def _init_templates(self) -> Dict[str, SMSTemplate]:
        """Initialize SMS templates"""
        return {
            "2fa_code": SMSTemplate(
                template_id="2fa_code",
                name="2FA Verification Code",
                body="Your verification code is: {{code}}. Valid for {{expiry_minutes}} minutes.",
                variables=["code", "expiry_minutes"],
                category="security"
            ),
            "password_reset": SMSTemplate(
                template_id="password_reset",
                name="Password Reset",
                body="Your password reset code: {{code}}. Don't share this code.",
                variables=["code"],
                category="security"
            ),
            "alert": SMSTemplate(
                template_id="alert",
                name="System Alert",
                body="[{{severity}}] {{alert_title}}: {{message}}",
                variables=["severity", "alert_title", "message"],
                category="notification"
            ),
            "welcome": SMSTemplate(
                template_id="welcome",
                name="Welcome Message",
                body="Welcome to {{company_name}}! Your account is ready. Login at {{url}}",
                variables=["company_name", "url"],
                category="onboarding"
            ),
            "invoice": SMSTemplate(
                template_id="invoice",
                name="Invoice Notification",
                body="Invoice #{{invoice_number}} for €{{amount}} is ready. View: {{url}}",
                variables=["invoice_number", "amount", "url"],
                category="billing"
            ),
            "appointment_reminder": SMSTemplate(
                template_id="appointment_reminder",
                name="Appointment Reminder",
                body="Reminder: Your appointment on {{date}} at {{time}}. {{location}}",
                variables=["date", "time", "location"],
                category="reminder"
            )
        }
    
    def render_template(self, template_id: str, variables: Dict[str, Any]) -> str:
        """Render SMS template with variables"""
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
        
        template = self.templates[template_id]
        body = template.body
        
        for var_name, var_value in variables.items():
            placeholder = "{{" + var_name + "}}"
            body = body.replace(placeholder, str(var_value))
        
        return body
    
    async def send_sms(
        self,
        to: str,
        body: str,
        tenant_id: Optional[str] = None
    ) -> SMSMessage:
        """Send SMS message"""
        # Validate phone number format
        if not to.startswith("+"):
            to = "+" + to
        
        message = SMSMessage(
            message_id=f"sms_{datetime.utcnow().timestamp()}",
            to=to,
            from_number=self.config["from_number"],
            body=body,
            status="pending",
            tenant_id=tenant_id,
            sent_at=None,
            delivered_at=None,
            error=None,
            cost=None
        )
        
        try:
            # Send via Twilio (simulated)
            print(f"Sending SMS to {to}: {body}")
            
            message.status = "sent"
            message.sent_at = datetime.utcnow()
            message.cost = 0.02  # €0.02 per SMS
            
        except Exception as e:
            message.status = "failed"
            message.error = str(e)
        
        self.sent_messages.append(message)
        return message
    
    async def send_templated_sms(
        self,
        to: str,
        template_id: str,
        variables: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> SMSMessage:
        """Send SMS using template"""
        body = self.render_template(template_id, variables)
        return await self.send_sms(to, body, tenant_id)
    
    async def send_batch(
        self,
        messages: List[Dict[str, Any]],
        tenant_id: Optional[str] = None
    ) -> List[SMSMessage]:
        """Send batch of SMS messages"""
        results = []
        for msg_data in messages:
            if "template_id" in msg_data:
                message = await self.send_templated_sms(
                    to=msg_data["to"],
                    template_id=msg_data["template_id"],
                    variables=msg_data.get("variables", {}),
                    tenant_id=tenant_id
                )
            else:
                message = await self.send_sms(
                    to=msg_data["to"],
                    body=msg_data["body"],
                    tenant_id=tenant_id
                )
            results.append(message)
        
        return results
    
    async def send_2fa_code(
        self,
        to: str,
        code: str,
        expiry_minutes: int = 10,
        tenant_id: Optional[str] = None
    ) -> SMSMessage:
        """Send 2FA verification code"""
        return await self.send_templated_sms(
            to=to,
            template_id="2fa_code",
            variables={"code": code, "expiry_minutes": expiry_minutes},
            tenant_id=tenant_id
        )
    
    def get_message_status(self, message_id: str) -> Optional[SMSMessage]:
        """Get SMS delivery status"""
        for message in self.sent_messages:
            if message.message_id == message_id:
                return message
        return None
    
    def get_templates(self, category: Optional[str] = None) -> List[SMSTemplate]:
        """Get available SMS templates"""
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates
    
    def get_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get SMS statistics"""
        messages = self.sent_messages
        if tenant_id:
            messages = [m for m in messages if m.tenant_id == tenant_id]
        
        total = len(messages)
        sent = len([m for m in messages if m.status in ["sent", "delivered"]])
        failed = len([m for m in messages if m.status == "failed"])
        total_cost = sum(m.cost or 0 for m in messages)
        
        return {
            "total_messages": total,
            "sent": sent,
            "failed": failed,
            "success_rate": (sent / total * 100) if total > 0 else 0,
            "total_cost": round(total_cost, 2),
            "by_template": {
                template_id: len([m for m in messages if hasattr(m, 'template_id') and m.template_id == template_id])
                for template_id in self.templates.keys()
            }
        }


# Global service instance
sms_service = SMSService()
