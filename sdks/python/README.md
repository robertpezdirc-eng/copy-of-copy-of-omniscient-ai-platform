# Omni Python SDK

Official Python client library for the Omni Enterprise Ultra Max Platform.

## Installation

```bash
pip install omni-client
```

## Quick Start

```python
from omni_client import OmniClient

# Initialize client with your API key
client = OmniClient(api_key="your-api-key-here")

# Get revenue predictions
predictions = client.intelligence.predict_revenue(user_id="user123")
print(f"Predicted revenue: ${predictions['amount']}")

# Analyze text with AI
analysis = client.ai.analyze_text(
    text="This product is amazing!",
    analysis_type="sentiment"
)
print(f"Sentiment: {analysis['sentiment']}")

# Get analytics dashboard
dashboard = client.analytics.get_dashboard()
print(f"Total users: {dashboard['total_users']}")
```

## Features

- **Type Hints**: Full type hint support for better IDE experience
- **Auto-Retry**: Automatic retry with exponential backoff
- **Error Handling**: Clear exceptions for different error types
- **Rate Limiting**: Automatic rate limit handling
- **Async Support**: Coming soon in v1.1.0

## Services

### Intelligence Service

```python
# Revenue predictions
predictions = client.intelligence.predict_revenue(user_id="123")

# Business insights
insights = client.intelligence.get_business_insights(timeframe="30d")

# Anomaly detection
anomalies = client.intelligence.detect_anomalies(data=data_points)

# Churn prediction
churn = client.intelligence.predict_churn(
    user_id="123",
    features={"activity_score": 0.7, "last_login_days": 10}
)
```

### AI Service

```python
# Text analysis
analysis = client.ai.analyze_text(
    text="Your text here",
    analysis_type="sentiment"  # or "entities", "summary"
)

# Get available models
models = client.ai.get_models()

# Get model details
model_info = client.ai.get_model_details("gpt-4-turbo")
```

### Analytics Service

```python
# Get dashboard data
dashboard = client.analytics.get_dashboard()

# Get specific metrics
metrics = client.analytics.get_metrics(
    metric_names=["active_users", "revenue", "conversion_rate"]
)

# Get dashboard types
types = client.analytics.get_dashboard_types()
```

## Error Handling

```python
from omni_client import OmniClient, OmniAuthError, OmniRateLimitError, OmniAPIError

try:
    client = OmniClient(api_key="your-key")
    result = client.intelligence.predict_revenue()
except OmniAuthError:
    print("Invalid API key")
except OmniRateLimitError as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after}s")
except OmniAPIError as e:
    print(f"API error: {e.message}")
```

## Configuration

```python
client = OmniClient(
    api_key="your-key",
    base_url="https://api.omni-platform.com",  # Custom API endpoint
    timeout=30,  # Request timeout in seconds
    max_retries=3,  # Maximum retry attempts
    retry_delay=1.0  # Initial retry delay in seconds
)
```

## Context Manager

```python
with OmniClient(api_key="your-key") as client:
    predictions = client.intelligence.predict_revenue()
    # Client automatically closes when exiting context
```

## Requirements

- Python 3.8+
- httpx >= 0.24.0

## License

MIT License

## Support

- Documentation: https://docs.omni-platform.com
- Email: support@omni-platform.com
- GitHub Issues: https://github.com/omni-platform/omni-python-sdk/issues
