"""
Billing & Invoicing Routes
Provides endpoints for invoice management, payment history, and billing analytics
"""

from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field

router = APIRouter()


class Invoice(BaseModel):
    """Invoice model"""
    id: str
    invoice_number: str
    tenant_id: str
    amount: float
    currency: str = "EUR"
    status: str  # paid, pending, overdue
    issue_date: str
    due_date: str
    paid_date: Optional[str] = None
    items: List[dict] = Field(default_factory=list)


class BillingCycle(BaseModel):
    """Billing cycle information"""
    period_start: str
    period_end: str
    total_usage: float
    estimated_cost: float
    currency: str = "EUR"


@router.get("/invoices", response_model=List[Invoice], tags=["Billing"])
async def get_invoices(
    tenant_id: Optional[str] = Query(default=None, description="Filter by tenant ID"),
    status: Optional[str] = Query(default=None, description="Filter by status (paid, pending, overdue)"),
    limit: int = Query(default=50, ge=1, le=200, description="Number of invoices to return")
):
    """
    Get list of invoices
    
    - **tenant_id**: Optional tenant filter
    - **status**: Filter by invoice status
    - **limit**: Number of invoices to return
    """
    # Mock data - would query database in production
    mock_invoices = [
        Invoice(
            id="inv_001",
            invoice_number="INV-2024-001",
            tenant_id=tenant_id or "tenant_default",
            amount=1299.99,
            status="paid",
            issue_date=(datetime.utcnow() - timedelta(days=30)).isoformat(),
            due_date=(datetime.utcnow() - timedelta(days=15)).isoformat(),
            paid_date=(datetime.utcnow() - timedelta(days=20)).isoformat(),
            items=[
                {"description": "API Usage", "quantity": 100000, "unit_price": 0.01, "amount": 1000.00},
                {"description": "Storage (GB)", "quantity": 100, "unit_price": 2.99, "amount": 299.99}
            ]
        ),
        Invoice(
            id="inv_002",
            invoice_number="INV-2024-002",
            tenant_id=tenant_id or "tenant_default",
            amount=1499.99,
            status="pending",
            issue_date=datetime.utcnow().isoformat(),
            due_date=(datetime.utcnow() + timedelta(days=15)).isoformat(),
            items=[
                {"description": "API Usage", "quantity": 120000, "unit_price": 0.01, "amount": 1200.00},
                {"description": "Storage (GB)", "quantity": 100, "unit_price": 2.99, "amount": 299.99}
            ]
        )
    ]
    
    if status:
        mock_invoices = [inv for inv in mock_invoices if inv.status == status]
    
    return mock_invoices[:limit]


@router.get("/invoices/{invoice_id}", response_model=Invoice, tags=["Billing"])
async def get_invoice(invoice_id: str):
    """Get detailed invoice information by ID"""
    # Mock data - would query database in production
    if invoice_id not in ["inv_001", "inv_002"]:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return Invoice(
        id=invoice_id,
        invoice_number=f"INV-2024-{invoice_id.split('_')[1]}",
        tenant_id="tenant_default",
        amount=1299.99,
        status="paid",
        issue_date=(datetime.utcnow() - timedelta(days=30)).isoformat(),
        due_date=(datetime.utcnow() - timedelta(days=15)).isoformat(),
        paid_date=(datetime.utcnow() - timedelta(days=20)).isoformat(),
        items=[
            {"description": "API Usage", "quantity": 100000, "unit_price": 0.01, "amount": 1000.00},
            {"description": "Storage (GB)", "quantity": 100, "unit_price": 2.99, "amount": 299.99}
        ]
    )


@router.get("/billing-cycle/current", response_model=BillingCycle, tags=["Billing"])
async def get_current_billing_cycle(
    tenant_id: Optional[str] = Query(default=None, description="Tenant ID")
):
    """Get current billing cycle information and estimated costs"""
    now = datetime.utcnow()
    period_start = now.replace(day=1)
    next_month = (period_start + timedelta(days=32)).replace(day=1)
    period_end = next_month - timedelta(days=1)
    
    return BillingCycle(
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        total_usage=75000.0,  # Mock usage units
        estimated_cost=875.50,
        currency="EUR"
    )


@router.post("/invoices/{invoice_id}/pay", tags=["Billing"])
async def pay_invoice(invoice_id: str):
    """Mark invoice as paid (simplified payment processing)"""
    # In production, this would integrate with payment gateway
    return {
        "invoice_id": invoice_id,
        "status": "payment_processing",
        "message": "Payment initiated successfully"
    }


@router.get("/payment-methods", tags=["Billing"])
async def get_payment_methods(
    tenant_id: Optional[str] = Query(default=None, description="Tenant ID")
):
    """Get configured payment methods"""
    return {
        "payment_methods": [
            {
                "id": "pm_001",
                "type": "credit_card",
                "last4": "4242",
                "brand": "visa",
                "is_default": True
            },
            {
                "id": "pm_002",
                "type": "bank_account",
                "last4": "6789",
                "bank_name": "Test Bank",
                "is_default": False
            }
        ]
    }
