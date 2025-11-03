"""
Stripe Payment Gateway Routes for Omni Enterprise Ultra Max

Handles subscription management and payment processing using Stripe API.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import os
import stripe
import uuid
from datetime import datetime, timezone, timedelta
from utils.gcp import get_firestore

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_YOUR_SECRET_KEY')

# Stripe webhook secret for signature verification
WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# Create Router
stripe_router = APIRouter()

# Pydantic models
class CheckoutRequest(BaseModel):
    plan: str

class PortalRequest(BaseModel):
    customer_id: str

class UsageRequest(BaseModel):
    subscription_item_id: str
    quantity: int = 1

# Subscription plans configuration
PLANS = {
    'starter': {
        'price_id': 'price_starter',  # Replace with actual Stripe Price ID
        'name': 'Starter Plan',
        'amount': 2900,  # €29.00 in cents
        'currency': 'eur',
        'features': ['10000 API requests/month', '5 AI agents', 'Basic monitoring']
    },
    'professional': {
        'price_id': 'price_professional',
        'name': 'Professional Plan',
        'amount': 9900,  # €99.00
        'currency': 'eur',
        'features': ['100000 API requests/month', '20 AI agents', 'Advanced monitoring']
    },
    'enterprise': {
        'price_id': 'price_enterprise',
        'name': 'Enterprise Plan',
        'amount': None,  # Custom pricing
        'currency': 'eur',
        'features': ['Unlimited API requests', 'All AI agents', 'Enterprise monitoring']
    }
}

@stripe_router.post('/create-checkout')
async def create_checkout_session(request: CheckoutRequest):
    """Create a Stripe Checkout session for subscription"""
    try:
        plan = request.plan

        if plan not in PLANS:
            raise HTTPException(status_code=400, detail='Invalid plan')

        plan_config = PLANS[plan]

        # Create Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': plan_config['price_id'],
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://omni-ultra.com/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://omni-ultra.com/cancel',
            metadata={
                'plan': plan,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )

        return {
            'sessionId': checkout_session.id,
            'url': checkout_session.url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@stripe_router.post('/create-portal')
async def create_portal_session(request: PortalRequest):
    """Create a Stripe Customer Portal session for subscription management"""
    try:
        if not request.customer_id:
            raise HTTPException(status_code=400, detail='Customer ID required')

        # Create portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=request.customer_id,
            return_url='https://omni-ultra.com/dashboard',
        )

        return {'url': portal_session.url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@stripe_router.post('/webhook')
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid payload')
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail='Invalid signature')

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)

    elif event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        handle_subscription_created(subscription)

    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)

    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_payment_succeeded(invoice)

    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_payment_failed(invoice)

    return {'status': 'success'}

def handle_checkout_session(session):
    """Handle completed checkout session"""
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')
    metadata = session.get('metadata', {})

    print(f"Checkout completed for customer {customer_id}")
    print(f"Subscription ID: {subscription_id}")
    print(f"Plan: {metadata.get('plan')}")

    # Persist to Firestore if tenant context exists (set by monetization wrapper)
    try:
        db = get_firestore()
        data = {
            'customer_id': customer_id,
            'subscription_id': subscription_id,
            'plan': metadata.get('plan'),
            'tenant_id': metadata.get('tenant_id'),
            'user_id': metadata.get('user_id'),
            'status': 'pending',
            'checkout_completed_at': datetime.now(timezone.utc).isoformat(),
        }
        key = subscription_id or session.get('id')
        if key:
            db.collection('subscriptions').document(key).set(data)
    except Exception as e:
        print(f"Failed to write checkout session to Firestore: {e}")

def handle_subscription_created(subscription):
    """Handle new subscription"""
    customer_id = subscription.get('customer')
    status = subscription.get('status')

    print(f"Subscription created for customer {customer_id}")
    print(f"Status: {status}")

    # Update Firestore status if exists
    try:
        db = get_firestore()
        db.collection('subscriptions').document(subscription.get('id')).set({
            'customer_id': customer_id,
            'status': status,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }, merge=True)
    except Exception as e:
        print(f"Failed to update subscription in Firestore: {e}")

def handle_subscription_updated(subscription):
    """Handle subscription update"""
    customer_id = subscription.get('customer')
    status = subscription.get('status')

    print(f"Subscription updated for customer {customer_id}")
    print(f"New status: {status}")

    try:
        db = get_firestore()
        db.collection('subscriptions').document(subscription.get('id')).set({
            'customer_id': customer_id,
            'status': status,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }, merge=True)
    except Exception as e:
        print(f"Failed to update subscription in Firestore: {e}")

def handle_subscription_deleted(subscription):
    """Handle subscription cancellation"""
    customer_id = subscription.get('customer')

    print(f"Subscription cancelled for customer {customer_id}")

    try:
        db = get_firestore()
        db.collection('subscriptions').document(subscription.get('id')).set({
            'customer_id': customer_id,
            'status': 'canceled',
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }, merge=True)
    except Exception as e:
        print(f"Failed to mark subscription canceled in Firestore: {e}")

def handle_payment_succeeded(invoice):
    """Handle successful payment"""
    customer_id = invoice.get('customer')
    amount_paid = invoice.get('amount_paid')

    print(f"Payment succeeded for customer {customer_id}")
    print(f"Amount: {amount_paid / 100} {invoice.get('currency').upper()}")

    try:
        db = get_firestore()
        db.collection('payments').document(invoice.get('id')).set({
            'customer_id': customer_id,
            'amount_paid': amount_paid,
            'currency': invoice.get('currency'),
            'status': 'succeeded',
            'paid_at': datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        print(f"Failed to store payment record in Firestore: {e}")

def handle_payment_failed(invoice):
    """Handle failed payment"""
    customer_id = invoice.get('customer')

    print(f"Payment failed for customer {customer_id}")

    try:
        db = get_firestore()
        db.collection('payments').document(invoice.get('id')).set({
            'customer_id': customer_id,
            'amount_due': invoice.get('amount_due'),
            'currency': invoice.get('currency'),
            'status': 'failed',
            'failed_at': datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        print(f"Failed to store failed payment in Firestore: {e}")

@stripe_router.get('/plans')
async def get_plans():
    """Get available subscription plans"""
    return {'plans': PLANS}

@stripe_router.get('/subscription/{customer_id}')
async def get_subscription(customer_id: str):
    """Get customer's current subscription"""
    try:
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status='active',
            limit=1
        )

        if subscriptions.data:
            sub = subscriptions.data[0]
            return {
                'subscription': {
                    'id': sub.id,
                    'status': sub.status,
                    'current_period_end': sub.current_period_end,
                    'plan': sub.plan.nickname or 'Unknown'
                }
            }
        else:
            return {'subscription': None}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@stripe_router.post('/usage')
