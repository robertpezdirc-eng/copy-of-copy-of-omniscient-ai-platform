# Backend Architecture Documentation

## Overview

The Omni Enterprise Ultra Max backend is a FastAPI-based microservices architecture designed for scalability, reliability, and maintainability. The backend supports both standalone and internal modes, with comprehensive middleware, service layers, and database integrations.

## Directory Structure

```
backend/
├── adapters/              # External service adapters
│   ├── audio_adapter.py   # Audio processing integration
│   ├── ipfs_storage_adapter.py
│   ├── message_broker.py
│   ├── meta_adapter.py
│   ├── net_agent_adapter.py
│   ├── omni_brain_adapter.py
│   ├── price_feed.py
│   ├── visual_adapter.py
│   └── websocket_sensor_adapter.py
├── alembic/               # Database migrations
├── middleware/            # Request/response middleware
│   ├── internal_prefix.py    # Internal routing support
│   ├── metrics.py            # Prometheus metrics
│   ├── performance_monitor.py
│   ├── rate_limiter.py
│   ├── response_cache.py
│   ├── security_headers.py
│   └── usage_tracker.py
├── models/                # SQLAlchemy models
│   ├── affiliate.py
│   ├── ai_agent.py
│   ├── analytics.py
│   ├── gdpr.py
│   ├── marketplace.py
│   ├── notification.py
│   ├── subscription.py
│   ├── tenant.py
│   └── user.py
├── observability/         # Tracing and monitoring
├── payment_gateways/      # Payment integrations
│   ├── acmepay.py
│   └── base.py
├── routes/                # API route handlers (44 files)
│   ├── ai_routes.py           # Core AI endpoints
│   ├── auth_routes.py         # Authentication & MFA
│   ├── analytics_usage_routes.py
│   ├── billing_routes.py
│   ├── developer_ecosystem_routes.py
│   ├── feedback_routes.py
│   ├── gdpr_routes.py
│   └── ... (40+ more)
├── services/              # Business logic layer
│   ├── ai/                    # AI/ML services
│   │   ├── anomaly_detection.py
│   │   ├── autonomous_agent.py
│   │   ├── dashboard_builder_service.py
│   │   ├── enhanced_rag_service.py
│   │   ├── multi_llm_router.py
│   │   ├── ollama_service.py
│   │   ├── predictive_analytics.py
│   │   ├── rag_service.py
│   │   ├── recommendation_engine.py
│   │   ├── sentiment_analysis.py
│   │   └── swarm_intelligence.py
│   ├── advanced_ai/           # Advanced ML features
│   │   ├── ab_testing.py
│   │   ├── automl.py
│   │   ├── model_registry.py
│   │   └── multimodal.py
│   ├── bi/                    # Business intelligence
│   │   └── realtime_analytics.py
│   ├── compliance/            # GDPR & compliance
│   │   ├── gdpr_health.py
│   │   ├── gdpr_repository.py
│   │   └── gdpr_service.py
│   ├── security/              # Security services
│   │   ├── encryption.py
│   │   └── gdpr.py
│   ├── analytics_service.py
│   ├── auth.py
│   ├── cache_service.py
│   ├── email_service.py
│   ├── integration_service.py
│   ├── mfa_service.py
│   ├── ml_models_service.py
│   ├── observability_service.py
│   ├── security_service.py
│   ├── tenant_service.py
│   └── ... (20+ more services)
├── tests/                 # Unit and integration tests
├── utils/                 # Utility modules
│   ├── ai_client.py
│   ├── background_tasks.py
│   ├── gcp.py
│   └── logging_filters.py
├── database.py            # Database configuration & connections
├── main.py                # Main application entry point
├── main_minimal.py        # Minimal mode for Cloud Run
└── requirements.txt       # Python dependencies
```

## Core Components

### 1. Main Application (main.py)

The main application initializes FastAPI with:
- **Lifespan management**: Async context manager for database init/cleanup
- **Middleware stack**: Security, metrics, performance monitoring, caching, rate limiting
- **Router registration**: Dynamic registration with error tolerance for optional features
- **Configuration modes**:
  - `OMNI_MINIMAL`: Lightweight startup for Cloud Run (default in K_SERVICE env)
  - `RUN_AS_INTERNAL`: Internal mode for gateway integration (strips `/internal` prefix, disables rate limiting)

### 2. Database Layer (database.py)

Supports multiple database systems:
- **PostgreSQL**: Primary relational database (SQLAlchemy)
- **MongoDB**: Document storage (Motor async driver)
- **Redis**: Caching and session storage
- **Firestore**: GCP document database

