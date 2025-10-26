#!/usr/bin/env python3
"""
OMNI Platform Google Cloud Smoke Test Suite
Comprehensive testing for Google Cloud Run, Vertex AI, Gemini, and entire platform

This smoke test validates:
- Google Cloud Run deployment and connectivity
- Vertex AI integration and Gemini model functionality
- Google Cloud Storage integration
- Platform dashboard and web interface
- All platform modules and services
- Error handling and recovery mechanisms

Author: OMNI Platform Smoke Test Suite
Version: 1.0.0
"""

import asyncio
import aiohttp
import json
import os
import sys
import time
import requests
import subprocess
import threading
import psutil
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('omni_smoke_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    status: str  # 'PASS', 'FAIL', 'ERROR', 'SKIP'
    duration: float
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

@dataclass
class SmokeTestConfig:
    """Configuration for smoke tests"""
    platform_url: str = "http://34.140.18.254:8080"
    vertex_api_key: str = "AQ.Ab8RN6LjDXj9_BHBcp-XvbSm0WCE2ftjfwyobHz-Zc3oNMVfhQ"
    google_cloud_project: str = "refined-graph-471712-n9"
    google_cloud_region: str = "europe-west1"
    vertex_model: str = "gemini-2.0-pro"
    storage_bucket: str = "omni-singularity-project-storage"
    test_timeout: int = 30
    max_retries: int = 3
    verbose: bool = True

class OmniSmokeTester:
    """Comprehensive smoke test suite for Google Cloud Omni Platform"""

    def __init__(self, config: SmokeTestConfig = None):
        self.config = config or SmokeTestConfig()
        self.results: List[TestResult] = []
        self.start_time = None
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.test_timeout))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def log(self, level: str, message: str):
        """Log message with appropriate level"""
        if self.config.verbose:
            if level == 'INFO':
                logger.info(message)
            elif level == 'ERROR':
                logger.error(message)
            elif level == 'WARNING':
                logger.warning(message)
            else:
                logger.info(message)

    def add_result(self, test_name: str, status: str, duration: float, message: str, details: Dict = None):
        """Add test result"""
        result = TestResult(
            test_name=test_name,
            status=status,
            duration=duration,
            message=message,
            details=details or {},
            timestamp=datetime.now().isoformat()
        )
        self.results.append(result)
        self.log(status, f"[{test_name}] {message} ({duration".2f"}s)")

    def test_google_cloud_connectivity(self) -> TestResult:
        """Test basic Google Cloud connectivity"""
        start_time = time.time()
        test_name = "Google Cloud Connectivity"

        try:
            # Test Google Cloud API endpoint
            response = requests.get(
                "https://www.googleapis.com/storage/v1/b",
                params={"project": self.config.google_cloud_project},
                timeout=self.config.test_timeout
            )

            if response.status_code == 200:
                return TestResult(
                    test_name=test_name,
                    status="PASS",
                    duration=time.time() - start_time,
                    message="Google Cloud connectivity verified"
                )
            else:
                return TestResult(
                    test_name=test_name,
                    status="FAIL",
                    duration=time.time() - start_time,
                    message=f"Google Cloud API returned status {response.status_code}"
                )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                status="ERROR",
                duration=time.time() - start_time,
                message=f"Google Cloud connectivity test failed: {str(e)}"
            )

    def test_vertex_ai_connectivity(self) -> TestResult:
        """Test Vertex AI connectivity and authentication"""
        start_time = time.time()
        test_name = "Vertex AI Connectivity"

        try:
            url = f"https://{self.config.google_cloud_region}-aiplatform.googleapis.com/v1/projects/{self.config.google_cloud_project}/locations/{self.config.google_cloud_region}/publishers/google/models/{self.config.vertex_model}:generateContent"

            headers = {
                'Authorization': f'Bearer {self.config.vertex_api_key}',
                'Content-Type': 'application/json'
            }

            data = {
                'contents': [{
                    'parts': [{
                        'text': 'Hello from OMNI Platform smoke test! Please respond with "OK" if you can read this.'
                    }]
                }]
            }

            response = requests.post(url, headers=headers, json=data, timeout=self.config.test_timeout)

            if response.status_code == 200:
                response_data = response.json()
                if 'candidates' in response_data and len(response_data['candidates']) > 0:
                    return TestResult(
                        test_name=test_name,
                        status="PASS",
                        duration=time.time() - start_time,
                        message="Vertex AI connectivity and authentication successful",
                        details={"response": response_data['candidates'][0]['content']['parts'][0]['text'][:100]}
                    )
                else:
                    return TestResult(
                        test_name=test_name,
                        status="FAIL",
                        duration=time.time() - start_time,
                        message="Vertex AI returned no candidates in response"
                    )
            else:
                return TestResult(
                    test_name=test_name,
                    status="FAIL",
                    duration=time.time() - start_time,
                    message=f"Vertex AI API returned status {response.status_code}: {response.text}"
                )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                status="ERROR",
                duration=time.time() - start_time,
                message=f"Vertex AI connectivity test failed: {str(e)}"
            )

    def test_platform_web_interface(self) -> TestResult:
        """Test platform web interface accessibility"""
        start_time = time.time()
        test_name = "Platform Web Interface"

        try:
            response = requests.get(
                f"{self.config.platform_url}/",
                timeout=self.config.test_timeout,
                allow_redirects=True
            )

            if response.status_code in [200, 301, 302]:
                return TestResult(
                    test_name=test_name,
                    status="PASS",
                    duration=time.time() - start_time,
                    message=f"Platform web interface accessible (status: {response.status_code})",
                    details={"url": self.config.platform_url, "status_code": response.status_code}
                )
            else:
                return TestResult(
                    test_name=test_name,
                    status="FAIL",
                    duration=time.time() - start_time,
                    message=f"Platform web interface returned status {response.status_code}"
                )

        except requests.exceptions.ConnectionError:
            return TestResult(
                test_name=test_name,
                status="FAIL",
                duration=time.time() - start_time,
                message="Cannot connect to platform web interface - service may not be running"
            )
        except Exception as e:
            return TestResult(
                test_name=test_name,
                status="ERROR",
                duration=time.time() - start_time,
                message=f"Platform web interface test failed: {str(e)}"
            )

    def test_platform_api_endpoints(self) -> TestResult:
        """Test platform API endpoints"""
        start_time = time.time()
        test_name = "Platform API Endpoints"

        endpoints = [
            "/health",
            "/status",
            "/api/v1/info",
            "/api/v1/vertex/test"
        ]

        results = []
        for endpoint in endpoints:
            try:
                url = f"{self.config.platform_url}{endpoint}"
                response = requests.get(url, timeout=self.config.test_timeout)

                if response.status_code == 200:
                    results.append(f"{endpoint}: OK ({response.status_code})")
                else:
                    results.append(f"{endpoint}: FAIL ({response.status_code})")

            except Exception as e:
                results.append(f"{endpoint}: ERROR ({str(e)})")

        success_count = sum(1 for r in results if "OK" in r)
        total_count = len(endpoints)

        if success_count == total_count:
            return TestResult(
                test_name=test_name,
                status="PASS",
                duration=time.time() - start_time,
                message=f"All API endpoints accessible ({success_count}/{total_count})",
                details={"endpoints": results}
            )
        elif success_count > 0:
            return TestResult(
                test_name=test_name,
                status="FAIL",
                duration=time.time() - start_time,
                message=f"Some API endpoints failed ({success_count}/{total_count} OK)",
                details={"endpoints": results}
            )
        else:
            return TestResult(
                test_name=test_name,
                status="FAIL",
                duration=time.time() - start_time,
                message="No API endpoints accessible",
                details={"endpoints": results}
            )

    def test_cloud_storage_integration(self) -> TestResult:
        """Test Google Cloud Storage integration"""
        start_time = time.time()
        test_name = "Cloud Storage Integration"

        try:
            # Test if google-cloud-storage is available
            try:
                from google.cloud import storage
                gcs_available = True
            except ImportError:
                gcs_available = False

            if not gcs_available:
                return TestResult(
                    test_name=test_name,
                    status="SKIP",
                    duration=time.time() - start_time,
                    message="Google Cloud Storage library not available"
                )

            # Initialize GCS client
            client = storage.Client()
            bucket = client.bucket(self.config.storage_bucket)

            # Test bucket access
            try:
                # Try to list objects (even if empty)
                list(bucket.list_blobs(max_results=1))
                bucket_accessible = True
            except Exception:
                bucket_accessible = False

            if bucket_accessible:
                # Test write operation
                test_blob_name = f"smoke_test/test_{int(time.time())}.txt"
                test_data = b"OMNI Platform Smoke Test Data"

                blob = bucket.blob(test_blob_name)
                blob.upload_from_string(test_data)

                # Test read operation
                downloaded_data = blob.download_as_text()

                # Clean up
                blob.delete()

                if downloaded_data == test_data.decode():
                    return TestResult(
                        test_name=test_name,
                        status="PASS",
                        duration=time.time() - start_time,
                        message="Cloud Storage read/write operations successful",
                        details={"bucket": self.config.storage_bucket, "test_file": test_blob_name}
                    )
                else:
                    return TestResult(
                        test_name=test_name,
                        status="FAIL",
                        duration=time.time() - start_time,
                        message="Cloud Storage data verification failed"
                    )
            else:
                return TestResult(
                    test_name=test_name,
                    status="FAIL",
                    duration=time.time() - start_time,
                    message=f"Cannot access Cloud Storage bucket: {self.config.storage_bucket}"
                )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                status="ERROR",
                duration=time.time() - start_time,
                message=f"Cloud Storage integration test failed: {str(e)}"
            )

    def test_platform_modules(self) -> TestResult:
        """Test platform modules and services"""
        start_time = time.time()
        test_name = "Platform Modules"

        modules_to_test = [
            "omni_platform_final",
            "omni_vertex_runner",
            "omni_system_optimizer",
            "omni_security_tools",
            "omni_development_tools"
        ]

        results = []
        for module in modules_to_test:
            try:
                # Try to import the module
                __import__(module.replace("-", "_"))
                results.append(f"{module}: IMPORT OK")
            except ImportError as e:
                results.append(f"{module}: IMPORT FAIL ({str(e)})")
            except Exception as e:
                results.append(f"{module}: ERROR ({str(e)})")

        success_count = sum(1 for r in results if "IMPORT OK" in r)
        total_count = len(modules_to_test)

        if success_count == total_count:
            return TestResult(
                test_name=test_name,
                status="PASS",
                duration=time.time() - start_time,
                message=f"All platform modules importable ({success_count}/{total_count})",
                details={"modules": results}
            )
        elif success_count > 0:
            return TestResult(
                test_name=test_name,
                status="FAIL",
                duration=time.time() - start_time,
                message=f"Some platform modules failed ({success_count}/{total_count} OK)",
                details={"modules": results}
            )
        else:
            return TestResult(
                test_name=test_name,
                status="FAIL",
                duration=time.time() - start_time,
                message="No platform modules importable",
                details={"modules": results}
            )

    def test_system_resources(self) -> TestResult:
        """Test system resource availability"""
        start_time = time.time()
        test_name = "System Resources"

        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Check memory usage
            memory = psutil.virtual_memory()

            # Check disk usage
            disk = psutil.disk_usage('/')

            # Check network connectivity
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=5)
                network_ok = True
            except:
                network_ok = False

            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "network_connected": network_ok
            }

            # Define thresholds
            if (cpu_percent < 90 and memory.percent < 90 and
                disk.percent < 95 and network_ok):
                return TestResult(
                    test_name=test_name,
                    status="PASS",
                    duration=time.time() - start_time,
                    message="System resources within acceptable limits",
                    details=details
                )
            else:
                return TestResult(
                    test_name=test_name,
                    status="FAIL",
                    duration=time.time() - start_time,
                    message="System resources outside acceptable limits",
                    details=details
                )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                status="ERROR",
                duration=time.time() - start_time,
                message=f"System resource test failed: {str(e)}"
            )

    def test_error_handling(self) -> TestResult:
        """Test error handling and recovery mechanisms"""
        start_time = time.time()
        test_name = "Error Handling"

        try:
            # Test invalid API key scenario
            original_key = self.config.vertex_api_key
            self.config.vertex_api_key = "invalid_key_for_testing"

            try:
                result = self.test_vertex_ai_connectivity()
                if result.status in ["FAIL", "ERROR"]:
                    error_handling_ok = True
                else:
                    error_handling_ok = False
            finally:
                # Restore original key
                self.config.vertex_api_key = original_key

            # Test invalid URL scenario
            original_url = self.config.platform_url
            self.config.platform_url = "http://invalid-url-that-should-fail"

            try:
                result = self.test_platform_web_interface()
                if result.status in ["FAIL", "ERROR"]:
                    invalid_url_handling_ok = True
                else:
                    invalid_url_handling_ok = False
            finally:
                # Restore original URL
                self.config.platform_url = original_url

            if error_handling_ok and invalid_url_handling_ok:
                return TestResult(
                    test_name=test_name,
                    status="PASS",
                    duration=time.time() - start_time,
                    message="Error handling mechanisms working correctly"
                )
            else:
                return TestResult(
                    test_name=test_name,
                    status="FAIL",
                    duration=time.time() - start_time,
                    message="Error handling mechanisms not working properly"
                )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                status="ERROR",
                duration=time.time() - start_time,
                message=f"Error handling test failed: {str(e)}"
            )

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all smoke tests"""
        self.start_time = datetime.now()
        self.log("INFO", "🚀 Starting OMNI Platform Google Cloud Smoke Test Suite")
        self.log("INFO", "=" * 70)

        # Run all tests
        tests = [
            self.test_google_cloud_connectivity,
            self.test_vertex_ai_connectivity,
            self.test_platform_web_interface,
            self.test_platform_api_endpoints,
            self.test_cloud_storage_integration,
            self.test_platform_modules,
            self.test_system_resources,
            self.test_error_handling
        ]

        for test_func in tests:
            try:
                result = test_func()
                self.add_result(
                    result.test_name,
                    result.status,
                    result.duration,
                    result.message,
                    result.details
                )
            except Exception as e:
                self.add_result(
                    test_func.__name__,
                    "ERROR",
                    0.0,
                    f"Test execution failed: {str(e)}"
                )

        # Generate summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        errors = sum(1 for r in self.results if r.status == "ERROR")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        total = len(self.results)

        summary = {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "duration": duration,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "results": [asdict(r) for r in self.results]
        }

        # Log summary
        self.log("INFO", "=" * 70)
        self.log("INFO", "📊 SMOKE TEST SUMMARY")
        self.log("INFO", f"Total Tests: {total}")
        self.log("INFO", f"✅ Passed: {passed}")
        self.log("INFO", f"❌ Failed: {failed}")
        self.log("INFO", f"🔥 Errors: {errors}")
        self.log("INFO", f"⏭️  Skipped: {skipped}")
        self.log("INFO", f"⏱️  Duration: {duration:.2".2f")
        self.log("INFO", f"🏆 Success Rate: {(passed/total)*100".1f"}%" if total > 0 else "N/A")

        if failed == 0 and errors == 0:
            self.log("INFO", "🎉 ALL TESTS PASSED! Platform is ready for production.")
        else:
            self.log("INFO", "⚠️  SOME TESTS FAILED! Please review the results above.")

        return summary

    def generate_report(self, summary: Dict[str, Any]) -> str:
        """Generate detailed test report"""
        report = []
        report.append("OMNI Platform Google Cloud Smoke Test Report")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Duration: {summary['duration']".2f"}s")
        report.append("")

        # Test Results
        report.append("TEST RESULTS:")
        report.append("-" * 30)

        for result in summary['results']:
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌",
                "ERROR": "🔥",
                "SKIP": "⏭️"
            }.get(result['status'], "❓")

            report.append(f"{status_icon} {result['test_name']}")
            report.append(f"   Status: {result['status']}")
            report.append(f"   Duration: {result['duration']".2f"}s")
            report.append(f"   Message: {result['message']}")

            if result.get('details'):
                for key, value in result['details'].items():
                    report.append(f"   {key}: {value}")

            report.append("")

        # Summary
        report.append("SUMMARY:")
        report.append("-" * 30)
        report.append(f"Total Tests: {summary['total_tests']}")
        report.append(f"Passed: {summary['passed']}")
        report.append(f"Failed: {summary['failed']}")
        report.append(f"Errors: {summary['errors']}")
        report.append(f"Skipped: {summary['skipped']}")

        success_rate = (summary['passed'] / summary['total_tests']) * 100 if summary['total_tests'] > 0 else 0
        report.append(f"Success Rate: {success_rate".1f"}%")

        return "\n".join(report)

def main():
    """Main function to run smoke tests"""
    print("🔥 OMNI Platform Google Cloud Smoke Test Suite")
    print("Testing Google Cloud Run, Vertex AI, Gemini, and entire platform")
    print()

    # Create tester instance
    config = SmokeTestConfig()
    tester = OmniSmokeTester(config)

    # Run all tests
    summary = tester.run_all_tests()

    # Generate and save report
    report = tester.generate_report(summary)

    # Save to file
    report_file = f"omni_smoke_test_report_{int(time.time())}.txt"
    with open(report_file, 'w') as f:
        f.write(report)

    print(f"\n📄 Detailed report saved to: {report_file}")

    # Exit with appropriate code
    if summary['failed'] == 0 and summary['errors'] == 0:
        print("\n🎉 SMOKE TESTS PASSED! Platform is production-ready.")
        sys.exit(0)
    else:
        print(f"\n⚠️  SMOKE TESTS FAILED! {summary['failed']} failed, {summary['errors']} errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()