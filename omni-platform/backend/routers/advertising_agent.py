from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import os
import uuid
import time
import asyncio
import aiohttp
from datetime import datetime, timedelta
import logging

router = APIRouter(prefix="/api/v1/ads", tags=["advertising"])

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CAMPAIGNS_FILE = DATA_DIR / "ads_campaigns.json"
# Use a safe default within the backend app directory to avoid IndexError
# when running inside containers where higher-level parents may not exist.
KPI_FILE = Path(os.environ.get("KPI_FILE", str(DATA_DIR / "business_kpis.json")))
OAUTH_FILE = DATA_DIR / "google_ads_oauth.json"
CANVA_OAUTH_FILE = DATA_DIR / "canva_oauth.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
if not CAMPAIGNS_FILE.exists():
    CAMPAIGNS_FILE.write_text(json.dumps({"campaigns": []}, ensure_ascii=False), encoding="utf-8")

# Google Ads API Configuration
GOOGLE_ADS_CONFIG = {
    "developer_token": os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN"),
    "client_id": os.environ.get("GOOGLE_ADS_CLIENT_ID"),
    "client_secret": os.environ.get("GOOGLE_ADS_CLIENT_SECRET"),
    "refresh_token": os.environ.get("GOOGLE_ADS_REFRESH_TOKEN"),
    "customer_id": os.environ.get("GOOGLE_ADS_CUSTOMER_ID"),
    "api_version": "v15"
}

# Canva API Configuration
CANVA_CONFIG = {
    "client_id": os.environ.get("CANVA_CLIENT_ID"),
    "client_secret": os.environ.get("CANVA_CLIENT_SECRET"),
    "redirect_uri": os.environ.get("CANVA_REDIRECT_URI", "http://localhost:8000/api/v1/ads/oauth/canva/callback"),
    "api_version": "v1"
}

# Canva API Configuration
CANVA_CONFIG = {
    "client_id": os.environ.get("CANVA_CLIENT_ID"),
    "client_secret": os.environ.get("CANVA_CLIENT_SECRET"),
    "redirect_uri": os.environ.get("CANVA_REDIRECT_URI", "http://localhost:8000/api/v1/ads/oauth/canva/callback"),
    "api_version": "v1"
}

logger = logging.getLogger(__name__)


class CampaignCreate(BaseModel):
    platform: str = Field(..., description="ad platform, e.g. 'google'")
    name: str
    budget_eur: float
    currency: str = "EUR"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    targeting: Optional[Dict[str, Any]] = None
    keywords: Optional[List[str]] = None
    ad_groups: Optional[List[Dict[str, Any]]] = None


class CampaignUpdateStatus(BaseModel):
    campaign_id: str


class CampaignBudgetUpdate(BaseModel):
    campaign_id: str
    new_budget_eur: float


class SyncKPI(BaseModel):
    revenue_eur: Optional[float] = None
    active_users: Optional[int] = None
    conversion_rate: Optional[float] = None


class GoogleAdsOAuth(BaseModel):
    authorization_code: str
    redirect_uri: str


class CanvaOAuth(BaseModel):
    authorization_code: str
    redirect_uri: str


class CanvaAdCreate(BaseModel):
    template_id: Optional[str] = None
    title: str = "Discover Omni Platform"
    description: str = "The ultimate AI-powered platform for automation and insights."
    call_to_action: str = "Learn More"


def _load_campaigns() -> Dict[str, Any]:
    try:
        return json.loads(CAMPAIGNS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"campaigns": []}


