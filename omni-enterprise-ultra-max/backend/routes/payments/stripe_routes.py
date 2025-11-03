"""
Stripe Payment Gateway Routes for Omni Enterprise Ultra Max

Handles subscription management and payment processing using Stripe API.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import os
import stripe
import uuid
from datetime import datetime, timezone
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
