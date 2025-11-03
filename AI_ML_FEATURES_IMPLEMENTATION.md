# Advanced AI/ML Features Implementation

## 🎯 Overview

This document describes the implementation of three advanced AI/ML features for the Omni Enterprise Ultra Max Platform:

1. **Multi-LLM Router** - Intelligent routing between multiple LLM providers
2. **Enhanced RAG** - Retrieval-Augmented Generation with FAISS and citation tracking
3. **Autonomous Agents** - Self-improving AI agents with web search and code generation

---

## 1. Multi-LLM Router

### Uvod (Slovenian)

Multi-LLM Router omogoča inteligentno usmerjanje med različnimi ponudniki jezikovnih modelov (OpenAI, Anthropic, Google Gemini, Ollama) glede na stroške, hitrost in kakovost.

### Features

- **Intelligent Routing** based on:
  - **Cost**: Cheapest option first (Ollama → Gemini → Anthropic → OpenAI)
  - **Speed**: Fastest response (Ollama → Gemini → Anthropic → OpenAI)
  - **Quality**: Best capability (OpenAI → Anthropic → Gemini → Ollama)
  - **Balanced**: Optimal mix of cost/speed/quality
  - **Failover**: Automatic retry with next provider on failure

- **Provider Configuration**:
  - **OpenAI GPT-4**: Premium quality, $0.03/1K tokens, ~2000ms latency
  - **Anthropic Claude 3.5 Sonnet**: Cost-effective, $0.015/1K tokens, ~1800ms latency
  - **Google Gemini Pro**: Specialist tasks, $0.0005/1K tokens, ~1500ms latency
  - **Local Ollama**: Fast & free, $0/1K tokens, ~500ms latency

- **Statistics & Monitoring**:
  - Request counts per provider
  - Average latency tracking
  - Failure rates
  - Cost estimation

### API Endpoints

#### POST `/api/v1/llm/complete`
Complete a prompt using intelligent routing.

**Request:**
```json
{
  "prompt": "Explain quantum computing in simple terms",
  "strategy": "balanced",
  "provider": null,
  "max_tokens": 500,
  "temperature": 0.7,
  "task_complexity": "medium",
  "system_prompt": "You are a helpful AI assistant"
}
```

**Parameters:**
- `strategy`: "cost" | "speed" | "quality" | "balanced" | "failover"
- `provider`: Optional force provider ("openai" | "anthropic" | "gemini" | "ollama")
- `task_complexity`: "simple" | "medium" | "complex" (affects balanced routing)

**Response:**
```json
{
  "content": "Quantum computing is...",
  "provider": "anthropic",
  "latency_ms": 1823,
  "estimated_cost": 0.000042,
  "strategy_used": "balanced",
  "tokens_estimated": 280
}
```

#### GET `/api/v1/llm/providers`
Get information about all LLM providers.

**Response:**
```json
{
  "openai": {
    "name": "OpenAI GPT-4",
    "cost_per_1k_tokens": 0.03,
    "avg_latency_ms": 2000,
    "quality_score": 95,
    "max_tokens": 8192,
    "supports_streaming": true,
    "is_available": true
  },
  ...
}
```

#### GET `/api/v1/llm/stats`
Get routing statistics.

**Response:**
```json
{
  "total_requests": 1247,
  "provider_usage": {
    "openai": 312,
    "anthropic": 589,
    "gemini": 234,
    "ollama": 112
  },
  "provider_failures": {...},
  "avg_latency_ms": {...},
  "provider_availability": {...}
}
```

#### POST `/api/v1/llm/compare`
Compare responses from multiple providers.

**Request:**
```json
{
  "prompt": "What is machine learning?",
  "providers": ["openai", "anthropic", "gemini"],
  "max_tokens": 200
}
```

### Configuration

Set environment variables for provider API keys:

```bash
# Required for providers you want to use
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."

# Optional: Ollama (local)
# Requires Ollama running on localhost:11434
```

### Usage Examples