Features:
- Connection pooling with pre-ping verification
- Configurable pool sizes and timeouts
- Graceful degradation (optional DBs don't fail startup)
- `CacheManager` utility for Redis operations

### 3. Middleware Stack

Applied in order (first added = outermost layer):

1. **InternalPrefixStripper** (conditional): Strips `/internal` prefix when `RUN_AS_INTERNAL=1`
2. **SecurityHeadersMiddleware**: Adds security headers (HSTS, CSP, etc.)
3. **MetricsMiddleware**: Prometheus metrics collection
4. **PerformanceMonitor**: Request timing and slow request logging
5. **ResponseCacheMiddleware** (conditional): Redis-backed response caching
6. **UsageTracker** (conditional): Request tracking
7. **RateLimiter** (conditional): IP-based rate limiting (100 req/min)
8. **CORS**: Cross-origin resource sharing

### 4. Routes Layer

All routes follow consistent patterns:
- **Router naming**: `router` or specific name like `ai_router`, `affiliate_router`
- **Tags**: Organized by feature area for API documentation
- **Models**: Pydantic models for request/response validation
- **Error handling**: HTTPException with proper status codes
- **Async handlers**: All routes are async for better performance

#### Route Categories:

- **AI & ML**: Core AI services, RAG, embeddings, multi-LLM routing
- **Authentication**: Login, registration, MFA (TOTP, SMS, email, backup codes)
- **Analytics**: Usage metrics, reporting, data export
- **Billing**: Invoices, payment methods, billing cycles
- **GDPR**: Consent management, data subject requests, compliance
- **Developer**: SDK management, API documentation, quickstart guides
- **Feedback**: Bug reports, feature requests, voting
- **Marketplace**: API marketplace, integrations
- **Monitoring**: Observability, health checks, metrics
- **Security**: Audit logs, threat detection, compliance
- **Tenant**: Multi-tenancy, RBAC, organization management

### 5. Services Layer

Business logic is separated into service classes:

- **Stateless services**: Utility functions without state
- **Stateful services**: Classes with initialization (e.g., API clients)
- **Separation of concerns**: Routes handle HTTP, services handle business logic

#### Service Organization:

- `services/ai/`: AI/ML specific services
- `services/advanced_ai/`: Advanced ML features (AutoML, A/B testing)
- `services/bi/`: Business intelligence and analytics
- `services/compliance/`: GDPR and compliance services
- `services/security/`: Security utilities
- Root level: General services (auth, analytics, cache, email, etc.)

### 6. Models Layer

SQLAlchemy ORM models for PostgreSQL:
- **Base**: Declarative base for all models
- **Relationships**: Proper foreign keys and relationships
- **Mixins**: Common fields (timestamps, soft deletes)

### 7. Adapters Layer

External service integrations:
- **Audio processing**: Audio transcription and analysis
- **IPFS**: Decentralized storage
- **Message brokers**: Event streaming
- **Meta services**: Facebook/Instagram integrations
- **Omni Brain**: Internal ML engine
- **Price feeds**: Cryptocurrency and stock data
- **WebSocket sensors**: Real-time data ingestion

## Configuration

### Environment Variables

Core configuration:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/omni
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# Mode flags
OMNI_MINIMAL=0                    # Enable minimal mode (auto in Cloud Run)
RUN_AS_INTERNAL=0                 # Internal mode for gateway integration
ENABLE_RESPONSE_CACHE=1           # Redis-backed caching

# Performance
DB_POOL_SIZE=20                   # Connection pool size
DB_MAX_OVERFLOW=40                # Max overflow connections
DB_POOL_RECYCLE=3600             # Recycle connections (seconds)
PERF_SLOW_THRESHOLD_SEC=1.0      # Slow request threshold

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# GCP
GCP_PROJECT_ID=your-project
```

## Deployment Modes

### 1. Standalone Mode (Default)
- Full middleware stack enabled
- All routes available
- Direct deployment (Cloud Run, GKE, VM)

### 2. Internal Mode (Behind Gateway)
Set `RUN_AS_INTERNAL=1`:
- Strips `/internal` prefix from paths
- Disables rate limiting (handled by gateway)
- Disables usage tracking (handled by gateway)
- Recommended for gateway → backend architecture

### 3. Minimal Mode (Fast Startup)
Set `OMNI_MINIMAL=1` or deploy to Cloud Run:
- Only critical routes registered (AI, Ollama, RAG, GDPR)
- Skips optional routes to reduce startup time
- Fewer dependencies loaded
- Ideal for serverless environments

## Best Practices

### Adding New Routes

1. Create route file in `backend/routes/`:
```python
"""
Feature Routes
Brief description
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class RequestModel(BaseModel):
    """Request model with validation"""
    field1: str
    field2: Optional[int] = None

@router.post("/endpoint", tags=["Feature"])
async def endpoint(data: RequestModel):
    """Endpoint documentation"""
    try:
        # Business logic
        return {"result": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

2. Register in `main.py`:
```python
_try("routes.feature_routes", "router", "/api/v1/feature", ["Feature"])
```

### Adding New Services

1. Create service file in `backend/services/`:
```python
"""
Feature Service
Business logic for feature
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)