async def report_usage(request: UsageRequest):
    """Report usage for metered billing"""
    try:
        stripe.SubscriptionItem.create_usage_record(
            request.subscription_item_id,
            quantity=request.quantity,
            timestamp=int(datetime.now(timezone.utc).timestamp())
        )

        return {'status': 'success'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@stripe_router.get('/analytics/{customer_id}')
async def get_payment_analytics(customer_id: str):
    """Get payment analytics for a customer"""
    try:
        # Get customer
        customer = stripe.Customer.retrieve(customer_id)
        
        # Get all invoices
        invoices = stripe.Invoice.list(customer=customer_id, limit=100)
        
        # Calculate analytics
        total_revenue = sum(inv.amount_paid for inv in invoices.data) / 100
        total_invoices = len(invoices.data)
        paid_invoices = sum(1 for inv in invoices.data if inv.status == 'paid')
        failed_invoices = sum(1 for inv in invoices.data if inv.status in ['uncollectible', 'void'])
        
        # Get subscriptions
        subscriptions = stripe.Subscription.list(customer=customer_id)
        active_subscriptions = sum(1 for sub in subscriptions.data if sub.status == 'active')
        
        return {
            'customer_id': customer_id,
            'customer_email': customer.email,
            'total_revenue': total_revenue,
            'currency': invoices.data[0].currency if invoices.data else 'eur',
            'total_invoices': total_invoices,
            'paid_invoices': paid_invoices,
            'failed_invoices': failed_invoices,
            'active_subscriptions': active_subscriptions,
            'lifetime_value': total_revenue,
            'avg_invoice_value': total_revenue / total_invoices if total_invoices > 0 else 0,
            'payment_methods': len(customer.get('invoice_settings', {}).get('default_payment_method', [])),
            'created_at': datetime.fromtimestamp(customer.created, timezone.utc).isoformat()
        }
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@stripe_router.get('/invoices/{customer_id}')
async def list_invoices(customer_id: str, limit: int = 10):
    """List all invoices for a customer"""
    try:
        invoices = stripe.Invoice.list(
            customer=customer_id,
            limit=limit
        )
        
        return {
            'invoices': [
                {
                    'id': inv.id,
                    'number': inv.number,
                    'amount_due': inv.amount_due / 100,
                    'amount_paid': inv.amount_paid / 100,
                    'currency': inv.currency,
                    'status': inv.status,
                    'created': datetime.fromtimestamp(inv.created, timezone.utc).isoformat(),
                    'due_date': datetime.fromtimestamp(inv.due_date, timezone.utc).isoformat() if inv.due_date else None,
                    'invoice_pdf': inv.invoice_pdf
                }
                for inv in invoices.data
            ]
        }
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@stripe_router.post('/invoices/create')
async def create_invoice(
    customer_id: str,
    items: list,
    auto_advance: bool = True
):
    """Create a new invoice for a customer
    
    Example items:
    [
        {"price": "price_xxx", "quantity": 1},
        {"price": "price_yyy", "quantity": 2}
    ]
    """
    try:
        # Create invoice
        invoice = stripe.Invoice.create(
            customer=customer_id,
            auto_advance=auto_advance
        )
        
        # Add line items
        for item in items:
            stripe.InvoiceItem.create(
                customer=customer_id,
                invoice=invoice.id,
                price=item['price'],
                quantity=item.get('quantity', 1)
            )
        
        # Finalize and send if auto_advance
        if auto_advance:
            invoice = stripe.Invoice.finalize_invoice(invoice.id)
        
        return {
            'invoice_id': invoice.id,
            'status': invoice.status,
            'amount_due': invoice.amount_due / 100,
            'currency': invoice.currency,
            'hosted_invoice_url': invoice.hosted_invoice_url,
            'invoice_pdf': invoice.invoice_pdf
        }
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@stripe_router.get('/revenue/monthly')
async def get_monthly_revenue(months: int = 12):
    """Get monthly revenue report"""
    try:
        # Calculate date range
        now = datetime.now(timezone.utc)
        start_date = int((now.replace(day=1) - timedelta(days=months * 30)).timestamp())
        
        # Get all charges
        charges = stripe.Charge.list(
            created={'gte': start_date},
            limit=100
        )
        
        # Group by month
        monthly_data = {}
        for charge in charges.auto_paging_iter():
            if charge.paid:
                charge_date = datetime.fromtimestamp(charge.created, timezone.utc)
                month_key = charge_date.strftime('%Y-%m')
                
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        'revenue': 0,
                        'transactions': 0,
                        'refunds': 0
                    }
                
                monthly_data[month_key]['revenue'] += charge.amount / 100
                monthly_data[month_key]['transactions'] += 1
                monthly_data[month_key]['refunds'] += charge.amount_refunded / 100
        
        # Convert to sorted list
        revenue_data = [
            {
                'month': month,
                'revenue': data['revenue'],
                'transactions': data['transactions'],
                'refunds': data['refunds'],
                'net_revenue': data['revenue'] - data['refunds']
            }
            for month, data in sorted(monthly_data.items())
        ]
        
        return {
            'period': f'{months} months',
            'data': revenue_data,
            'total_revenue': sum(d['revenue'] for d in revenue_data),
            'total_transactions': sum(d['transactions'] for d in revenue_data),
            'total_refunds': sum(d['refunds'] for d in revenue_data)
        }
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
