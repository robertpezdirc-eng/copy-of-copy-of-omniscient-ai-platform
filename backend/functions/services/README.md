# Backend Services Directory

This directory contains all business logic services for the Omni Enterprise Ultra Max platform. Services are organized by domain and provide reusable functionality for the API routes.

## Directory Structure

```
services/
├── README.md                      # This file
├── __init__.py                    # Services package initialization
│
├── advanced_ai/                   # Advanced AI/ML capabilities
│   ├── ab_testing.py             # A/B testing experiments
│   ├── automl.py                 # AutoML model training
│   ├── model_registry.py         # ML model versioning
│   └── multimodal.py             # Multi-modal AI processing
│
├── ai/                           # Core AI services
│   ├── anomaly_detection.py      # Anomaly detection algorithms
│   ├── autonomous_agent.py       # Autonomous AI agents
│   ├── dashboard_builder_service.py  # Dynamic dashboard generation
│   ├── enhanced_rag_service.py   # Enhanced RAG with advanced features
│   ├── multi_llm_router.py       # Multi-LLM routing and fallback
│   ├── ollama_service.py         # Ollama integration
│   ├── predictive_analytics.py   # Predictive modeling
│   ├── rag_service.py            # Basic RAG implementation
│   ├── recommendation_engine.py  # Recommendation algorithms
│   ├── sentiment_analysis.py     # Sentiment analysis
│   └── swarm_intelligence.py     # Swarm-based AI coordination
│
├── bi/                           # Business Intelligence
│   └── realtime_analytics.py    # Real-time analytics processing
│
├── compliance/                   # Compliance services
│   ├── gdpr_health.py           # GDPR health monitoring
│   ├── gdpr_repository.py       # GDPR data persistence
│   └── gdpr_service.py          # Comprehensive GDPR compliance
│
├── security/                     # Security services
│   ├── encryption.py            # Data encryption/decryption
│   └── gdpr.py                  # Basic GDPR operations (legacy)
│
└── [Root Level Services]         # Standalone service files
    ├── ai_assistant_service.py   # AI assistant functionality
    ├── analytics_service.py      # Analytics tracking and reporting
    ├── auth.py                   # Authentication logic
    ├── cache_service.py          # Caching layer (Redis)
    ├── compliance_service.py     # HIPAA, SOC2, ISO compliance
    ├── email_service.py          # Email sending (SMTP, SendGrid)
    ├── hubspot_service.py        # HubSpot CRM integration
    ├── integration_service.py    # General integration framework
    ├── mfa_service.py            # Multi-factor authentication
    ├── ml_models_service.py      # ML model management
    ├── nlp_service.py            # Natural language processing
    ├── observability_service.py  # Monitoring and logging
    ├── partner_service.py        # Partner/affiliate management
    ├── salesforce_service.py     # Salesforce CRM integration
    ├── security_service.py       # Advanced security features
    ├── shopify_service.py        # Shopify e-commerce integration
    ├── sms_service.py            # SMS sending (Twilio)
    ├── tenant_service.py         # Multi-tenancy management
    ├── websocket_service.py      # WebSocket connections
    ├── whitelabel_service.py     # White-label customization
    └── zapier_service.py         # Zapier integration
```

## Service Categories

### 1. AI & Machine Learning (23 services)
Advanced AI capabilities including RAG, LLM routing, predictive analytics, and AutoML.

**Subdirectories:**
- `ai/` - Core AI services (13 services)
- `advanced_ai/` - Advanced ML features (4 services)

**Root Level:**
- `ai_assistant_service.py` - AI-powered assistant
- `ml_models_service.py` - ML model lifecycle management
- `nlp_service.py` - Natural language processing

**Key Features:**
- Multiple LLM provider support (OpenAI, Anthropic, Ollama)
- RAG (Retrieval-Augmented Generation) with vector search
- Autonomous agents and swarm intelligence
- Predictive analytics and anomaly detection
- A/B testing and experimentation
- Multi-modal AI (text, image, audio)

### 2. Integration Services (7 services)
Third-party integrations for CRM, e-commerce, and automation platforms.

**Services:**
- `hubspot_service.py` - HubSpot CRM
- `salesforce_service.py` - Salesforce CRM
- `shopify_service.py` - Shopify e-commerce
- `zapier_service.py` - Zapier automation
- `integration_service.py` - Generic integration framework
- `partner_service.py` - Partner/affiliate management
- `whitelabel_service.py` - White-label customization

**Common Patterns:**
- OAuth 2.0 authentication
- Webhook handling
- Rate limiting and retry logic
- Data synchronization

### 3. Security & Compliance (7 services)
Security features and regulatory compliance (GDPR, HIPAA, SOC 2).

**Subdirectories:**
- `security/` - Core security (2 services)
- `compliance/` - GDPR compliance (3 services)

**Root Level:**
- `security_service.py` - Advanced security (2FA, SSO, audit logs)
- `mfa_service.py` - Multi-factor authentication
- `compliance_service.py` - HIPAA, SOC 2, ISO 27001

**Key Features:**
- GDPR compliance (consent, right to erasure, data portability)
- Multi-factor authentication (TOTP, SMS, email)
- Encryption at rest and in transit
- Audit logging and security scanning
- Data breach notifications

### 4. Communication Services (2 services)
Email and SMS communication.

**Services:**
- `email_service.py` - Email sending (SMTP, SendGrid)
- `sms_service.py` - SMS sending (Twilio)

**Features:**
- Template-based messaging
- Async sending with retry logic
- Multiple provider support
- Tracking and analytics

### 5. Infrastructure Services (7 services)
Core infrastructure and platform services.

