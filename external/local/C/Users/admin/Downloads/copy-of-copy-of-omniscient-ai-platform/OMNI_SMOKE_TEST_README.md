# OMNI Platform Google Cloud Smoke Test Suite

## Overview

This comprehensive smoke test suite validates the entire Google Cloud Omni Platform, including Google Cloud Run deployment, Vertex AI integration, Gemini model functionality, and all platform components. The suite provides detailed testing and reporting to ensure production readiness.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Internet connection for Google Cloud API access
- Required Python packages (automatically installed)

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements-smoke-test.txt
   ```

2. **Run all tests:**
   ```bash
   # Linux/Mac
   ./run_omni_smoke_tests.sh

   # Windows
   run_omni_smoke_tests.bat
   ```

3. **Run individual tests:**
   ```bash
   python omni_smoke_test.py          # Main smoke tests
   python omni_cloudrun_test.py       # Cloud Run tests
   python omni_vertex_gemini_test.py  # Vertex AI tests
   ```

## 📋 Test Coverage

### 1. Main Smoke Test (`omni_smoke_test.py`)
- ✅ Google Cloud connectivity verification
- ✅ Vertex AI API authentication and response
- ✅ Platform web interface accessibility
- ✅ API endpoints functionality
- ✅ Google Cloud Storage integration
- ✅ Platform modules import and basic functionality
- ✅ System resource monitoring
- ✅ Error handling and recovery mechanisms

### 2. Cloud Run Tests (`omni_cloudrun_test.py`)
- ✅ Service deployment verification
- ✅ Service connectivity and response times
- ✅ Concurrent request handling (50 parallel requests)
- ✅ Service scaling behavior
- ✅ Regional availability testing

### 3. Vertex AI Tests (`omni_vertex_gemini_test.py`)
- ✅ API connectivity and authentication
- ✅ Text generation capabilities (creative, technical, code)
- ✅ Code generation and analysis
- ✅ Concurrent request handling (20 parallel requests)
- ✅ Performance metrics (response times, token generation)
- ✅ Error handling scenarios

### 4. Unified Test Runner (`omni_smoke_test_runner.py`)
- ✅ Orchestrates all test suites
- ✅ Generates comprehensive reports
- ✅ HTML report generation with browser opening
- ✅ JSON results export
- ✅ Cross-platform compatibility

## 🔧 Configuration

### Environment Variables

The tests use the following default configuration:

```bash
export VERTEX_AI_API_KEY="AQ.Ab8RN6LjDXj9_BHBcp-XvbSm0WCE2ftjfwyobHz-Zc3oNMVfhQ"
export GOOGLE_CLOUD_PROJECT="refined-graph-471712-n9"
export GOOGLE_CLOUD_REGION="europe-west1"
export PLATFORM_URL="http://34.140.18.254:8080"
```

### Customization

You can modify the test configuration by editing the test scripts or creating a configuration file:

```python
# Example configuration override
config = SmokeTestConfig(
    platform_url="http://your-domain.com:8080",
    vertex_api_key="your-api-key",
    google_cloud_project="your-project-id"
)
```

## 📊 Test Results and Reports

### Report Types

1. **Text Reports** (`.txt`) - Human-readable summaries
2. **JSON Reports** (`.json`) - Machine-readable results
3. **HTML Reports** (`.html`) - Interactive web reports

### Report Contents

- **Overall Summary**: Pass/fail status, duration, success rates
- **Individual Test Results**: Detailed results for each test case
- **Performance Metrics**: Response times, throughput, error rates
- **Error Details**: Stack traces and troubleshooting information
- **Recommendations**: Actionable suggestions for failed tests

### Example Report Output

```
OMNI Platform Google Cloud Smoke Test Report
==============================================
Generated: 2025-10-19 16:23:45 UTC
Total Duration: 245.67s

OVERALL SUMMARY:
------------------------------
Total Test Suites: 3
✅ Passed: 3
❌ Failed: 0
🔥 Errors: 0
🏆 Success Rate: 100.0%

✅ Main Smoke Test
   Status: PASS
   Duration: 45.23s
   Message: All core functionality tests passed

✅ Cloud Run Tests
   Status: PASS
   Duration: 67.89s
   Message: Deployment and scaling tests successful

✅ Vertex AI Tests
   Status: PASS
   Duration: 132.55s
   Message: All AI functionality tests passed

🎉 ALL TESTS PASSED! Platform is ready for production.
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Authentication Errors
```
Error: Vertex AI connectivity failed: authentication
```
**Solution:**
- Verify API key is valid and has Vertex AI permissions
- Check Google Cloud project configuration
- Ensure proper authentication setup

#### 2. Network Connectivity Issues
```
Error: Cannot connect to platform web interface
```
**Solution:**
- Verify platform URL and port
- Check firewall and network configuration
- Ensure Cloud Run service is deployed and accessible

#### 3. Import Errors
```
Error: No module named 'requests'
```
**Solution:**
- Install missing dependencies: `pip install -r requirements-smoke-test.txt`
- Check Python version compatibility

#### 4. Timeout Errors
```
Error: Request timed out
```
**Solution:**
- Increase timeout values in test configuration
- Check network latency and bandwidth
- Verify service performance and scaling

