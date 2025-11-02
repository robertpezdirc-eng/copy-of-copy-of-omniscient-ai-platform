# Ollama Integration & CI/CD Guide

## Overview

This guide covers the two major enhancements to the Omni Platform:
- **Option A**: Ollama Integration - Local AI provider with automatic fallback
- **Option B**: CI/CD Pipeline - Automated deployment to Google Cloud Run

---

## Option A: Ollama Integration

### Configuration

Set these environment variables in your `.env` file or deployment environment:

```bash
# Enable Ollama as the primary AI provider
USE_OLLAMA=true

# Ollama server URL (default: http://localhost:11434)
OLLAMA_URL=http://localhost:11434
OLLAMA_BASE_URL=http://localhost:11434

# Default model to use
OLLAMA_MODEL=qwen3-coder:30b
```

### Features

#### 1. Unified AI Generation Endpoint

**POST** `/api/ai/generate`

Automatically uses Ollama if enabled, falls back to LangChain providers (OpenAI, etc.) if Ollama fails or is disabled.

Request:
```json
{
  "prompt": "Explain quantum computing",
  "model": "qwen3-coder:30b",
  "temperature": 0.7,
  "max_tokens": 500
}
```

Response:
```json
{
  "provider": "ollama",
  "model": "qwen3-coder:30b",
  "response": "Quantum computing is...",
  "success": true
}
```

#### 2. AI Provider Status

**GET** `/api/ai/status`

Check which AI providers are available and their configuration.

Response:
```json
{
  "ollama": {
    "enabled": true,
    "url": "http://localhost:11434",
    "available": true
  },
  "langchain": {
    "available": true
  }
}
```

#### 3. Direct Ollama Endpoints

- **GET** `/api/ollama/health` - Check Ollama server health
- **GET** `/api/ollama/models` - List available Ollama models
- **POST** `/api/ollama/generate` - Direct Ollama generation
- **POST** `/api/ollama/chat` - Direct Ollama chat

### Fallback Logic

1. If `USE_OLLAMA=true`, try Ollama first
2. If Ollama fails or is disabled, fall back to LangChain providers
3. Return appropriate error if no providers are available

### Running Locally with Ollama

1. Install Ollama: https://ollama.ai
2. Pull a model: `ollama pull qwen3-coder:30b`
3. Start Ollama: `ollama serve`
4. Set environment variables:
   ```bash
   export USE_OLLAMA=true
   export OLLAMA_URL=http://localhost:11434
   ```
5. Start the backend: `cd backend && uvicorn main:app --reload`

---

## Option B: CI/CD Pipeline

### Overview

Automated deployment to Google Cloud Run using GitHub Actions.

### Prerequisites

1. **Google Cloud Project** with Cloud Run API enabled
2. **Service Account** with appropriate permissions:
   - Cloud Run Admin
   - Service Account User
   - Storage Admin (for Container Registry)

3. **GitHub Secrets** (Repository Settings → Secrets and variables → Actions):
   - `GCP_PROJECT_ID` - Your Google Cloud project ID
   - `GCP_SA_KEY` - Service account JSON key (entire file content)

4. **GitHub Variables** (optional):
   - `GCP_REGION` - Deployment region (default: europe-west1)
   - `SERVICE_NAME` - Cloud Run service name (default: omni-backend)
   - `USE_OLLAMA` - Enable Ollama in production (default: false)
   - `OLLAMA_URL` - Ollama server URL for production

### Workflow Triggers

The CI/CD pipeline automatically runs on:
- Push to `main` branch
- Push to `master` branch
- Manual trigger (workflow_dispatch)

### Deployment Process

1. **Checkout code** - Gets the latest code from the repository
2. **Setup Google Cloud SDK** - Configures gcloud CLI
3. **Authenticate** - Uses service account credentials
4. **Build & Deploy** - Builds Docker image and deploys to Cloud Run
5. **Run Smoke Tests** - Validates deployment with health checks

### Smoke Tests

The pipeline automatically runs these tests after deployment:

1. **Health Check**: `GET /api/health` - Ensures the service is responding
2. **AI Status Check**: `GET /api/ai/status` - Validates AI provider configuration

### Manual Deployment

You can also deploy manually using the script:

```bash
# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="europe-west1"
export SERVICE_NAME="omni-backend"
export USE_OLLAMA="false"

# Run deployment script
./scripts/deploy/deploy-cloud-run.sh
```

### Monitoring Deployment

After deployment, the pipeline outputs:
- Service URL
- Deployment status
- Smoke test results

View logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=omni-backend" --limit 50
```

Check service status:
```bash
gcloud run services describe omni-backend --region=europe-west1
```

---

## Testing

### Running Tests Locally

```bash
# Install dependencies
pip install pytest httpx fastapi uvicorn requests prometheus-client

# Run Ollama integration tests
pytest tests/test_ollama_integration.py -v

# Run all tests
pytest tests/ -v
```

### Test Coverage

The new test suite includes:
- AI status endpoint validation
- Ollama configuration checks
- Environment variable handling
- Provider fallback logic
- Health endpoint verification
- Mock tests for Ollama responses

All 8 tests pass successfully! ✅

---

## Configuration Summary

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `USE_OLLAMA` | Enable Ollama as primary AI provider | `false` | No |
| `OLLAMA_URL` | Ollama server URL | `http://localhost:11434` | No |
| `OLLAMA_BASE_URL` | Alternative URL variable | `http://localhost:11434` | No |
| `OLLAMA_MODEL` | Default model to use | `qwen3-coder:30b` | No |

### GitHub Secrets (for CI/CD)

| Secret | Description | Required |
|--------|-------------|----------|
| `GCP_PROJECT_ID` | Google Cloud project ID | Yes |
| `GCP_SA_KEY` | Service account JSON key | Yes |

### GitHub Variables (for CI/CD)

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_REGION` | Deployment region | `europe-west1` |
| `SERVICE_NAME` | Cloud Run service name | `omni-backend` |
| `USE_OLLAMA` | Enable Ollama in production | `false` |
| `OLLAMA_URL` | Production Ollama URL | `http://localhost:11434` |

---

## Troubleshooting

### Ollama Connection Issues

1. Verify Ollama is running: `curl http://localhost:11434`
2. Check Ollama logs: `journalctl -u ollama -f` (Linux) or check Ollama app logs
3. Verify the model is pulled: `ollama list`
4. Test model directly: `ollama run qwen3-coder:30b "Hello"`

### CI/CD Deployment Issues

1. Check GitHub Actions logs in the Actions tab
2. Verify Google Cloud authentication
3. Ensure service account has required permissions
4. Check Cloud Run service logs in Google Cloud Console
5. Verify secrets are correctly set in GitHub repository settings

### API Errors

1. Check `/api/ai/status` to see which providers are available
2. Review backend logs for error details
3. Verify environment variables are set correctly
4. Test with direct Ollama endpoints first if debugging Ollama issues

---

## Next Steps

1. **Production Deployment**: Configure GitHub secrets and push to main branch
2. **Monitoring**: Set up Cloud Monitoring alerts for the deployed service
3. **Scaling**: Adjust Cloud Run min/max instances based on traffic
4. **Custom Domain**: Configure a custom domain for your service
5. **Authentication**: Add authentication for production use (service is currently public)

---

## Support

For issues or questions:
1. Check the logs: Backend logs or Cloud Run logs
2. Review test results: Run local tests to verify functionality
3. Consult documentation: Google Cloud Run docs, Ollama docs
4. Check environment: Verify all environment variables are set correctly
