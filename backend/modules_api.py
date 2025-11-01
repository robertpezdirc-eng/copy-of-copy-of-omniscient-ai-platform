"""
OMNI Platform Modules API
Provides API endpoints for all 20+ specialized modules
"""
import os
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import random

router = APIRouter()


# Pydantic models
class ModuleInfo(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    price: float
    category: str
    active: bool = False
    demo_available: bool = True


class ModuleActivation(BaseModel):
    module_id: str
    active: bool


class AIQuery(BaseModel):
    message: str
    context: Optional[str] = None


# Module definitions (matching problem statement)
MODULES = [
    {"id": "sales", "name": "Prodaja", "icon": "📊", "description": "Spremljaj prihodke, trende, AI vpoglede", "price": 9.0, "category": "business"},
    {"id": "customers", "name": "Stranke", "icon": "👥", "description": "CRM + engagement analiza", "price": 12.0, "category": "business"},
    {"id": "ai_chat", "name": "AI Chat Bot", "icon": "💬", "description": "Notranji asistent za podatke", "price": 0.0, "category": "ai"},
    {"id": "inventory", "name": "Zaloga", "icon": "📦", "description": "Nadzor zalog, napoved povpraševanja", "price": 8.0, "category": "operations"},
    {"id": "finance", "name": "Finance", "icon": "💰", "description": "AI analiza stroškov, prihodkov", "price": 10.0, "category": "finance"},
    {"id": "planning", "name": "Planiranje", "icon": "📅", "description": "Pametno planiranje dela in resursov", "price": 7.0, "category": "operations"},
    {"id": "seo", "name": "SEO Analitika", "icon": "🔍", "description": "Sledenje ključnim besedam", "price": 6.0, "category": "marketing"},
    {"id": "marketing", "name": "Marketing", "icon": "📢", "description": "Analiza kampanj + predlogi", "price": 11.0, "category": "marketing"},
    {"id": "performance", "name": "Performance", "icon": "⚡", "description": "Hitrost sistema, uptime", "price": 5.0, "category": "tech"},
    {"id": "web_analytics", "name": "Web Analytics", "icon": "🌐", "description": "Obisk, bounce rate, zemljevid", "price": 6.0, "category": "analytics"},
    {"id": "ai_forecast", "name": "AI Forecast", "icon": "🧮", "description": "Napoved prodaje in trendov", "price": 12.0, "category": "ai"},
    {"id": "research", "name": "Omni Research", "icon": "🧠", "description": "Analize trga in konkurence", "price": 14.0, "category": "analytics"},
    {"id": "security", "name": "Varnostni center", "icon": "🔐", "description": "Prijave, grožnje, MFA nadzor", "price": 7.0, "category": "security"},
    {"id": "projects", "name": "Projektni modul", "icon": "🏗️", "description": "Nadzor projektov, Gantt AI", "price": 10.0, "category": "operations"},
    {"id": "suppliers", "name": "Dobavitelji", "icon": "📦", "description": "Nadzor cen, AI predlog menjav", "price": 9.0, "category": "business"},
    {"id": "bi_analytics", "name": "BI Analytics Pro", "icon": "📈", "description": "Napredna poslovna inteligenca", "price": 15.0, "category": "analytics"},
    {"id": "reports", "name": "Poročila", "icon": "🧾", "description": "PDF, Excel, e-mail reporti", "price": 5.0, "category": "operations"},
    {"id": "kpi", "name": "Cilji in KPI", "icon": "🎯", "description": "Postavljanje ciljev z AI spremljanjem", "price": 6.0, "category": "analytics"},
    {"id": "data_science", "name": "Data Science Lab", "icon": "🧬", "description": "Analize modelov in LLM testiranja", "price": 18.0, "category": "ai"},
    {"id": "api_management", "name": "API Management", "icon": "🔗", "description": "Pregled povezav in kvot", "price": 4.0, "category": "tech"},
]


@router.get("/api/modules")
async def get_modules(category: Optional[str] = None):
    """Get all available modules, optionally filtered by category"""
    modules = MODULES.copy()
    if category:
        modules = [m for m in modules if m["category"] == category]
    return {"modules": modules, "total": len(modules)}


@router.get("/api/modules/{module_id}")
async def get_module(module_id: str):
    """Get details for a specific module"""
    module = next((m for m in MODULES if m["id"] == module_id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module


@router.post("/api/modules/{module_id}/activate")
async def activate_module(module_id: str, activation: ModuleActivation):
    """Activate or deactivate a module for the current user"""
    module = next((m for m in MODULES if m["id"] == module_id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    return {
        "module_id": module_id,
        "active": activation.active,
        "message": f"Module {'activated' if activation.active else 'deactivated'} successfully"
    }


@router.get("/api/modules/{module_id}/data")
async def get_module_data(module_id: str):
    """Get data/metrics for a specific module"""
    module = next((m for m in MODULES if m["id"] == module_id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    # Generate demo data based on module type
    now = datetime.now(timezone.utc)
    
    if module_id == "sales":
        return {
            "revenue": round(random.uniform(15000, 35000), 2),
            "growth": round(random.uniform(-5, 25), 2),
            "transactions": random.randint(150, 450),
            "avg_value": round(random.uniform(50, 200), 2),
            "trend": "up" if random.random() > 0.3 else "down",
            "forecast": [round(random.uniform(15000, 40000), 2) for _ in range(7)]
        }
    elif module_id == "customers":
        return {
            "total": random.randint(500, 2000),
            "active": random.randint(300, 1500),
            "new_this_month": random.randint(20, 150),
            "churn_rate": round(random.uniform(2, 8), 2),
            "satisfaction": round(random.uniform(7.5, 9.5), 2),
            "segments": {
                "vip": random.randint(50, 200),
                "regular": random.randint(300, 1000),
                "new": random.randint(50, 300)
            }
        }
    elif module_id == "finance":
        return {
            "revenue": round(random.uniform(45000, 85000), 2),
            "expenses": round(random.uniform(25000, 55000), 2),
            "profit": round(random.uniform(15000, 35000), 2),
            "profit_margin": round(random.uniform(20, 45), 2),
            "cash_flow": [round(random.uniform(5000, 15000), 2) for _ in range(12)]
        }
    elif module_id == "marketing":
        return {
            "campaigns": random.randint(5, 15),
            "impressions": random.randint(50000, 500000),
            "clicks": random.randint(2000, 25000),
            "ctr": round(random.uniform(2, 6), 2),
            "conversions": random.randint(50, 500),
            "roi": round(random.uniform(150, 450), 2)
        }
    elif module_id == "web_analytics":
        return {
            "visitors": random.randint(5000, 50000),
            "pageviews": random.randint(15000, 150000),
            "bounce_rate": round(random.uniform(35, 65), 2),
            "avg_session": round(random.uniform(2, 8), 2),
            "top_pages": [
                {"path": "/", "views": random.randint(1000, 10000)},
                {"path": "/products", "views": random.randint(500, 5000)},
                {"path": "/about", "views": random.randint(200, 2000)}
            ]
        }
    elif module_id == "performance":
        return {
            "uptime": round(random.uniform(99.5, 99.99), 2),
            "response_time": round(random.uniform(50, 200), 2),
            "requests_per_sec": random.randint(100, 1000),
            "errors": random.randint(0, 50),
            "cpu_usage": round(random.uniform(20, 80), 2),
            "memory_usage": round(random.uniform(30, 75), 2)
        }
    elif module_id == "ai_forecast":
        return {
            "next_month_revenue": round(random.uniform(50000, 100000), 2),
            "confidence": round(random.uniform(75, 95), 2),
            "trend": "increasing" if random.random() > 0.3 else "decreasing",
            "predictions": [round(random.uniform(40000, 90000), 2) for _ in range(6)]
        }
    else:
        # Generic module data
        return {
            "status": "active",
            "last_updated": now.isoformat(),
            "metrics": {
                "value_1": round(random.uniform(100, 1000), 2),
                "value_2": random.randint(50, 500),
                "value_3": round(random.uniform(10, 100), 2)
            }
        }


@router.post("/api/ai-assistant")
async def ai_assistant(query: AIQuery):
    """AI Personal Assistant endpoint with AI Gateway integration"""
    import requests
    
    # Try to use AI Gateway first, fallback to rule-based
    ai_gateway_url = os.getenv("AI_GATEWAY_URL", "https://ai-gateway-661612368188.europe-west1.run.app")
    
    try:
        # Prepare context about available modules
        modules_context = f"Available modules: {', '.join([m['name'] + ' (€' + str(m['price']) + ')' for m in MODULES[:5]])}..."
        
        # Try AI Gateway
        response = requests.post(
            f"{ai_gateway_url}/api/chat",
            json={
                "message": query.message,
                "context": query.context or modules_context,
                "system_prompt": "You are Omni, a helpful AI assistant for the Omni Intelligence Platform. Help users understand modules, pricing, and platform features. Respond in Slovenian language."
            },
            timeout=10
        )
        
        if response.ok:
            ai_response = response.json()
            return {
                "response": ai_response.get("response", ai_response.get("text", "")),
                "source": "ai_gateway",
                "model": ai_response.get("model", "unknown")
            }
    except Exception as e:
        # Fallback to rule-based responses
        print(f"AI Gateway error: {e}, falling back to rule-based responses")
    
    # Rule-based fallback responses
    message = query.message.lower()
    
    if "modul" in message or "module" in message:
        if "priporoč" in message or "suggest" in message:
            return {
                "response": "Na podlagi vaše uporabe priporočam: BI Analytics Pro za napredne analize, "
                           "AI Forecast za napovedovanje in Marketing modul za optimizacijo kampanj.",
                "suggested_modules": ["bi_analytics", "ai_forecast", "marketing"],
                "confidence": 0.85,
                "source": "rule_based"
            }
        else:
            return {
                "response": "Trenutno imate na voljo več kot 20 specializiranih modulov. "
                           "Kateri vas zanima? (npr. Prodaja, Marketing, Finance)",
                "modules_count": len(MODULES),
                "source": "rule_based"
            }
    elif "cena" in message or "price" in message or "kolik" in message:
        return {
            "response": f"Cene modulov se gibljejo od €{min(m['price'] for m in MODULES)} "
                       f"do €{max(m['price'] for m in MODULES)} na mesec. "
                       "AI Chat Bot je vključen brezplačno!",
            "price_range": {
                "min": min(m["price"] for m in MODULES),
                "max": max(m["price"] for m in MODULES)
            },
            "source": "rule_based"
        }
    elif "pomoč" in message or "help" in message:
        return {
            "response": "Lahko vam pomagam z: nastavitev modulov, priporočila za optimizacijo, "
                       "razlago funkcionalnosti, analizo podatkov. Kaj vas zanima?",
            "suggestions": [
                "Kateri modul je najboljši za moje poslovanje?",
                "Kako aktiviram modul?",
                "Pokaži mi cene"
            ],
            "source": "rule_based"
        }
    else:
        return {
            "response": f"Razumem vaše vprašanje: '{query.message}'. "
                       "Za natančen odgovor potrebujem več konteksta. "
                       "Lahko vprašate o modulih, cenah, funkcionalnostih ali nastavitvi platforme.",
            "suggestions": [
                "Priporoči mi module",
                "Koliko stane?",
                "Kako začnem?"
            ],
            "source": "rule_based"
        }


@router.get("/api/dashboard/overview")
async def get_dashboard_overview():
    """Get main dashboard overview with KPIs"""
    now = datetime.now(timezone.utc)
    
    return {
        "timestamp": now.isoformat(),
        "kpis": {
            "revenue": round(random.uniform(20000, 30000), 2),
            "growth": round(random.uniform(10, 25), 2),
            "active_users": random.randint(150, 250),
            "requests": random.randint(2500, 4000),
            "uptime": round(random.uniform(99.5, 99.99), 2)
        },
        "trends": {
            "revenue": [round(random.uniform(15000, 30000), 2) for _ in range(7)],
            "users": [random.randint(100, 200) for _ in range(7)],
            "requests": [random.randint(2000, 4000) for _ in range(7)]
        },
        "ai_score": round(random.uniform(75, 95), 2),
        "active_modules": random.randint(5, 12)
    }


@router.get("/api/marketplace/categories")
async def get_marketplace_categories():
    """Get all module categories for marketplace filtering"""
    categories = list(set(m["category"] for m in MODULES))
    category_counts = {}
    for cat in categories:
        category_counts[cat] = len([m for m in MODULES if m["category"] == cat])
    
    return {
        "categories": categories,
        "counts": category_counts
    }


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "modules-api"}
