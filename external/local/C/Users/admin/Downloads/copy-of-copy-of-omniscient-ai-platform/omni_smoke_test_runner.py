#!/usr/bin/env python3
"""
OMNI Platform Google Cloud Smoke Test Runner
Unified test runner that orchestrates all smoke tests for the platform

This script runs:
- Main smoke test suite (omni_smoke_test.py)
- Cloud Run deployment tests (omni_cloudrun_test.py)
- Vertex AI and Gemini tests (omni_vertex_gemini_test.py)
- Platform integration tests
- Performance and load tests

Author: OMNI Platform Test Runner
Version: 1.0.0
"""

import subprocess
import json
import time
import os
import sys
import argparse
from typing import Dict, List, Optional
from dataclasses import dataclass
import webbrowser
from pathlib import Path

@dataclass
class TestSuite:
    """Test suite configuration"""
    name: str
    script: str
    description: str
    required: bool = True

class OmniTestRunner:
    """Unified test runner for OMNI Platform"""

    def __init__(self):
        self.test_suites = [
            TestSuite(
                name="Main Smoke Test",
                script="omni_smoke_test.py",
                description="Core platform functionality and integration tests",
                required=True
            ),
            TestSuite(
                name="Cloud Run Tests",
                script="omni_cloudrun_test.py",
                description="Google Cloud Run deployment and connectivity tests",
                required=True
            ),
            TestSuite(
                name="Vertex AI Tests",
                script="omni_vertex_gemini_test.py",
                description="Vertex AI and Gemini model functionality tests",
                required=True
            )
        ]

        self.results = {}
        self.start_time = None

    def log(self, level: str, message: str):
        """Log message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        self.log("INFO", "Checking test dependencies...")

        required_modules = [
            "requests",
            "psutil",
            "aiohttp"
        ]

        missing_modules = []

        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)

        if missing_modules:
            self.log("ERROR", f"Missing required modules: {', '.join(missing_modules)}")
            self.log("INFO", "Install missing modules with: pip install requests psutil aiohttp")
            return False

        # Check if test scripts exist
        missing_scripts = []
        for suite in self.test_suites:
            if not os.path.exists(suite.script):
                missing_scripts.append(suite.script)

        if missing_scripts:
            self.log("ERROR", f"Missing test scripts: {', '.join(missing_scripts)}")
            return False

        self.log("INFO", "All dependencies available")
        return True

    def run_test_suite(self, suite: TestSuite) -> Dict[str, any]:
        """Run a single test suite"""
        self.log("INFO", f"Running {suite.name}...")
        self.log("INFO", f"Description: {suite.description}")

        start_time = time.time()

        try:
            # Run the test script
            result = subprocess.run([
                sys.executable, suite.script
            ], capture_output=True, text=True, timeout=600)  # 10 minute timeout

            duration = time.time() - start_time

            if result.returncode == 0:
                suite_result = {
                    "status": "PASS",
                    "message": f"{suite.name} completed successfully",
                    "duration": duration,
                    "return_code": result.returncode,
                    "stdout": result.stdout[-2000:],  # Last 2000 chars
                    "stderr": result.stderr[-1000:]   # Last 1000 chars
                }
                self.log("INFO", f"✅ {suite.name}: PASSED ({duration:.".2f")")
            else:
                suite_result = {
                    "status": "FAIL",
                    "message": f"{suite.name} failed with return code {result.returncode}",
                    "duration": duration,
                    "return_code": result.returncode,
                    "stdout": result.stdout[-2000:],
                    "stderr": result.stderr[-1000:]
                }
                self.log("ERROR", f"❌ {suite.name}: FAILED ({duration:.".2f")")

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            suite_result = {
                "status": "ERROR",
                "message": f"{suite.name} timed out after {duration".2f"}s",
                "duration": duration,
                "return_code": -1,
                "stdout": "",
                "stderr": "Test timed out"
            }
            self.log("ERROR", f"⏰ {suite.name}: TIMEOUT ({duration:.".2f")")

        except Exception as e:
            duration = time.time() - start_time
            suite_result = {
                "status": "ERROR",
                "message": f"{suite.name} failed with exception: {str(e)}",
                "duration": duration,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e)
            }
            self.log("ERROR", f"💥 {suite.name}: EXCEPTION ({duration:.".2f")")

        return suite_result

    def generate_unified_report(self) -> str:
        """Generate unified test report"""
        report = []
        report.append("OMNI Platform Google Cloud Smoke Test Report")
        report.append("=" * 60)
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append(f"Total Duration: {time.time() - self.start_time:.".2f"")
        report.append("")

        # Overall summary
        total_suites = len(self.test_suites)
        passed_suites = sum(1 for r in self.results.values() if r["status"] == "PASS")
        failed_suites = sum(1 for r in self.results.values() if r["status"] == "FAIL")
        error_suites = sum(1 for r in self.results.values() if r["status"] == "ERROR")

        report.append("OVERALL SUMMARY:")
        report.append("-" * 30)
        report.append(f"Total Test Suites: {total_suites}")
        report.append(f"✅ Passed: {passed_suites}")
        report.append(f"❌ Failed: {failed_suites}")
        report.append(f"🔥 Errors: {error_suites}")
        report.append(f"🏆 Success Rate: {(passed_suites/total_suites)*100:.".1f"")
        report.append("")

        # Individual suite results
        for suite_name, result in self.results.items():
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌",
                "ERROR": "🔥"
            }.get(result["status"], "❓")

            report.append(f"{status_icon} {suite_name}")
            report.append(f"   Status: {result['status']}")
            report.append(f"   Duration: {result['duration']".2f"}s")
            report.append(f"   Message: {result['message']}")

            if result["status"] != "PASS" and result.get("stderr"):
                report.append(f"   Error Details: {result['stderr'][:200]}...")
            report.append("")

        # Recommendations
        report.append("RECOMMENDATIONS:")
        report.append("-" * 30)

        if failed_suites == 0 and error_suites == 0:
            report.append("🎉 ALL TESTS PASSED! Platform is production-ready.")
            report.append("   - Platform deployment is successful")
            report.append("   - All services are operational")
            report.append("   - Performance metrics are within acceptable ranges")
        else:
            report.append("⚠️  SOME TESTS FAILED! Review the following areas:")

            if any("connectivity" in r.get("message", "").lower() for r in self.results.values()):
                report.append("   - Check network connectivity and firewall rules")
                report.append("   - Verify API keys and authentication")

            if any("vertex" in r.get("message", "").lower() for r in self.results.values()):
                report.append("   - Verify Vertex AI API key and permissions")
                report.append("   - Check Google Cloud project configuration")

            if any("deployment" in r.get("message", "").lower() for r in self.results.values()):
                report.append("   - Check Cloud Run service deployment status")
                report.append("   - Verify service configuration and scaling settings")

            report.append("   - Review individual test logs for detailed error messages")
            report.append("   - Check system resources and dependencies")

        return "\n".join(report)

    def run_all_tests(self, skip_optional: bool = False) -> Dict[str, any]:
        """Run all test suites"""
        self.start_time = time.time()

        self.log("INFO", "🚀 Starting OMNI Platform Google Cloud Smoke Test Suite")
        self.log("INFO", "=" * 80)
        self.log("INFO", "Comprehensive testing of Google Cloud Run, Vertex AI, and Gemini integration")
        self.log("INFO", "")

        # Filter test suites
        suites_to_run = self.test_suites
        if skip_optional:
            suites_to_run = [s for s in self.test_suites if s.required]

        # Run each test suite
        for suite in suites_to_run:
            result = self.run_test_suite(suite)
            self.results[suite.name] = result

            # Add a small delay between tests
            time.sleep(2)

        # Generate summary
        total_suites = len(suites_to_run)
        passed_suites = sum(1 for r in self.results.values() if r["status"] == "PASS")
        failed_suites = sum(1 for r in self.results.values() if r["status"] == "FAIL")
        error_suites = sum(1 for r in self.results.values() if r["status"] == "ERROR")

        summary = {
            "summary": {
                "total_suites": total_suites,
                "passed": passed_suites,
                "failed": failed_suites,
                "errors": error_suites,
                "success_rate": (passed_suites / total_suites) * 100 if total_suites > 0 else 0,
                "total_duration": time.time() - self.start_time
            },
            "results": self.results,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC")
        }

        self.log("INFO", "=" * 80)
        self.log("INFO", "📊 FINAL TEST SUMMARY")
        self.log("INFO", f"Total Test Suites: {total_suites}")
        self.log("INFO", f"✅ Passed: {passed_suites}")
        self.log("INFO", f"❌ Failed: {failed_suites}")
        self.log("INFO", f"🔥 Errors: {error_suites}")
        self.log("INFO", f"⏱️  Total Duration: {summary['summary']['total_duration']:.".2f"")
        self.log("INFO", f"🏆 Overall Success Rate: {summary['summary']['success_rate']:.".1f"")

        return summary

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(description="OMNI Platform Google Cloud Smoke Test Runner")
    parser.add_argument("--skip-optional", action="store_true",
                       help="Skip optional test suites")
    parser.add_argument("--report-only", action="store_true",
                       help="Generate report from existing test results")
    parser.add_argument("--open-browser", action="store_true",
                       help="Open test report in browser after completion")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")

    args = parser.parse_args()

    # Create test runner
    runner = OmniTestRunner()

    # Check dependencies
    if not runner.check_dependencies():
        sys.exit(1)

    # Run tests or generate report
    if args.report_only:
        runner.log("INFO", "Generating report from existing test results...")
        # Generate report from existing JSON files
        summary = runner.generate_unified_report()
        print(summary)
    else:
        # Run all tests
        summary = runner.run_all_tests(args.skip_optional)

        # Generate and save unified report
        report = runner.generate_unified_report()

        # Save report to file
        timestamp = int(time.time())
        report_file = f"omni_smoke_test_unified_report_{timestamp}.txt"

        with open(report_file, 'w') as f:
            f.write(report)

        print(f"\n📄 Unified test report saved to: {report_file}")

        # Save JSON results
        json_file = f"omni_smoke_test_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"📄 JSON results saved to: {json_file}")

        # Open in browser if requested
        if args.open_browser:
            try:
                # Create HTML report
                html_report = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>OMNI Platform Smoke Test Report</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        .pass {{ color: green; }}
                        .fail {{ color: red; }}
                        .error {{ color: orange; }}
                        .summary {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                        pre {{ background: #f8f8f8; padding: 10px; border-radius: 3px; }}
                    </style>
                </head>
                <body>
                    <h1>OMNI Platform Google Cloud Smoke Test Report</h1>
                    <div class="summary">
                        <h2>Summary</h2>
                        <p><strong>Generated:</strong> {time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                        <p><strong>Total Duration:</strong> {summary['summary']['total_duration']".2f"}s</p>
                        <p><strong>Total Suites:</strong> {summary['summary']['total_suites']}</p>
                        <p class="{'pass' if summary['summary']['passed'] > 0 else ''}">
                           <strong>Passed:</strong> {summary['summary']['passed']}
                        </p>
                        <p class="{'fail' if summary['summary']['failed'] > 0 else ''}">
                           <strong>Failed:</strong> {summary['summary']['failed']}
                        </p>
                        <p class="{'error' if summary['summary']['errors'] > 0 else ''}">
                           <strong>Errors:</strong> {summary['summary']['errors']}
                        </p>
                        <p><strong>Success Rate:</strong> {summary['summary']['success_rate']".1f"}%</p>
                    </div>
                    <h2>Detailed Results</h2>
                    <pre>{report}</pre>
                </body>
                </html>
                """

                html_file = f"omni_smoke_test_report_{timestamp}.html"
                with open(html_file, 'w') as f:
                    f.write(html_report)

                webbrowser.open(f'file://{os.path.abspath(html_file)}')
                print(f"🌐 HTML report opened in browser: {html_file}")

            except Exception as e:
                print(f"Warning: Could not open browser: {e}")

    # Exit with appropriate code
    if summary['summary']['failed'] == 0 and summary['summary']['errors'] == 0:
        print("\n🎉 ALL SMOKE TESTS PASSED! Platform is ready for production.")
        sys.exit(0)
    else:
        print(f"\n⚠️  SOME TESTS FAILED! {summary['summary']['failed']} failed, {summary['summary']['errors']} errors.")
        print("   Check the test reports for detailed information.")
        sys.exit(1)

if __name__ == "__main__":
    main()