**Services:**
- `auth.py` - Authentication and authorization
- `cache_service.py` - Redis-based caching
- `tenant_service.py` - Multi-tenancy management
- `websocket_service.py` - Real-time WebSocket connections
- `observability_service.py` - Monitoring, logging, tracing
- `analytics_service.py` - Usage analytics and reporting
- `bi/realtime_analytics.py` - Real-time BI

**Features:**
- JWT token management
- Redis caching with TTL
- Tenant isolation and resource limits
- Prometheus metrics
- Distributed tracing

## Service Design Patterns

### 1. Singleton Pattern
Most services use a singleton pattern for state management:

```python
_service_instance: Optional[MyService] = None

def get_my_service() -> MyService:
    global _service_instance
    if _service_instance is None:
        _service_instance = MyService()
    return _service_instance
```

### 2. Async/Await
All services use async/await for I/O operations:

```python
async def fetch_data(self, id: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{self.api_url}/data/{id}")
        return response.json()
```

### 3. Optional Dependencies
Services gracefully handle missing dependencies:

```python
try:
    from redis import Redis
    redis_available = True
except ImportError:
    redis_available = False
    logger.warning("Redis not available, using in-memory cache")
```

### 4. Error Handling
Consistent error handling with logging:

```python
try:
    result = await external_api_call()
    return result
except Exception as e:
    logger.error(f"API call failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

## Adding a New Service

1. **Create the service file** in the appropriate directory:
   - Domain-specific: `services/{domain}/my_service.py`
   - General purpose: `services/my_service.py`

2. **Follow the standard structure**:

```python
"""
My Service
Brief description of service purpose
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MyService:
    """Service description"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        logger.info("MyService initialized")
    
    async def do_something(self, param: str) -> Dict[str, Any]:
        """Method description"""
        try:
            # Implementation
            return {"success": True}
        except Exception as e:
            logger.error(f"Operation failed: {e}")
            raise


_service_instance: Optional[MyService] = None


def get_my_service() -> MyService:
    """Get or create service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = MyService()
    return _service_instance
```

3. **Add to `__init__.py`** if exporting:

```python
from .my_service import MyService, get_my_service

__all__ = ["MyService", "get_my_service"]
```

4. **Create tests** in `tests/test_my_service.py`:

```python
import pytest
from backend.services.my_service import get_my_service


@pytest.mark.asyncio
async def test_my_service():
    service = get_my_service()
    result = await service.do_something("test")
    assert result["success"] is True
```

5. **Document in README** if it's a new category or significant service

## Service Dependencies

### Database Services
Many services depend on database connections:
- **PostgreSQL**: Relational data, user management
- **MongoDB**: Document storage, logs
- **Redis**: Caching, sessions, rate limiting
- **Firestore**: Real-time data, mobile sync

Get database connections from `database.py`:

```python
from backend.database import get_postgres, get_mongodb, get_redis

async def my_operation():
    postgres = await get_postgres()
    mongo = await get_mongodb()
    redis = await get_redis()
```

### External APIs
Services integrate with external APIs:
- **OpenAI**: GPT models, embeddings
- **Anthropic**: Claude models
- **Pinecone**: Vector database
- **SendGrid**: Email delivery
- **Twilio**: SMS delivery
- **Stripe**: Payment processing

Use environment variables for API keys:

```python
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

## Testing Services

### Unit Tests
Test individual service methods:

```bash
pytest backend/tests/test_my_service.py -v
```

### Integration Tests
Test service interactions with databases and APIs:

```bash
pytest backend/tests/integration/test_my_service_integration.py -v
```

### Mocking External Services
Use `unittest.mock` for external dependencies:

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mock():
    with patch('services.my_service.external_api') as mock_api:
        mock_api.return_value = AsyncMock(return_value={"data": "test"})
        service = get_my_service()
        result = await service.do_something()
        assert result["data"] == "test"
```

## Performance Considerations

### Caching
Use Redis for caching expensive operations:

```python
from services.cache_service import get_cache_service

async def get_expensive_data(key: str):
    cache = get_cache_service()
    cached = await cache.get(key)
    if cached:
        return cached
    
    data = await compute_expensive_data()
    await cache.set(key, data, ttl=300)  # 5 minutes
    return data
```

### Connection Pooling
Reuse HTTP clients:

```python
class MyService:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=100)
        )
    
    async def close(self):
        await self.client.aclose()
```

### Batch Operations
Process items in batches:

```python
async def process_batch(items: List[str], batch_size: int = 100):
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        await process_items(batch)
```

## Known Issues

### GDPR Service Duplication
There are currently two GDPR services:
- `services/security/gdpr.py` - Basic, best-effort implementation (legacy)
- `services/compliance/gdpr_service.py` - Comprehensive, production-ready

**Recommendation**: Migrate to `compliance/gdpr_service.py` for production use. The security/gdpr.py version is kept for backward compatibility with existing routes.

### Service Organization
Some services in the root level could be organized into subdirectories:
- Communication services (`email_service.py`, `sms_service.py`) → `services/communication/`
- Integration services (multiple CRM/platform integrations) → `services/integrations/`

This is planned for future refactoring but kept flat for now to avoid breaking imports.

## Related Documentation

- [Backend Architecture](../ARCHITECTURE.md) - Overall backend structure
- [Backend README](../README.md) - Quick start and setup
- [GDPR Implementation](../GDPR_TODO_IMPLEMENTATION.md) - GDPR compliance roadmap
- [Advanced AI README](./advanced_ai/README.md) - Advanced AI features

## Support

For questions about specific services:
1. Check the service file docstrings
2. Review the related route file in `backend/routes/`
3. Check test files in `backend/tests/`
4. Refer to the main architecture documentation
