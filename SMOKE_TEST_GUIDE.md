# OMNI Intelligence Platform - Smoke Test Guide

## Overview

This smoke test suite validates the OMNI Intelligence Platform implementation including:
- ✅ Backend API endpoints (8 RESTful endpoints)
- ✅ Module system (20+ modules)
- ✅ AI Assistant with AI Gateway integration
- ✅ Dashboard KPIs and analytics
- ✅ Frontend pages and navigation

## Quick Start

### Prerequisites

- Python 3.8+
- Backend running on port 8080
- Frontend running on port 8000 (optional)

### Running Tests

```bash
# Make script executable (first time only)
chmod +x test_omni_platform.sh

# Run all smoke tests
./test_omni_platform.sh

# Or run directly with Python
python3 test_omni_platform.py
```

### Starting Services

If services aren't running, start them:

```bash
# Terminal 1: Start Backend
cd backend
python3 -m pip install fastapi uvicorn pydantic requests prometheus-client
AI_GATEWAY_URL=https://ai-gateway-661612368188.europe-west1.run.app python3 -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2: Start Frontend
cd frontend
python3 -m http.server 8000
```

## Test Coverage

### 1. Backend Health Check ✅
- Tests: `/health` endpoint
- Validates: Backend service is running and responding

### 2. Modules API ✅
- Tests: `/api/modules` endpoint
- Validates: Returns 20+ modules with correct structure
- Expected: 20 modules (Sales, Customers, Finance, Marketing, etc.)

### 3. Module Data ✅
- Tests: `/api/modules/{id}/data` endpoint
- Validates: Returns module-specific data and metrics
- Example: Sales module returns revenue, growth, transactions

### 4. Dashboard Overview ✅
- Tests: `/api/dashboard/overview` endpoint
- Validates: Returns KPIs, trends, and AI score
- Expected fields: revenue, uptime, active_users, requests, ai_score

### 5. AI Assistant ✅
- Tests: `/api/ai-assistant` endpoint
- Validates: AI responses with AI Gateway integration
- Features: 
  - AI Gateway integration (primary)
  - Rule-based fallback (when gateway unavailable)
  - Slovenian language support

### 6. Marketplace Categories ✅
- Tests: `/api/marketplace/categories` endpoint
- Validates: Returns module categories for filtering
- Expected: 8+ categories (Business, AI, Finance, etc.)

### 7. Module Activation ✅
- Tests: `/api/modules/{id}/activate` endpoint
- Validates: Module activation/deactivation workflow

### 8. Frontend Accessibility ✅
- Tests: Frontend pages loading correctly
- Pages tested:
  - `/omni-dashboard.html` - Main dashboard
  - `/landing.html` - Landing page
  - `/module-demo.html` - Module demo system

## Test Results

### Example Output

```
============================================================
OMNI Intelligence Platform - Smoke Test Suite
============================================================

[INFO] Backend URL: http://localhost:8080
[INFO] Frontend URL: http://localhost:8000
[INFO] Start time: 2025-11-01 20:49:35

[1/8] Backend Health Check
✓ Backend health check passed

[2/8] Modules API
✓ Modules API returned 20 modules

[3/8] Module Data
✓ Module data endpoint working correctly

[4/8] Dashboard Overview
✓ Dashboard KPIs: Revenue=€21487.37, Uptime=99.94%

[5/8] AI Assistant
✓ AI assistant responding (source: rule_based)

[6/8] Marketplace Categories
✓ Marketplace has 8 categories

[7/8] Module Activation
✓ Module activation working

[8/8] Frontend Accessibility
✓ Main Dashboard accessible
✓ Landing Page accessible
✓ Module Demo accessible

============================================================
TEST SUMMARY
============================================================

PASS   - Backend Health Check
PASS   - Modules API
PASS   - Module Data
PASS   - Dashboard Overview
PASS   - AI Assistant
PASS   - Marketplace Categories
PASS   - Module Activation
PASS   - Frontend Accessibility

RESULTS:
  Total: 8
  Passed: 8
  Failed: 0
  Success Rate: 100.0%
  Duration: 5.32s

✓ ALL TESTS PASSED!
Platform is ready for use.
```

