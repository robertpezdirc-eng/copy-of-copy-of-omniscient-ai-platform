# Omni Enterprise Ultra Max - Backend

High-performance, enterprise-grade FastAPI backend with AI/ML capabilities, multi-tenancy, GDPR compliance, and comprehensive integrations.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- MongoDB 6+ (optional)

### Installation

1. **Clone and navigate to backend:**
```bash
cd backend
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run database migrations:**
```bash
alembic upgrade head
```

5. **Start the server:**
```bash
python main.py
```

The API will be available at `http://localhost:8080`

### Docker Deployment

```bash
# Build
docker build -f Dockerfile.backend -t omni-backend .

# Run
docker run -p 8080:8080 --env-file .env omni-backend
```

### Docker Compose (Recommended for local development)

```bash
# Start all services (backend + databases)
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## 📚 API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8080/api/docs
- **ReDoc**: http://localhost:8080/api/redoc
- **Health Check**: http://localhost:8080/api/health

## 🏗️ Architecture

```
Backend (FastAPI)
├── Routes Layer        → HTTP request handlers
├── Services Layer      → Business logic
├── Models Layer        → Database models
├── Middleware Stack    → Request/response processing
└── Adapters Layer      → External integrations
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed documentation.

## 🔑 Key Features

### AI & Machine Learning
- **Multi-LLM Support**: OpenAI, Anthropic, Ollama
- **RAG (Retrieval-Augmented Generation)**: Advanced document search
- **Embeddings & Vector Search**: FAISS, ChromaDB
- **Autonomous Agents**: Self-learning AI agents
- **Sentiment Analysis**: Real-time text analysis
- **Predictive Analytics**: Time-series forecasting
- **Anomaly Detection**: Outlier detection

### Enterprise Features
- **Multi-tenancy**: Complete tenant isolation
- **RBAC**: Role-based access control
- **GDPR Compliance**: Consent management, DSRs
- **Audit Logging**: Comprehensive activity tracking
- **MFA**: TOTP, SMS, Email, Backup codes
- **API Marketplace**: Monetization platform
- **Affiliate System**: Multi-tier commission tracking

### Analytics & Monitoring
- **Real-time Analytics**: Usage metrics, performance data
- **Custom Reports**: Automated report generation
- **Prometheus Metrics**: Observability integration
- **Performance Monitoring**: Request timing, slow query detection
- **Usage Tracking**: API call tracking and billing

### Integrations
- **Payment Gateways**: Stripe, PayPal, Crypto
- **Communication**: SendGrid, Twilio, Telegram
- **CRM**: Salesforce, HubSpot
- **E-commerce**: Shopify
- **Automation**: Zapier
- **Storage**: GCS, Firestore, IPFS

## 🛠️ Configuration

### Environment Variables

#### Core Settings
```bash
# Server
PORT=8080
UVICORN_RELOAD=0

# Mode Flags
OMNI_MINIMAL=0              # Minimal mode for fast startup
RUN_AS_INTERNAL=0           # Internal mode (behind gateway)
ENABLE_RESPONSE_CACHE=1     # Redis caching
```

#### Database Configuration
```bash
# PostgreSQL (Required)
DATABASE_URL=postgresql://user:pass@localhost:5432/omni
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_RECYCLE=3600

# Redis (Required for caching)
REDIS_URL=redis://localhost:6379

# MongoDB (Optional)
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=omni

# MySQL (Optional)
MYSQL_URL=mysql://user:pass@localhost:3306/omni
```

#### AI & ML Services
```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Ollama (Local LLM)
OLLAMA_BASE_URL=http://localhost:11434
```

#### Payment Gateways
```bash
# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# PayPal
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...
```

#### Communication Services
```bash
# SendGrid (Email)
SENDGRID_API_KEY=SG...

# Twilio (SMS)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
```

#### Google Cloud Platform
```bash
GCP_PROJECT_ID=your-project
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

#### Security
```bash
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
```

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=term --cov-report=html
```

