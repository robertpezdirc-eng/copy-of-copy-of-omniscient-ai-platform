# 🧪 Phase 1 Testing & Validation Guide
## Comprehensive Testing for Critical Updates

**Purpose:** Validate Phase 1A/1B critical dependency updates before production deployment  
**Status:** Testing in Progress  
**Last Updated:** November 3, 2025

---

## ✅ Pre-Testing Checklist

### Environment Setup
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] Docker & Docker Compose available
- [ ] Access to staging environment
- [ ] API keys configured (OpenAI, Anthropic, etc.)

### Backup Verification
- [ ] Production database backup created
- [ ] Current Docker images tagged
- [ ] Rollback procedure documented
- [ ] Incident response team notified

---

## 🔧 Backend Testing (Python Dependencies)

### 1. Dependency Installation Test

```bash
cd backend

# Create fresh virtual environment
python3 -m venv venv_test
source venv_test/bin/activate  # On Windows: venv_test\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify critical packages
pip show openai | grep Version        # Should be 1.54.0
pip show anthropic | grep Version     # Should be 0.39.0
pip show fastapi | grep Version       # Should be 0.121.0
pip show pydantic | grep Version      # Should be 2.10.0
pip show cryptography | grep Version  # Should be 44.0.0
pip show transformers | grep Version  # Should be 4.46.0
```

**Expected Output:**
```
openai (1.54.0)
anthropic (0.39.0)
fastapi (0.121.0)
pydantic (2.10.0)
cryptography (44.0.0)
transformers (4.46.0)
```

### 2. Import Test

```bash
# Test critical imports
python3 << 'EOF'
# Test OpenAI SDK v1.x
from openai import OpenAI, AsyncOpenAI
print("✅ OpenAI SDK v1.x import successful")

# Test Anthropic SDK
from anthropic import Anthropic, AsyncAnthropic
print("✅ Anthropic SDK import successful")

# Test FastAPI & Pydantic
from fastapi import FastAPI
from pydantic import BaseModel
print("✅ FastAPI & Pydantic import successful")

# Test Transformers
from transformers import AutoTokenizer
print("✅ Transformers import successful")

# Test Cryptography
from cryptography.fernet import Fernet
print("✅ Cryptography import successful")

print("\n✅ All critical imports successful!")
EOF
```

### 3. RAG Service Test

Create test file: `backend/tests/test_rag_service_updated.py`

```python
import pytest
import os
from services.ai.rag_service import RAGService

@pytest.mark.asyncio
async def test_openai_embeddings():
    """Test OpenAI embeddings with new SDK"""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    rag = RAGService(
        vector_db="faiss",
        embedding_model="openai",
        llm_backend="openai"
    )
    
    # Test single embedding
    embedding = await rag.embed_text("Hello, world!")
    assert len(embedding) == 1536  # text-embedding-3-small dimension
    assert all(isinstance(x, float) for x in embedding)
    print("✅ OpenAI embedding test passed")

@pytest.mark.asyncio
async def test_anthropic_llm():
    """Test Anthropic LLM with new SDK"""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    
    rag = RAGService(
        vector_db="faiss",
        embedding_model="sentence-transformers",
        llm_backend="anthropic"
    )
    
    # Test query generation
    context_docs = [{"content": "The sky is blue."}]
    response = await rag.generate_response(
        query="What color is the sky?",
        context_documents=context_docs,
        model="claude-3-5-sonnet-20241022",
        max_tokens=100
    )
    
    assert "answer" in response
    assert len(response["answer"]) > 0
    print("✅ Anthropic LLM test passed")

@pytest.mark.asyncio
async def test_batch_embeddings():
    """Test batch embedding with new OpenAI SDK"""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    rag = RAGService(
        vector_db="faiss",
        embedding_model="openai"
    )
    
    texts = ["Hello", "World", "Test"]
    embeddings = await rag.embed_batch(texts)
    
    assert len(embeddings) == 3
    assert all(len(emb) == 1536 for emb in embeddings)
    print("✅ Batch embeddings test passed")
```

Run tests:
```bash
cd backend
pytest tests/test_rag_service_updated.py -v
```

### 4. API Endpoint Smoke Test

```bash
# Start backend locally
cd backend
uvicorn main:app --reload --port 8080 &

# Wait for startup
sleep 5

# Test health endpoint
curl http://localhost:8080/api/health

# Test OpenAI integration (if RAG route exists)
curl -X POST http://localhost:8080/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key-123" \
  -d '{
    "query": "What is AI?",
    "top_k": 3
  }'

# Stop backend
pkill -f uvicorn
```

---

## 🌐 Gateway Testing

### 1. Gateway Dependency Test