def _save_campaigns(data: Dict[str, Any]) -> None:
    CAMPAIGNS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_oauth_tokens() -> Dict[str, Any]:
    try:
        return json.loads(OAUTH_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_oauth_tokens(tokens: Dict[str, Any]) -> None:
    OAUTH_FILE.write_text(json.dumps(tokens, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_canva_oauth_tokens() -> Dict[str, Any]:
    try:
        return json.loads(CANVA_OAUTH_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_canva_oauth_tokens(tokens: Dict[str, Any]) -> None:
    CANVA_OAUTH_FILE.write_text(json.dumps(tokens, ensure_ascii=False, indent=2), encoding="utf-8")


async def _get_google_ads_access_token() -> str:
    """Get fresh access token using refresh token"""
    if not GOOGLE_ADS_CONFIG["refresh_token"]:
        raise HTTPException(status_code=401, detail="Google Ads OAuth not configured")

    tokens = _load_oauth_tokens()

    # Check if we have a valid access token
    if tokens.get("access_token") and tokens.get("expires_at", 0) > time.time() + 300:
        return tokens["access_token"]

    # Refresh the access token
    async with aiohttp.ClientSession() as session:
        data = {
            "client_id": GOOGLE_ADS_CONFIG["client_id"],
            "client_secret": GOOGLE_ADS_CONFIG["client_secret"],
            "refresh_token": GOOGLE_ADS_CONFIG["refresh_token"],
            "grant_type": "refresh_token"
        }

        async with session.post("https://oauth2.googleapis.com/token", data=data) as response:
            if response.status != 200:
                raise HTTPException(status_code=401, detail="Failed to refresh Google Ads token")

            token_data = await response.json()
            tokens.update({
                "access_token": token_data["access_token"],
                "expires_at": time.time() + token_data.get("expires_in", 3600)
            })
            _save_oauth_tokens(tokens)
            return token_data["access_token"]


async def _google_ads_api_request(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Make authenticated request to Google Ads API"""
    access_token = await _get_google_ads_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": GOOGLE_ADS_CONFIG["developer_token"],
        "Content-Type": "application/json"
    }

    base_url = f"https://googleads.googleapis.com/{GOOGLE_ADS_CONFIG['api_version']}"
    url = f"{base_url}/{endpoint}"

    async with aiohttp.ClientSession() as session:
        if method == "POST":
            async with session.post(url, headers=headers, json=data) as response:
                return await response.json()
        else:
            async with session.get(url, headers=headers) as response:
                return await response.json()


async def _get_canva_access_token() -> str:
    """Get fresh access token using refresh token for Canva"""
    if not CANVA_CONFIG["client_id"]:
        raise HTTPException(status_code=401, detail="Canva OAuth not configured")

    tokens = _load_canva_oauth_tokens()

    # Check if we have a valid access token
    if tokens.get("access_token") and tokens.get("expires_at", 0) > time.time() + 300:
        return tokens["access_token"]

    # Refresh the access token
    async with aiohttp.ClientSession() as session:
        data = {
            "client_id": CANVA_CONFIG["client_id"],
            "client_secret": CANVA_CONFIG["client_secret"],
            "refresh_token": tokens.get("refresh_token"),
            "grant_type": "refresh_token"
        }

        async with session.post("https://api.canva.com/oauth/token", data=data) as response:
            if response.status != 200:
                raise HTTPException(status_code=401, detail="Failed to refresh Canva token")

            token_data = await response.json()
            tokens.update({
                "access_token": token_data["access_token"],
                "expires_at": time.time() + token_data.get("expires_in", 3600)
            })
            _save_canva_oauth_tokens(tokens)
            return token_data["access_token"]


async def _canva_api_request(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Make authenticated request to Canva API"""
    access_token = await _get_canva_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    base_url = f"https://api.canva.com/{CANVA_CONFIG['api_version']}"
    url = f"{base_url}/{endpoint}"

    async with aiohttp.ClientSession() as session:
        if method == "POST":
            async with session.post(url, headers=headers, json=data) as response:
                return await response.json()
        else:
            async with session.get(url, headers=headers) as response:
                return await response.json()


async def _create_canva_design(ad_data: Dict) -> Dict:
    """Create a Canva design for promotional ad"""
    # Use a default template if not provided
    template_id = ad_data.get("template_id", "DAE6z8z8z8z8z8z8z8z8z8z8z8z8z8z8")  # Example template ID

    design_data = {
        "design_type": "poster",
        "title": ad_data["title"],
        "elements": [
            {
                "type": "text",
                "content": ad_data["title"],
                "font_size": 48,
                "color": "#000000",
                "position": {"x": 100, "y": 100}
            },
            {
                "type": "text",
                "content": ad_data["description"],
                "font_size": 24,
                "color": "#666666",
                "position": {"x": 100, "y": 200}
            },
            {
                "type": "text",
                "content": ad_data["call_to_action"],
                "font_size": 32,
                "color": "#007bff",
                "position": {"x": 100, "y": 300}
            }
        ]
    }

    endpoint = "designs"
    result = await _canva_api_request(endpoint, "POST", design_data)
    return result


async def _create_google_ads_campaign(campaign_data: Dict) -> Dict:
    """Create actual Google Ads campaign"""
    customer_id = GOOGLE_ADS_CONFIG["customer_id"]

    # Create campaign resource
    campaign_resource = {
        "name": campaign_data["name"],
        "status": "ENABLED",
        "advertisingChannelType": "SEARCH",
        "biddingStrategyType": "TARGET_CPA",
        "campaignBudget": {
            "amountMicros": int(campaign_data["budget_eur"] * 1000000),  # Convert to micros
            "deliveryMethod": "STANDARD"
        },
        "networkSettings": {
            "targetGoogleSearch": True,
            "targetSearchNetwork": True,
            "targetContentNetwork": False
        }
    }

    if campaign_data.get("start_date"):
        campaign_resource["startDate"] = campaign_data["start_date"]
    if campaign_data.get("end_date"):
        campaign_resource["endDate"] = campaign_data["end_date"]

    # Create campaign via API
    endpoint = f"customers/{customer_id}/campaigns:mutate"
    mutation_data = {
        "operations": [{
            "create": campaign_resource
        }]
    }

    result = await _google_ads_api_request(endpoint, "POST", mutation_data)
    return result


async def _update_google_ads_campaign_status(campaign_id: str, status: str) -> Dict:
    """Update Google Ads campaign status"""
    customer_id = GOOGLE_ADS_CONFIG["customer_id"]

    mutation_data = {
        "operations": [{
            "update": {
                "resourceName": f"customers/{customer_id}/campaigns/{campaign_id}",
                "status": "ENABLED" if status == "active" else "PAUSED"
            },
            "updateMask": "status"
        }]
    }

    endpoint = f"customers/{customer_id}/campaigns:mutate"
    return await _google_ads_api_request(endpoint, "POST", mutation_data)


async def _get_google_ads_campaign_performance(campaign_id: str) -> Dict:
    """Get campaign performance metrics"""
    customer_id = GOOGLE_ADS_CONFIG["customer_id"]

    query = f"""
    SELECT
        campaign.id,
        campaign.name,
        campaign.status,
        metrics.impressions,
        metrics.clicks,
        metrics.cost_micros,
        metrics.conversions,
        metrics.ctr,
        metrics.average_cpc
    FROM campaign
    WHERE campaign.id = {campaign_id}
    AND segments.date DURING LAST_30_DAYS
    """

    endpoint = f"customers/{customer_id}/googleAds:searchStream"
    search_data = {"query": query}

    return await _google_ads_api_request(endpoint, "POST", search_data)


@router.get("/oauth/google/test-refresh")
async def test_google_ads_refresh():
    """Test refresh flow using configured GOOGLE_ADS_REFRESH_TOKEN.
    Returns access token prefix on success, or propagates error status.
    """
    try:
        token = await _get_google_ads_access_token()
        return {"ok": True, "access_token_prefix": token[:12]}
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"ok": False, "error": e.detail})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oauth/google/url")
def get_google_oauth_url():
    """Get Google Ads OAuth authorization URL"""
    if not GOOGLE_ADS_CONFIG["client_id"]:
        raise HTTPException(status_code=500, detail="Google Ads OAuth not configured")

    scopes = "https://www.googleapis.com/auth/adwords"
    redirect_uri = "http://localhost:8000/api/v1/ads/oauth/google/callback"

    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_ADS_CONFIG['client_id']}&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scopes}&"
        f"response_type=code&"
        f"access_type=offline&"
        f"prompt=consent"
    )

    return {"authorization_url": auth_url, "redirect_uri": redirect_uri}


