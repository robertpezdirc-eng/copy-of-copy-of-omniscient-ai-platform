"""
Partner/Reseller Program Service
Multi-level partner management with commission tracking
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class PartnerTier(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class PartnerService:
    """Service for managing partner/reseller program"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.partners = {}
        self.referrals = {}
        self.commissions = {}
        
        # Commission rates by tier
        self.commission_rates = {
            PartnerTier.BRONZE: 0.05,  # 5%
            PartnerTier.SILVER: 0.10,  # 10%
            PartnerTier.GOLD: 0.15,    # 15%
            PartnerTier.PLATINUM: 0.20 # 20%
        }
    
    async def create_partner(self, partner_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new partner account"""
        partner_id = f"partner_{int(datetime.now().timestamp())}"
        
        partner = {
            "id": partner_id,
            "company_name": partner_data.get("company_name", ""),
            "contact_name": partner_data.get("contact_name", ""),
            "email": partner_data.get("email", ""),
            "phone": partner_data.get("phone", ""),
            "tier": partner_data.get("tier", PartnerTier.BRONZE),
            "parent_partner_id": partner_data.get("parent_partner_id"),  # For multi-level
            "referral_code": f"REF-{partner_id[-8:].upper()}",
            "commission_rate": self.commission_rates.get(partner_data.get("tier", PartnerTier.BRONZE)),
            "status": "active",
            "total_referrals": 0,
            "total_commission_earned": 0.0,
            "total_commission_paid": 0.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.partners[partner_id] = partner
        return partner
    
    async def get_partner(self, partner_id: str) -> Optional[Dict[str, Any]]:
        """Get partner by ID"""
        return self.partners.get(partner_id)
    
    async def get_partner_by_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """Get partner by referral code"""
        for partner_id, partner in self.partners.items():
            if partner["referral_code"] == referral_code:
                return partner
        return None
    
    async def update_partner_tier(self, partner_id: str, new_tier: PartnerTier) -> Optional[Dict[str, Any]]:
        """Update partner tier and commission rate"""
        partner = self.partners.get(partner_id)
        if not partner:
            return None
        
        partner["tier"] = new_tier
        partner["commission_rate"] = self.commission_rates[new_tier]
        partner["updated_at"] = datetime.now().isoformat()
        
        return partner
    
    async def create_referral(self, partner_id: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record new customer referral"""
        referral_id = f"ref_{int(datetime.now().timestamp())}"
        
        referral = {
            "id": referral_id,
            "partner_id": partner_id,
            "customer_id": customer_data.get("customer_id"),
            "customer_email": customer_data.get("email", ""),
            "subscription_tier": customer_data.get("subscription_tier", "basic"),
            "monthly_value": customer_data.get("monthly_value", 0.0),
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        
        self.referrals[referral_id] = referral
        
        # Update partner stats
        partner = self.partners.get(partner_id)
        if partner:
            partner["total_referrals"] += 1
        
        return referral
    
    async def calculate_commission(self, partner_id: str, revenue: float) -> Dict[str, Any]:
        """Calculate commission for partner"""
        partner = self.partners.get(partner_id)
        if not partner:
            return {}
        
        commission_amount = revenue * partner["commission_rate"]
        commission_id = f"comm_{int(datetime.now().timestamp())}"
        
        commission = {
            "id": commission_id,
            "partner_id": partner_id,
            "revenue": revenue,
            "commission_rate": partner["commission_rate"],
            "commission_amount": commission_amount,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "paid_at": None
        }
        
        self.commissions[commission_id] = commission
        
        # Update partner total
        partner["total_commission_earned"] += commission_amount
        
        # Calculate parent commission (multi-level)
        if partner.get("parent_partner_id"):
            parent_commission_rate = 0.02  # 2% for parent partner
            parent_commission_amount = revenue * parent_commission_rate
            
            parent_commission_id = f"comm_{int(datetime.now().timestamp())}_parent"
            parent_commission = {
                "id": parent_commission_id,
                "partner_id": partner["parent_partner_id"],
                "revenue": revenue,
                "commission_rate": parent_commission_rate,
                "commission_amount": parent_commission_amount,
                "status": "pending",
                "source": "sub_partner",
                "sub_partner_id": partner_id,
                "created_at": datetime.now().isoformat(),
                "paid_at": None
            }
            self.commissions[parent_commission_id] = parent_commission
        
        return commission
    
    async def pay_commission(self, commission_id: str) -> bool:
        """Mark commission as paid"""
        commission = self.commissions.get(commission_id)
        if not commission:
            return False
        
        commission["status"] = "paid"
        commission["paid_at"] = datetime.now().isoformat()
        
        # Update partner stats
        partner_id = commission["partner_id"]
        partner = self.partners.get(partner_id)
        if partner:
            partner["total_commission_paid"] += commission["commission_amount"]
        
        return True
    
    async def get_partner_analytics(self, partner_id: str) -> Dict[str, Any]:
        """Get analytics for partner"""
        partner = self.partners.get(partner_id)
        if not partner:
            return {}
        
        # Get all referrals
        partner_referrals = [
            ref for ref_id, ref in self.referrals.items()
            if ref["partner_id"] == partner_id
        ]
        
        # Get all commissions
        partner_commissions = [
            comm for comm_id, comm in self.commissions.items()
            if comm["partner_id"] == partner_id
        ]
        
        # Calculate metrics
        active_referrals = len([r for r in partner_referrals if r["status"] == "active"])
        total_revenue = sum([r.get("monthly_value", 0) for r in partner_referrals]) * 12  # Annual
        pending_commission = sum([c["commission_amount"] for c in partner_commissions if c["status"] == "pending"])
        
        return {
            "partner_id": partner_id,
            "tier": partner["tier"],
            "total_referrals": partner["total_referrals"],
            "active_referrals": active_referrals,
            "total_revenue_generated": total_revenue,
            "commission_rate": partner["commission_rate"],
            "total_commission_earned": partner["total_commission_earned"],
            "total_commission_paid": partner["total_commission_paid"],
            "pending_commission": pending_commission,
            "referral_code": partner["referral_code"]
        }
    
    async def get_sub_partners(self, partner_id: str) -> List[Dict[str, Any]]:
        """Get all sub-partners (multi-level)"""
        return [
            partner for pid, partner in self.partners.items()
            if partner.get("parent_partner_id") == partner_id
        ]