```bash
cd gateway

# Create virtual environment
python3 -m venv venv_test
source venv_test/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify versions
pip show fastapi | grep Version    # Should be 0.121.0
pip show pydantic | grep Version   # Should be 2.10.0
pip show sentry-sdk | grep Version # Should be 2.18.0
```

### 2. Gateway Integration Test

```bash
# Start gateway locally
cd gateway
uvicorn app.main:app --reload --port 8081 &

# Wait for startup
sleep 5

# Test health endpoint
curl http://localhost:8081/health

# Test metrics endpoint
curl http://localhost:8081/metrics

# Test proxy to backend (if backend is running)
curl -X POST http://localhost:8081/api/v1/ai/predict \
  -H "x-api-key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"data": [1,2,3,4,5]}'

# Stop gateway
pkill -f uvicorn
```

---

## 🎨 Frontend Testing

### 1. Frontend Dependency Update

```bash
cd frontend

# Update dependencies
npm install

# Verify versions
npm list react react-dom axios typescript vite
```

**Expected Output:**
```
├── axios@1.7.7
├── react@18.3.1
├── react-dom@18.3.1
├── typescript@5.6.3
└── vite@5.4.11
```

### 2. Build Test

```bash
cd frontend

# Run TypeScript compiler
npm run build

# Expected: Successful build with no errors
```

### 3. Development Server Test

```bash
cd frontend

# Start dev server
npm run dev

# Visit http://localhost:5173 in browser
# Verify:
# - [ ] App loads without errors
# - [ ] No console errors
# - [ ] Navigation works
# - [ ] API calls work (if backend running)
```

---

## 🐳 Docker Integration Test

### 1. Build Images

```bash
# Build backend image
docker build -f Dockerfile.backend -t omni-backend:phase1-test .

# Build gateway image
cd gateway
docker build -t omni-gateway:phase1-test .
cd ..
```

### 2. Run with Docker Compose

```bash
# Start services
docker-compose up --build

# In another terminal, test endpoints
curl http://localhost:8080/api/health  # Backend
curl http://localhost:8081/health      # Gateway

# Check logs
docker-compose logs backend | tail -50
docker-compose logs gateway | tail -50

# Stop services
docker-compose down
```

---

## 🔍 Regression Testing

### Critical Workflows to Test

#### 1. AI Prediction Flow
```bash
# Test LSTM prediction
curl -X POST http://localhost:8080/api/v1/predict/revenue-lstm \
  -H "Content-Type: application/json" \
  -d '{
    "time_series": [100, 110, 120, 130, 140],
    "forecast_steps": 3,
    "tenant_id": "test"
  }'
```

#### 2. Sentiment Analysis
```bash
curl -X POST http://localhost:8080/api/v1/ai/sentiment \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This product is amazing!",
    "tenant_id": "test"
  }'
```

#### 3. Authentication Flow
```bash
# Test JWT token generation
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass"
  }'
```

---

## 📊 Performance Testing

### 1. Load Test with Apache Bench

```bash
# Install Apache Bench if needed
# sudo apt-get install apache2-utils

# Test health endpoint
ab -n 1000 -c 10 http://localhost:8080/api/health

# Expected:
# - Requests per second: > 500
# - Time per request: < 20ms (mean)
# - Failed requests: 0
```

### 2. Memory Usage Test

```bash
# Monitor backend memory
docker stats omni-backend --no-stream

# Expected:
# - Memory usage: < 2GB
# - CPU usage: < 50% (idle)
```

---

## 🛡️ Security Testing

### 1. Vulnerability Scan

```bash
cd backend

# Install safety
pip install safety

# Scan for known vulnerabilities
safety check

# Expected: No critical vulnerabilities
```

### 2. Dependency Audit

```bash
cd backend

# Install pip-audit
pip install pip-audit

# Run audit
pip-audit

# Expected: No high/critical vulnerabilities
```

---

## ✅ Validation Checklist

### Backend Validation
- [ ] All dependencies installed without errors
- [ ] All imports successful
- [ ] RAG service tests pass
- [ ] API endpoints respond correctly
- [ ] No deprecation warnings
- [ ] Docker build succeeds
- [ ] Memory usage within limits
- [ ] No security vulnerabilities

### Gateway Validation
- [ ] All dependencies installed without errors
- [ ] Gateway starts without errors
- [ ] Health endpoint responds
- [ ] Metrics endpoint responds
- [ ] Proxy functionality works
- [ ] Rate limiting works
- [ ] Docker build succeeds

### Frontend Validation
- [ ] Dependencies updated successfully
- [ ] TypeScript compiles without errors
- [ ] Build succeeds
- [ ] Dev server runs without errors
- [ ] No browser console errors
- [ ] API integration works

