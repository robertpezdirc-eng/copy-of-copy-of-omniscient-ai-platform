""""""

Automated Billing & Invoicing RoutesOMNI Platform - Automated Billing & Invoicing System

"""Complete billing automation with invoices, receipts, and tax reports

"""

from fastapi import APIRouter

from pydantic import BaseModelfrom fastapi import APIRouter, HTTPException, Query, Body, Depends, Header

from datetime import datetime, timezonefrom pydantic import BaseModel

import uuidfrom typing import List, Optional, Dict, Any

import randomfrom datetime import datetime, timedelta, timezone

import random

router = APIRouter()import os

from jose import jwt, JWTError



class InvoiceCreate(BaseModel):from utils.gcp import get_firestore

    customer_id: strfrom services.billing_service import create_or_update_invoice

    amount: floatfrom services.email_service import send_email

    description: str

router = APIRouter()



@router.post("/invoices/generate")JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-prod")

async def generate_invoice(invoice: InvoiceCreate):

    """Generate new invoice"""

    def get_current_user(authorization: Optional[str] = Header(None)):

    invoice_id = f"INV-{uuid.uuid4().hex[:12].upper()}"    if not authorization or not authorization.lower().startswith("bearer "):

            raise HTTPException(status_code=401, detail="Missing token")

    return {    token = authorization.split(" ", 1)[1]

        "invoice_id": invoice_id,    try:

        "customer_id": invoice.customer_id,        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

        "amount": invoice.amount,        return payload

        "description": invoice.description,    except JWTError:

        "status": "pending",        raise HTTPException(status_code=401, detail="Invalid token")

        "due_date": datetime.now(timezone.utc).isoformat(),

        "created_at": datetime.now(timezone.utc).isoformat()# ============================================================================

    }# BILLING & INVOICING

# ============================================================================



@router.get("/invoices/{invoice_id}")@router.post("/invoices/generate")

async def get_invoice(invoice_id: str):async def generate_invoice(

    """Get invoice details"""    user_id: str = Body(...),

        items: List[Dict[str, Any]] = Body(...),

    return {    due_date: Optional[str] = Body(None)

        "invoice_id": invoice_id,):

        "amount": round(random.uniform(100, 1000), 2),    """Generate invoice automatically"""

        "status": "paid",    

        "paid_at": datetime.now(timezone.utc).isoformat()    invoice_id = f"INV-{random.randint(10000, 99999)}"

    }    subtotal = sum(item.get("amount", 0) for item in items)

    tax = subtotal * 0.22  # 22% VAT

    total = subtotal + tax

@router.get("/billing/summary")    

async def get_billing_summary(customer_id: str):    return {

    """Get billing summary"""        "invoice_id": invoice_id,

            "user_id": user_id,

    return {        "invoice_number": f"2025-{random.randint(1000, 9999)}",

        "customer_id": customer_id,        "issue_date": datetime.now().isoformat(),

        "total_invoices": random.randint(5, 50),        "due_date": due_date or (datetime.now() + timedelta(days=30)).isoformat(),

        "total_amount": round(random.uniform(1000, 10000), 2),        "items": items,

        "outstanding_amount": round(random.uniform(0, 500), 2)        "subtotal": round(subtotal, 2),

    }        "tax": round(tax, 2),

        "tax_rate": 22,
        "total": round(total, 2),
        "currency": "EUR",
        "status": "issued",
        "pdf_url": f"https://invoices.omni.com/{invoice_id}.pdf",
        "payment_link": f"https://pay.omni.com/invoice/{invoice_id}"
    }

@router.get("/invoices/list")
async def list_invoices(user_id: str, status: Optional[str] = None):
    """List all invoices for user"""
    
    invoices = []
    for i in range(5):
        invoices.append({
            "invoice_id": f"INV-{random.randint(10000, 99999)}",
            "invoice_number": f"2025-{random.randint(1000, 9999)}",
            "issue_date": (datetime.now() - timedelta(days=i*30)).isoformat(),
            "due_date": (datetime.now() - timedelta(days=i*30-30)).isoformat(),
            "amount": round(random.uniform(100, 1000), 2),
            "currency": "EUR",
            "status": random.choice(["paid", "pending", "overdue"])
        })
    
    return {"invoices": invoices, "total": len(invoices)}

@router.post("/receipts/generate")
async def generate_receipt(payment_id: str = Body(...)):
    """Generate payment receipt"""
    
    receipt_id = f"REC-{random.randint(10000, 99999)}"
    
    return {
        "receipt_id": receipt_id,
        "payment_id": payment_id,
        "receipt_number": f"2025-R-{random.randint(1000, 9999)}",
        "payment_date": datetime.now().isoformat(),
        "amount_paid": round(random.uniform(100, 1000), 2),
        "payment_method": random.choice(["Credit Card", "PayPal", "Bank Transfer"]),
        "currency": "EUR",
        "pdf_url": f"https://receipts.omni.com/{receipt_id}.pdf",
        "email_sent": True
    }