@router.post("/oauth/google/callback")
async def google_oauth_callback(oauth_data: GoogleAdsOAuth):
    """Handle Google OAuth callback and exchange code for tokens"""
    async with aiohttp.ClientSession() as session:
        data = {
            "client_id": GOOGLE_ADS_CONFIG["client_id"],
            "client_secret": GOOGLE_ADS_CONFIG["client_secret"],
            "code": oauth_data.authorization_code,
            "grant_type": "authorization_code",
            "redirect_uri": oauth_data.redirect_uri
        }

        async with session.post("https://oauth2.googleapis.com/token", data=data) as response:
            if response.status != 200:
                raise HTTPException(status_code=400, detail="Failed to exchange OAuth code")

            token_data = await response.json()

            tokens = {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "expires_at": time.time() + token_data.get("expires_in", 3600),
                "scope": token_data.get("scope")
            }

            _save_oauth_tokens(tokens)

            return {"ok": True, "message": "Google Ads OAuth configured successfully"}


@router.get("/oauth/canva/url")
def get_canva_oauth_url():
    """Get Canva OAuth authorization URL"""
    if not CANVA_CONFIG["client_id"]:
        raise HTTPException(status_code=500, detail="Canva OAuth not configured")

    scopes = "design:meta:read design:content:read design:content:write"
    redirect_uri = CANVA_CONFIG["redirect_uri"]

    auth_url = (
        f"https://www.canva.com/api/oauth/authorize?"
        f"client_id={CANVA_CONFIG['client_id']}&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scopes}&"
        f"response_type=code"
    )

    return {"authorization_url": auth_url, "redirect_uri": redirect_uri}


