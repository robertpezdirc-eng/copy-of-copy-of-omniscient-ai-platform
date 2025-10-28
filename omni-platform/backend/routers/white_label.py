from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import os
import uuid
import logging
from pathlib import Path

router = APIRouter(prefix="/white-label", tags=["White Label Solutions"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data Models
class BrandingConfig(BaseModel):
    logo_url: Optional[str] = None
    primary_color: str = "#667eea"
    secondary_color: str = "#764ba2"
    company_name: str
    domain: Optional[str] = None
    favicon_url: Optional[str] = None
    custom_css: Optional[str] = None

class FeatureConfig(BaseModel):
    ai_chat: bool = True
    specialized_agents: bool = True
    quantum_computing: bool = False
    api_access: bool = True
    analytics: bool = True
    custom_integrations: bool = False
    white_label_branding: bool = True
    sso_integration: bool = False
    dedicated_support: bool = False

class WhiteLabelInstance(BaseModel):
    instance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    company_name: str
    branding: BrandingConfig
    features: FeatureConfig
    subdomain: str
    custom_domain: Optional[str] = None
    api_limits: Dict[str, int] = Field(default_factory=lambda: {"monthly_calls": 100000, "concurrent_users": 100})
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "active"  # active, suspended, terminated
    billing_plan: str = "enterprise"
    monthly_fee: float = 299.0

class WhiteLabelRequest(BaseModel):
    client_id: str
    company_name: str
    branding: BrandingConfig
    features: FeatureConfig
    subdomain: str
    custom_domain: Optional[str] = None
    api_limits: Optional[Dict[str, int]] = None
    monthly_fee: Optional[float] = None

class WhiteLabelUpdate(BaseModel):
    branding: Optional[BrandingConfig] = None
    features: Optional[FeatureConfig] = None
    api_limits: Optional[Dict[str, int]] = None
    status: Optional[str] = None

class DeploymentConfig(BaseModel):
    instance_id: str
    deployment_type: str = "cloud"  # cloud, on-premise, hybrid
    infrastructure: Dict[str, Any] = Field(default_factory=dict)
    environment_vars: Dict[str, str] = Field(default_factory=dict)
    ssl_certificate: Optional[str] = None
    backup_config: Dict[str, Any] = Field(default_factory=dict)

class WhiteLabelAnalytics(BaseModel):
    instance_id: str
    total_users: int = 0
    monthly_api_calls: int = 0
    revenue: float = 0.0
    uptime: float = 99.9
    last_updated: datetime = Field(default_factory=datetime.now)

# Data storage paths
DATA_DIR = Path("data/white_label")
DATA_DIR.mkdir(parents=True, exist_ok=True)

INSTANCES_FILE = DATA_DIR / "instances.json"
DEPLOYMENTS_FILE = DATA_DIR / "deployments.json"
ANALYTICS_FILE = DATA_DIR / "analytics.json"

# Helper functions
def load_instances() -> List[WhiteLabelInstance]:
    """Load white-label instances from file"""
    if INSTANCES_FILE.exists():
        try:
            with open(INSTANCES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [WhiteLabelInstance(**item) for item in data]
        except Exception as e:
            logger.error(f"Error loading instances: {e}")
    return []

def save_instances(instances: List[WhiteLabelInstance]):
    """Save white-label instances to file"""
    try:
        with open(INSTANCES_FILE, 'w', encoding='utf-8') as f:
            json.dump([instance.dict() for instance in instances], f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving instances: {e}")
        raise HTTPException(status_code=500, detail="Failed to save instances")

def load_deployments() -> List[DeploymentConfig]:
    """Load deployment configurations from file"""
    if DEPLOYMENTS_FILE.exists():
        try:
            with open(DEPLOYMENTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [DeploymentConfig(**item) for item in data]
        except Exception as e:
            logger.error(f"Error loading deployments: {e}")
    return []

def save_deployments(deployments: List[DeploymentConfig]):
    """Save deployment configurations to file"""
    try:
        with open(DEPLOYMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump([deployment.dict() for deployment in deployments], f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving deployments: {e}")
        raise HTTPException(status_code=500, detail="Failed to save deployments")

def load_analytics() -> List[WhiteLabelAnalytics]:
    """Load analytics data from file"""
    if ANALYTICS_FILE.exists():
        try:
            with open(ANALYTICS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [WhiteLabelAnalytics(**item) for item in data]
        except Exception as e:
            logger.error(f"Error loading analytics: {e}")
    return []

def save_analytics(analytics: List[WhiteLabelAnalytics]):
    """Save analytics data to file"""
    try:
        with open(ANALYTICS_FILE, 'w', encoding='utf-8') as f:
            json.dump([analytic.dict() for analytic in analytics], f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to save analytics")

async def deploy_instance(instance: WhiteLabelInstance) -> Dict[str, Any]:
    """Deploy white-label instance (mock implementation)"""
    # In a real implementation, this would:
    # 1. Create Docker containers with custom branding
    # 2. Set up DNS records for subdomain/custom domain
    # 3. Configure SSL certificates
    # 4. Deploy to cloud infrastructure
    # 5. Set up monitoring and logging
    
    deployment_info = {
        "instance_id": instance.instance_id,
        "subdomain": f"{instance.subdomain}.omni-platform.com",
        "custom_domain": instance.custom_domain,
        "deployment_url": f"https://{instance.subdomain}.omni-platform.com",
        "api_endpoint": f"https://api-{instance.subdomain}.omni-platform.com",
        "status": "deployed",
        "deployed_at": datetime.now().isoformat()
    }
    
    return deployment_info

# API Endpoints

@router.get("/instances", response_model=List[WhiteLabelInstance])
async def get_white_label_instances():
    """Get all white-label instances"""
    try:
        instances = load_instances()
        return instances
    except Exception as e:
        logger.error(f"Error retrieving instances: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve instances")

@router.get("/instances/{instance_id}", response_model=WhiteLabelInstance)
async def get_white_label_instance(instance_id: str):
    """Get specific white-label instance"""
    try:
        instances = load_instances()
        instance = next((i for i in instances if i.instance_id == instance_id), None)
        
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        return instance
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve instance")

@router.post("/instances", response_model=Dict[str, Any])
async def create_white_label_instance(request: WhiteLabelRequest, background_tasks: BackgroundTasks):
    """Create new white-label instance"""
    try:
        instances = load_instances()
        
        # Check if subdomain is already taken
        if any(i.subdomain == request.subdomain for i in instances):
            raise HTTPException(status_code=400, detail="Subdomain already taken")
        
        # Create new instance
        instance = WhiteLabelInstance(
            client_id=request.client_id,
            company_name=request.company_name,
            branding=request.branding,
            features=request.features,
            subdomain=request.subdomain,
            custom_domain=request.custom_domain,
            api_limits=request.api_limits or {"monthly_calls": 100000, "concurrent_users": 100},
            monthly_fee=request.monthly_fee or 299.0
        )
        
        instances.append(instance)
        save_instances(instances)
        
        # Deploy instance in background
        background_tasks.add_task(deploy_instance, instance)
        
        # Initialize analytics
        analytics = load_analytics()
        analytics.append(WhiteLabelAnalytics(instance_id=instance.instance_id))
        save_analytics(analytics)
        
        return {
            "instance_id": instance.instance_id,
            "message": "White-label instance created successfully",
            "deployment_url": f"https://{instance.subdomain}.omni-platform.com",
            "api_endpoint": f"https://api-{instance.subdomain}.omni-platform.com",
            "status": "deploying"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating instance: {e}")
        raise HTTPException(status_code=500, detail="Failed to create instance")

@router.put("/instances/{instance_id}", response_model=Dict[str, str])
async def update_white_label_instance(instance_id: str, update: WhiteLabelUpdate):
    """Update white-label instance configuration"""
    try:
        instances = load_instances()
        instance_index = next((i for i, inst in enumerate(instances) if inst.instance_id == instance_id), None)
        
        if instance_index is None:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        instance = instances[instance_index]
        
        # Update fields
        if update.branding:
            instance.branding = update.branding
        if update.features:
            instance.features = update.features
        if update.api_limits:
            instance.api_limits = update.api_limits
        if update.status:
            instance.status = update.status
        
        instances[instance_index] = instance
        save_instances(instances)
        
        return {"message": "Instance updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update instance")

@router.delete("/instances/{instance_id}")
async def delete_white_label_instance(instance_id: str):
    """Delete white-label instance"""
    try:
        instances = load_instances()
        instance = next((i for i in instances if i.instance_id == instance_id), None)
        
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        # Remove instance
        instances = [i for i in instances if i.instance_id != instance_id]
        save_instances(instances)
        
        # Remove analytics
        analytics = load_analytics()
        analytics = [a for a in analytics if a.instance_id != instance_id]
        save_analytics(analytics)
        
        return {"message": "Instance deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete instance")

@router.post("/instances/{instance_id}/deploy")
async def deploy_white_label_instance(instance_id: str, deployment_config: Optional[DeploymentConfig] = None):
    """Deploy or redeploy white-label instance"""
    try:
        instances = load_instances()
        instance = next((i for i in instances if i.instance_id == instance_id), None)
        
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        # Deploy instance
        deployment_info = await deploy_instance(instance)
        
        # Save deployment config
        if deployment_config:
            deployments = load_deployments()
            deployment_config.instance_id = instance_id
            deployments.append(deployment_config)
            save_deployments(deployments)
        
        return deployment_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deploying instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to deploy instance")

@router.get("/instances/{instance_id}/analytics", response_model=WhiteLabelAnalytics)
async def get_instance_analytics(instance_id: str):
    """Get analytics for specific white-label instance"""
    try:
        analytics = load_analytics()
        instance_analytics = next((a for a in analytics if a.instance_id == instance_id), None)
        
        if not instance_analytics:
            # Create default analytics if not found
            instance_analytics = WhiteLabelAnalytics(instance_id=instance_id)
            analytics.append(instance_analytics)
            save_analytics(analytics)
        
        return instance_analytics
        
    except Exception as e:
        logger.error(f"Error retrieving analytics for {instance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

@router.get("/templates", response_model=List[Dict[str, Any]])
async def get_white_label_templates():
    """Get available white-label templates"""
    templates = [
        {
            "id": "corporate",
            "name": "Corporate",
            "description": "Professional corporate template",
            "branding": {
                "primary_color": "#2c3e50",
                "secondary_color": "#3498db",
                "company_name": "Your Company"
            },
            "features": {
                "ai_chat": True,
                "specialized_agents": True,
                "analytics": True,
                "api_access": True
            }
        },
        {
            "id": "healthcare",
            "name": "Healthcare",
            "description": "Healthcare industry template",
            "branding": {
                "primary_color": "#27ae60",
                "secondary_color": "#2ecc71",
                "company_name": "Healthcare Solutions"
            },
            "features": {
                "ai_chat": True,
                "specialized_agents": True,
                "analytics": True,
                "sso_integration": True
            }
        },
        {
            "id": "fintech",
            "name": "FinTech",
            "description": "Financial technology template",
            "branding": {
                "primary_color": "#8e44ad",
                "secondary_color": "#9b59b6",
                "company_name": "FinTech Solutions"
            },
            "features": {
                "ai_chat": True,
                "specialized_agents": True,
                "quantum_computing": True,
                "analytics": True,
                "dedicated_support": True
            }
        }
    ]
    
    return templates

@router.get("/pricing", response_model=List[Dict[str, Any]])
async def get_white_label_pricing():
    """Get white-label pricing tiers"""
    pricing = [
        {
            "tier": "Starter",
            "monthly_fee": 199.0,
            "setup_fee": 500.0,
            "features": {
                "monthly_api_calls": 50000,
                "concurrent_users": 50,
                "custom_branding": True,
                "subdomain": True,
                "email_support": True
            }
        },
        {
            "tier": "Professional",
            "monthly_fee": 399.0,
            "setup_fee": 1000.0,
            "features": {
                "monthly_api_calls": 200000,
                "concurrent_users": 200,
                "custom_branding": True,
                "custom_domain": True,
                "sso_integration": True,
                "priority_support": True
            }
        },
        {
            "tier": "Enterprise",
            "monthly_fee": 799.0,
            "setup_fee": 2000.0,
            "features": {
                "monthly_api_calls": "unlimited",
                "concurrent_users": "unlimited",
                "custom_branding": True,
                "custom_domain": True,
                "on_premise_option": True,
                "dedicated_support": True,
                "sla_guarantee": True
            }
        }
    ]
    
    return pricing

@router.get("/revenue-analytics", response_model=Dict[str, Any])
async def get_white_label_revenue():
    """Get white-label revenue analytics"""
    try:
        instances = load_instances()
        analytics = load_analytics()
        
        total_instances = len(instances)
        active_instances = len([i for i in instances if i.status == "active"])
        total_monthly_revenue = sum(i.monthly_fee for i in instances if i.status == "active")
        
        # Calculate growth metrics
        current_month = datetime.now().month
        last_month = current_month - 1 if current_month > 1 else 12
        
        return {
            "total_instances": total_instances,
            "active_instances": active_instances,
            "suspended_instances": len([i for i in instances if i.status == "suspended"]),
            "total_monthly_revenue": total_monthly_revenue,
            "average_revenue_per_instance": total_monthly_revenue / max(active_instances, 1),
            "growth_rate": 15.5,  # Mock growth rate
            "churn_rate": 2.3,    # Mock churn rate
            "top_clients": [
                {"company": i.company_name, "revenue": i.monthly_fee, "instance_id": i.instance_id}
                for i in sorted(instances, key=lambda x: x.monthly_fee, reverse=True)[:5]
            ]
        }
        
    except Exception as e:
        logger.error(f"Error calculating revenue analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate revenue analytics")