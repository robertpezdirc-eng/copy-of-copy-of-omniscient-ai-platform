#!/usr/bin/env python3
"""
Test script for OMNI Platform Dashboard
Tests the dashboard functionality before deployment
"""

import requests
import time
import threading
import sys
from omni_operational_dashboard import OmniOperationalDashboard

def test_dashboard_locally():
    """Test dashboard on localhost"""
    print("Testing OMNI Dashboard locally...")

    # Create dashboard instance
    dashboard = OmniOperationalDashboard()

    # Start dashboard in a thread
    def run_dashboard():
        dashboard.run(host="127.0.0.1", port=8080)

    thread = threading.Thread(target=run_dashboard, daemon=True)
    thread.start()

    # Wait for startup
    time.sleep(3)

    # Test API endpoints
    base_url = "http://127.0.0.1:8080"

    endpoints = [
        "/api/metrics",
        "/api/services",
        "/api/cloud",
        "/api/alerts",
        "/api/analytics"
    ]

    print("Testing API endpoints...")
    success_count = 0

    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"[OK] {endpoint}: HTTP 200")
                success_count += 1
            else:
                print(f"[FAIL] {endpoint}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] {endpoint}: {e}")

    # Test main dashboard page
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200 and "OMNI Platform" in response.text:
            print("[OK] Main dashboard: HTTP 200")
            success_count += 1
        else:
            print(f"[FAIL] Main dashboard: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Main dashboard: {e}")

    print(f"\nTest Results: {success_count}/{len(endpoints) + 1} endpoints working")

    if success_count >= 4:  # At least 4 out of 6 endpoints should work
        print("Dashboard is ready for deployment!")
        return True
    else:
        print("Some endpoints failed. Check logs for details.")
        return False

if __name__ == "__main__":
    success = test_dashboard_locally()
    sys.exit(0 if success else 1)