@router.get("/tax-reports/generate")
async def generate_tax_report(
    year: int = Query(...),
    user_id: Optional[str] = None
):
    """Generate annual tax report"""
    
    return {
        "report_id": f"TAX-{year}-{random.randint(1000, 9999)}",
        "year": year,
        "total_revenue": round(random.uniform(50000, 500000), 2),
        "total_expenses": round(random.uniform(10000, 100000), 2),
        "taxable_income": round(random.uniform(40000, 400000), 2),
        "tax_owed": round(random.uniform(8000, 80000), 2),
        "payments_received": random.randint(500, 5000),
        "transactions": random.randint(1000, 10000),
        "pdf_url": f"https://tax-reports.omni.com/{year}.pdf",
        "generated_at": datetime.now().isoformat()
    }

@router.get("/billing/subscriptions")
async def list_subscriptions(user_id: Optional[str] = None, user=Depends(get_current_user)):
    """List active subscriptions (placeholder; pulls from Firestore if present)"""
    tenant_id = user.get("tenant_id", "unknown")
    db = get_firestore()
    try:
        subs_ref = (
            db.collection("subscriptions")
            .where("tenant_id", "==", tenant_id)
            .order_by("created_at", direction="DESCENDING")
            .limit(5)
        )
        subs = [doc.to_dict() for doc in subs_ref.stream()]
        if subs:
            return {"subscriptions": subs}
    except Exception:
        pass

    # Fallback demo data
    return {
        "subscriptions": [
            {
                "subscription_id": "sub_demo",
                "tenant_id": tenant_id,
                "plan": "free",
                "amount": 0,
                "currency": "EUR",
                "interval": "monthly",
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }


# ============================ Automation Endpoints ============================

class InvoiceRequest(BaseModel):
    period: Optional[str] = None  # YYYY-MM, defaults to current month


@router.post("/automation/generate-monthly")
async def automation_generate_monthly_invoice(payload: InvoiceRequest, user=Depends(get_current_user)):
    """
    Generate monthly usage-based invoice automatically.
    
    **Authentication:** Requires JWT Bearer token
    
    **Request Body:**
    ```json
    {
        "period": "2025-10"  // optional, defaults to current month (YYYY-MM)
    }
    ```
    
    **Response:**
    ```json
    {
        "invoice": {
            "invoice_id": "t_mycompany_2025-10",
            "tenant_id": "t_mycompany",
            "period": "2025-10",
            "plan": "Professional",
            "base_price": 99.0,
            "included_calls": 10000000,
            "actual_calls": 12500000,
            "overage_calls": 2500000,
            "overage_price": 2500.0,
            "amount": 2599.0,
            "currency": "EUR",
            "status": "issued"
        }
    }
    ```
    
    **Pricing:** Free (€0+€2/1k), Starter (€29+€1.5/1k), Pro (€99+€1/1k), Enterprise (€499+unlimited)
    """
    tenant_id = user.get("tenant_id", "unknown")
    now = datetime.now(timezone.utc)
    period = payload.period or now.strftime("%Y-%m")
    invoice = create_or_update_invoice(tenant_id, period)
    return {"invoice": invoice}


class SendInvoiceRequest(BaseModel):
    invoice_id: str
    to_email: Optional[str] = None


@router.post("/automation/send-invoice")
async def automation_send_invoice(payload: SendInvoiceRequest, user=Depends(get_current_user)):
    """
    Send invoice email via SendGrid (or log if not configured).
    
    **Authentication:** Requires JWT Bearer token
    
    **Request Body:**
    ```json
    {
        "invoice_id": "t_mycompany_2025-10",
        "to_email": "billing@mycompany.com"  // optional, defaults to user email
    }
    ```
    
    **Response:**
    ```json
    {
        "status": "sent",      // or "queued" if using log-only mode
        "provider": "sendgrid" // or "log" if SENDGRID_API_KEY not set
    }
    ```
    
    **Errors:**
    - 400: No recipient email available
    - 401: Missing or invalid JWT token
    - 403: Invoice does not belong to your tenant
    - 404: Invoice not found
    
    **Configuration:**
    Set environment variables for email delivery:
    - SENDGRID_API_KEY: Your SendGrid API key
    - EMAIL_FROM: Sender email address (e.g., billing@omni-ultra.com)
    """
    tenant_id = user.get("tenant_id", "unknown")
    email = payload.to_email or user.get("email") or user.get("sub")
    if not email:
        raise HTTPException(status_code=400, detail="No recipient email available")

    db = get_firestore()
    doc = db.collection("invoices").document(payload.invoice_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Invoice not found")
    inv = doc.to_dict() or {}
    if inv.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=403, detail="Invoice does not belong to your tenant")

    subject = f"Invoice {inv.get('invoice_id')} for {inv.get('period')}"
    html = f"""
    <h2>Invoice {inv.get('invoice_id')}</h2>
    <p>Period: <b>{inv.get('period')}</b></p>
    <p>Plan: <b>{inv.get('plan')}</b></p>
    <p>Total: <b>{inv.get('amount')} {inv.get('currency')}</b></p>
    <p><a href='{inv.get('pdf_url')}'>Download PDF</a> | <a href='{inv.get('payment_link')}'>Pay Now</a></p>
    <hr/>
    <p>Thank you for using Omni Ultra Platform.</p>
    """
    result = send_email(email, subject, html)

    # Update invoice status if actually sent
    if result.get("sent"):
        db.collection("invoices").document(payload.invoice_id).update({
            "status": "sent",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

    return {"status": "queued" if not result.get("sent") else "sent", "provider": result.get("provider")}
