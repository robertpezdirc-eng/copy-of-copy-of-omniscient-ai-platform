from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import json
import os
import uuid
import logging
from pathlib import Path
from enum import Enum

router = APIRouter(prefix="/enterprise", tags=["Enterprise Packages"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enums
class PackageType(str, Enum):
    BASIC_ENTERPRISE = "basic_enterprise"
    ADVANCED_ENTERPRISE = "advanced_enterprise"
    PREMIUM_ENTERPRISE = "premium_enterprise"
    CUSTOM_ENTERPRISE = "custom_enterprise"

class DeploymentType(str, Enum):
    CLOUD = "cloud"
    ON_PREMISE = "on_premise"
    HYBRID = "hybrid"
    MULTI_CLOUD = "multi_cloud"

class SupportLevel(str, Enum):
    STANDARD = "standard"
    PRIORITY = "priority"
    DEDICATED = "dedicated"
    WHITE_GLOVE = "white_glove"

# Data Models
class SecurityFeatures(BaseModel):
    sso_integration: bool = True
    multi_factor_auth: bool = True
    role_based_access: bool = True
    audit_logging: bool = True
    data_encryption: bool = True
    compliance_reports: bool = False
    penetration_testing: bool = False
    security_monitoring: bool = False

class ScalabilityFeatures(BaseModel):
    auto_scaling: bool = True
    load_balancing: bool = True
    cdn_integration: bool = False
    database_clustering: bool = False
    microservices_architecture: bool = True
    kubernetes_deployment: bool = False
    global_distribution: bool = False
    disaster_recovery: bool = False

class IntegrationFeatures(BaseModel):
    api_gateway: bool = True
    webhook_support: bool = True
    custom_connectors: bool = False
    enterprise_sso: bool = True
    crm_integration: bool = False
    erp_integration: bool = False
    data_warehouse_sync: bool = False
    third_party_apis: List[str] = Field(default_factory=list)

class SupportFeatures(BaseModel):
    support_level: SupportLevel = SupportLevel.STANDARD
    response_time_sla: str = "24 hours"
    dedicated_account_manager: bool = False
    technical_consultation: bool = False
    implementation_support: bool = False
    training_sessions: int = 0
    custom_development: bool = False
    priority_feature_requests: bool = False

class EnterprisePackage(BaseModel):
    package_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    package_type: PackageType
    name: str
    description: str
    monthly_price: float
    annual_price: float
    setup_fee: float
    minimum_users: int
    maximum_users: Optional[int] = None
    api_call_limit: Union[int, str] = "unlimited"
    storage_limit: Union[int, str] = "unlimited"
    security_features: SecurityFeatures
    scalability_features: ScalabilityFeatures
    integration_features: IntegrationFeatures
    support_features: SupportFeatures
    deployment_options: List[DeploymentType]
    custom_features: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

class EnterpriseSubscription(BaseModel):
    subscription_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    company_name: str
    package_id: str
    deployment_type: DeploymentType
    user_count: int
    custom_requirements: Dict[str, Any] = Field(default_factory=dict)
    contract_start: datetime
    contract_end: datetime
    monthly_fee: float
    annual_discount: float = 0.0
    status: str = "active"  # active, suspended, terminated, pending
    billing_cycle: str = "monthly"  # monthly, annual
    auto_renewal: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

class CustomRequirement(BaseModel):
    requirement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    title: str
    description: str
    priority: str = "medium"  # low, medium, high, critical
    estimated_cost: Optional[float] = None
    estimated_timeline: Optional[str] = None
    status: str = "pending"  # pending, approved, in_development, completed, rejected
    created_at: datetime = Field(default_factory=datetime.now)

class EnterpriseQuote(BaseModel):
    quote_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    company_name: str
    contact_email: str
    package_type: PackageType
    user_count: int
    deployment_type: DeploymentType
    custom_requirements: List[str] = Field(default_factory=list)
    estimated_price: float
    valid_until: datetime
    status: str = "pending"  # pending, sent, accepted, rejected, expired
    created_at: datetime = Field(default_factory=datetime.now)

class EnterpriseAnalytics(BaseModel):
    subscription_id: str
    monthly_revenue: float = 0.0
    user_adoption_rate: float = 0.0
    api_usage: int = 0
    support_tickets: int = 0
    satisfaction_score: float = 0.0
    uptime: float = 99.9
    last_updated: datetime = Field(default_factory=datetime.now)

# Data storage paths
DATA_DIR = Path("data/enterprise")
DATA_DIR.mkdir(parents=True, exist_ok=True)

PACKAGES_FILE = DATA_DIR / "packages.json"
SUBSCRIPTIONS_FILE = DATA_DIR / "subscriptions.json"
REQUIREMENTS_FILE = DATA_DIR / "custom_requirements.json"
QUOTES_FILE = DATA_DIR / "quotes.json"
ANALYTICS_FILE = DATA_DIR / "analytics.json"

# Default enterprise packages
DEFAULT_PACKAGES = [
    EnterprisePackage(
        package_type=PackageType.BASIC_ENTERPRISE,
        name="Basic Enterprise",
        description="Essential enterprise features for growing businesses",
        monthly_price=999.0,
        annual_price=9990.0,
        setup_fee=2000.0,
        minimum_users=25,
        maximum_users=100,
        api_call_limit=1000000,
        storage_limit="100GB",
        security_features=SecurityFeatures(),
        scalability_features=ScalabilityFeatures(),
        integration_features=IntegrationFeatures(),
        support_features=SupportFeatures(
            support_level=SupportLevel.PRIORITY,
            response_time_sla="12 hours"
        ),
        deployment_options=[DeploymentType.CLOUD]
    ),
    EnterprisePackage(
        package_type=PackageType.ADVANCED_ENTERPRISE,
        name="Advanced Enterprise",
        description="Advanced features with enhanced security and scalability",
        monthly_price=2499.0,
        annual_price=24990.0,
        setup_fee=5000.0,
        minimum_users=100,
        maximum_users=500,
        api_call_limit="unlimited",
        storage_limit="1TB",
        security_features=SecurityFeatures(
            compliance_reports=True,
            security_monitoring=True
        ),
        scalability_features=ScalabilityFeatures(
            cdn_integration=True,
            kubernetes_deployment=True
        ),
        integration_features=IntegrationFeatures(
            custom_connectors=True,
            crm_integration=True
        ),
        support_features=SupportFeatures(
            support_level=SupportLevel.DEDICATED,
            response_time_sla="4 hours",
            dedicated_account_manager=True,
            training_sessions=5
        ),
        deployment_options=[DeploymentType.CLOUD, DeploymentType.HYBRID]
    ),
    EnterprisePackage(
        package_type=PackageType.PREMIUM_ENTERPRISE,
        name="Premium Enterprise",
        description="Full-featured enterprise solution with white-glove support",
        monthly_price=4999.0,
        annual_price=49990.0,
        setup_fee=10000.0,
        minimum_users=500,
        maximum_users=None,
        api_call_limit="unlimited",
        storage_limit="unlimited",
        security_features=SecurityFeatures(
            compliance_reports=True,
            penetration_testing=True,
            security_monitoring=True
        ),
        scalability_features=ScalabilityFeatures(
            cdn_integration=True,
            database_clustering=True,
            kubernetes_deployment=True,
            global_distribution=True,
            disaster_recovery=True
        ),
        integration_features=IntegrationFeatures(
            custom_connectors=True,
            crm_integration=True,
            erp_integration=True,
            data_warehouse_sync=True,
            third_party_apis=["Salesforce", "SAP", "Oracle", "Microsoft"]
        ),
        support_features=SupportFeatures(
            support_level=SupportLevel.WHITE_GLOVE,
            response_time_sla="1 hour",
            dedicated_account_manager=True,
            technical_consultation=True,
            implementation_support=True,
            training_sessions=20,
            custom_development=True,
            priority_feature_requests=True
        ),
        deployment_options=[DeploymentType.CLOUD, DeploymentType.ON_PREMISE, DeploymentType.HYBRID, DeploymentType.MULTI_CLOUD]
    )
]

# Helper functions
def load_packages() -> List[EnterprisePackage]:
    """Load enterprise packages from file"""
    if PACKAGES_FILE.exists():
        try:
            with open(PACKAGES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [EnterprisePackage(**item) for item in data]
        except Exception as e:
            logger.error(f"Error loading packages: {e}")
    
    # Return default packages if file doesn't exist
    save_packages(DEFAULT_PACKAGES)
    return DEFAULT_PACKAGES

def save_packages(packages: List[EnterprisePackage]):
    """Save enterprise packages to file"""
    try:
        with open(PACKAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump([package.dict() for package in packages], f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving packages: {e}")
        raise HTTPException(status_code=500, detail="Failed to save packages")

def load_subscriptions() -> List[EnterpriseSubscription]:
    """Load enterprise subscriptions from file"""
    if SUBSCRIPTIONS_FILE.exists():
        try:
            with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [EnterpriseSubscription(**item) for item in data]
        except Exception as e:
            logger.error(f"Error loading subscriptions: {e}")
    return []

def save_subscriptions(subscriptions: List[EnterpriseSubscription]):
    """Save enterprise subscriptions to file"""
    try:
        with open(SUBSCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump([subscription.dict() for subscription in subscriptions], f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving subscriptions: {e}")
        raise HTTPException(status_code=500, detail="Failed to save subscriptions")

def load_quotes() -> List[EnterpriseQuote]:
    """Load enterprise quotes from file"""
    if QUOTES_FILE.exists():
        try:
            with open(QUOTES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [EnterpriseQuote(**item) for item in data]
        except Exception as e:
            logger.error(f"Error loading quotes: {e}")
    return []

def save_quotes(quotes: List[EnterpriseQuote]):
    """Save enterprise quotes to file"""
    try:
        with open(QUOTES_FILE, 'w', encoding='utf-8') as f:
            json.dump([quote.dict() for quote in quotes], f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving quotes: {e}")
        raise HTTPException(status_code=500, detail="Failed to save quotes")

def calculate_custom_price(base_price: float, user_count: int, custom_requirements: List[str]) -> float:
    """Calculate custom pricing based on requirements"""
    # Base calculation
    price = base_price
    
    # User scaling
    if user_count > 1000:
        price *= 1.5
    elif user_count > 500:
        price *= 1.2
    
    # Custom requirements pricing
    requirement_costs = {
        "custom_ai_model": 5000,
        "dedicated_infrastructure": 3000,
        "advanced_analytics": 2000,
        "custom_integrations": 1500,
        "24_7_support": 1000,
        "compliance_certification": 2500,
        "data_migration": 1000,
        "training_program": 500
    }
    
    for req in custom_requirements:
        if req in requirement_costs:
            price += requirement_costs[req]
    
    return price

# API Endpoints

@router.get("/packages", response_model=List[EnterprisePackage])
async def get_enterprise_packages():
    """Get all available enterprise packages"""
    try:
        packages = load_packages()
        return [pkg for pkg in packages if pkg.is_active]
    except Exception as e:
        logger.error(f"Error retrieving packages: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve packages")

@router.get("/packages/{package_id}", response_model=EnterprisePackage)
async def get_enterprise_package(package_id: str):
    """Get specific enterprise package"""
    try:
        packages = load_packages()
        package = next((pkg for pkg in packages if pkg.package_id == package_id), None)
        
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        
        return package
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving package {package_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve package")

@router.post("/quotes", response_model=Dict[str, Any])
async def create_enterprise_quote(
    client_id: str,
    company_name: str,
    contact_email: str,
    package_type: PackageType,
    user_count: int,
    deployment_type: DeploymentType,
    custom_requirements: List[str] = []
):
    """Create enterprise quote"""
    try:
        packages = load_packages()
        base_package = next((pkg for pkg in packages if pkg.package_type == package_type), None)
        
        if not base_package:
            raise HTTPException(status_code=404, detail="Package type not found")
        
        # Calculate custom pricing
        estimated_price = calculate_custom_price(
            base_package.monthly_price,
            user_count,
            custom_requirements
        )
        
        # Create quote
        quote = EnterpriseQuote(
            client_id=client_id,
            company_name=company_name,
            contact_email=contact_email,
            package_type=package_type,
            user_count=user_count,
            deployment_type=deployment_type,
            custom_requirements=custom_requirements,
            estimated_price=estimated_price,
            valid_until=datetime.now() + timedelta(days=30)
        )
        
        quotes = load_quotes()
        quotes.append(quote)
        save_quotes(quotes)
        
        return {
            "quote_id": quote.quote_id,
            "estimated_price": estimated_price,
            "valid_until": quote.valid_until,
            "message": "Enterprise quote created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating quote: {e}")
        raise HTTPException(status_code=500, detail="Failed to create quote")

@router.get("/quotes/{quote_id}", response_model=EnterpriseQuote)
async def get_enterprise_quote(quote_id: str):
    """Get specific enterprise quote"""
    try:
        quotes = load_quotes()
        quote = next((q for q in quotes if q.quote_id == quote_id), None)
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        return quote
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving quote {quote_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quote")

@router.post("/subscriptions", response_model=Dict[str, Any])
async def create_enterprise_subscription(
    client_id: str,
    company_name: str,
    package_id: str,
    deployment_type: DeploymentType,
    user_count: int,
    contract_months: int = 12,
    billing_cycle: str = "monthly",
    custom_requirements: Dict[str, Any] = {}
):
    """Create enterprise subscription"""
    try:
        packages = load_packages()
        package = next((pkg for pkg in packages if pkg.package_id == package_id), None)
        
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        
        # Calculate pricing
        monthly_fee = package.monthly_price
        if user_count > package.minimum_users:
            # Add per-user pricing for additional users
            additional_users = user_count - package.minimum_users
            monthly_fee += additional_users * 50  # $50 per additional user
        
        # Apply annual discount
        annual_discount = 0.15 if billing_cycle == "annual" else 0.0
        
        # Create subscription
        subscription = EnterpriseSubscription(
            client_id=client_id,
            company_name=company_name,
            package_id=package_id,
            deployment_type=deployment_type,
            user_count=user_count,
            custom_requirements=custom_requirements,
            contract_start=datetime.now(),
            contract_end=datetime.now() + timedelta(days=contract_months * 30),
            monthly_fee=monthly_fee,
            annual_discount=annual_discount,
            billing_cycle=billing_cycle
        )
        
        subscriptions = load_subscriptions()
        subscriptions.append(subscription)
        save_subscriptions(subscriptions)
        
        return {
            "subscription_id": subscription.subscription_id,
            "monthly_fee": monthly_fee,
            "annual_discount": annual_discount,
            "contract_end": subscription.contract_end,
            "message": "Enterprise subscription created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")

@router.get("/subscriptions", response_model=List[EnterpriseSubscription])
async def get_enterprise_subscriptions():
    """Get all enterprise subscriptions"""
    try:
        subscriptions = load_subscriptions()
        return subscriptions
    except Exception as e:
        logger.error(f"Error retrieving subscriptions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscriptions")

@router.get("/subscriptions/{subscription_id}", response_model=EnterpriseSubscription)
async def get_enterprise_subscription(subscription_id: str):
    """Get specific enterprise subscription"""
    try:
        subscriptions = load_subscriptions()
        subscription = next((s for s in subscriptions if s.subscription_id == subscription_id), None)
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving subscription {subscription_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription")

@router.get("/analytics/revenue", response_model=Dict[str, Any])
async def get_enterprise_revenue_analytics():
    """Get enterprise revenue analytics"""
    try:
        subscriptions = load_subscriptions()
        active_subscriptions = [s for s in subscriptions if s.status == "active"]
        
        total_monthly_revenue = sum(s.monthly_fee for s in active_subscriptions)
        total_annual_revenue = sum(
            s.monthly_fee * 12 * (1 - s.annual_discount) if s.billing_cycle == "annual" 
            else s.monthly_fee * 12 
            for s in active_subscriptions
        )
        
        # Calculate metrics by package type
        revenue_by_package = {}
        for subscription in active_subscriptions:
            package_type = subscription.package_id  # Simplified
            if package_type not in revenue_by_package:
                revenue_by_package[package_type] = 0
            revenue_by_package[package_type] += subscription.monthly_fee
        
        return {
            "total_subscriptions": len(subscriptions),
            "active_subscriptions": len(active_subscriptions),
            "total_monthly_revenue": total_monthly_revenue,
            "projected_annual_revenue": total_annual_revenue,
            "average_deal_size": total_monthly_revenue / max(len(active_subscriptions), 1),
            "revenue_by_package": revenue_by_package,
            "growth_metrics": {
                "monthly_growth_rate": 12.5,  # Mock data
                "churn_rate": 3.2,
                "expansion_revenue": 25000
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating enterprise revenue: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate revenue analytics")

@router.get("/deployment-options", response_model=List[Dict[str, Any]])
async def get_deployment_options():
    """Get available deployment options"""
    options = [
        {
            "type": "cloud",
            "name": "Cloud Deployment",
            "description": "Fully managed cloud solution",
            "features": ["Auto-scaling", "Global CDN", "99.9% SLA"],
            "setup_time": "1-2 weeks",
            "additional_cost": 0
        },
        {
            "type": "on_premise",
            "name": "On-Premise Deployment",
            "description": "Deploy on your own infrastructure",
            "features": ["Full control", "Data sovereignty", "Custom security"],
            "setup_time": "4-6 weeks",
            "additional_cost": 5000
        },
        {
            "type": "hybrid",
            "name": "Hybrid Deployment",
            "description": "Combination of cloud and on-premise",
            "features": ["Flexible architecture", "Data locality", "Scalability"],
            "setup_time": "6-8 weeks",
            "additional_cost": 3000
        },
        {
            "type": "multi_cloud",
            "name": "Multi-Cloud Deployment",
            "description": "Deploy across multiple cloud providers",
            "features": ["Vendor independence", "High availability", "Global reach"],
            "setup_time": "8-12 weeks",
            "additional_cost": 7500
        }
    ]
    
    return options