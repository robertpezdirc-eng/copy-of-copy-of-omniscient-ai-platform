#!/usr/bin/env python3
"""
OMNI Intelligence Platform Smoke Test
Tests the complete platform including frontend, backend, and AI assistant
"""

import sys
import requests
import time
from datetime import datetime
from typing import Dict, List, Tuple

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class OmniPlatformTester:
    """Smoke test runner for OMNI Intelligence Platform"""
    
    def __init__(self, backend_url: str = "http://localhost:8080", frontend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.results = []
        self.start_time = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with color coding"""
        color = {
            "INFO": Colors.BLUE,
            "SUCCESS": Colors.GREEN,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED
        }.get(level, "")
        print(f"{color}[{level}]{Colors.END} {message}")
    
    def test_backend_health(self) -> bool:
        """Test backend health endpoint"""
        try:
            self.log("Testing backend health endpoint...")
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            
            if response.status_code == 200:
                self.log("✓ Backend health check passed", "SUCCESS")
                return True
            else:
                self.log(f"✗ Backend health check failed: HTTP {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ Backend health check failed: {str(e)}", "ERROR")
            return False
    
    def test_modules_api(self) -> bool:
        """Test modules API endpoint"""
        try:
            self.log("Testing modules API...")
            response = requests.get(f"{self.backend_url}/api/modules", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                modules = data.get("modules", [])
                
                if len(modules) >= 20:
                    self.log(f"✓ Modules API returned {len(modules)} modules", "SUCCESS")
                    return True
                else:
                    self.log(f"✗ Expected 20+ modules, got {len(modules)}", "ERROR")
                    return False
            else:
                self.log(f"✗ Modules API failed: HTTP {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ Modules API test failed: {str(e)}", "ERROR")
            return False
    
    def test_module_data(self) -> bool:
        """Test module data endpoint"""
        try:
            self.log("Testing module data endpoint (sales)...")
            response = requests.get(f"{self.backend_url}/api/modules/sales/data", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for expected fields
                required_fields = ["revenue", "growth", "transactions"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if not missing_fields:
                    self.log("✓ Module data endpoint working correctly", "SUCCESS")
                    return True
                else:
                    self.log(f"✗ Missing fields in response: {missing_fields}", "ERROR")
                    return False
            else:
                self.log(f"✗ Module data test failed: HTTP {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ Module data test failed: {str(e)}", "ERROR")
            return False
    
    def test_dashboard_overview(self) -> bool:
        """Test dashboard overview endpoint"""
        try:
            self.log("Testing dashboard overview...")
            response = requests.get(f"{self.backend_url}/api/dashboard/overview", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for KPI fields
                required_fields = ["kpis", "trends", "ai_score"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if not missing_fields:
                    kpis = data.get("kpis", {})
                    self.log(f"✓ Dashboard KPIs: Revenue=€{kpis.get('revenue', 0):.2f}, Uptime={kpis.get('uptime', 0)}%", "SUCCESS")
                    return True
                else:
                    self.log(f"✗ Missing fields in dashboard: {missing_fields}", "ERROR")
                    return False
            else:
                self.log(f"✗ Dashboard overview failed: HTTP {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ Dashboard overview test failed: {str(e)}", "ERROR")
            return False
    
    def test_ai_assistant(self) -> bool:
        """Test AI assistant endpoint"""
        try:
            self.log("Testing AI assistant...")
            payload = {"message": "Priporoči mi module"}
            response = requests.post(
                f"{self.backend_url}/api/ai-assistant",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "response" in data and "source" in data:
                    source = data.get("source", "unknown")
                    self.log(f"✓ AI assistant responding (source: {source})", "SUCCESS")
                    return True
                else:
                    self.log("✗ AI assistant response missing required fields", "ERROR")
                    return False
            else:
                self.log(f"✗ AI assistant failed: HTTP {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ AI assistant test failed: {str(e)}", "ERROR")
            return False
    
    def test_marketplace_categories(self) -> bool:
        """Test marketplace categories endpoint"""
        try:
            self.log("Testing marketplace categories...")
            response = requests.get(f"{self.backend_url}/api/marketplace/categories", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                categories = data.get("categories", [])
                
                if len(categories) >= 5:
                    self.log(f"✓ Marketplace has {len(categories)} categories", "SUCCESS")
                    return True
                else:
                    self.log(f"✗ Expected 5+ categories, got {len(categories)}", "ERROR")
                    return False
            else:
                self.log(f"✗ Marketplace categories failed: HTTP {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ Marketplace categories test failed: {str(e)}", "ERROR")
            return False
    
    def test_frontend_accessibility(self) -> bool:
        """Test frontend accessibility"""
        try:
            self.log("Testing frontend accessibility...")
            
            pages = [
                ("Main Dashboard", "/omni-dashboard.html"),
                ("Landing Page", "/landing.html"),
                ("Module Demo", "/module-demo.html"),
            ]
            
            all_passed = True
            for name, path in pages:
                try:
                    response = requests.get(f"{self.frontend_url}{path}", timeout=10)
                    if response.status_code == 200:
                        self.log(f"  ✓ {name} accessible", "SUCCESS")
                    else:
                        self.log(f"  ✗ {name} returned HTTP {response.status_code}", "WARNING")
                        all_passed = False
                except Exception as e:
                    self.log(f"  ✗ {name} not accessible: {str(e)}", "WARNING")
                    all_passed = False
            
            return all_passed
        except Exception as e:
            self.log(f"✗ Frontend accessibility test failed: {str(e)}", "ERROR")
            return False
    
    def test_module_activation(self) -> bool:
        """Test module activation endpoint"""
        try:
            self.log("Testing module activation...")
            payload = {"module_id": "sales", "active": True}
            response = requests.post(
                f"{self.backend_url}/api/modules/sales/activate",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log("✓ Module activation working", "SUCCESS")
                    return True
                else:
                    self.log("✗ Module activation response incomplete", "ERROR")
                    return False
            else:
                self.log(f"✗ Module activation failed: HTTP {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ Module activation test failed: {str(e)}", "ERROR")
            return False
    
    def run_all_tests(self) -> Dict:
        """Run all smoke tests"""
        self.start_time = time.time()
        
        print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}OMNI Intelligence Platform - Smoke Test Suite{Colors.END}")
        print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")
        
        self.log(f"Backend URL: {self.backend_url}", "INFO")
        self.log(f"Frontend URL: {self.frontend_url}", "INFO")
        self.log(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", "INFO")
        
        # Define tests
        tests = [
            ("Backend Health Check", self.test_backend_health),
            ("Modules API", self.test_modules_api),
            ("Module Data", self.test_module_data),
            ("Dashboard Overview", self.test_dashboard_overview),
            ("AI Assistant", self.test_ai_assistant),
            ("Marketplace Categories", self.test_marketplace_categories),
            ("Module Activation", self.test_module_activation),
            ("Frontend Accessibility", self.test_frontend_accessibility),
        ]
        
        # Run tests
        passed = 0
        failed = 0
        
        for i, (name, test_func) in enumerate(tests, 1):
            print(f"\n{Colors.BOLD}[{i}/{len(tests)}] {name}{Colors.END}")
            print("-" * 60)
            
            try:
                result = test_func()
                self.results.append((name, "PASS" if result else "FAIL"))
                
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"Test crashed: {str(e)}", "ERROR")
                self.results.append((name, "ERROR"))
                failed += 1
            
            time.sleep(0.5)  # Brief pause between tests
        
        # Print summary
        duration = time.time() - self.start_time
        
        print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")
        
        for name, status in self.results:
            color = Colors.GREEN if status == "PASS" else Colors.RED
            print(f"{color}{status:6}{Colors.END} - {name}")
        
        print(f"\n{Colors.BOLD}RESULTS:{Colors.END}")
        print(f"  Total: {len(tests)}")
        print(f"  {Colors.GREEN}Passed: {passed}{Colors.END}")
        print(f"  {Colors.RED}Failed: {failed}{Colors.END}")
        print(f"  Success Rate: {(passed/len(tests)*100):.1f}%")
        print(f"  Duration: {duration:.2f}s\n")
        
        if failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED!{Colors.END}")
            print(f"{Colors.GREEN}Platform is ready for use.{Colors.END}\n")
            return {"status": "success", "passed": passed, "failed": failed}
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED!{Colors.END}")
            print(f"{Colors.YELLOW}Please review the failures above.{Colors.END}\n")
            return {"status": "failure", "passed": passed, "failed": failed}

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OMNI Platform Smoke Tests")
    parser.add_argument("--backend", default="http://localhost:8080", help="Backend URL")
    parser.add_argument("--frontend", default="http://localhost:8000", help="Frontend URL")
    args = parser.parse_args()
    
    tester = OmniPlatformTester(args.backend, args.frontend)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results["status"] == "success" else 1)

if __name__ == "__main__":
    main()