class FeatureService:
    """Service for feature operations"""
    
    def __init__(self):
        self.config = {}
    
    async def do_something(self, param: str) -> dict:
        """Do something with param"""
        try:
            # Business logic
            return {"result": "success"}
        except Exception as e:
            logger.error(f"Error in do_something: {e}")
            raise
```

2. Import in route:
```python
from services.feature_service import FeatureService

feature_service = FeatureService()
```

### Database Operations

Use dependency injection:
```python
from database import get_db
from sqlalchemy.orm import Session

@router.get("/items")
async def get_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return items
```

### Caching

Use CacheManager:
```python
from database import CacheManager

# Get from cache
cached = await CacheManager.get("key")
if cached:
    return json.loads(cached)

# Set cache
result = await compute_expensive_result()
await CacheManager.set("key", json.dumps(result), ttl=300)
```

### Error Handling

Use HTTPException with proper status codes:
```python
from fastapi import HTTPException

# 400 Bad Request
raise HTTPException(status_code=400, detail="Invalid input")

# 401 Unauthorized
raise HTTPException(status_code=401, detail="Authentication required")

# 403 Forbidden
raise HTTPException(status_code=403, detail="Insufficient permissions")

# 404 Not Found
raise HTTPException(status_code=404, detail="Resource not found")

# 500 Internal Server Error
raise HTTPException(status_code=500, detail=str(e))
```

## Testing

Run tests:
```bash
cd backend
pytest tests/ -v --cov=. --cov-report=term
```

Test structure:
- `tests/`: Unit tests
- `tests/unit/`: Service unit tests
- Test files match module names: `test_<module>.py`

## Monitoring

### Health Checks

- `/api/health`: Basic health check
- `/metrics`: Prometheus metrics (when prometheus-client installed)
- `/api/v1/omni/summary`: System summary

### Logging

All services use Python logging:
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

PII redaction filter automatically applied to root logger.

## Security

### Built-in Security Features

1. **Security Headers**: HSTS, CSP, X-Frame-Options, etc.
2. **Rate Limiting**: IP-based (100 req/min default)
3. **Authentication**: JWT-based with MFA support
4. **CORS**: Configurable allowed origins
5. **Input Validation**: Pydantic models
6. **SQL Injection Protection**: SQLAlchemy ORM
7. **PII Redaction**: Automatic in logs

### MFA Support

Multiple methods supported:
- TOTP (Authenticator apps)
- SMS codes
- Email codes
- Backup codes

See `routes/auth_routes.py` and `routes/mfa_routes.py` for details.

## Performance Optimization

### Connection Pooling

PostgreSQL uses optimized pooling:
- Pool size: 20 (configurable)
- Max overflow: 40
- Pre-ping: Verify before use
- Recycle: 1 hour

### Caching

Response caching via Redis:
- Default TTL: 60 seconds
- Cache key based on path + params
- Automatic invalidation

### Async Operations

All routes and database operations are async for better concurrency.

## Troubleshooting

### Common Issues

**Import errors on startup:**
- Check `OMNI_MINIMAL` mode
- Verify all dependencies installed
- Review router registration try/except blocks

**Database connection failures:**
- Verify connection strings
- Check network accessibility
- Review pool configuration

**Rate limiting issues:**
- Set `RUN_AS_INTERNAL=1` if behind gateway
- Adjust rate limit in `middleware/rate_limiter.py`

**Slow startup:**
- Enable `OMNI_MINIMAL=1`
- Reduce pool sizes
- Disable optional features

## Additional Resources

- API Documentation: `/api/docs` (Swagger UI)
- Alternative docs: `/api/redoc` (ReDoc)
- GitHub Actions: `.github/workflows/backend-ci.yml`
- Docker: `Dockerfile.backend`, `Dockerfile.backend.minimal`
- Cloud Build: `cloudbuild-backend.yaml`