@router.post("/oauth/canva/callback")
async def canva_oauth_callback(oauth_data: CanvaOAuth):
    """Handle Canva OAuth callback and exchange code for tokens"""
    async with aiohttp.ClientSession() as session:
        data = {
            "client_id": CANVA_CONFIG["client_id"],
            "client_secret": CANVA_CONFIG["client_secret"],
            "code": oauth_data.authorization_code,
            "grant_type": "authorization_code",
            "redirect_uri": oauth_data.redirect_uri
        }

        async with session.post("https://api.canva.com/oauth/token", data=data) as response:
            if response.status != 200:
                raise HTTPException(status_code=400, detail="Failed to exchange OAuth code")

            token_data = await response.json()

            tokens = {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "expires_at": time.time() + token_data.get("expires_in", 3600),
                "scope": token_data.get("scope")
            }

            _save_canva_oauth_tokens(tokens)

            return {"ok": True, "message": "Canva OAuth configured successfully"}


@router.post("/campaigns/create")
async def create_campaign(payload: CampaignCreate):
    if payload.platform.lower() not in {"google", "facebook", "linkedin", "twitter", "canva"}:
        raise HTTPException(status_code=400, detail="Unsupported platform")

    data = _load_campaigns()
    campaign_id = str(uuid.uuid4())

    record = {
        "id": campaign_id,
        "platform": payload.platform.lower(),
        "name": payload.name,
        "budget_eur": payload.budget_eur,
        "currency": payload.currency,
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "targeting": payload.targeting or {},
        "keywords": payload.keywords or [],
        "ad_groups": payload.ad_groups or [],
        "status": "active",
        "created_at": time.time(),
        "google_ads_id": None,
        "performance": {}
    }

    # Create actual Google Ads campaign if platform is Google
    if payload.platform.lower() == "google" and GOOGLE_ADS_CONFIG["developer_token"]:
        try:
            google_result = await _create_google_ads_campaign(record)
            if google_result.get("results"):
                google_campaign_id = google_result["results"][0]["resourceName"].split("/")[-1]
                record["google_ads_id"] = google_campaign_id
                logger.info(f"Created Google Ads campaign: {google_campaign_id}")
        except Exception as e:
            logger.error(f"Failed to create Google Ads campaign: {e}")
            record["error"] = str(e)

    # Create Canva design if platform is Canva
    if payload.platform.lower() == "canva" and CANVA_CONFIG["client_id"]:
        try:
            ad_data = {
                "title": payload.name,
                "description": payload.targeting.get("description", "The ultimate AI-powered platform for automation and insights."),
                "call_to_action": payload.targeting.get("call_to_action", "Learn More"),
                "template_id": payload.targeting.get("template_id")
            }
            canva_result = await _create_canva_design(ad_data)
            if canva_result.get("id"):
                record["canva_design_id"] = canva_result["id"]
                record["canva_design_url"] = canva_result.get("url")
                logger.info(f"Created Canva design: {canva_result['id']}")
        except Exception as e:
            logger.error(f"Failed to create Canva design: {e}")
            record["error"] = str(e)

    data["campaigns"].append(record)
    _save_campaigns(data)

    return {"ok": True, "campaign": record}


