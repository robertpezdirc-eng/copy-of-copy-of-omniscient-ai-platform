"""
Email Service for Transactional Emails
Supports SendGrid and SMTP with template rendering
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


@dataclass
class EmailTemplate:
    """Email template structure"""
    template_id: str
    name: str
    subject: str
    html_body: str
    text_body: str
    variables: List[str]
    category: str


@dataclass
class Email:
    """Email message structure"""
    email_id: str
    to: List[str]
    subject: str
    html_body: str
    text_body: str
    from_email: str
    from_name: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    template_id: Optional[str] = None
    tenant_id: Optional[str] = None
    status: str = "pending"  # pending, sent, failed, bounced
    sent_at: Optional[datetime] = None
    error: Optional[str] = None


class EmailService:
    """Service for sending transactional emails"""
    
    def __init__(self):
        self.templates = self._init_templates()
        self.sent_emails: List[Email] = []
        
        # Configuration (should come from environment)
        self.smtp_config = {
            "host": "smtp.sendgrid.net",
            "port": 587,
            "username": "apikey",
            "password": "SG.your_api_key",
            "from_email": "noreply@omniscient.ai",
            "from_name": "Omni Platform"
        }
    
    def _init_templates(self) -> Dict[str, EmailTemplate]:
        """Initialize email templates"""
        return {
            "welcome": EmailTemplate(
                template_id="welcome",
                name="Welcome Email",
                subject="Welcome to {{company_name}}!",
                html_body="""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h1>Welcome {{user_name}}!</h1>
                    <p>Thank you for joining {{company_name}}.</p>
                    <p>Your account has been created successfully.</p>
                    <a href="{{login_url}}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Get Started
                    </a>
                </body>
                </html>
                """,
                text_body="Welcome {{user_name}}! Thank you for joining {{company_name}}.",
                variables=["user_name", "company_name", "login_url"],
                category="onboarding"
            ),
            "password_reset": EmailTemplate(
                template_id="password_reset",
                name="Password Reset",
                subject="Reset Your Password",
                html_body="""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>Password Reset Request</h2>
                    <p>Hi {{user_name}},</p>
                    <p>Click the link below to reset your password:</p>
                    <a href="{{reset_url}}" style="background: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Reset Password
                    </a>
                    <p>This link expires in {{expiry_hours}} hours.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                </body>
                </html>
                """,
                text_body="Password reset: {{reset_url}}",
                variables=["user_name", "reset_url", "expiry_hours"],
                category="security"
            ),
            "invoice": EmailTemplate(
                template_id="invoice",
                name="Invoice Email",
                subject="Invoice #{{invoice_number}} from {{company_name}}",
                html_body="""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>Invoice #{{invoice_number}}</h2>
                    <p>Hi {{customer_name}},</p>
                    <p>Thank you for your payment of €{{amount}}.</p>
                    <p>Invoice Date: {{invoice_date}}</p>
                    <p>Due Date: {{due_date}}</p>
                    <a href="{{invoice_url}}" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        View Invoice
                    </a>
                </body>
                </html>
                """,
                text_body="Invoice #{{invoice_number}} - Amount: €{{amount}}",
                variables=["invoice_number", "customer_name", "amount", "invoice_date", "due_date", "invoice_url", "company_name"],
                category="billing"
            ),
            "notification": EmailTemplate(
                template_id="notification",
                name="System Notification",
                subject="{{notification_title}}",
                html_body="""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>{{notification_title}}</h2>
                    <p>{{notification_message}}</p>
                    <p><a href="{{action_url}}">{{action_text}}</a></p>
                </body>
                </html>
                """,
                text_body="{{notification_title}}: {{notification_message}}",
                variables=["notification_title", "notification_message", "action_url", "action_text"],
                category="notification"
            ),
            "2fa_code": EmailTemplate(
                template_id="2fa_code",
                name="2FA Code",
                subject="Your verification code",
                html_body="""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>Verification Code</h2>
                    <p>Your verification code is:</p>
                    <h1 style="background: #f8f9fa; padding: 20px; text-align: center; font-size: 32px; letter-spacing: 5px;">
                        {{code}}
                    </h1>
                    <p>This code expires in {{expiry_minutes}} minutes.</p>
                </body>
                </html>
                """,
                text_body="Your verification code: {{code}}",
                variables=["code", "expiry_minutes"],
                category="security"
            ),
            "subscription_confirmation": EmailTemplate(
                template_id="subscription_confirmation",
                name="Subscription Confirmation",
                subject="Subscription Confirmed - {{plan_name}}",
                html_body="""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>Subscription Confirmed!</h2>
                    <p>Hi {{user_name}},</p>
                    <p>Your subscription to <strong>{{plan_name}}</strong> has been confirmed.</p>
                    <p>Amount: €{{amount}}/{{billing_period}}</p>
                    <p>Next billing date: {{next_billing_date}}</p>
                    <a href="{{dashboard_url}}">Go to Dashboard</a>
                </body>
                </html>
                """,
                text_body="Subscription confirmed: {{plan_name}} - €{{amount}}/{{billing_period}}",
                variables=["user_name", "plan_name", "amount", "billing_period", "next_billing_date", "dashboard_url"],
                category="billing"
            ),
            "alert": EmailTemplate(
                template_id="alert",
                name="System Alert",
                subject="[{{severity}}] {{alert_title}}",
                html_body="""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="background: {{severity_color}}; color: white; padding: 20px; border-radius: 5px;">
                        <h2>{{severity}} Alert</h2>
                        <h3>{{alert_title}}</h3>
                    </div>
                    <p>{{alert_message}}</p>
                    <p>Time: {{timestamp}}</p>
                    <a href="{{dashboard_url}}">View in Dashboard</a>
                </body>
                </html>
                """,
                text_body="[{{severity}}] {{alert_title}}: {{alert_message}}",
                variables=["severity", "severity_color", "alert_title", "alert_message", "timestamp", "dashboard_url"],
                category="alert"
            ),
            "report": EmailTemplate(
                template_id="report",
                name="Scheduled Report",
                subject="{{report_name}} - {{period}}",
                html_body="""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>{{report_name}}</h2>
                    <p>Period: {{period}}</p>
                    <p>{{summary}}</p>
                    <a href="{{report_url}}">View Full Report</a>
                </body>
                </html>
                """,
                text_body="{{report_name}} for {{period}}",
                variables=["report_name", "period", "summary", "report_url"],
                category="reporting"
            )
        }
    
    def render_template(self, template_id: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Render email template with variables"""
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
        
        template = self.templates[template_id]
        
        subject = template.subject
        html_body = template.html_body
        text_body = template.text_body
        
        # Replace variables
        for var_name, var_value in variables.items():
            placeholder = "{{" + var_name + "}}"
            subject = subject.replace(placeholder, str(var_value))
            html_body = html_body.replace(placeholder, str(var_value))
            text_body = text_body.replace(placeholder, str(var_value))
        
        return {
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body
        }
    
    async def send_email(
        self,
        to: List[str],
        subject: str,
        html_body: str,
        text_body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        tenant_id: Optional[str] = None
    ) -> Email:
        """Send email via SMTP"""
        email = Email(
            email_id=f"email_{datetime.utcnow().timestamp()}",
            to=to,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            from_email=self.smtp_config["from_email"],
            from_name=self.smtp_config["from_name"],
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            tenant_id=tenant_id
        )
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.smtp_config['from_name']} <{self.smtp_config['from_email']}>"
            msg["To"] = ", ".join(to)
            
            if cc:
                msg["Cc"] = ", ".join(cc)
            
            # Attach text and HTML parts
            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")
            msg.attach(part1)
            msg.attach(part2)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment["content"])
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={attachment['filename']}"
                    )
                    msg.attach(part)
            
            # Send via SMTP (simulated)
            # In production, connect to actual SMTP server
            print(f"Sending email to {to}: {subject}")
            
            email.status = "sent"
            email.sent_at = datetime.utcnow()
            
        except Exception as e:
            email.status = "failed"
            email.error = str(e)
        
        self.sent_emails.append(email)
        return email
    
    async def send_templated_email(
        self,
        to: List[str],
        template_id: str,
        variables: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> Email:
        """Send email using template"""
        rendered = self.render_template(template_id, variables)
        
        email = await self.send_email(
            to=to,
            subject=rendered["subject"],
            html_body=rendered["html_body"],
            text_body=rendered["text_body"],
            tenant_id=tenant_id
        )
        
        email.template_id = template_id
        return email
    
    async def send_batch(
        self,
        emails: List[Dict[str, Any]],
        tenant_id: Optional[str] = None
    ) -> List[Email]:
        """Send batch of emails"""
        results = []
        for email_data in emails:
            if "template_id" in email_data:
                email = await self.send_templated_email(
                    to=email_data["to"],
                    template_id=email_data["template_id"],
                    variables=email_data.get("variables", {}),
                    tenant_id=tenant_id
                )
            else:
                email = await self.send_email(
                    to=email_data["to"],
                    subject=email_data["subject"],
                    html_body=email_data["html_body"],
                    text_body=email_data["text_body"],
                    tenant_id=tenant_id
                )
            results.append(email)
        
        return results
    
    def get_email_status(self, email_id: str) -> Optional[Email]:
        """Get email delivery status"""
        for email in self.sent_emails:
            if email.email_id == email_id:
                return email
        return None
    
    def get_templates(self, category: Optional[str] = None) -> List[EmailTemplate]:
        """Get available email templates"""
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates
    
    def get_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get email statistics"""
        emails = self.sent_emails
        if tenant_id:
            emails = [e for e in emails if e.tenant_id == tenant_id]
        
        total = len(emails)
        sent = len([e for e in emails if e.status == "sent"])
        failed = len([e for e in emails if e.status == "failed"])
        
        return {
            "total_emails": total,
            "sent": sent,
            "failed": failed,
            "success_rate": (sent / total * 100) if total > 0 else 0,
            "by_template": {
                template_id: len([e for e in emails if e.template_id == template_id])
                for template_id in self.templates.keys()
            }
        }


# Global service instance
email_service = EmailService()
