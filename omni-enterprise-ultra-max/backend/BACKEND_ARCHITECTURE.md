# 🏗️ Backend Architecture - Professional Organization

## 📋 Overview

Backend OMNI ENTERPRISE ULTRA MAX platforme je organiziran po profesionalnih standardih, ki omogočajo:
- ✅ **Jasna separacija skrbi** (Separation of Concerns)
- ✅ **Skalabilnost** in vzdrževalnost
- ✅ **Enostavno testiranje** in debugging
- ✅ **Modularna arhitektura** za lažje dodajanje funkcionalnosti

---

## 🎯 Arhitekturni Principi

### 1. Layered Architecture (Slojna Arhitektura)

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│         (routes/)                       │  ← API Endpoints
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         Business Logic Layer            │
│         (services/)                     │  ← Core Logic
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         Data Access Layer               │
│         (models/, database.py)          │  ← Database
└─────────────────────────────────────────┘
```

### 2. Domain-Driven Design (DDD)

Backend je organiziran po poslovnih domenah:
- **AI/ML** - Umetna inteligenca in strojno učenje
- **Compliance** - GDPR in regulativa
- **Payments** - Plačilni sistemi
- **Analytics** - Analitika in BI
- **Security** - Varnost
- **Integration** - Zunanje integracije

### 3. SOLID Principles

- **S**ingle Responsibility - Vsak modul ima eno odgovornost
- **O**pen/Closed - Odprt za razširitve, zaprt za spremembe
- **L**iskov Substitution - Možnost zamenjave implementacij
- **I**nterface Segregation - Manjši, specifični interfejsi
- **D**ependency Inversion - Odvisnost od abstrakcij, ne konkretnih implementacij

---

## 📁 Directory Structure

### Core Application Files

```
backend/
├── main.py                    # FastAPI aplikacija (entry point)
├── database.py                # Database connections & initialization
├── requirements.txt           # Python dependencies
└── README.md                  # Backend documentation
```

**main.py** - Glavna aplikacija:
- Inicializacija FastAPI app
- Registracija route-ov
- Middleware konfiguracija
- Startup/shutdown eventi
- Error handling

**database.py** - Centralno upravljanje DB:
- PostgreSQL connection pool
- MongoDB client
- Redis client
- Firestore client
- Neo4j connection (optional)

### 1. Routes Layer (API Endpoints)

```
backend/routes/
├── ai/                        # AI/ML endpoints
│   ├── ai_intelligence_routes.py
│   ├── ai_assistant_routes.py
│   ├── autonomous_agent_routes.py
│   ├── advanced_ai_routes.py
│   ├── multi_llm_router_routes.py
│   └── ml_models_routes.py
│
├── analytics/                 # Analytics & BI endpoints
│   ├── analytics_routes.py
│   ├── analytics_reports_routes.py
│   └── analytics_usage_routes.py
│
├── payments/                  # Payment endpoints
│   ├── stripe_routes.py
│   ├── paypal_routes.py
│   ├── crypto_routes.py
│   └── payments.py
│
├── compliance/                # Compliance & GDPR endpoints
│   ├── gdpr_routes.py
│   ├── gdpr_enhanced_routes.py
│   └── security_compliance_routes.py
│
├── business/                  # Business logic endpoints
│   ├── affiliate_routes.py
│   ├── marketplace_routes.py
│   ├── growth_engine_routes.py
│   ├── monetization_routes.py
│   └── billing_routes.py
│
├── platform/                  # Platform management endpoints
│   ├── tenant_routes.py
│   ├── capacity_routes.py
│   ├── global_scaling_routes.py
│   ├── performance_routes.py
│   └── observability_routes.py
│
├── integration/               # External integrations
│   ├── integration_hub_routes.py
│   ├── developer_ecosystem_routes.py
│   ├── iot_routes.py
│   └── websocket_routes.py
│
├── security/                  # Security endpoints
│   ├── auth_routes.py
│   ├── mfa_routes.py
│   ├── security_routes.py
│   ├── advanced_security_routes.py
│   └── threat_detection_routes.py
│
├── data/                      # Data management endpoints
│   ├── rag_routes.py
│   ├── enhanced_rag_routes.py
│   ├── ingestion_routes.py
│   └── dashboard_builder_routes.py
│
├── support/                   # Support & community
│   ├── support_community_routes.py
│   ├── feedback_routes.py
│   └── learning_routes.py
│
├── infrastructure/            # Infrastructure endpoints
│   ├── adapters_routes.py
│   ├── orchestrator_routes.py
│   └── ollama_health_routes.py
│
└── __init__.py
```

**Organizacijski principi za route:**
- Grupirani po domeni (AI, payments, compliance, etc.)
- Vsak route file vsebuje povezane endpoint-e
- Jasna navigacija in iskanje
- Enostavno dodajanje novih funkcionalnosti

### 2. Services Layer (Business Logic)

```
backend/services/
├── ai/                        # AI/ML servisi
│   ├── rag_service.py
│   ├── enhanced_rag_service.py
│   ├── predictive_analytics.py
│   ├── sentiment_analysis.py
│   ├── anomaly_detection.py
│   ├── recommendation_engine.py
│   ├── dashboard_builder_service.py
│   ├── ollama_service.py
│   ├── multi_llm_router.py
│   ├── autonomous_agent.py
│   └── swarm_intelligence.py
│
├── advanced_ai/               # Napredni AI servisi
│   ├── automl.py
│   ├── ab_testing.py
│   ├── model_registry.py
│   └── multimodal.py
│
├── compliance/                # GDPR & compliance
│   ├── gdpr_service.py
│   ├── gdpr_repository.py
│   └── gdpr_health.py
│
├── bi/                        # Business Intelligence
│   └── realtime_analytics.py
│
├── security/                  # Security services
│   ├── encryption.py
│   └── gdpr.py
│
├── analytics_service.py       # Analytics engine
├── ai_assistant_service.py    # AI assistant
├── auth.py                    # Authentication
├── cache_service.py           # Caching logic
├── compliance_service.py      # Compliance management
├── email_service.py           # Email notifications
├── hubspot_service.py         # HubSpot integration
├── integration_service.py     # External integrations
├── mfa_service.py             # Multi-factor auth
├── ml_models_service.py       # ML model management
├── nlp_service.py             # Natural Language Processing
├── observability_service.py   # Monitoring & observability
├── partner_service.py         # Partner management
├── salesforce_service.py      # Salesforce integration
├── security_service.py        # Security management
├── shopify_service.py         # Shopify integration
├── sms_service.py             # SMS notifications
├── tenant_service.py          # Multi-tenant management
├── websocket_service.py       # WebSocket management
├── whitelabel_service.py      # White-label support
├── zapier_service.py          # Zapier integration
└── __init__.py
```

**Service principi:**
- Vsak service vsebuje poslovn logiko ene domene
- Service ne sme dostopati direktno do HTTP request/response
- Service je neodvisen od route layer-ja
- Lahko se uporablja v različnih kontekstih (API, CLI, background jobs)

### 3. Models Layer (Data Models)

```
backend/models/
├── user.py                    # User model
├── tenant.py                  # Tenant model (multi-tenancy)
├── subscription.py            # Subscription model
├── affiliate.py               # Affiliate program model
├── marketplace.py             # Marketplace model
├── analytics.py               # Analytics model
├── notification.py            # Notification model
├── ai_agent.py                # AI agent model
├── gdpr.py                    # GDPR data model
└── __init__.py
```

**Model principi:**
- Pydantic modeli za validacijo
- SQLAlchemy modeli za database ORM
- Jasna definicija podatkovnih struktur
- Type hints za boljši type checking

### 4. Middleware Layer

```
backend/middleware/
├── metrics.py                 # Prometheus metrics
├── rate_limiter.py            # Rate limiting
├── response_cache.py          # Response caching
├── performance_monitor.py     # Performance tracking
├── internal_prefix.py         # Internal mode support
├── security_headers.py        # Security headers
├── usage_tracker.py           # Usage analytics
└── __init__.py
```

**Middleware vrstni red (pomembno!):**
1. `internal_prefix` - Strip /internal prefix
2. `security_headers` - Add security headers
3. `metrics` - Prometheus metrics
4. `performance_monitor` - Latency tracking
5. `usage_tracker` - Usage stats (skip if internal)
6. `rate_limiter` - Rate limiting (skip if internal)
7. `response_cache` - Caching

### 5. Adapters (External Integrations)

```
backend/adapters/
├── audio_adapter.py           # Audio processing
├── visual_adapter.py          # Image/video processing
├── ipfs_storage_adapter.py    # IPFS storage
├── message_broker.py          # Message queue
├── meta_adapter.py            # Meta/Facebook integration
├── net_agent_adapter.py       # Network agent
├── omni_brain_adapter.py      # Omni brain AI
├── price_feed.py              # Cryptocurrency price feed
├── websocket_sensor_adapter.py # WebSocket sensors
└── __init__.py
```

**Adapter pattern principi:**
- Abstrahiranje zunanjih sistemov
- Enostavna zamenjava implementacij
- Testiranje z mock adapters

### 6. Payment Gateways

```
backend/payment_gateways/
├── base.py                    # Base payment gateway interface
├── acmepay.py                 # AcmePay integration
└── __init__.py
```

**Payment gateway principi:**
- Skupni interface za vse plačilne sisteme
- Strategy pattern za različne gateway-e
- Lažje dodajanje novih plačilnih sistemov

### 7. Utils (Utility Functions)

```
backend/utils/
├── ai_client.py               # AI client utilities
├── background_tasks.py        # Background task management
├── gcp.py                     # Google Cloud utilities
├── logging_filters.py         # Custom logging filters
└── __init__.py
```

**Utils principi:**
- Splošne funkcije, ki jih uporabljajo različni moduli
- Brez poslovne logike
- Stateless funkcije
- Lahko se uporabljajo kjerkoli

### 8. Kubernetes (Infrastructure)

```
backend/k8s/
└── deployment.yaml            # K8s deployment manifest
```

**K8s konfiguracija:**
- Deployment manifest za GKE
- HorizontalPodAutoscaler
- Service definition
- ConfigMaps & Secrets

---

## 🔄 Data Flow

### Tipičen Request Flow

```
1. Client Request
   ↓
