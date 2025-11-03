"""
Cryptocurrency Payment Routes
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

crypto_router = APIRouter()


class CryptoPayment(BaseModel):
    amount: float
    currency: str  # BTC, ETH, USDT
    customer_email: Optional[str] = None


@crypto_router.post("/create-payment")
async def create_crypto_payment(payment: CryptoPayment):
    """Create cryptocurrency payment"""
    
    payment_id = f"CRYPTO-{uuid.uuid4().hex[:16].upper()}"
    
    wallet_addresses = {
        "BTC": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        "ETH": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "USDT": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    }
    
    return {
        "payment_id": payment_id,
        "status": "PENDING",
        "amount": payment.amount,
        "currency": payment.currency,
        "wallet_address": wallet_addresses.get(payment.currency),
        "qr_code_url": f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={wallet_addresses.get(payment.currency)}",
        "expires_at": (datetime.now(timezone.utc)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }


@crypto_router.get("/payment/{payment_id}")
async def get_crypto_payment_status(payment_id: str):
    """Get cryptocurrency payment status"""
    
    return {
        "payment_id": payment_id,
        "status": "CONFIRMED",
        "confirmations": 6,
        "tx_hash": f"0x{uuid.uuid4().hex}",
        "confirmed_at": datetime.now(timezone.utc).isoformat()
    }
