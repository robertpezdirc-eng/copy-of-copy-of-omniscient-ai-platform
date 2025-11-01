# 🔑 API Keys for TIER 1 Testing

## Demo API Keys

These are **demo keys** included in the codebase for testing purposes. **DO NOT use these in production!**

### Free Tier (100 requests/minute)
```
X-API-Key: demo-free-key-12345
```
- **Tenant ID**: demo-tenant-1
- **Rate Limit**: 100/minute
- **Use Case**: Testing, development

### Pro Tier (1,000 requests/minute)
```
X-API-Key: demo-pro-key-67890
```
- **Tenant ID**: demo-tenant-2
- **Rate Limit**: 1000/minute
- **Use Case**: Production applications

### Enterprise Tier (10,000 requests/minute)
```
X-API-Key: demo-enterprise-key-abcdef
```
- **Tenant ID**: demo-tenant-3
- **Rate Limit**: 10000/minute
- **Use Case**: Large-scale deployments

---

## Usage Examples

### cURL
```bash
curl -X POST https://omni-ai-worker-guzjyv6gfa-ew.a.run.app/predict/revenue-lstm \
  -H "X-API-Key: demo-pro-key-67890" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "my-tenant",
    "time_series": [100, 110, 120, 130, 140, 150, 160, 170, 180, 190],
    "forecast_steps": 5,
    "sequence_length": 5
  }'
```

### Python requests
```python
import requests

response = requests.post(
    "https://omni-ai-worker-guzjyv6gfa-ew.a.run.app/predict/revenue-lstm",
    headers={"X-API-Key": "demo-pro-key-67890"},
    json={
        "tenant_id": "my-tenant",
        "time_series": [100, 110, 120, 130, 140, 150, 160, 170, 180, 190],
        "forecast_steps": 5,
        "sequence_length": 5
    }
)

print(response.json())
```

### JavaScript fetch
```javascript
fetch('https://omni-ai-worker-guzjyv6gfa-ew.a.run.app/predict/revenue-lstm', {
  method: 'POST',
  headers: {
    'X-API-Key': 'demo-pro-key-67890',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    tenant_id: 'my-tenant',
    time_series: [100, 110, 120, 130, 140, 150, 160, 170, 180, 190],
    forecast_steps: 5,
    sequence_length: 5
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

---

## Creating Production API Keys

### Generate Secure Key

```python
from middleware.auth import create_api_key

# Create new API key for customer
api_key = create_api_key(
    tenant_id="customer-abc-123",
    tier="pro",
    name="Customer Production Key"
)

print(f"New API Key: {api_key}")
# Output: omni_pro_a1b2c3d4e5f6...
```

### Recommended Key Management

1. **Store in Secret Manager**
```bash
# Google Cloud Secret Manager
gcloud secrets create customer-api-key-123 \
  --data-file=- <<< "$api_key"
```

2. **Rotate Keys Regularly**
```python
# Revoke old key
from middleware.auth import revoke_api_key
revoke_api_key("old-key-12345")

# Create new key
new_key = create_api_key(tenant_id="customer-123", tier="pro")
```

3. **Track Usage**
```python
# Monitor via Prometheus metrics
# model_requests_total{tenant_id="customer-123"}
```

---

## Rate Limit Testing

### Test Rate Limiting

```python
import requests
import time

api_key = "demo-free-key-12345"  # 100/minute limit
url = "https://omni-ai-worker-guzjyv6gfa-ew.a.run.app/health"

# Send 150 requests rapidly
for i in range(150):
    response = requests.get(
        url,
        headers={"X-API-Key": api_key}
    )
    
    if response.status_code == 429:
        print(f"Rate limited at request {i+1}")
        print(f"Retry after: {response.headers.get('Retry-After')} seconds")
        break
    
    time.sleep(0.1)
```

Expected behavior:
- Requests 1-100: Success (200)
- Request 101+: Rate limited (429)

---

## Security Best Practices

### ⚠️ NEVER commit production API keys to git!

1. **Use environment variables**
```bash
export CUSTOMER_API_KEY="omni_pro_secure_key_here"
```

2. **Use .env file (gitignored)**
```bash
# .env
PRODUCTION_API_KEY=omni_pro_secure_key_here
```

3. **Store in Secret Manager**
```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name prod/omni/api-key \
  --secret-string "$api_key"

# Google Cloud Secret Manager
echo -n "$api_key" | gcloud secrets create omni-api-key --data-file=-
```

4. **Implement key rotation**
- Rotate keys every 90 days
- Track key usage before revoking
- Notify customers of upcoming rotation

---

## Troubleshooting

### "Authentication required" error
```json
{
  "error": "Authentication required",
  "message": "Please provide an API key in the X-API-Key header"
}
```
**Solution**: Add `X-API-Key` header to request

### "Invalid API key" error
```json
{
  "error": "Invalid API key",
  "message": "The provided API key is not valid"
}
```
**Solution**: Check key spelling, ensure it's not revoked

### "Rate limit exceeded" error
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later."
}
```
**Solution**: 
- Wait for rate limit window to reset (1 minute)
- Upgrade to higher tier
- Implement exponential backoff

---

## Master API Key

For administrative access, use the master key:

```bash
# Set in environment
MASTER_API_KEY=your-super-secure-master-key

# Use in requests (bypasses rate limiting)
curl -H "X-API-Key: $MASTER_API_KEY" \
  https://your-api.run.app/endpoint
```

**⚠️ Master key has unlimited access - protect it carefully!**

---

## Next Steps

1. ✅ Test with demo keys
2. ✅ Create production keys
3. ✅ Store keys securely
4. ✅ Monitor usage via metrics
5. ✅ Set up key rotation schedule
6. ✅ Document keys for team

**See `TIER1_README.md` for complete documentation.**
