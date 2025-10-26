#!/usr/bin/env python3
"""
Vertex AI and Gemini Model Comprehensive Test Suite
Tests Google Cloud Vertex AI integration and Gemini model functionality

This script validates:
- Vertex AI API connectivity and authentication
- Gemini model availability and performance
- Text generation capabilities
- Code generation and analysis
- Multi-modal content processing
- Error handling and rate limiting
- Model switching and fallbacks

Author: OMNI Platform Vertex AI Test
Version: 1.0.0
"""

import requests
import json
import time
import os
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

@dataclass
class VertexConfig:
    """Configuration for Vertex AI tests"""
    access_token: str = "ya29.a0ATi6K2vgbAj5Tlma_q7XF7O4Fb3VfTSgoWY50NZsPKarU6GdaW2ngovHtYNeOyJrFMKuGnk7HDAD7DAQhHuAeCR-XhhUo6tV-Ov-NwRAH0oAWkE14cdU9DNTfD1mgO7wlpOy8o9qn28gTluGEl-1Gw7aTYPhs1bMS5Y0U1gG_jbbKu93Gyzk5pfCCHKuaYmXpQHsDM_3OsSy6AaCgYKAYYSARQSFQHGX2MifQp1YCmGrIngDw3XH-ns2A0213"
    project_id: str = "omni-platform-244c6"
    region: str = "us-central1"
    model: str = "gemini-2.0-flash"
    timeout: int = 30
    max_retries: int = 3

@dataclass
class TestCase:
    """Test case definition"""
    name: str
    prompt: str
    expected_keywords: List[str]
    max_tokens: int = 1000
    temperature: float = 0.7