2. Middleware Stack
   - Internal Prefix Stripper
   - Security Headers
   - Metrics Collection
   - Performance Monitor
   - Usage Tracker
   - Rate Limiter
   - Response Cache
   ↓
3. Route Handler (routes/)
   - Request validation
   - Parameter extraction
   ↓
4. Service Layer (services/)
   - Business logic
   - External API calls
   - Data processing
   ↓
5. Data Layer (models/, database.py)
   - Database queries
   - Data validation
   - Model transformations
   ↓
6. Response
   - Format response
   - Add headers
   - Return to client
```

### Primer: AI Prediction Request

```python
# 1. Route (routes/ai/ai_intelligence_routes.py)
@router.post("/api/v1/ai-intelligence/churn-prediction")
async def predict_churn(request: ChurnPredictionRequest):
    # Validate request
    # Extract parameters
    
    # 2. Call service
    result = await prediction_service.predict_churn(
        user_data=request.user_data
    )
    
    # 3. Return response
    return ChurnPredictionResponse(**result)


# 4. Service (services/ai/predictive_analytics.py)
class PredictiveAnalytics:
    async def predict_churn(self, user_data: dict):
        # Load model from cache/disk
        model = await self.load_model("churn_model_v1")
        
        # Preprocess data
        features = self.preprocess(user_data)
        
        # Make prediction
        prediction = model.predict(features)
        
        # Post-process
        result = self.interpret_prediction(prediction)
        
        # Store in DB
        await self.store_prediction(user_data, result)
        
        return result