### Run Specific Test Suite
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/test_auth_routes.py -v
```

### Linting
```bash
# Format code
black .

# Check style
flake8 .
```

## 🚀 Deployment

### Cloud Run (Recommended)

```bash
# Build and deploy
gcloud builds submit --config cloudbuild-backend.yaml \
  --substitutions=_PROJECT_ID=your-project,_TAG=v1.0.0
```

### Google Kubernetes Engine (GKE)

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Docker

```bash
# Build image
docker build -f Dockerfile.backend -t omni-backend:latest .

# Push to registry
docker tag omni-backend:latest gcr.io/your-project/omni-backend:latest
docker push gcr.io/your-project/omni-backend:latest

# Deploy
docker run -d \
  --name omni-backend \
  -p 8080:8080 \
  --env-file .env \
  omni-backend:latest
```

## 📊 Monitoring

### Health Endpoints

- **Health Check**: `GET /api/health`
- **System Summary**: `GET /api/v1/omni/summary`
- **Prometheus Metrics**: `GET /metrics` (when enabled)

### Logging

Structured JSON logging with PII redaction:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Processing request", extra={"user_id": "12345", "action": "create"})
```

## 🔐 Security

### Best Practices

1. **Environment Variables**: Never commit `.env` files
2. **API Keys**: Rotate regularly, use secrets manager
3. **Database**: Use strong passwords, enable SSL
4. **JWT**: Use long, random secret keys
5. **HTTPS**: Always use TLS in production
6. **Rate Limiting**: Configure appropriate limits
7. **CORS**: Restrict to known origins

### Security Headers

All responses include:
- Strict-Transport-Security (HSTS)
- X-Content-Type-Options
- X-Frame-Options
- Referrer-Policy
- Content-Security-Policy (Report-Only)

## 🐛 Troubleshooting

### Common Issues

#### "Module not found" errors
```bash
# Ensure you're in the backend directory
cd backend

# Reinstall dependencies
pip install -r requirements.txt
```

#### Database connection failures
```bash
# Check PostgreSQL is running
psql -U user -d omni -c "SELECT 1"

# Verify DATABASE_URL
echo $DATABASE_URL
```

#### Redis connection issues
```bash
# Check Redis is running
redis-cli ping

# Verify REDIS_URL
echo $REDIS_URL
```

#### Slow startup
```bash
# Enable minimal mode
export OMNI_MINIMAL=1
python main.py
```

#### Rate limiting in development
```bash
# Run in internal mode (disables rate limiting)
export RUN_AS_INTERNAL=1
python main.py
```

## 📖 API Examples

### Authentication

```bash
# Register user
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123"}'

# Login
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123"}'
```

### AI Chat

```bash
# Send chat message
curl -X POST http://localhost:8080/api/v1/ai/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello, how are you?","model":"gpt-4"}'
```

### Analytics

```bash
# Get usage metrics
curl -X GET "http://localhost:8080/api/v1/analytics/usage?days=7" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Export data
curl -X POST http://localhost:8080/api/v1/analytics/usage/export \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date":"2024-10-01T00:00:00Z",
    "end_date":"2024-10-31T23:59:59Z",
    "format":"csv"
  }'
```

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Add tests
4. Run linting and tests
5. Submit a pull request

## 📝 License

Proprietary - Omni Enterprise Ultra Max

## 🔗 Related Documentation

- [Architecture Documentation](./ARCHITECTURE.md)
- [MFA Implementation Guide](../MFA_IMPLEMENTATION.md)
- [GDPR Compliance Guide](./GDPR_PERSISTENCE.md)
- [Deployment Guide](./DEPLOYMENT_GKE.md)
- [Gateway Integration](../gateway/README.md)

## 📞 Support

- Documentation: https://docs.omni-ultra.com
- API Reference: http://localhost:8080/api/docs
- Issues: GitHub Issues
- Email: support@omni-ultra.com
