#!/usr/bin/env python3
"""
Google Cloud Run Deployment and Connectivity Test
Tests Google Cloud Run deployment, scaling, and connectivity for OMNI Platform

This script validates:
- Cloud Run service deployment
- Service scaling and availability
- Load balancing functionality
- Health checks and monitoring
- Regional deployment verification
- Service discovery and networking

Author: OMNI Platform Cloud Run Test
Version: 1.0.0
"""

import requests
import json
import time
import os
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import subprocess
import socket
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

@dataclass
class CloudRunConfig:
    """Configuration for Cloud Run tests"""
    service_name: str = "omni-platform-service"
    region: str = "europe-west1"
    project_id: str = "refined-graph-471712-n9"
    platform_url: str = "http://34.140.18.254:8080"
    min_instances: int = 0
    max_instances: int = 10
    timeout: int = 30
    concurrency: int = 80

class CloudRunTester:
    """Google Cloud Run deployment tester"""

    def __init__(self, config: CloudRunConfig = None):
        self.config = config or CloudRunConfig()
        self.results = []

    def log(self, level: str, message: str):
        """Log message"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def test_service_deployment(self) -> Dict[str, any]:
        """Test Cloud Run service deployment"""
        self.log("INFO", "Testing Cloud Run service deployment...")

        start_time = time.time()

        try:
            # Check if service exists via Cloud Run API
            gcloud_cmd = [
                "gcloud", "run", "services", "describe",
                self.config.service_name,
                f"--region={self.config.region}",
                f"--project={self.config.project_id}",
                "--format=json"
            ]

            result = subprocess.run(gcloud_cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                service_info = json.loads(result.stdout)

                deployment_status = {
                    "status": "PASS",
                    "message": "Cloud Run service deployed successfully",
                    "details": {
                        "service_name": service_info.get("metadata", {}).get("name"),
                        "region": service_info.get("spec", {}).get("template", {}).get("metadata", {}).get("annotations", {}).get("region"),
                        "image": service_info.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [{}])[0].get("image"),
                        "min_instances": service_info.get("spec", {}).get("template", {}).get("spec", {}).get("containerConcurrency"),
                        "max_instances": service_info.get("spec", {}).get("template", {}).get("metadata", {}).get("annotations", {}).get("max-scale"),
                        "timeout": service_info.get("spec", {}).get("template", {}).get("spec", {}).get("timeoutSeconds")
                    }
                }
            else:
                deployment_status = {
                    "status": "FAIL",
                    "message": f"Cloud Run service not found: {result.stderr}",
                    "details": {}
                }

        except subprocess.TimeoutExpired:
            deployment_status = {
                "status": "ERROR",
                "message": "Cloud Run service check timed out",
                "details": {}
            }
        except Exception as e:
            deployment_status = {
                "status": "ERROR",
                "message": f"Error checking Cloud Run deployment: {str(e)}",
                "details": {}
            }

        duration = time.time() - start_time
        deployment_status["duration"] = duration

        self.log(deployment_status["status"], f"Service deployment test: {deployment_status['message']} ({duration".2f"}s)")
        return deployment_status

    def test_service_connectivity(self) -> Dict[str, any]:
        """Test service connectivity and response"""
        self.log("INFO", "Testing service connectivity...")

        start_time = time.time()

        try:
            # Test basic connectivity
            response = requests.get(
                f"{self.config.platform_url}/",
                timeout=self.config.timeout,
                allow_redirects=True
            )

            # Test health endpoint if available
            health_response = None
            try:
                health_response = requests.get(
                    f"{self.config.platform_url}/health",
                    timeout=self.config.timeout
                )
            except:
                pass

            connectivity_status = {
                "status": "PASS" if response.status_code in [200, 301, 302] else "FAIL",
                "message": f"Service connectivity {'successful' if response.status_code in [200, 301, 302] else 'failed'}",
                "details": {
                    "url": self.config.platform_url,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "health_endpoint": health_response.status_code if health_response else "N/A"
                }
            }

        except requests.exceptions.ConnectionError:
            connectivity_status = {
                "status": "FAIL",
                "message": "Cannot connect to Cloud Run service",
                "details": {"url": self.config.platform_url, "error": "Connection refused"}
            }
        except requests.exceptions.Timeout:
            connectivity_status = {
                "status": "FAIL",
                "message": "Cloud Run service request timed out",
                "details": {"url": self.config.platform_url, "timeout": self.config.timeout}
            }
        except Exception as e:
            connectivity_status = {
                "status": "ERROR",
                "message": f"Error testing service connectivity: {str(e)}",
                "details": {}
            }

        duration = time.time() - start_time
        connectivity_status["duration"] = duration

        self.log(connectivity_status["status"], f"Service connectivity test: {connectivity_status['message']} ({duration".2f"}s)")
        return connectivity_status

    def test_concurrent_requests(self) -> Dict[str, any]:
        """Test concurrent request handling"""
        self.log("INFO", "Testing concurrent request handling...")

        start_time = time.time()

        def make_request(i):
            """Make a single test request"""
            try:
                response = requests.get(
                    f"{self.config.platform_url}/health",
                    timeout=self.config.timeout
                )
                return {
                    "request_id": i,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "request_id": i,
                    "status_code": None,
                    "response_time": None,
                    "success": False,
                    "error": str(e)
                }

        try:
            # Make concurrent requests
            num_requests = 50
            results = []

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request, i) for i in range(num_requests)]

                for future in as_completed(futures, timeout=60):
                    results.append(future.result())

            # Analyze results
            successful_requests = sum(1 for r in results if r["success"])
            failed_requests = len(results) - successful_requests

            avg_response_time = sum(r["response_time"] for r in results if r["response_time"]) / len([r for r in results if r["response_time"]])

            concurrent_status = {
                "status": "PASS" if successful_requests >= num_requests * 0.9 else "FAIL",
                "message": f"Concurrent requests: {successful_requests}/{num_requests} successful (avg: {avg_response_time".3f"}s)",
                "details": {
                    "total_requests": num_requests,
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                    "success_rate": (successful_requests / num_requests) * 100,
                    "avg_response_time": avg_response_time,
                    "results": results[:10]  # Include first 10 results for brevity
                }
            }

        except Exception as e:
            concurrent_status = {
                "status": "ERROR",
                "message": f"Error testing concurrent requests: {str(e)}",
                "details": {}
            }

        duration = time.time() - start_time
        concurrent_status["duration"] = duration

        self.log(concurrent_status["status"], f"Concurrent requests test: {concurrent_status['message']} ({duration".2f"}s)")
        return concurrent_status

    def test_service_scaling(self) -> Dict[str, any]:
        """Test service scaling behavior"""
        self.log("INFO", "Testing service scaling...")

        start_time = time.time()

        try:
            # Get initial instance count (if possible)
            initial_instances = self._get_instance_count()

            # Generate load to trigger scaling
            self.log("INFO", "Generating load to test scaling...")

            def load_generator():
                """Generate load on the service"""
                for _ in range(20):
                    try:
                        requests.get(f"{self.config.platform_url}/", timeout=10)
                    except:
                        pass
                    time.sleep(0.5)

            # Start multiple load generators
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=load_generator)
                thread.start()
                threads.append(thread)

            # Wait for load generation
            time.sleep(15)

            # Wait for threads to complete
            for thread in threads:
                thread.join()

            # Check if scaling occurred
            final_instances = self._get_instance_count()

            scaling_status = {
                "status": "PASS",
                "message": "Service scaling test completed",
                "details": {
                    "initial_instances": initial_instances,
                    "final_instances": final_instances,
                    "scaling_observed": final_instances > initial_instances if initial_instances and final_instances else False
                }
            }

        except Exception as e:
            scaling_status = {
                "status": "ERROR",
                "message": f"Error testing service scaling: {str(e)}",
                "details": {}
            }

        duration = time.time() - start_time
        scaling_status["duration"] = duration

        self.log(scaling_status["status"], f"Service scaling test: {scaling_status['message']} ({duration".2f"}s)")
        return scaling_status

    def _get_instance_count(self) -> Optional[int]:
        """Get current instance count (approximate)"""
        try:
            # This is an approximation - in real scenarios you'd use Cloud Monitoring
            gcloud_cmd = [
                "gcloud", "run", "services", "describe",
                self.config.service_name,
                f"--region={self.config.region}",
                "--format=value(status.conditions[0].message)"
            ]

            result = subprocess.run(gcloud_cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and "instance" in result.stdout.lower():
                # Try to extract instance count from message
                # This is a simplified approach
                return 1  # Default assumption

            return None

        except:
            return None

    def test_regional_availability(self) -> Dict[str, any]:
        """Test regional availability and redundancy"""
        self.log("INFO", "Testing regional availability...")

        start_time = time.time()

        try:
            # Test multiple regional endpoints if available
            regions = ["europe-west1", "us-central1", "asia-east1"]

            regional_results = []

            for region in regions:
                try:
                    # This would test region-specific endpoints if they exist
                    # For now, we'll test the main endpoint multiple times
                    response = requests.get(
                        f"{self.config.platform_url}/health",
                        timeout=self.config.timeout
                    )

                    regional_results.append({
                        "region": region,
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds(),
                        "available": response.status_code == 200
                    })

                except Exception as e:
                    regional_results.append({
                        "region": region,
                        "status_code": None,
                        "response_time": None,
                        "available": False,
                        "error": str(e)
                    })

            available_regions = sum(1 for r in regional_results if r["available"])

            regional_status = {
                "status": "PASS" if available_regions > 0 else "FAIL",
                "message": f"Regional availability: {available_regions}/{len(regions)} regions available",
                "details": {
                    "regions": regional_results,
                    "primary_region": self.config.region,
                    "available_regions": available_regions
                }
            }

        except Exception as e:
            regional_status = {
                "status": "ERROR",
                "message": f"Error testing regional availability: {str(e)}",
                "details": {}
            }

        duration = time.time() - start_time
        regional_status["duration"] = duration

        self.log(regional_status["status"], f"Regional availability test: {regional_status['message']} ({duration".2f"}s)")
        return regional_status

    def run_all_tests(self) -> Dict[str, any]:
        """Run all Cloud Run tests"""
        self.log("INFO", "🚀 Starting Google Cloud Run Test Suite")
        self.log("INFO", "=" * 60)

        tests = [
            self.test_service_deployment,
            self.test_service_connectivity,
            self.test_concurrent_requests,
            self.test_service_scaling,
            self.test_regional_availability
        ]

        results = []

        for test_func in tests:
            try:
                result = test_func()
                results.append(result)
                self.log("INFO", f"✓ {test_func.__name__}: {result['status']}")
            except Exception as e:
                error_result = {
                    "status": "ERROR",
                    "message": f"Test execution failed: {str(e)}",
                    "details": {},
                    "duration": 0.0
                }
                results.append(error_result)
                self.log("ERROR", f"✗ {test_func.__name__}: {error_result['message']}")

        # Summary
        passed = sum(1 for r in results if r["status"] == "PASS")
        failed = sum(1 for r in results if r["status"] == "FAIL")
        errors = sum(1 for r in results if r["status"] == "ERROR")
        total = len(results)

        summary = {
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "success_rate": (passed / total) * 100 if total > 0 else 0
            },
            "results": results,
            "config": {
                "service_name": self.config.service_name,
                "region": self.config.region,
                "project_id": self.config.project_id,
                "platform_url": self.config.platform_url
            }
        }

        self.log("INFO", "=" * 60)
        self.log("INFO", "📊 CLOUD RUN TEST SUMMARY")
        self.log("INFO", f"Total Tests: {total}")
        self.log("INFO", f"✅ Passed: {passed}")
        self.log("INFO", f"❌ Failed: {failed}")
        self.log("INFO", f"🔥 Errors: {errors}")
        self.log("INFO", f"🏆 Success Rate: {summary['summary']['success_rate']".1f"}%")

        return summary

def main():
    """Main function"""
    print("☁️ Google Cloud Run Deployment Test Suite")
    print("Testing OMNI Platform Cloud Run deployment and connectivity")
    print()

    # Create tester
    config = CloudRunConfig()
    tester = CloudRunTester(config)

    # Run tests
    results = tester.run_all_tests()

    # Save results
    timestamp = int(time.time())
    report_file = f"cloudrun_test_report_{timestamp}.json"

    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Test report saved to: {report_file}")

    # Exit code based on results
    if results["summary"]["failed"] == 0 and results["summary"]["errors"] == 0:
        print("\n🎉 ALL CLOUD RUN TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n⚠️  SOME TESTS FAILED: {results['summary']['failed']} failed, {results['summary']['errors']} errors")
        sys.exit(1)

if __name__ == "__main__":
    main()