# 5. Model (models/analytics.py)
class ChurnPrediction(BaseModel):
    user_id: str
    churn_probability: float
    risk_level: str
    recommendations: List[str]
    timestamp: datetime
```

---

## 🎯 Best Practices

### 1. Route Organization

✅ **DO:**
- Grupiraj route po domeni
- Uporabljaj jasna in konsistentna imena
- Dokumentiraj z docstrings
- Uporabljaj Pydantic modele za validacijo

❌ **DON'T:**
- Ne miksaj različnih domen v istem file-u
- Ne dupliciraj logike med route-i
- Ne vstavljaj poslovne logike v route handler

### 2. Service Design

✅ **DO:**
- Vsak service ima eno jasno odgovornost
- Uporabljaj dependency injection
- Async kjer je mogoče
- Logging za pomembne akcije

❌ **DON'T:**
- Ne dostopaj direktno do database v route-ih
- Ne uporabljaj globalnih spremenljivk
- Ne miksaj različnih domen v istem service-u

### 3. Error Handling

✅ **DO:**
```python
from fastapi import HTTPException

# Service layer
def process_data(data):
    try:
        result = external_api.call(data)
        return result
    except ExternalAPIError as e:
        logger.error(f"External API failed: {e}")
        raise ServiceException("Failed to process data")

# Route layer
@router.post("/process")
async def process(data: DataModel):
    try:
        result = service.process_data(data.dict())
        return {"result": result}
    except ServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))
```

❌ **DON'T:**
- Ne ignoriraj exceptione
- Ne vračaj generičnih error message-ov
- Ne logaj sensitive podatkov

### 4. Testing

✅ **DO:**
```python
# Unit test za service
def test_predict_churn():
    service = PredictiveAnalytics()
    result = await service.predict_churn(mock_data)
    assert result["risk_level"] == "medium"

