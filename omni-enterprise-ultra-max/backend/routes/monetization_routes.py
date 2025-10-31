"""import os

Monetization & Subscription Plans Routesfrom datetime import datetime, timezone

"""from typing import Optional



from fastapi import APIRouterimport stripe

from pydantic import BaseModelfrom fastapi import APIRouter, HTTPException, Header, Depends

from datetime import datetime, timezonefrom jose import jwt, JWTError

import uuidfrom pydantic import BaseModel



router = APIRouter()from utils.gcp import get_firestore

from routes.stripe_routes import PLANS  # reuse existing plans config



class SubscriptionRequest(BaseModel):

    plan: strrouter = APIRouter()

    payment_method: str = "stripe"

stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_YOUR_SECRET_KEY')



@router.get("/plans")JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-prod")

async def get_subscription_plans():

    """Get available subscription plans"""

    def get_current_user(authorization: Optional[str] = Header(None)):

    return {    if not authorization or not authorization.lower().startswith("bearer "):

        "plans": [        raise HTTPException(status_code=401, detail="Missing token")

            {    token = authorization.split(" ", 1)[1]

                "plan_id": "starter",    try:

                "name": "Starter",        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

                "price": 29.00,        return payload

                "currency": "EUR",    except JWTError:

                "features": ["10K API calls/month", "Basic support", "5 team members"]        raise HTTPException(status_code=401, detail="Invalid token")

            },

            {

                "plan_id": "professional",class SubscribeRequest(BaseModel):

                "name": "Professional",    plan: str

                "price": 99.00,

                "currency": "EUR",

                "features": ["100K API calls/month", "Priority support", "20 team members", "Advanced analytics"]@router.get("/plans")

            },async def list_plans():

            {    return {"plans": PLANS}

                "plan_id": "enterprise",

                "name": "Enterprise",

                "price": 499.00,@router.post("/subscribe")

                "currency": "EUR",async def subscribe(req: SubscribeRequest, user=Depends(get_current_user)):

                "features": ["Unlimited API calls", "24/7 support", "Unlimited team members", "Custom integrations"]    plan_key = req.plan

            }    if plan_key not in PLANS:

        ]        raise HTTPException(status_code=400, detail="Invalid plan")

    }    plan = PLANS[plan_key]

    if not plan.get("price_id"):

        raise HTTPException(status_code=400, detail="Plan requires custom pricing — contact sales")

@router.post("/subscribe")

async def subscribe_to_plan(subscription: SubscriptionRequest):    try:

    """Subscribe to a plan"""        session = stripe.checkout.Session.create(

                payment_method_types=['card'],

    subscription_id = f"sub_{uuid.uuid4().hex[:12]}"            line_items=[{

                    'price': plan['price_id'],

    return {                'quantity': 1,

        "subscription_id": subscription_id,            }],

        "plan": subscription.plan,            mode='subscription',

        "status": "active",            success_url=os.getenv('CHECKOUT_SUCCESS_URL', 'https://omni-ultra.com/success?session_id={CHECKOUT_SESSION_ID}'),

        "started_at": datetime.now(timezone.utc).isoformat()            cancel_url=os.getenv('CHECKOUT_CANCEL_URL', 'https://omni-ultra.com/cancel'),

    }            metadata={

                'plan': plan_key,

                'tenant_id': user.get('tenant_id', 'default'),

@router.get("/subscription/{user_id}")                'user_id': user.get('sub'),

async def get_user_subscription(user_id: str):                'ts': datetime.now(timezone.utc).isoformat(),

    """Get user's current subscription"""            }

            )

    return {

        "user_id": user_id,        # Store intent for traceability

        "plan": "professional",        db = get_firestore()

        "status": "active",        db.collection('checkout_intents').document(session.id).set({

        "renewal_date": datetime.now(timezone.utc).isoformat()            'session_id': session.id,

    }            'plan': plan_key,

            'tenant_id': user.get('tenant_id', 'default'),
            'user_id': user.get('sub'),
            'status': 'initiated',
            'created_at': datetime.now(timezone.utc).isoformat(),
        })

        return {'sessionId': session.id, 'url': session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