## Configuration

### Custom URLs

Test with custom backend/frontend URLs:

```bash
python3 test_omni_platform.py --backend http://custom-backend:8080 --frontend http://custom-frontend:8000
```

### Environment Variables

Configure AI Gateway and other settings:

```bash
export AI_GATEWAY_URL=https://ai-gateway-661612368188.europe-west1.run.app
export GOOGLE_CLOUD_PROJECT=refined-graph-471712-n9
```

## Troubleshooting

### Backend Not Running

```
✗ Backend health check failed: Connection refused
```

**Solution:**
```bash
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8080
```

### Frontend Not Accessible

```
✗ Main Dashboard not accessible: Connection refused
```

**Solution:**
```bash
cd frontend
python3 -m http.server 8000
```

### Missing Dependencies

```
ModuleNotFoundError: No module named 'requests'
```

**Solution:**
```bash
pip3 install requests
```

### AI Gateway Fallback

If AI Gateway is unavailable, the system automatically falls back to rule-based responses:

```
✓ AI assistant responding (source: rule_based)
```

This is normal and expected when:
- AI Gateway is down for maintenance
- Network connectivity issues
- API rate limits reached

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: OMNI Platform Smoke Tests

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
      run: |
        pip install -r backend/requirements.txt
        pip install requests
    
    - name: Start Backend
      run: |
        cd backend
        python3 -m uvicorn main:app --host 0.0.0.0 --port 8080 &
        sleep 5
    
    - name: Run Smoke Tests
      run: python3 test_omni_platform.py --backend http://localhost:8080
    
    - name: Upload Test Results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: smoke-test-results
        path: test-results/
```

## API Endpoint Reference

### Backend Endpoints Tested

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/modules` | GET | List all modules |
| `/api/modules/{id}` | GET | Get module details |
| `/api/modules/{id}/data` | GET | Get module metrics |
| `/api/modules/{id}/activate` | POST | Activate/deactivate module |
| `/api/dashboard/overview` | GET | Dashboard KPIs |
| `/api/ai-assistant` | POST | AI chat interface |
| `/api/marketplace/categories` | GET | Module categories |

### Expected Response Codes

- ✅ 200 OK - Successful request
- ✅ 201 Created - Resource created
- ⚠️ 400 Bad Request - Invalid input
- ⚠️ 404 Not Found - Resource not found
- ❌ 500 Internal Server Error - Server error

## Performance Expectations

| Test | Expected Duration | Threshold |
|------|------------------|-----------|
| Backend Health | < 1s | ✅ Fast |
| Modules API | < 2s | ✅ Good |
| Module Data | < 2s | ✅ Good |
| Dashboard Overview | < 2s | ✅ Good |
| AI Assistant | < 15s | ✅ Acceptable |
| Marketplace Categories | < 2s | ✅ Good |
| Module Activation | < 2s | ✅ Good |
| Frontend Pages | < 3s | ✅ Good |

**Total Suite Duration**: ~5-10 seconds

## Success Criteria

For the platform to be considered ready:

- ✅ All backend endpoints responding with 200 OK
- ✅ All 20+ modules returning correct data
- ✅ Dashboard KPIs calculating correctly
- ✅ AI Assistant responding (AI Gateway or fallback)
- ✅ Frontend pages loading successfully
- ✅ No critical errors or exceptions

## Next Steps

After smoke tests pass:

1. **Load Testing**: Test with concurrent users
2. **Security Testing**: Validate authentication and authorization
3. **Performance Testing**: Measure response times under load
4. **Integration Testing**: Test complete user workflows
5. **E2E Testing**: Test browser automation scenarios

## Support

For issues or questions:
- Check backend logs: `tail -f backend/logs/app.log`
- Check frontend console: Browser DevTools → Console
- Review API documentation: `http://localhost:8080/docs`

---

**Status**: ✅ Smoke tests implemented and validated

**Last Updated**: 2025-11-01

**Test Coverage**: 8 test cases covering all critical functionality