### Debug Mode

Run tests with verbose output for detailed debugging:

```bash
python omni_smoke_test_runner.py --verbose
```

### Manual Testing

Test individual components manually:

```bash
# Test Vertex AI directly
curl -X POST "https://europe-west1-aiplatform.googleapis.com/v1/projects/refined-graph-471712-n9/locations/europe-west1/publishers/google/models/gemini-2.0-pro:generateContent" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents": [{"parts": [{"text": "Hello!"}]}]}'

# Test platform endpoint
curl http://34.140.18.254:8080/health
```

## 🔍 Advanced Usage

### Custom Test Configuration

```python
from omni_smoke_test import SmokeTestConfig, OmniSmokeTester

# Custom configuration
config = SmokeTestConfig(
    platform_url="http://your-custom-domain.com:8080",
    vertex_api_key="your-custom-api-key",
    google_cloud_project="your-project-id",
    test_timeout=60,  # Longer timeout
    max_retries=5     # More retries
)

# Run with custom config
tester = OmniSmokeTester(config)
results = tester.run_all_tests()
```

### CI/CD Integration

Integrate tests into your deployment pipeline:

```yaml
# GitHub Actions example
name: Smoke Tests
on: [push, pull_request]

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: pip install -r requirements-smoke-test.txt
    - name: Run smoke tests
      run: python omni_smoke_test_runner.py
    - name: Upload reports
      uses: actions/upload-artifact@v3
      with:
        name: smoke-test-reports
        path: omni_smoke_test*.*
```

### Load Testing

For extended load testing beyond smoke tests:

```bash
# Install additional load testing tools
pip install locust

# Run load tests
locust -f load_test_platform.py --host=http://34.140.18.254:8080
```

## 📈 Performance Benchmarks

### Expected Performance Metrics

| Test Type | Metric | Expected Range | Status |
|-----------|--------|---------------|---------|
| API Response | Response Time | < 2 seconds | ✅ Good |
| Concurrent Requests | Success Rate | > 95% | ✅ Good |
| Text Generation | Tokens/Second | > 10 | ✅ Good |
| Platform Load | CPU Usage | < 80% | ✅ Good |
| Memory Usage | RAM Utilization | < 85% | ✅ Good |

### Performance Optimization Tips

1. **Enable Cloud Run concurrency:**
   ```bash
   gcloud run services update omni-platform-service \
     --concurrency 80 \
     --cpu 2 \
     --memory 2Gi
   ```

2. **Configure Vertex AI optimization:**
   ```python
   # Use appropriate temperature and token limits
   generation_config = {
       "temperature": 0.7,
       "max_output_tokens": 1000,
       "top_p": 0.8
   }
   ```

3. **Implement caching:**
   ```python
   # Cache frequent API responses
   from functools import lru_cache

   @lru_cache(maxsize=1000)
   def get_vertex_response(prompt: str):
       # Your Vertex AI call here
       pass
   ```

## 🔒 Security Considerations

### API Key Management

- Store API keys securely (environment variables, secret managers)
- Rotate keys regularly
- Use least-privilege permissions
- Monitor API usage for anomalies

### Network Security

- Use HTTPS for all endpoints
- Implement proper firewall rules
- Enable Cloud Run authentication
- Monitor access logs

### Data Protection

- Encrypt sensitive data in transit and at rest
- Implement proper access controls
- Regular security audits
- Compliance with GDPR, HIPAA, etc.

## 📞 Support and Maintenance

### Regular Testing Schedule

- **Smoke Tests**: Before each deployment
- **Integration Tests**: Daily in staging
- **Load Tests**: Weekly in production
- **Security Tests**: Monthly

### Monitoring and Alerting

Set up monitoring for:
- API response times and error rates
- Platform resource utilization
- Vertex AI quota usage
- Security events and anomalies

### Maintenance Tasks

1. **Update dependencies regularly**
2. **Review and rotate API keys**
3. **Monitor test flakiness**
4. **Update test cases for new features**
5. **Archive old test reports**

## 🎯 Best Practices

### Testing Strategy

1. **Test early and often** - Run smoke tests before deployments
2. **Use realistic data** - Test with production-like scenarios
3. **Monitor performance** - Track metrics over time
4. **Automate everything** - Integrate into CI/CD pipelines
5. **Document failures** - Maintain troubleshooting guides

### Platform Optimization

1. **Right-size Cloud Run instances** based on load patterns
2. **Optimize Vertex AI usage** with appropriate model selection
3. **Implement caching** for frequently accessed data
4. **Use CDN** for static content delivery
5. **Monitor costs** and optimize resource usage

## 📚 Additional Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Gemini API Reference](https://ai.google.dev/api)
- [Python Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)

## 🤝 Contributing

To contribute to the smoke test suite:

1. Fork the repository
2. Create a feature branch
3. Add new test cases or improve existing ones
4. Update documentation
5. Submit a pull request

## 📄 License

This smoke test suite is part of the OMNI Platform and follows the same licensing terms.

---

**🎉 Ready for Production!**

Your OMNI Platform Google Cloud deployment is now thoroughly tested and validated. The comprehensive smoke test suite ensures reliability, performance, and production readiness across all critical components.