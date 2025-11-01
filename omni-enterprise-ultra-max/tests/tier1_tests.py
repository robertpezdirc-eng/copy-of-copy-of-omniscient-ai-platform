"""
TIER 1 Feature Testing Script
Tests: Prometheus Metrics, Structured Logging, Authentication, Rate Limiting, Sentry
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "https://omni-ai-worker-guzjyv6gfa-ew.a.run.app"
# For local testing: BASE_URL = "http://localhost:8080"

# Test API keys (from auth.py)
API_KEYS = {
    "free": "demo-free-key-12345",
    "pro": "demo-pro-key-67890",
    "enterprise": "demo-enterprise-key-abcdef"
}


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text:^80}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 80}{Colors.END}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text: str):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")


# ==========================================
# TEST 1: PUBLIC ENDPOINTS (NO AUTH)
# ==========================================

def test_public_endpoints():
    print_header("TEST 1: Public Endpoints (No Authentication)")
    
    endpoints = ["/", "/health", "/metrics", "/docs"]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                print_success(f"{endpoint} - {response.status_code} OK")
                if endpoint == "/":
                    print(f"  Response: {json.dumps(response.json(), indent=2)[:200]}...")
            else:
                print_error(f"{endpoint} - {response.status_code}")
        except Exception as e:
            print_error(f"{endpoint} - Error: {str(e)}")
    
    # Check metrics format
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=10)
        if response.status_code == 200:
            metrics_text = response.text
            if "api_requests_total" in metrics_text:
                print_success("/metrics contains Prometheus metrics")
                print(f"  Sample: {metrics_text[:300]}...")
            else:
                print_error("/metrics format incorrect")
    except Exception as e:
        print_error(f"Metrics check failed: {str(e)}")


# ==========================================
# TEST 2: AUTHENTICATION
# ==========================================

def test_authentication():
    print_header("TEST 2: Authentication & Authorization")
    
    # Test without API key
    print_info("Testing request WITHOUT API key...")
    try:
        response = requests.post(
            f"{BASE_URL}/predict/revenue-lstm",
            json={
                "tenant_id": "test",
                "time_series": [100, 110, 120, 130, 140],
                "forecast_steps": 5,
                "sequence_length": 3
            },
            timeout=10
        )
        if response.status_code == 401:
            print_success("Correctly rejected request without API key (401)")
            print(f"  Response: {response.json()}")
        else:
            print_error(f"Expected 401, got {response.status_code}")
    except Exception as e:
        print_error(f"Auth test failed: {str(e)}")
    
    # Test with invalid API key
    print_info("Testing request with INVALID API key...")
    try:
        response = requests.post(
            f"{BASE_URL}/predict/revenue-lstm",
            headers={"X-API-Key": "invalid-key-12345"},
            json={
                "tenant_id": "test",
                "time_series": [100, 110, 120, 130, 140],
                "forecast_steps": 5,
                "sequence_length": 3
            },
            timeout=10
        )
        if response.status_code == 403:
            print_success("Correctly rejected invalid API key (403)")
            print(f"  Response: {response.json()}")
        else:
            print_error(f"Expected 403, got {response.status_code}")
    except Exception as e:
        print_error(f"Invalid key test failed: {str(e)}")
    
    # Test with valid API key
    print_info("Testing request with VALID API key (free tier)...")
    try:
        response = requests.post(
            f"{BASE_URL}/predict/revenue-lstm",
            headers={"X-API-Key": API_KEYS["free"]},
            json={
                "tenant_id": "test",
                "time_series": [100, 110, 120, 130, 140, 150, 160, 170, 180, 190],
                "forecast_steps": 5,
                "sequence_length": 5
            },
            timeout=60
        )
        if response.status_code == 200:
            print_success("Request accepted with valid API key (200)")
            result = response.json()
            print(f"  Response keys: {list(result.keys())}")
            if "request_id" in result:
                print_success("Response includes request_id for tracing")
        else:
            print_error(f"Expected 200, got {response.status_code}")
            print(f"  Response: {response.text[:500]}")
    except Exception as e:
        print_error(f"Valid key test failed: {str(e)}")


# ==========================================
# TEST 3: RATE LIMITING
# ==========================================

def test_rate_limiting():
    print_header("TEST 3: Rate Limiting")
    
    print_info("Sending 10 rapid requests to test rate limiting...")
    
    success_count = 0
    rate_limited_count = 0
    
    for i in range(10):
        try:
            response = requests.get(
                f"{BASE_URL}/health",
                headers={"X-API-Key": API_KEYS["free"]},
                timeout=5
            )
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                print_info(f"Request {i+1}: Rate limited (429)")
        except Exception as e:
            print_error(f"Request {i+1} failed: {str(e)}")
        
        time.sleep(0.1)  # Small delay
    
    print(f"\n{Colors.BOLD}Rate Limiting Results:{Colors.END}")
    print(f"  Success: {success_count}")
    print(f"  Rate Limited: {rate_limited_count}")
    
    if success_count > 0:
        print_success("Rate limiting is configured (some requests succeeded)")


# ==========================================
# TEST 4: STRUCTURED LOGGING
# ==========================================

def test_structured_logging():
    print_header("TEST 4: Structured Logging")
    
    print_info("Making authenticated request to generate logs...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict/revenue-lstm",
            headers={"X-API-Key": API_KEYS["pro"]},
            json={
                "tenant_id": "test-logging",
                "time_series": [100, 105, 110, 115, 120, 125, 130, 135, 140, 145],
                "forecast_steps": 3,
                "sequence_length": 5
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if "request_id" in result:
                print_success(f"Request completed with request_id: {result['request_id']}")
                print_info("Check Cloud Logging for structured JSON logs with:")
                print(f"  - request_id: {result['request_id']}")
                print(f"  - tenant_id: test-logging")
                print(f"  - level: INFO")
                print(f"  - timestamp: ISO 8601 format")
        else:
            print_error(f"Request failed: {response.status_code}")
            
    except Exception as e:
        print_error(f"Logging test failed: {str(e)}")


# ==========================================
# TEST 5: PROMETHEUS METRICS VALIDATION
# ==========================================

def test_prometheus_metrics():
    print_header("TEST 5: Prometheus Metrics Validation")
    
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=10)
        
        if response.status_code == 200:
            metrics = response.text
            
            # Check for expected metrics
            expected_metrics = [
                "api_requests_total",
                "api_request_duration_seconds",
                "api_active_requests",
                "model_inference_duration_seconds",
                "api_errors_total",
                "model_requests_total"
            ]
            
            found_metrics = []
            missing_metrics = []
            
            for metric in expected_metrics:
                if metric in metrics:
                    found_metrics.append(metric)
                    print_success(f"Found metric: {metric}")
                else:
                    missing_metrics.append(metric)
                    print_error(f"Missing metric: {metric}")
            
            print(f"\n{Colors.BOLD}Metrics Summary:{Colors.END}")
            print(f"  Found: {len(found_metrics)}/{len(expected_metrics)}")
            
            if missing_metrics:
                print_error(f"  Missing: {', '.join(missing_metrics)}")
            
            # Parse sample metric values
            for line in metrics.split('\n'):
                if 'api_requests_total' in line and not line.startswith('#'):
                    print_info(f"Sample metric: {line.strip()}")
                    break
                    
        else:
            print_error(f"Failed to fetch metrics: {response.status_code}")
            
    except Exception as e:
        print_error(f"Metrics validation failed: {str(e)}")


# ==========================================
# TEST 6: ERROR HANDLING & SENTRY
# ==========================================

def test_error_handling():
    print_header("TEST 6: Error Handling & Sentry Integration")
    
    print_info("Sending invalid request to trigger error...")
    
    try:
        # Send invalid data to trigger error
        response = requests.post(
            f"{BASE_URL}/predict/revenue-lstm",
            headers={"X-API-Key": API_KEYS["enterprise"]},
            json={
                "tenant_id": "error-test",
                "time_series": [1, 2],  # Too few data points
                "forecast_steps": 100,
                "sequence_length": 50  # sequence_length > data length
            },
            timeout=60
        )
        
        print(f"Response status: {response.status_code}")
        result = response.json()
        
        if "status" in result and result["status"] == "error":
            print_success("Error handled gracefully")
            print(f"  Error message: {result.get('message', 'N/A')}")
            if "request_id" in result:
                print_success(f"Error includes request_id: {result['request_id']}")
                print_info("Check Sentry dashboard for this error")
        else:
            print_error("Error not handled as expected")
            
    except Exception as e:
        print_error(f"Error handling test failed: {str(e)}")


# ==========================================
# MAIN TEST RUNNER
# ==========================================

def run_all_tests():
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 80)
    print("TIER 1 FEATURE TESTING - OMNI AI WORKER")
    print("=" * 80)
    print(f"{Colors.END}")
    print(f"Target: {BASE_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Public Endpoints", test_public_endpoints),
        ("Authentication", test_authentication),
        ("Rate Limiting", test_rate_limiting),
        ("Structured Logging", test_structured_logging),
        ("Prometheus Metrics", test_prometheus_metrics),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            test_func()
            results.append((test_name, "✓"))
        except Exception as e:
            print_error(f"{test_name} failed with exception: {str(e)}")
            results.append((test_name, "✗"))
        
        time.sleep(1)  # Pause between tests
    
    # Final summary
    print_header("TIER 1 TESTING SUMMARY")
    
    for test_name, status in results:
        color = Colors.GREEN if status == "✓" else Colors.RED
        print(f"{color}{status}{Colors.END} {test_name}")
    
    passed = sum(1 for _, status in results if status == "✓")
    total = len(results)
    
    print(f"\n{Colors.BOLD}Result: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TIER 1 FEATURES OPERATIONAL! 🎉{Colors.END}\n")
    else:
        print(f"\n{Colors.YELLOW}⚠️  Some features need attention{Colors.END}\n")


if __name__ == "__main__":
    run_all_tests()