@router.put("/campaigns/pause")
async def pause_campaign(payload: CampaignUpdateStatus):
    data = _load_campaigns()
    for c in data.get("campaigns", []):
        if c.get("id") == payload.campaign_id:
            c["status"] = "paused"

            # Update Google Ads campaign status
            if c.get("google_ads_id") and c.get("platform") == "google":
                try:
                    await _update_google_ads_campaign_status(c["google_ads_id"], "paused")
                except Exception as e:
                    logger.error(f"Failed to pause Google Ads campaign: {e}")
                    c["sync_error"] = str(e)

            _save_campaigns(data)
            return {"ok": True, "campaign": c}

    raise HTTPException(status_code=404, detail="Campaign not found")


@router.put("/campaigns/resume")
async def resume_campaign(payload: CampaignUpdateStatus):
    data = _load_campaigns()
    for c in data.get("campaigns", []):
        if c.get("id") == payload.campaign_id:
            c["status"] = "active"

            # Update Google Ads campaign status
            if c.get("google_ads_id") and c.get("platform") == "google":
                try:
                    await _update_google_ads_campaign_status(c["google_ads_id"], "active")
                except Exception as e:
                    logger.error(f"Failed to resume Google Ads campaign: {e}")
                    c["sync_error"] = str(e)

            _save_campaigns(data)
            return {"ok": True, "campaign": c}

    raise HTTPException(status_code=404, detail="Campaign not found")


@router.put("/campaigns/budget")
async def update_campaign_budget(payload: CampaignBudgetUpdate):
    """Update campaign budget with budget pacing"""
    data = _load_campaigns()
    for c in data.get("campaigns", []):
        if c.get("id") == payload.campaign_id:
            old_budget = c.get("budget_eur", 0)
            c["budget_eur"] = payload.new_budget_eur
            c["budget_updated_at"] = time.time()

            # Calculate budget pacing (daily spend rate)
            if c.get("start_date") and c.get("end_date"):
                start = datetime.fromisoformat(c["start_date"])
                end = datetime.fromisoformat(c["end_date"])
                days_remaining = (end - datetime.now()).days
                if days_remaining > 0:
                    c["daily_budget_eur"] = payload.new_budget_eur / days_remaining

            # Update Google Ads campaign budget
            if c.get("google_ads_id") and c.get("platform") == "google":
                try:
                    customer_id = GOOGLE_ADS_CONFIG["customer_id"]
                    mutation_data = {
                        "operations": [{
                            "update": {
                                "resourceName": f"customers/{customer_id}/campaigns/{c['google_ads_id']}",
                                "campaignBudget": {
                                    "amountMicros": int(payload.new_budget_eur * 1000000)
                                }
                            },
                            "updateMask": "campaignBudget.amountMicros"
                        }]
                    }

                    endpoint = f"customers/{customer_id}/campaigns:mutate"
                    await _google_ads_api_request(endpoint, "POST", mutation_data)

                except Exception as e:
                    logger.error(f"Failed to update Google Ads campaign budget: {e}")
                    c["sync_error"] = str(e)

            _save_campaigns(data)
            return {
                "ok": True,
                "campaign": c,
                "budget_change": payload.new_budget_eur - old_budget
            }

    raise HTTPException(status_code=404, detail="Campaign not found")