**Python:**
```python
from services.ai.multi_llm_router import get_multi_llm_router, RoutingStrategy

router = get_multi_llm_router()

# Cost-optimized completion
result = await router.complete(
    prompt="Summarize this article...",
    strategy=RoutingStrategy.COST_OPTIMIZED,
    max_tokens=500
)

# Quality-optimized for complex task
result = await router.complete(
    prompt="Write a detailed technical analysis...",
    strategy=RoutingStrategy.QUALITY_OPTIMIZED,
    task_complexity="complex"
)

# Force specific provider
result = await router.complete(
    prompt="Quick answer needed...",
    provider="ollama"
)
```

**cURL:**
```bash
curl -X POST http://localhost:8080/api/v1/llm/complete \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is AI?",
    "strategy": "balanced",
    "max_tokens": 200
  }'
```

---

## 2. Enhanced RAG (Retrieval-Augmented Generation)

### Uvod (Slovenian)

Enhanced RAG sistem uporablja FAISS za hitro iskanje po vektorjih, sentence transformers za semantične vložitve in sledenje virom za transparentnost.

### Features

- **FAISS Vector Database**:
  - Fast similarity search (L2 distance)
  - Incremental indexing
  - Persistent storage
  - ID mapping for document retrieval

- **Semantic Embeddings**:
  - Sentence Transformers (all-MiniLM-L6-v2)
  - 384-dimensional embeddings
  - Multilingual support

- **Citation Tracking**:
  - Automatic citation IDs ([1], [2], etc.)
  - Source attribution in answers
  - Confidence scoring

- **Multi-Tenancy**:
  - Tenant-based document isolation
  - Per-tenant statistics
  - Tenant data deletion (GDPR)

- **Context Injection**:
  - Top-k relevant documents
  - Metadata filtering
  - LLM-generated answers with sources

### API Endpoints

#### POST `/api/v1/rag-enhanced/ingest`
Ingest documents into the RAG system.

**Request:**
```json
{
  "documents": [
    {
      "id": "doc1",
      "content": "The Omni platform provides advanced monitoring with Grafana...",
      "metadata": {
        "category": "documentation",
        "version": "2.0",
        "author": "engineering"
      }
    }
  ],
  "tenant_id": "acme-corp"
}
```

**Response:**
```json
{
  "status": "success",
  "documents_ingested": 1,
  "document_ids": ["doc1"],
  "total_documents": 247,
  "tenant_id": "acme-corp"
}
```

#### POST `/api/v1/rag-enhanced/search`
Semantic search for relevant documents.

**Request:**
```json
{
  "query": "How does the monitoring system work?",
  "top_k": 5,
  "tenant_id": "acme-corp",
  "filter_metadata": {"category": "documentation"}
}
```

**Response:**
```json
{
  "query": "How does the monitoring system work?",
  "results": [
    {
      "document_id": "doc1",
      "content": "The monitoring system uses Prometheus and Grafana...",
      "metadata": {...},
      "score": 0.89,
      "rank": 1,
      "citation_id": "[1]"
    }
  ],
  "num_results": 5
}
```

#### POST `/api/v1/rag-enhanced/query`
Full RAG query with answer generation.

**Request:**
```json
{
  "query": "What security features are available?",
  "top_k": 5,
  "tenant_id": "acme-corp",
  "llm_provider": "anthropic",
  "temperature": 0.7
}
```

**Response:**
```json
{
  "answer": "The platform offers several security features [1]:\n\n1. GDPR compliance with data export and deletion [2]\n2. Multi-factor authentication (MFA) with TOTP support [3]\n3. Threat detection including brute force protection [4]...",
  "citations": [
    {"id": "[1]", "score": 0.92, "metadata": {...}},
    {"id": "[2]", "score": 0.89, "metadata": {...}}
  ],
  "sources": [
    {
      "document_id": "security-doc",
      "content_preview": "The platform provides comprehensive security...",
      "metadata": {...},
      "score": 0.92
    }
  ],
  "confidence": 0.91,
  "query_id": "a3f21bc7",
  "generation_info": {
    "provider": "anthropic",
    "latency_ms": 1823,
    "estimated_cost": 0.000156
  },
  "num_context_docs": 5
}
```

#### GET `/api/v1/rag-enhanced/stats`
Get RAG system statistics.

**Response:**
```json
{
  "total_documents": 1247,
  "index_size": 1247,
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_dimension": 384,
  "tenant_document_counts": {
    "acme-corp": 547,
    "tech-startup": 423,
    "enterprise": 277
  },
  "total_queries": 3421,
  "index_path": "/tmp/faiss_index"
}
```