# Integration test za route
def test_churn_prediction_endpoint(client):
    response = client.post(
        "/api/v1/ai-intelligence/churn-prediction",
        json=test_data
    )
    assert response.status_code == 200
    assert "churn_probability" in response.json()
```

### 5. Security

✅ **DO:**
- Validiraj vse inpute s Pydantic
- Uporabljaj SQL parametrizirane query-je
- Šifriraj sensitive data
- Rate limiting za vse endpoint-e
- Logging za security events

❌ **DON'T:**
- Ne shranjuj passwordov v plain text
- Ne logaj API keys ali tokens
- Ne vrački internal error details uporabniku

---

## 📊 Monitoring & Observability

### Metrics (Prometheus)

```python
# v middleware/metrics.py
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# v services
ml_predictions_total = Counter(
    'ml_predictions_total',
    'Total ML predictions',
    ['model', 'outcome']
)
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Structured logging
logger.info(
    "Prediction completed",
    extra={
        "user_id": user_id,
        "model": "churn_v1",
        "probability": 0.23,
        "duration_ms": 234
    }
)
```

### Tracing (OpenTelemetry)

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("predict_churn")
def predict_churn(data):
    # Automatically traced
    pass
```

---

## 🚀 Skalabilnost

### Horizontal Scaling

- **Stateless Design** - Nobenih shared state-ov
- **Cache Externally** - Redis za cache
- **Database Connection Pooling** - Optimiziraj DB connections
- **Async Processing** - FastAPI async/await

### Vertical Scaling

- **Resource Limits** - CPU/Memory limits v K8s
- **Auto-scaling** - HPA za GKE
- **Performance Monitoring** - Identify bottlenecks

### Caching Strategy

```python
# L1: In-memory cache (local)
@lru_cache(maxsize=100)
def get_model(model_id: str):
    pass

# L2: Redis cache (distributed)
async def get_prediction(user_id: str):
    cached = await redis.get(f"prediction:{user_id}")
    if cached:
        return cached
    
    result = await compute_prediction(user_id)
    await redis.setex(f"prediction:{user_id}", 300, result)
    return result
```

---

## 🔧 Development Guidelines

### Adding New Functionality

1. **Identificiraj domeno** - AI, payments, compliance, etc.
2. **Ustvari service** - Dodaj v ustrezno services/ mapo
3. **Ustvari route** - Dodaj v ustrezno routes/ mapo
4. **Dodaj models** - Če potrebuješ nove podatkovne strukture
5. **Piši teste** - Unit + integration tests
6. **Dokumentiraj** - Docstrings + API docs
7. **Review** - Code review pred merge-om

### Code Style

- **PEP 8** - Python style guide
- **Type Hints** - Uporabljaj type annotations
- **Docstrings** - Google style docstrings
- **Naming** - Descriptive variable names
- **Comments** - Samo kjer je potrebno

### Git Workflow

```bash
# 1. Ustvari feature branch
git checkout -b feature/new-ai-model

# 2. Develop and test
# 3. Commit with clear messages
git commit -m "Add churn prediction model"

# 4. Push and create PR
git push origin feature/new-ai-model

# 5. Code review
# 6. Merge to master
```

---

## 📚 Additional Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)

### Books
- "Clean Architecture" by Robert C. Martin
- "Domain-Driven Design" by Eric Evans
- "Designing Data-Intensive Applications" by Martin Kleppmann

### Tools
- **Black** - Code formatter
- **Mypy** - Static type checker
- **Pytest** - Testing framework
- **Pylint** - Code linter

---

## ✅ Summary

Backend OMNI ENTERPRISE ULTRA MAX platforme sledi profesionalnim standardom:

✅ **Jasna struktura** - Routes, Services, Models, Middleware  
✅ **Separation of Concerns** - Vsak layer ima svojo vlogo  
✅ **Skalabilnost** - Horizontal + vertical scaling  
✅ **Testabilnost** - Unit + integration tests  
✅ **Maintainability** - Clean code, dokumentacija  
✅ **Security** - Best practices za varnost  
✅ **Observability** - Metrics, logging, tracing  

**To je enterprise-ready backend, ki podpira:**
- 50+ AI/ML storitev
- Multi-tenant arhitekturo
- Globalno skaliranje
- GDPR compliance
- Real-time processing
- High availability

---

*Last updated: 3. november 2025*  
*Version: 1.0.0*