@router.get("/campaigns/{campaign_id}/status")
async def campaign_status(campaign_id: str):
    data = _load_campaigns()
    for c in data.get("campaigns", []):
        if c.get("id") == campaign_id:
            # Fetch real-time performance from Google Ads
            if c.get("google_ads_id") and c.get("platform") == "google":
                try:
                    performance = await _get_google_ads_campaign_performance(c["google_ads_id"])
                    c["performance"] = performance
                except Exception as e:
                    logger.error(f"Failed to fetch Google Ads performance: {e}")
                    c["performance_error"] = str(e)

            return {"ok": True, "status": c.get("status"), "campaign": c}

    raise HTTPException(status_code=404, detail="Campaign not found")


@router.get("/campaigns")
def list_campaigns():
    """List all campaigns with performance data"""
    data = _load_campaigns()
    return {"ok": True, "campaigns": data.get("campaigns", [])}


@router.post("/campaigns/sync-all")
async def sync_all_campaigns():
    """Sync all Google Ads campaigns with latest performance data"""
    data = _load_campaigns()
    synced_count = 0
    errors = []

    for c in data.get("campaigns", []):
        if c.get("google_ads_id") and c.get("platform") == "google":
            try:
                performance = await _get_google_ads_campaign_performance(c["google_ads_id"])
                c["performance"] = performance
                c["last_synced"] = time.time()
                synced_count += 1
            except Exception as e:
                error_msg = f"Campaign {c['id']}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Failed to sync campaign {c['id']}: {e}")

    _save_campaigns(data)

    return {
        "ok": True,
        "synced_campaigns": synced_count,
        "errors": errors,
        "total_campaigns": len(data.get("campaigns", []))
    }


@router.post("/sync-kpi")
def sync_kpi(payload: SyncKPI):
    try:
        current = {}
        if KPI_FILE.exists():
            current = json.loads(KPI_FILE.read_text(encoding="utf-8"))

        # Calculate advertising metrics from campaigns
        campaigns_data = _load_campaigns()
        total_ad_spend = sum(c.get("budget_eur", 0) for c in campaigns_data.get("campaigns", []))
        active_campaigns = len([c for c in campaigns_data.get("campaigns", []) if c.get("status") == "active"])

        updated = {
            "revenue_eur": payload.revenue_eur if payload.revenue_eur is not None else current.get("revenue_eur", 0),
            "active_users": payload.active_users if payload.active_users is not None else current.get("active_users", 0),
            "conversion_rate": payload.conversion_rate if payload.conversion_rate is not None else current.get("conversion_rate", 0.0),
            "advertising": {
                "total_ad_spend_eur": total_ad_spend,
                "active_campaigns": active_campaigns,
                "last_updated": time.time()
            },
            "timestamp": time.time()
        }

        KPI_FILE.parent.mkdir(parents=True, exist_ok=True)
        KPI_FILE.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "updated": updated, "kpi_file": str(KPI_FILE)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI sync failed: {e}")


@router.post("/canva/create-ad")
async def create_canva_ad(payload: CanvaAdCreate):
    """Create a promotional ad for Omni platform using Canva"""
    try:
        ad_data = {
            "title": payload.title,
            "description": payload.description,
            "call_to_action": payload.call_to_action,
            "template_id": payload.template_id
        }

        result = await _create_canva_design(ad_data)

        if result.get("id"):
            return {"ok": True, "design_id": result["id"], "design_url": result.get("url")}
        else:
            raise HTTPException(status_code=500, detail="Failed to create Canva design")

    except Exception as e:
        logger.error(f"Failed to create Canva ad: {e}")
        raise HTTPException(status_code=500, detail=str(e))
