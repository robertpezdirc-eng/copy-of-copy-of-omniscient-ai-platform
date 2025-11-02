# Ollama Integration Guide

## Overview
The backend now supports **Ollama** as a local LLM provider alternative to OpenAI and Gemini. This enables:
- Local inference without external API costs
- Privacy-first deployments
- Custom model hosting
- Reduced latency for on-premise setups

---

## Configuration

### Environment Variables

Add these to your `.env` file or Cloud Run environment:

```bash
# Enable Ollama integration (default: false)
USE_OLLAMA=true

# Ollama server URL (default: http://localhost:11434)
OLLAMA_URL=http://localhost:11434

# Default model to use (default: llama3)
OLLAMA_MODEL=llama3

# Request timeout in seconds (default: 60)
OLLAMA_TIMEOUT=60
```

### Local Development

1. **Install Ollama**
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Windows (via WSL or download from ollama.com)
   ```

2. **Pull a model**
   ```bash
   ollama pull llama3
   # or
   ollama pull mistral
   ollama pull codellama
   ```

3. **Start Ollama server**
   ```bash
   ollama serve
   # Server runs on http://localhost:11434 by default
   ```

4. **Configure backend**
   ```bash
   # In your .env file
   USE_OLLAMA=true
   OLLAMA_URL=http://localhost:11434
   OLLAMA_MODEL=llama3
   ```

5. **Start backend**
   ```bash
   cd backend
   uvicorn main:app --reload --port 8080
   ```

---

## Usage

### API Endpoints

#### 1. Chat with Ollama
```bash
POST /api/v1/ai/chat
Content-Type: application/json

{
  "prompt": "Explain quantum computing in simple terms",
  "provider": "ollama",
  "model": "llama3",
  "temperature": 0.7
}
```

**Response:**
```json
{
  "reply": "Quantum computing uses quantum mechanics principles...",
  "model": "llama3",
  "provider": "ollama",
  "raw": { /* full Ollama response */ }
}
```

#### 2. Check Ollama Health
```bash
GET /api/v1/ollama/health
```

**Response (healthy):**
```json
{
  "status": "healthy",
  "enabled": true,
  "url": "http://localhost:11434",
  "models": ["llama3", "mistral", "codellama"]
}
```

**Response (disabled):**
```json
{
  "status": "disabled",
  "enabled": false
}
```

#### 3. Get Ollama Status
```bash
GET /api/v1/ollama/status
```

**Response:**
```json
{
  "enabled": true,
  "url": "http://localhost:11434",
  "default_model": "llama3",
  "timeout": 60
}
```

---

## Deployment Scenarios

### Scenario 1: Cloud Run with Ollama Sidecar (Not Recommended)
Cloud Run doesn't support sidecars natively. Use GKE instead for this pattern.

### Scenario 2: Cloud Run Backend → External Ollama Server (Recommended)
```bash
# Deploy Ollama on a VM or GKE
# Then configure backend:
gcloud run services update omni-ultra-backend \
  --set-env-vars USE_OLLAMA=true \
  --set-env-vars OLLAMA_URL=http://<ollama-vm-ip>:11434 \
  --set-env-vars OLLAMA_MODEL=llama3
```

### Scenario 3: GKE Deployment with Ollama Pod
```yaml
# k8s/ollama-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
---
apiVersion: v1
kind: Service
metadata:
  name: ollama
spec:
  selector:
    app: ollama
  ports:
  - port: 11434
    targetPort: 11434
```

Then configure backend:
```bash
# In backend ConfigMap or env vars
USE_OLLAMA=true
OLLAMA_URL=http://ollama.default.svc.cluster.local:11434
OLLAMA_MODEL=llama3
```

### Scenario 4: Hybrid (OpenAI/Gemini + Ollama)
```bash
# Backend with fallback logic
USE_OLLAMA=false  # Default to cloud AI
OLLAMA_URL=http://ollama-vm:11434