#### DELETE `/api/v1/rag-enhanced/tenant/{tenant_id}`
Clear all documents for a tenant (GDPR compliance).

**Response:**
```json
{
  "status": "success",
  "tenant_id": "acme-corp",
  "documents_removed": 547
}
```

### Usage Examples

**Python:**
```python
from services.ai.enhanced_rag_service import get_enhanced_rag_service

rag = get_enhanced_rag_service()

# Ingest documents
rag.ingest_documents(
    documents=[
        {"content": "...", "metadata": {"category": "docs"}}
    ],
    tenant_id="my-tenant"
)

# Search
results = rag.search("machine learning", top_k=5)

# Full RAG query
answer = rag.generate_answer(
    query="What is the platform architecture?",
    llm_provider="anthropic"
)
```

**cURL:**
```bash
# Ingest
curl -X POST http://localhost:8080/api/v1/rag-enhanced/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [{"content": "...", "metadata": {}}],
    "tenant_id": "test"
  }'

# Query
curl -X POST http://localhost:8080/api/v1/rag-enhanced/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What features are available?",
    "top_k": 5
  }'
```

---

## 3. Autonomous Agents

### Uvod (Slovenian)

Avtonomni agenti so samo-izboljševalni AI sistemi, ki lahko samostojno izvajajo naloge, iščejo po spletu, generirajo kodo in predlagajo izboljšave platforme.

### Features

- **Web Search Integration**:
  - DuckDuckGo API (no key required)
  - Real-time information retrieval
  - Related topics and sources

- **Self-Healing**:
  - Automatic error recovery
  - Step modification using LLM
  - Up to 3 retries per step
  - Execution trace logging

- **Code Generation**:
  - Type-hinted Python code
  - Docstrings and error handling
  - PEP 8 compliant
  - Multiple language support (via LLM)

- **Platform Analysis**:
  - Architecture review
  - Performance optimization suggestions
  - Security enhancement recommendations
  - Cost optimization ideas

- **Autonomous Execution**:
  - LLM-based planning
  - Multi-step task execution
  - Context accumulation
  - Result synthesis

### API Endpoints

#### POST `/api/v1/agents/execute`
Execute a task autonomously.

**Request:**
```json
{
  "task": "Research Redis caching best practices and create a summary",
  "context": {"focus_area": "performance"},
  "max_steps": 10
}
```

**Process:**
1. Agent plans the task (using LLM)
2. Executes steps (search, generate, analyze)
3. Self-heals on errors
4. Synthesizes final result

**Response:**
```json
{
  "execution_id": "exec_1730000000_0",
  "task": "Research Redis caching...",
  "state": "completed",
  "actions": [
    {
      "action_type": "plan",
      "description": "Created execution plan",
      "parameters": {...},
      "result": {...},
      "timestamp": "2024-11-03T00:00:00Z"
    },
    {
      "action_type": "web_search",
      "description": "Search for Redis best practices",
      "parameters": {"query": "Redis caching best practices"},
      "result": {
        "status": "success",
        "results": {...}
      },
      "timestamp": "2024-11-03T00:00:05Z"
    }
  ],
  "final_result": {
    "synthesis": "Redis caching best practices include...",
    "provider": "anthropic"
  },
  "start_time": "2024-11-03T00:00:00Z",
  "end_time": "2024-11-03T00:00:15Z",
  "error_count": 0,
  "heal_count": 0
}
```

#### POST `/api/v1/agents/web-search`
Search the web for information.

**Request:**
```json
{
  "query": "artificial intelligence trends 2024"
}
```

**Response:**
```json
{
  "status": "success",
  "results": {
    "query": "artificial intelligence trends 2024",
    "abstract": "Artificial intelligence in 2024...",
    "abstract_url": "https://...",
    "related_topics": [
      {"title": "...", "url": "https://..."}
    ]
  },
  "source": "DuckDuckGo"
}
```

#### POST `/api/v1/agents/generate-code`
Generate Python code.

**Request:**
```json
{
  "requirements": "Create a function that calculates the factorial of a number with memoization"
}
```