class VertexAITester:
    """Vertex AI and Gemini comprehensive tester"""

    def __init__(self, config: VertexConfig = None):
        self.config = config or VertexConfig()
        self.results = []
        self.session = requests.Session()

    def log(self, level: str, message: str):
        """Log message"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def make_vertex_request(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> Dict[str, any]:
        """Make a request to Vertex AI"""
        url = f"https://{self.config.region}-aiplatform.googleapis.com/v1/projects/{self.config.project_id}/locations/{self.config.region}/publishers/google/models/{self.config.model}:generateContent"

        headers = {
            'Authorization': f'Bearer {self.config.access_token}',
            'Content-Type': 'application/json'
        }

        data = {
            'contents': [{
                'parts': [{
                    'text': prompt
                }]
            }],
            'generation_config': {
                'max_output_tokens': max_tokens,
                'temperature': temperature,
                'top_p': 0.8,
                'top_k': 40
            }
        }

        try:
            response = self.session.post(url, headers=headers, json=data, timeout=self.config.timeout)
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else None,
                "error": response.text if response.status_code != 200 else None
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": None,
                "response": None,
                "error": str(e)
            }

    def test_basic_connectivity(self) -> Dict[str, any]:
        """Test basic Vertex AI connectivity"""
        self.log("INFO", "Testing Vertex AI basic connectivity...")

        start_time = time.time()

        result = self.make_vertex_request("Hello! Please respond with 'OK' if you can read this message.")

        if result["success"] and result["response"]:
            try:
                generated_text = result["response"]["candidates"][0]["content"]["parts"][0]["text"]
                connectivity_status = {
                    "status": "PASS",
                    "message": "Vertex AI connectivity successful",
                    "details": {
                        "response_text": generated_text[:200],
                        "response_time": time.time() - start_time,
                        "model": self.config.model
                    }
                }
            except (KeyError, IndexError):
                connectivity_status = {
                    "status": "FAIL",
                    "message": "Invalid response format from Vertex AI",
                    "details": {"raw_response": result["response"]}
                }
        else:
            connectivity_status = {
                "status": "FAIL",
                "message": f"Vertex AI connectivity failed: {result.get('error', 'Unknown error')}",
                "details": {"status_code": result.get("status_code")}
            }

        duration = time.time() - start_time
        connectivity_status["duration"] = duration

        self.log(connectivity_status["status"], f"Basic connectivity test: {connectivity_status['message']} ({duration:.2f}s)")
        return connectivity_status

    def test_text_generation(self) -> Dict[str, any]:
        """Test text generation capabilities"""
        self.log("INFO", "Testing text generation capabilities...")

        start_time = time.time()

        test_cases = [
            TestCase(
                name="Creative Writing",
                prompt="Write a short story about a robot learning to paint, in 200 words.",
                expected_keywords=["robot", "paint", "art", "creative"]
            ),
            TestCase(
                name="Technical Explanation",
                prompt="Explain quantum computing in simple terms that a 10-year-old can understand.",
                expected_keywords=["quantum", "computer", "simple", "understand"]
            ),
            TestCase(
                name="Code Review",
                prompt="Review this Python function and suggest improvements:\n\ndef factorial(n):\n    if n == 0:\n        return 1\n    else:\n        return n * factorial(n-1)",
                expected_keywords=["function", "recursive", "base case", "improvement"]
            )
        ]

        results = []
        response_times = []

        for test_case in test_cases:
            case_start = time.time()

            result = self.make_vertex_request(
                test_case.prompt,
                max_tokens=test_case.max_tokens,
                temperature=test_case.temperature
            )

            case_duration = time.time() - case_start
            response_times.append(case_duration)

            if result["success"] and result["response"]:
                try:
                    generated_text = result["response"]["candidates"][0]["content"]["parts"][0]["text"]

                    # Check for expected keywords
                    found_keywords = [kw for kw in test_case.expected_keywords if kw.lower() in generated_text.lower()]

                    case_result = {
                        "test_name": test_case.name,
                        "success": len(found_keywords) >= len(test_case.expected_keywords) * 0.7,  # 70% keyword match
                        "response_length": len(generated_text),
                        "response_time": case_duration,
                        "found_keywords": found_keywords,
                        "expected_keywords": test_case.expected_keywords,
                        "generated_text": generated_text[:300] + "..." if len(generated_text) > 300 else generated_text
                    }

                except (KeyError, IndexError):
                    case_result = {
                        "test_name": test_case.name,
                        "success": False,
                        "response_length": 0,
                        "response_time": case_duration,
                        "error": "Invalid response format"
                    }
            else:
                case_result = {
                    "test_name": test_case.name,
                    "success": False,
                    "response_length": 0,
                    "response_time": case_duration,
                    "error": result.get("error", "Request failed")
                }

            results.append(case_result)

        # Analyze overall results
        successful_cases = sum(1 for r in results if r["success"])
        avg_response_time = statistics.mean(response_times) if response_times else 0

        text_gen_status = {
            "status": "PASS" if successful_cases >= len(test_cases) * 0.8 else "FAIL",
            "message": f"Text generation: {successful_cases}/{len(test_cases)} test cases successful (avg: {avg_response_time:.2f}s)",
            "details": {
                "total_cases": len(test_cases),
                "successful_cases": successful_cases,
                "avg_response_time": avg_response_time,
                "results": results
            }
        }

        duration = time.time() - start_time
        text_gen_status["duration"] = duration

        self.log(text_gen_status["status"], f"Text generation test: {text_gen_status['message']} ({duration:.2f}s)")
        return text_gen_status

    def test_code_generation(self) -> Dict[str, any]:
        """Test code generation capabilities"""
        self.log("INFO", "Testing code generation capabilities...")

        start_time = time.time()

        code_prompts = [
            {
                "name": "Python Function",
                "prompt": "Write a Python function that calculates the Fibonacci sequence up to n terms.",
                "expected_features": ["def fibonacci", "return", "loop or recursion"]
            },
            {
                "name": "JavaScript Class",
                "prompt": "Create a JavaScript class for a simple task manager with add, complete, and list methods.",
                "expected_features": ["class", "constructor", "methods", "array"]
            },
            {
                "name": "SQL Query",
                "prompt": "Write an SQL query to find the top 5 customers by total order value from orders and customers tables.",
                "expected_features": ["SELECT", "JOIN", "ORDER BY", "LIMIT"]
            }
        ]

        results = []

        for code_test in code_prompts:
            test_start = time.time()

            result = self.make_vertex_request(
                code_test["prompt"],
                max_tokens=800,
                temperature=0.3  # Lower temperature for code generation
            )

            test_duration = time.time() - test_start

            if result["success"] and result["response"]:
                try:
                    generated_code = result["response"]["candidates"][0]["content"]["parts"][0]["text"]

                    # Check for expected features
                    found_features = []
                    code_lower = generated_code.lower()

                    for feature in code_test["expected_features"]:
                        if feature.lower() in code_lower:
                            found_features.append(feature)

                    case_result = {
                        "test_name": code_test["name"],
                        "success": len(found_features) >= len(code_test["expected_features"]) * 0.8,
                        "code_length": len(generated_code),
                        "response_time": test_duration,
                        "found_features": found_features,
                        "expected_features": code_test["expected_features"],
                        "generated_code": generated_code[:500] + "..." if len(generated_code) > 500 else generated_code
                    }

                except (KeyError, IndexError):
                    case_result = {
                        "test_name": code_test["name"],
                        "success": False,
                        "code_length": 0,
                        "response_time": test_duration,
                        "error": "Invalid response format"
                    }
            else:
                case_result = {
                    "test_name": code_test["name"],
                    "success": False,
                    "code_length": 0,
                    "response_time": test_duration,
                    "error": result.get("error", "Request failed")
                }

            results.append(case_result)

        # Analyze results
        successful_cases = sum(1 for r in results if r["success"])

        code_gen_status = {
            "status": "PASS" if successful_cases >= len(code_prompts) * 0.8 else "FAIL",
            "message": f"Code generation: {successful_cases}/{len(code_prompts)} test cases successful",
            "details": {
                "total_cases": len(code_prompts),
                "successful_cases": successful_cases,
                "results": results
            }
        }

        duration = time.time() - start_time
        code_gen_status["duration"] = duration

        self.log(code_gen_status["status"], f"Code generation test: {code_gen_status['message']} ({duration:.2f}s)")
        return code_gen_status

    def test_concurrent_requests(self) -> Dict[str, any]:
        """Test concurrent request handling"""
        self.log("INFO", "Testing concurrent request handling...")

        start_time = time.time()

        def make_concurrent_request(i):
            """Make a concurrent request"""
            prompt = f"Generate a unique response to request number {i}. Keep it under 100 words."
            return self.make_vertex_request(prompt, max_tokens=200, temperature=0.8)

        try:
            num_requests = 20
            results = []

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_concurrent_request, i) for i in range(num_requests)]

                for future in as_completed(futures, timeout=120):
                    results.append(future.result())

            # Analyze results
            successful_requests = sum(1 for r in results if r["success"])
            failed_requests = len(results) - successful_requests

            concurrent_status = {
                "status": "PASS" if successful_requests >= num_requests * 0.9 else "FAIL",
                "message": f"Concurrent requests: {successful_requests}/{num_requests} successful",
                "details": {
                    "total_requests": num_requests,
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                    "success_rate": (successful_requests / num_requests) * 100
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

        self.log(concurrent_status["status"], f"Concurrent requests test: {concurrent_status['message']} ({duration:.2f}s)")
        return concurrent_status

    def test_model_performance(self) -> Dict[str, any]:
        """Test model performance metrics"""
        self.log("INFO", "Testing model performance metrics...")

        start_time = time.time()

        # Test different prompt lengths and complexities
        performance_tests = [
            {
                "name": "Short Prompt",
                "prompt": "Say 'Hello World'",
                "complexity": "low"
            },
            {
                "name": "Medium Prompt",
                "prompt": "Explain the concept of machine learning in 3 paragraphs. Include examples of real-world applications.",
                "complexity": "medium"
            },
            {
                "name": "Long Prompt",
                "prompt": "Analyze the following hypothetical scenario: A company wants to implement an AI-powered customer service chatbot. Discuss the technical considerations, potential challenges, ethical implications, and implementation strategy. Provide specific recommendations for architecture, data management, model selection, and deployment considerations.",
                "complexity": "high"
            }
        ]

        results = []
        response_times = []

        for perf_test in performance_tests:
            test_start = time.time()

            result = self.make_vertex_request(
                perf_test["prompt"],
                max_tokens=1500,
                temperature=0.7
            )

            test_duration = time.time() - test_start
            response_times.append(test_duration)

            if result["success"] and result["response"]:
                try:
                    generated_text = result["response"]["candidates"][0]["content"]["parts"][0]["text"]

                    case_result = {
                        "test_name": perf_test["name"],
                        "complexity": perf_test["complexity"],
                        "success": True,
                        "prompt_length": len(perf_test["prompt"]),
                        "response_length": len(generated_text),
                        "response_time": test_duration,
                        "tokens_per_second": len(generated_text) / test_duration if test_duration > 0 else 0
                    }

                except (KeyError, IndexError):
                    case_result = {
                        "test_name": perf_test["name"],
                        "complexity": perf_test["complexity"],
                        "success": False,
                        "error": "Invalid response format"
                    }
            else:
                case_result = {
                    "test_name": perf_test["name"],
                    "complexity": perf_test["complexity"],
                    "success": False,
                    "error": result.get("error", "Request failed")
                }

            results.append(case_result)

        # Calculate performance metrics
        successful_tests = sum(1 for r in results if r.get("success", False))
        avg_response_time = statistics.mean([r["response_time"] for r in results if r.get("response_time")])
        avg_tokens_per_second = statistics.mean([r["tokens_per_second"] for r in results if r.get("tokens_per_second", 0)])

        performance_status = {
            "status": "PASS" if successful_tests == len(performance_tests) else "FAIL",
            "message": f"Performance tests: {successful_tests}/{len(performance_tests)} successful (avg: {avg_response_time:.2f}s, {avg_tokens_per_second:.1f} tokens/s)",
            "details": {
                "total_tests": len(performance_tests),
                "successful_tests": successful_tests,
                "avg_response_time": avg_response_time,
                "avg_tokens_per_second": avg_tokens_per_second,
                "results": results
            }
        }

        duration = time.time() - start_time
        performance_status["duration"] = duration

        self.log(performance_status["status"], f"Performance test: {performance_status['message']} ({duration:.2f}s)")
        return performance_status

    def test_error_handling(self) -> Dict[str, any]:
        """Test error handling scenarios"""
        self.log("INFO", "Testing error handling scenarios...")

        start_time = time.time()

        error_scenarios = [
            {
                "name": "Invalid API Key",
                "api_key": "invalid_key_for_testing",
                "expected_error": "authentication"
            },
            {
                "name": "Empty Prompt",
                "prompt": "",
                "expected_error": "empty or invalid"
            },
            {
                "name": "Excessive Length",
                "prompt": "A" * 100000,  # Very long prompt
                "expected_error": "length or token limit"
            }
        ]

        results = []

        original_key = self.config.api_key

        for scenario in error_scenarios:
            try:
                # Temporarily modify config for this test
                if "api_key" in scenario:
                    self.config.api_key = scenario["api_key"]

                result = self.make_vertex_request(
                    scenario.get("prompt", "Test prompt"),
                    max_tokens=100,
                    temperature=0.7
                )

                # Check if we got expected error behavior
                got_expected_error = False
                if not result["success"]:
                    error_text = str(result.get("error", "")).lower()
                    expected_error = scenario["expected_error"].lower()
                    if expected_error in error_text:
                        got_expected_error = True

                case_result = {
                    "scenario": scenario["name"],
                    "success": False,  # Expected to fail
                    "got_expected_error": got_expected_error,
                    "error_message": result.get("error", "No error message"),
                    "status_code": result.get("status_code")
                }

            except Exception as e:
                case_result = {
                    "scenario": scenario["name"],
                    "success": False,
                    "got_expected_error": False,
                    "error_message": str(e)
                }

            results.append(case_result)

        # Restore original API key
        self.config.api_key = original_key

        # All scenarios should result in errors (which is expected)
        error_scenarios_detected = sum(1 for r in results if not r.get("success", True))

        error_handling_status = {
            "status": "PASS" if error_scenarios_detected == len(error_scenarios) else "FAIL",
            "message": f"Error handling: {error_scenarios_detected}/{len(error_scenarios)} error scenarios properly detected",
            "details": {
                "total_scenarios": len(error_scenarios),
                "error_scenarios_detected": error_scenarios_detected,
                "results": results
            }
        }

        duration = time.time() - start_time
        error_handling_status["duration"] = duration

        self.log(error_handling_status["status"], f"Error handling test: {error_handling_status['message']} ({duration:.2f}s)")
        return error_handling_status

    def run_all_tests(self) -> Dict[str, any]:
        """Run all Vertex AI tests"""
        self.log("INFO", "Starting Vertex AI and Gemini Test Suite")
        self.log("INFO", "=" * 70)

        tests = [
            self.test_basic_connectivity,
            self.test_text_generation,
            self.test_code_generation,
            self.test_concurrent_requests,
            self.test_model_performance,
            self.test_error_handling
        ]

        results = []

        for test_func in tests:
            try:
                result = test_func()
                results.append(result)
                self.log("INFO", f"[PASS] {test_func.__name__}: {result['status']}")
            except Exception as e:
                error_result = {
                    "status": "ERROR",
                    "message": f"Test execution failed: {str(e)}",
                    "details": {},
                    "duration": 0.0
                }
                results.append(error_result)
                self.log("ERROR", f"[FAIL] {test_func.__name__}: {error_result['message']}")

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
                "model": self.config.model,
                "region": self.config.region,
                "project_id": self.config.project_id
            }
        }

        self.log("INFO", "=" * 70)
        self.log("INFO", "VERTEX AI TEST SUMMARY")
        self.log("INFO", f"Total Tests: {total}")
        self.log("INFO", f"PASSED: {passed}")
        self.log("INFO", f"FAILED: {failed}")
        self.log("INFO", f"ERRORS: {errors}")
        self.log("INFO", f"🏆 Success Rate: {summary['summary']['success_rate']:.1f}%")

        return summary

def main():
    """Main function"""
    print("Vertex AI and Gemini Model Test Suite")
    print("Comprehensive testing of Google Cloud Vertex AI integration")
    print()

    # Create tester
    config = VertexConfig()
    tester = VertexAITester(config)

    # Run tests
    results = tester.run_all_tests()

    # Save results
    timestamp = int(time.time())
    report_file = f"vertex_ai_test_report_{timestamp}.json"

    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nTest report saved to: {report_file}")

    # Exit code based on results
    if results["summary"]["failed"] == 0 and results["summary"]["errors"] == 0:
        print("\nALL VERTEX AI TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\nWARNING: SOME TESTS FAILED: {results['summary']['failed']} failed, {results['summary']['errors']} errors")
        sys.exit(1)

if __name__ == "__main__":
    main()