# Clients can explicitly request Ollama via provider="ollama"
```

---

## Switching Providers

The `/api/v1/ai/chat` endpoint supports multiple providers:

| Provider | Environment | API Request |
|----------|-------------|-------------|
| OpenAI | `OPENAI_API_KEY=sk-...` | `{"provider": "openai"}` |
| Gemini | `GEMINI_API_KEY=...` | `{"provider": "gemini"}` |
| Ollama | `USE_OLLAMA=true` | `{"provider": "ollama"}` |
| Auto | Any of above | `{"provider": "auto"}` or omit |

**Priority:**
1. If `USE_OLLAMA=true` → Always route to Ollama
2. Else if `provider="ollama"` → Route to Ollama
3. Else → Use OmniBrainAdapter (OpenAI/Gemini based on keys)

---

## Troubleshooting

### Issue: "Ollama service unavailable"
**Cause:** Ollama server not running or unreachable.

**Fix:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve

# Verify OLLAMA_URL is correct
echo $OLLAMA_URL
```

### Issue: "Model not found"
**Cause:** Requested model not pulled.

**Fix:**
```bash
# List available models
ollama list

# Pull the model
ollama pull llama3
```

### Issue: Slow responses
**Cause:** Ollama running on CPU or small GPU.

**Fix:**
- Use GPU-enabled VM (e.g., GCE with NVIDIA T4)
- Reduce model size (use `mistral:7b` instead of `llama3:70b`)
- Increase `OLLAMA_TIMEOUT` env var

### Issue: Health check fails
**Cause:** Ollama server unreachable.

**Fix:**
```bash
# Test connectivity
curl http://localhost:11434/api/tags

# Check firewall rules (if remote)
gcloud compute firewall-rules create allow-ollama \
  --allow tcp:11434 \
  --source-ranges 0.0.0.0/0
```

---

## Performance Tips

1. **Use smaller models for faster inference:**
   - `llama3:8b` (8 billion params) → ~2-5s/response
   - `mistral:7b` → ~1-3s/response
   - `phi-2` → ~0.5-1s/response

2. **GPU acceleration:**
   - Ollama auto-detects CUDA/Metal/ROCm
   - Verify: `ollama list` shows GPU usage

3. **Preload models:**
   ```bash
   # Keep model in VRAM
   ollama run llama3 "warmup"
   ```

4. **Batch requests:**
   - Ollama handles concurrent requests efficiently
   - Use async clients to maximize throughput

---

## Monitoring

### Prometheus Metrics
Ollama service automatically registers with existing backend metrics:
- `http_requests_total{endpoint="/api/v1/ai/chat", provider="ollama"}`
- `http_request_duration_seconds{endpoint="/api/v1/ai/chat"}`

### Health Checks
```bash
# Backend health includes Ollama status
curl https://omni-ultra-backend-guzjyv6gfa-ew.a.run.app/api/health

# Ollama-specific health
curl https://omni-ultra-backend-guzjyv6gfa-ew.a.run.app/api/v1/ollama/health
```

---

## Cost Comparison

| Provider | Cost per 1M tokens | Latency | Privacy |
|----------|-------------------|---------|---------|
| OpenAI GPT-4 | $30-60 | 2-5s | ❌ Cloud |
| Gemini Pro | $7-21 | 1-3s | ❌ Cloud |
| **Ollama (local)** | **$0** | 2-10s (CPU) / 0.5-3s (GPU) | ✅ On-prem |

**Recommendation:**
- Development/testing: Use Ollama (no API costs)
- Production (high quality): Use OpenAI/Gemini
- Production (privacy/cost): Use Ollama on GPU VM

---

## Next Steps
1. Set `USE_OLLAMA=true` in `.env`
2. Ensure Ollama server is running (`ollama serve`)
3. Test via `/api/v1/ai/chat` with `provider="ollama"`
4. Monitor `/api/v1/ollama/health` for status
5. For production, deploy Ollama on GKE or GPU VM

---

## References
- [Ollama Documentation](https://ollama.com/docs)
- [Supported Models](https://ollama.com/library)
- [Ollama GitHub](https://github.com/ollama/ollama)