**Response:**
```json
{
  "status": "success",
  "code": "from functools import lru_cache\n\n@lru_cache(maxsize=None)\ndef factorial(n: int) -> int:\n    \"\"\"Calculate factorial with memoization.\"\"\"\n    if n < 0:\n        raise ValueError(\"Factorial not defined for negative numbers\")\n    return 1 if n <= 1 else n * factorial(n - 1)",
  "requirements": "...",
  "provider": "openai"
}
```

#### POST `/api/v1/agents/analyze-platform`
Analyze platform and generate improvement suggestions.

**Response:**
```json
{
  "status": "success",
  "analysis": {
    "recommendations": [
      {
        "title": "Implement Connection Pooling",
        "category": "performance",
        "priority": "high",
        "description": "Add database connection pooling to reduce latency...",
        "implementation": "Use SQLAlchemy pool_size and max_overflow parameters..."
      }
    ]
  },
  "suggestions_added": 5
}
```

#### GET `/api/v1/agents/suggestions`
Get platform improvement suggestions.

**Query Parameters:**
- `category`: performance | security | features | architecture | cost
- `priority`: high | medium | low
- `status`: pending | implemented | rejected

**Response:**
```json
[
  {
    "title": "Add Redis Connection Pooling",
    "category": "performance",
    "priority": "high",
    "description": "...",
    "implementation": "...",
    "timestamp": "2024-11-03T00:00:00Z",
    "status": "pending"
  }
]
```

#### GET `/api/v1/agents/executions`
Get execution history.

**Response:**
```json
{
  "executions": [
    {
      "execution_id": "exec_...",
      "task": "...",
      "state": "completed",
      "actions_count": 5,
      "error_count": 0,
      "heal_count": 0,
      "start_time": "...",
      "end_time": "..."
    }
  ],
  "count": 10
}
```

#### GET `/api/v1/agents/stats`
Get agent statistics.

**Response:**
```json
{
  "agent_name": "OmniAgent",
  "total_executions": 127,
  "successful_executions": 118,
  "failed_executions": 9,
  "success_rate": 92.9,
  "total_self_heals": 23,
  "improvement_suggestions": 47,
  "pending_suggestions": 31,
  "capabilities": {
    "web_search": true,
    "llm_reasoning": true,
    "code_generation": true,
    "self_healing": true
  }
}
```

#### POST `/api/v1/agents/self-improve`
Trigger agent self-improvement cycle (background task).

**Response:**
```json
{
  "status": "started",
  "message": "Self-improvement cycle started in background"
}
```

### Usage Examples

**Python:**
```python
from services.ai.autonomous_agent import get_autonomous_agent

agent = get_autonomous_agent()

# Execute task
execution = await agent.execute_task(
    task="Research machine learning frameworks and compare them",
    context={"languages": ["Python", "JavaScript"]},
    max_steps=10
)

# Web search
results = await agent._web_search("quantum computing")

# Generate code
code_result = await agent._generate_code(
    "Binary search algorithm with type hints"
)

# Get suggestions
suggestions = agent.get_improvement_suggestions(
    category="performance",
    priority="high"
)
```

**cURL:**
```bash
# Execute task
curl -X POST http://localhost:8080/api/v1/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Search for AI trends and summarize",
    "max_steps": 5
  }'

# Get suggestions
curl -X GET "http://localhost:8080/api/v1/agents/suggestions?priority=high"

# Generate code
curl -X POST http://localhost:8080/api/v1/agents/generate-code \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "Fibonacci sequence generator"
  }'
```

---

## Dependencies

The following packages are required (already added to `backend/requirements.txt`):

```
# AI/ML Core
openai==1.54.4
anthropic==0.39.0
google-generativeai==0.8.3

# Vector Search & Embeddings
faiss-cpu==1.7.4
sentence-transformers==3.3.1
transformers==4.46.3

# ML Frameworks (optional)
tensorflow==2.17.1
torch==2.5.1
```

## Environment Variables

```bash
# LLM Providers (at least one required)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."

# Optional: Ollama (local LLM)
# Requires Ollama running on localhost:11434
# Install: curl https://ollama.ai/install.sh | sh
# Run: ollama serve
```

## Testing

Run the comprehensive test suite:

```bash
# All AI features
pytest tests/test_ai_features.py -v

# Specific feature
pytest tests/test_ai_features.py::TestMultiLLMRouter -v
pytest tests/test_ai_features.py::TestEnhancedRAG -v
pytest tests/test_ai_features.py::TestAutonomousAgent -v
```

## Performance Considerations

### Multi-LLM Router
- **Latency**: 500ms (Ollama) to 2000ms (OpenAI)
- **Cost**: $0 (Ollama) to $0.03/1K tokens (OpenAI)
- **Throughput**: Limited by provider rate limits

### Enhanced RAG
- **Indexing**: ~100ms per document
- **Search**: ~10ms for 1K documents, ~50ms for 100K documents
- **Storage**: ~1.5KB per document (embedding + metadata)
- **Memory**: ~600MB for 1M documents

### Autonomous Agents
- **Execution**: Variable (depends on task complexity)
- **Web Search**: ~500ms per query
- **Code Generation**: ~2-5 seconds
- **Self-Healing**: +1-3 seconds per retry

## Production Deployment

### Docker Compose

```yaml
services:
  backend:
    build: ./backend
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    volumes:
      - ./faiss_index:/app/faiss_index  # Persistent RAG storage
    
  ollama:  # Optional: Local LLM
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
```

### Kubernetes

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-config
data:
  FAISS_INDEX_PATH: "/data/faiss_index"

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: faiss-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

## Security Considerations

1. **API Keys**: Store in Secret Manager, not environment variables
2. **Rate Limiting**: Implement per-user rate limits for LLM calls
3. **Cost Control**: Set monthly budget limits per tenant
4. **Input Validation**: Sanitize all user inputs before LLM calls
5. **Output Filtering**: Check generated code for security issues
6. **Tenant Isolation**: Strict RAG document isolation
7. **Audit Logging**: Log all agent actions and LLM calls

## Monitoring with Grafana

Add these metrics to your Prometheus/Grafana setup:

```python
# LLM Router metrics
llm_requests_total = Counter('llm_requests_total', 'Total LLM requests', ['provider', 'strategy'])
llm_latency_seconds = Histogram('llm_latency_seconds', 'LLM latency', ['provider'])
llm_cost_dollars = Counter('llm_cost_dollars', 'LLM costs', ['provider'])

# RAG metrics
rag_documents_total = Gauge('rag_documents_total', 'Total documents', ['tenant'])
rag_search_latency_seconds = Histogram('rag_search_latency_seconds', 'Search latency')
rag_query_confidence = Histogram('rag_query_confidence', 'Query confidence scores')

# Agent metrics
agent_executions_total = Counter('agent_executions_total', 'Total executions', ['state'])
agent_self_heals_total = Counter('agent_self_heals_total', 'Self-healing attempts')
agent_suggestions_total = Gauge('agent_suggestions_total', 'Improvement suggestions', ['category', 'priority'])
```

## Troubleshooting

### Multi-LLM Router

**Issue**: "No available LLM providers"
- **Solution**: Check API keys are set correctly and providers are reachable

**Issue**: High costs
- **Solution**: Use `strategy="cost"` or set provider="ollama" for free local inference

### Enhanced RAG

**Issue**: "FAISS index not initialized"
- **Solution**: Ensure faiss-cpu is installed: `pip install faiss-cpu`

**Issue**: Poor search results
- **Solution**: Ingest more diverse documents, increase top_k parameter

### Autonomous Agents

**Issue**: "Web search not available"
- **Solution**: Install httpx: `pip install httpx`

**Issue**: Agent fails frequently
- **Solution**: Check LLM provider availability, increase max_steps parameter

## Future Enhancements

- [ ] Streaming responses for LLM completions
- [ ] Hybrid search (semantic + keyword) for RAG
- [ ] Multi-modal support (images, audio)
- [ ] Agent collaboration (multi-agent systems)
- [ ] Fine-tuned local models
- [ ] Advanced caching strategies
- [ ] Vector database alternatives (Pinecone, Weaviate)
- [ ] GraphRAG for connected knowledge

## Support

For issues or questions:
- GitHub Issues: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/issues
- Documentation: See README-GRAFANA.md, SECURITY_FEATURES_IMPLEMENTATION.md

---

**Status**: ✅ Production Ready
**Version**: 1.0.0
**Last Updated**: 2024-11-03
