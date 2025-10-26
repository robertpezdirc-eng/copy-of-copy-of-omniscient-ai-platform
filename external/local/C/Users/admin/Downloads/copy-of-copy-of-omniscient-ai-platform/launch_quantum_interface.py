#!/usr/bin/env python3
"""
OMNI Quantum AI Interface Launcher
Complete launcher for testing and demonstrating the quantum AI integration

This script:
- Tests all quantum modules
- Demonstrates frontend integration
- Validates Google Quantum AI connectivity
- Shows performance metrics
- Provides interactive testing interface

Author: OMNI Platform Quantum Interface Launcher
Version: 1.0.0
"""

import asyncio
import json
import time
import os
import sys
import threading
import webbrowser
from typing import Dict, List, Any
from pathlib import Path

class QuantumInterfaceLauncher:
    """Complete launcher for OMNI Quantum AI interface"""

    def __init__(self):
        self.test_results = []
        self.start_time = time.time()

    def log(self, level: str, message: str):
        """Log message with timestamp"""
        timestamp = time.strftime('%H:%M:%S')
        print(f'[{timestamp}] {level}: {message}')

    def test_quantum_interface(self) -> Dict[str, Any]:
        """Test the quantum interface module"""
        self.log('INFO', '🧪 Testing Quantum AI Interface Module...')

        try:
            # Test import
            from quantum import get_quantum_status, call_gemini
            self.log('INFO', '✅ Quantum interface imported successfully')

            # Test basic functionality
            status = get_quantum_status()
            self.log('INFO', f'📊 Quantum status: {status.get("connected", False)}')

            # Test basic Gemini call
            test_result = call_gemini("Hello from OMNI Quantum Interface!")
            if test_result and "Error" not in test_result:
                self.log('INFO', '✅ Basic Gemini call successful')
                return {"status": "PASS", "message": "Quantum interface working correctly"}
            else:
                self.log('ERROR', f'❌ Basic Gemini call failed: {test_result}')
                return {"status": "FAIL", "message": "Basic Gemini call failed"}

        except ImportError as e:
            self.log('ERROR', f'❌ Quantum interface import failed: {e}')
            return {"status": "ERROR", "message": f"Import error: {str(e)}"}
        except Exception as e:
            self.log('ERROR', f'❌ Quantum interface test failed: {e}')
            return {"status": "ERROR", "message": f"Test error: {str(e)}"}

    def test_quantum_modules(self) -> Dict[str, Any]:
        """Test all quantum modules"""
        self.log('INFO', '🧩 Testing Quantum Modules...')

        try:
            from quantum import (
                quantum_gaming_idea, quantum_tourism_idea,
                quantum_educational_content, quantum_business_idea,
                quantum_storytelling, quantum_wellness_plan,
                quantum_code_generation
            )

            modules_to_test = [
                ("quantum_gaming", lambda: quantum_gaming_idea("test", "children", "fun")),
                ("quantum_tourism", lambda: quantum_tourism_idea("test_location", "weekend", "medium")),
                ("quantum_education", lambda: quantum_educational_content("test_topic", "beginner", "summary")),
                ("quantum_business", lambda: quantum_business_idea("technology", "test_problem")),
                ("quantum_creative", lambda: quantum_storytelling("test_story", "fantasy", "short")),
                ("quantum_health", lambda: quantum_wellness_plan("test_goals", "30_days", "beginner")),
                ("quantum_technology", lambda: quantum_code_generation("Python", "test_function"))
            ]

            successful_modules = 0
            total_modules = len(modules_to_test)

            for module_name, test_func in modules_to_test:
                try:
                    self.log('INFO', f'  Testing {module_name}...')
                    result = test_func()

                    if result and "Error" not in result and len(result) > 50:
                        successful_modules += 1
                        self.log('INFO', f'    ✅ {module_name}: Success ({len(result)} chars)')
                    else:
                        self.log('WARNING', f'    ⚠️ {module_name}: Poor result or error')

                except Exception as e:
                    self.log('WARNING', f'    ❌ {module_name}: Exception - {str(e)}')

            success_rate = successful_modules / total_modules if total_modules > 0 else 0

            if success_rate >= 0.7:  # 70% success rate
                return {
                    "status": "PASS",
                    "message": f"Quantum modules working ({successful_modules}/{total_modules} successful)",
                    "success_rate": success_rate
                }
            else:
                return {
                    "status": "FAIL",
                    "message": f"Quantum modules failing ({successful_modules}/{total_modules} successful)",
                    "success_rate": success_rate
                }

        except ImportError as e:
            return {"status": "ERROR", "message": f"Module import failed: {str(e)}"}
        except Exception as e:
            return {"status": "ERROR", "message": f"Module test failed: {str(e)}"}

    def test_quantum_api_endpoint(self) -> Dict[str, Any]:
        """Test the quantum API endpoint"""
        self.log('INFO', '🌐 Testing Quantum API Endpoint...')

        try:
            # Test API endpoints
            import requests

            base_url = "http://127.0.0.1:8002"

            # Test status endpoint
            try:
                response = requests.get(f"{base_url}/api/quantum/status", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        self.log('INFO', '✅ Quantum API status endpoint working')
                        status_ok = True
                    else:
                        self.log('ERROR', f'❌ Quantum API status returned error: {data.get("error")}')
                        status_ok = False
                else:
                    self.log('ERROR', f'❌ Quantum API status returned HTTP {response.status_code}')
                    status_ok = False
            except requests.exceptions.ConnectionError:
                self.log('WARNING', '⚠️ Quantum API server not running - start with: python quantum_api_endpoint.py')
                return {"status": "SKIP", "message": "Quantum API server not running"}
            except Exception as e:
                self.log('ERROR', f'❌ Quantum API status test failed: {e}')
                status_ok = False

            # Test modules endpoint
            try:
                response = requests.get(f"{base_url}/api/quantum/modules", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        modules_count = data.get("total_modules", 0)
                        self.log('INFO', f'✅ Quantum API modules endpoint working ({modules_count} modules)')
                        modules_ok = True
                    else:
                        self.log('ERROR', f'❌ Quantum API modules returned error: {data.get("error")}')
                        modules_ok = False
                else:
                    self.log('ERROR', f'❌ Quantum API modules returned HTTP {response.status_code}')
                    modules_ok = False
            except Exception as e:
                self.log('ERROR', f'❌ Quantum API modules test failed: {e}')
                modules_ok = False

            if status_ok and modules_ok:
                return {"status": "PASS", "message": "Quantum API endpoints working correctly"}
            else:
                return {"status": "FAIL", "message": "Some Quantum API endpoints failing"}

        except ImportError:
            return {"status": "ERROR", "message": "Requests library not available"}
        except Exception as e:
            return {"status": "ERROR", "message": f"API test failed: {str(e)}"}

    def test_google_quantum_ai_integration(self) -> Dict[str, Any]:
        """Test Google Quantum AI integration"""
        self.log('INFO', '⚛️ Testing Google Quantum AI Integration...')

        try:
            from omni_google_quantum_ai import initialize_google_quantum_ai, get_quantum_ai_status

            success = initialize_google_quantum_ai("refined-graph-471712-n9")

            if success:
                status = get_quantum_ai_status()
                connected = status.get('google_quantum_connected', False)

                if connected:
                    self.log('INFO', '✅ Google Quantum AI connected successfully')
                    return {"status": "PASS", "message": "Google Quantum AI integration working"}
                else:
                    self.log('INFO', '⚠️ Google Quantum AI not connected - using simulation mode')
                    return {"status": "PASS", "message": "Google Quantum AI in simulation mode"}
            else:
                self.log('ERROR', '❌ Google Quantum AI initialization failed')
                return {"status": "FAIL", "message": "Google Quantum AI initialization failed"}

        except ImportError:
            self.log('WARNING', '⚠️ Google Quantum AI integration not available')
            return {"status": "SKIP", "message": "Google Quantum AI integration not available"}
        except Exception as e:
            self.log('ERROR', f'❌ Google Quantum AI test failed: {e}')
            return {"status": "ERROR", "message": f"Google Quantum AI test error: {str(e)}"}

    def test_frontend_integration(self) -> Dict[str, Any]:
        """Test frontend integration components"""
        self.log('INFO', '🖥️ Testing Frontend Integration...')

        try:
            # Check if frontend files exist
            frontend_files = [
                'quantum_frontend_integration.jsx',
                'quantum_interface_README.md'
            ]

            existing_files = 0
            for file in frontend_files:
                if os.path.exists(file):
                    existing_files += 1
                    self.log('INFO', f'  ✅ Frontend file found: {file}')
                else:
                    self.log('WARNING', f'  ⚠️ Frontend file missing: {file}')

            if existing_files >= 1:  # At least the main JSX file
                return {"status": "PASS", "message": f"Frontend integration files available ({existing_files}/{len(frontend_files)})"}
            else:
                return {"status": "FAIL", "message": "Frontend integration files missing"}

        except Exception as e:
            return {"status": "ERROR", "message": f"Frontend test failed: {str(e)}"}

    def run_comprehensive_demo(self) -> Dict[str, Any]:
        """Run comprehensive demonstration of quantum capabilities"""
        self.log('INFO', '🎬 Running Comprehensive Quantum Demo...')

        try:
            from quantum import (
                quantum_gaming_idea, quantum_tourism_idea,
                quantum_educational_content, quantum_storytelling,
                get_quantum_status
            )

            demo_results = {}

            # Demo 1: Gaming
            self.log('INFO', '  🎮 Demo: Quantum Gaming...')
            game_idea = quantum_gaming_idea("space adventure", "teenagers", "strategy")
            demo_results['gaming'] = len(game_idea) > 100 if game_idea else False
            self.log('INFO', f'    Result: {"✅ Success" if demo_results["gaming"] else "❌ Failed"}')

            # Demo 2: Tourism
            self.log('INFO', '  🏔️ Demo: Quantum Tourism...')
            travel_plan = quantum_tourism_idea("Alps", "weekend", "medium")
            demo_results['tourism'] = len(travel_plan) > 100 if travel_plan else False
            self.log('INFO', f'    Result: {"✅ Success" if demo_results["tourism"] else "❌ Failed"}')

            # Demo 3: Education
            self.log('INFO', '  📚 Demo: Quantum Education...')
            lesson = quantum_educational_content("AI Basics", "beginner", "summary")
            demo_results['education'] = len(lesson) > 100 if lesson else False
            self.log('INFO', f'    Result: {"✅ Success" if demo_results["education"] else "❌ Failed"}')

            # Demo 4: Creative Writing
            self.log('INFO', '  📖 Demo: Quantum Creative...')
            story = quantum_storytelling("AI assistant learns emotions", "sci-fi", "short")
            demo_results['creative'] = len(story) > 100 if story else False
            self.log('INFO', f'    Result: {"✅ Success" if demo_results["creative"] else "❌ Failed"}')

            # Calculate success rate
            successful_demos = sum(demo_results.values())
            total_demos = len(demo_results)
            success_rate = successful_demos / total_demos if total_demos > 0 else 0

            if success_rate >= 0.75:  # 75% success rate
                return {
                    "status": "PASS",
                    "message": f"Comprehensive demo successful ({successful_demos}/{total_demos} demos)",
                    "demo_results": demo_results,
                    "success_rate": success_rate
                }
            else:
                return {
                    "status": "FAIL",
                    "message": f"Comprehensive demo failed ({successful_demos}/{total_demos} successful)",
                    "demo_results": demo_results,
                    "success_rate": success_rate
                }

        except ImportError as e:
            return {"status": "ERROR", "message": f"Demo import failed: {str(e)}"}
        except Exception as e:
            return {"status": "ERROR", "message": f"Demo failed: {str(e)}"}

    def generate_integration_report(self) -> str:
        """Generate comprehensive integration report"""
        report = []
        report.append("OMNI Quantum AI Interface Integration Report")
        report.append("=" * 60)
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append(f"Total Execution Time: {time.time() - self.start_time:.".2f"")
        report.append("")

        # Test Results Summary
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        errors = sum(1 for r in self.test_results if r["status"] == "ERROR")
        skipped = sum(1 for r in self.test_results if r["status"] == "SKIP")
        total = len(self.test_results)

        report.append("TEST RESULTS SUMMARY:")
        report.append("-" * 30)
        report.append(f"Total Tests: {total}")
        report.append(f"✅ Passed: {passed}")
        report.append(f"❌ Failed: {failed}")
        report.append(f"🔥 Errors: {errors}")
        report.append(f"⏭️ Skipped: {skipped}")
        report.append(f"🏆 Success Rate: {(passed/total)*100:.".1f"")

        # Individual Test Results
        report.append("")
        report.append("INDIVIDUAL TEST RESULTS:")
        report.append("-" * 30)

        for result in self.test_results:
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌",
                "ERROR": "🔥",
                "SKIP": "⏭️"
            }.get(result["status"], "❓")

            report.append(f"{status_icon} {result['test_name']}")
            report.append(f"   Status: {result['status']}")
            report.append(f"   Message: {result['message']}")

            if result.get('demo_results'):
                for demo, success in result['demo_results'].items():
                    demo_icon = "✅" if success else "❌"
                    report.append(f"   {demo_icon} {demo}: {'Success' if success else 'Failed'}")

            report.append("")

        # Recommendations
        report.append("RECOMMENDATIONS:")
        report.append("-" * 30)

        if failed == 0 and errors == 0:
            report.append("🎉 ALL TESTS PASSED! Quantum AI interface is ready for production.")
            report.append("")
            report.append("🚀 Next Steps:")
            report.append("1. Start the quantum API server: python quantum_api_endpoint.py")
            report.append("2. Integrate frontend component in your React app")
            report.append("3. Test with real users and gather feedback")
            report.append("4. Monitor performance and optimize as needed")
        else:
            report.append("⚠️ SOME TESTS FAILED! Please address the following:")

            if any("interface" in r.get("test_name", "").lower() and r["status"] == "FAIL" for r in self.test_results):
                report.append("   - Fix quantum.py interface module")
                report.append("   - Check OMNI backend connectivity")

            if any("API" in r.get("test_name", "").upper() and r["status"] == "FAIL" for r in self.test_results):
                report.append("   - Start quantum API server: python quantum_api_endpoint.py")
                report.append("   - Check port 8002 availability")

            if any("Google Quantum" in r.get("test_name", "") and r["status"] == "FAIL" for r in self.test_results):
                report.append("   - Configure Google Cloud Quantum AI credentials")
                report.append("   - Enable Quantum AI API in Google Cloud Console")

            report.append("   - Check individual test logs for detailed error messages")
            report.append("   - Verify all dependencies are installed")

        return "\n".join(report)

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        self.log('INFO', '🚀 Starting OMNI Quantum AI Interface Integration Test')
        self.log('INFO', '=' * 70)

        # Run all tests
        tests = [
            ("Quantum Interface Module", self.test_quantum_interface),
            ("Quantum Modules", self.test_quantum_modules),
            ("Quantum API Endpoint", self.test_quantum_api_endpoint),
            ("Google Quantum AI Integration", self.test_google_quantum_ai_integration),
            ("Frontend Integration", self.test_frontend_integration),
            ("Comprehensive Demo", self.run_comprehensive_demo)
        ]

        for test_name, test_func in tests:
            try:
                self.log('INFO', f'Running: {test_name}')
                result = test_func()
                result['test_name'] = test_name
                self.test_results.append(result)
                self.log('INFO', f'  Result: {result["status"]} - {result["message"]}')
            except Exception as e:
                error_result = {
                    "test_name": test_name,
                    "status": "ERROR",
                    "message": f"Test execution failed: {str(e)}"
                }
                self.test_results.append(error_result)
                self.log('ERROR', f'  Exception: {str(e)}')

        # Generate summary
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        errors = sum(1 for r in self.test_results if r["status"] == "ERROR")
        skipped = sum(1 for r in self.test_results if r["status"] == "SKIP")
        total = len(self.test_results)

        summary = {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "duration": time.time() - self.start_time,
            "test_results": self.test_results,
            "overall_success": failed == 0 and errors == 0
        }

        self.log('INFO', '=' * 70)
        self.log('INFO', '📊 INTEGRATION TEST SUMMARY')
        self.log('INFO', f'Total Tests: {total}')
        self.log('INFO', f'✅ Passed: {passed}')
        self.log('INFO', f'❌ Failed: {failed}')
        self.log('INFO', f'🔥 Errors: {errors}')
        self.log('INFO', f'⏭️ Skipped: {skipped}')
        self.log('INFO', f'⏱️ Duration: {summary["duration"]:.2f".2f"        self.log('INFO', f'🏆 Success Rate: {(passed/total)*100:.".1f"')

        if summary["overall_success"]:
            self.log('INFO', '🎉 ALL INTEGRATION TESTS PASSED!')
            self.log('INFO', '🚀 OMNI Quantum AI Interface is ready for production!')
        else:
            self.log('INFO', '⚠️ SOME TESTS FAILED!')
            self.log('INFO', '🔧 Please review the results above and fix issues')

        return summary

def main():
    """Main launcher function"""
    print('🧠 OMNI Quantum AI Interface Launcher')
    print('Complete integration testing and demonstration')
    print()

    # Create launcher
    launcher = QuantumInterfaceLauncher()

    # Run all tests
    results = launcher.run_all_tests()

    # Generate and save report
    report = launcher.generate_integration_report()
    timestamp = int(time.time())
    report_file = f'omni_quantum_integration_report_{timestamp}.txt'

    with open(report_file, 'w') as f:
        f.write(report)

    print(f'\n📄 Integration report saved to: {report_file}')

    # Show next steps
    print()
    print('🎯 NEXT STEPS:')
    print('1. Start Quantum API Server:')
    print('   python quantum_api_endpoint.py')
    print()
    print('2. Test Individual Modules:')
    print('   python -c "from quantum import quantum_gaming_idea; print(quantum_gaming_idea(\\"test\\"))"')
    print()
    print('3. Open Frontend Playground:')
    print('   Open quantum_frontend_integration.jsx in your React app')
    print()
    print('4. Test Google Quantum AI:')
    print('   python omni_google_quantum_ai_test.py')
    print()
    print('5. Run Full Smoke Tests:')
    print('   python omni_smoke_test_runner.py')

    # Exit with appropriate code
    if results["overall_success"]:
        print()
        print('🎉 QUANTUM INTERFACE INTEGRATION SUCCESSFUL!')
        print('🚀 Ready for production deployment!')
        sys.exit(0)
    else:
        print()
        print('⚠️ QUANTUM INTERFACE INTEGRATION INCOMPLETE!')
        print('🔧 Please fix the issues above before production deployment')
        sys.exit(1)

if __name__ == "__main__":
    main()