### Integration Validation
- [ ] Backend ↔ Gateway communication works
- [ ] Frontend ↔ Gateway communication works
- [ ] Docker Compose stack runs successfully
- [ ] All services healthy simultaneously
- [ ] End-to-end workflows complete

---

## 🚨 Common Issues & Solutions

### Issue 1: OpenAI Import Error
```
ImportError: cannot import name 'OpenAI' from 'openai'
```
**Solution:** Ensure openai==1.54.0 is installed, not 0.x version
```bash
pip uninstall openai
pip install openai==1.54.0
```

### Issue 2: Pydantic Validation Error
```
ValidationError: field required
```
**Solution:** Pydantic v2 stricter validation. Update model definitions:
```python
from pydantic import BaseModel, Field
from typing import Optional

class MyModel(BaseModel):
    field: Optional[str] = Field(default=None)
```

### Issue 3: Anthropic API Error
```
anthropic.APIError: model not found
```
**Solution:** Use correct model name for Claude 3.5:
```python
model="claude-3-5-sonnet-20241022"  # Correct
# Not: "claude-3-sonnet" or "claude-2"
```

### Issue 4: FastAPI Deprecation Warning
```
DeprecationWarning: The 'json_encoders' config option is deprecated
```
**Solution:** Use Pydantic v2 serialization:
```python
from pydantic import ConfigDict

class MyModel(BaseModel):
    model_config = ConfigDict(json_encoders={...})
```

---

## 📈 Performance Benchmarks

### Before Updates (Baseline)
```
OpenAI Embedding:     ~200ms per request
Anthropic Chat:       ~800ms per request
API Health Check:     ~10ms
Backend Memory:       ~1.2GB
Gateway Latency:      ~5ms overhead
```

### After Updates (Expected)
```
OpenAI Embedding:     ~150ms per request (25% faster, new model)
Anthropic Chat:       ~600ms per request (25% faster, new SDK)
API Health Check:     ~10ms (no change)
Backend Memory:       ~1.3GB (slight increase acceptable)
Gateway Latency:      ~5ms (no change)
```

---

## 🎯 Success Criteria

### Must Pass (Blocking)
1. ✅ Zero import errors
2. ✅ Zero failed unit tests
3. ✅ All smoke tests pass
4. ✅ Docker builds succeed
5. ✅ No critical security vulnerabilities

### Should Pass (Important)
6. ✅ No high-severity security vulnerabilities
7. ✅ Performance within 10% of baseline
8. ✅ Memory usage < 2GB per service
9. ✅ Zero error logs during tests
10. ✅ All integration tests pass

### Nice to Have (Optional)
11. 📊 Performance improved vs baseline
12. 📊 Reduced memory footprint
13. 📊 Faster startup times
14. 📊 Better error messages

---

## 🚀 Staging Deployment

Once all tests pass locally:

```bash
# 1. Tag images
docker tag omni-backend:phase1-test omni-backend:phase1-staging
docker tag omni-gateway:phase1-test omni-gateway:phase1-staging

# 2. Push to registry
docker push gcr.io/refined-graph-471712-n9/omni-backend:phase1-staging
docker push gcr.io/refined-graph-471712-n9/omni-gateway:phase1-staging

# 3. Deploy to staging
gcloud run deploy omni-ultra-backend-staging \
  --image=gcr.io/refined-graph-471712-n9/omni-backend:phase1-staging \
  --region=europe-west1 \
  --project=refined-graph-471712-n9

gcloud run deploy ai-gateway-staging \
  --image=gcr.io/refined-graph-471712-n9/omni-gateway:phase1-staging \
  --region=europe-west1 \
  --project=refined-graph-471712-n9

# 4. Smoke test staging
curl https://omni-ultra-backend-staging-xxx.run.app/api/health
curl https://ai-gateway-staging-xxx.run.app/health

# 5. Monitor for 24-48 hours
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=100 \
  --project=refined-graph-471712-n9
```

---

## 📝 Test Results Log

### Test Execution: [Date/Time]

**Tester:** _______________  
**Environment:** _______________  
**Branch/Commit:** _______________

| Test Category | Status | Notes |
|---------------|--------|-------|
| Dependency Installation | ⏳ | |
| Import Tests | ⏳ | |
| RAG Service Tests | ⏳ | |
| API Smoke Tests | ⏳ | |
| Gateway Tests | ⏳ | |
| Frontend Build | ⏳ | |
| Docker Build | ⏳ | |
| Integration Tests | ⏳ | |
| Performance Tests | ⏳ | |
| Security Scan | ⏳ | |

**Overall Status:** ⏳ Not Started | 🔄 In Progress | ✅ Passed | ❌ Failed

**Issues Found:** _______________

**Recommendation:** _______________

---

**Document Version:** 1.0  
**Last Updated:** November 3, 2025  
**Status:** Ready for Testing
