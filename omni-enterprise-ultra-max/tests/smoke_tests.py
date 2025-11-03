#!/usr/bin/env python3
"""
Omni Enterprise Ultra Max - AGI Services Smoke Tests
Comprehensive testing suite for all deployed AGI capabilities
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import sys

# Configuration
BASE_URL = "https://omni-ai-worker-guzjyv6gfa-ew.a.run.app"
TIMEOUT = 30

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class SmokeTestRunner:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = []
        self.start_time = None
        
    def print_header(self, text: str):
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}\n")
        
    def print_test(self, name: str, status: str, details: str = "", latency: float = 0):
        status_color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
        print(f"[{status_color}{status}{Colors.ENDC}] {name}")
        if details:
            print(f"      └─ {details}")
        if latency > 0:
            print(f"      └─ Latency: {latency:.2f}ms")
        
        self.results.append({
            "test": name,
            "status": status,
            "details": details,
            "latency_ms": latency
        })
    
    def test_health(self) -> bool:
        """Test 0: Health Check"""
        self.print_header("TEST 0: Health Check")
        try:
            start = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=TIMEOUT)
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.print_test("Health Endpoint", "PASS", 
                              f"Status: {data.get('status')}, Service: {data.get('service')}", latency)
                return True
            else:
                self.print_test("Health Endpoint", "FAIL", f"Status code: {response.status_code}", latency)
                return False
        except Exception as e:
            self.print_test("Health Endpoint", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_lstm_forecasting(self) -> bool:
        """Test 1: LSTM Revenue Forecasting"""
        self.print_header("TEST 1: LSTM Neural Networks - Revenue Forecasting")
        try:
            # Prepare test data
            payload = {
                "time_series": [100, 120, 115, 130, 125, 140, 135, 150, 145, 160, 155, 170, 165, 180, 175, 190],
                "forecast_steps": 5,
                "sequence_length": 10,
                "tenant_id": "test_tenant_smoke"
            }
            
            start = time.time()
            response = requests.post(
                f"{self.base_url}/predict/revenue-lstm",
                json=payload,
                timeout=TIMEOUT
            )
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                forecast = data.get('forecast', [])
                training = data.get('training', {})
                
                self.print_test("LSTM Forecast", "PASS", 
                              f"Predictions: {len(forecast)} steps, Loss: {training.get('final_loss', 0):.4f}", latency)
                print(f"      └─ Forecast values: {[round(p, 2) for p in forecast[:3]]}...")
                return True
            else:
                self.print_test("LSTM Forecast", "FAIL", f"Status: {response.status_code}", latency)
                return False
        except Exception as e:
            self.print_test("LSTM Forecast", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_huggingface_search(self) -> bool:
        """Test 2a: HuggingFace Model Search"""
        self.print_header("TEST 2a: HuggingFace Hub - Model Search")
        try:
            payload = {
                "query": "sentiment",
                "task": "text-classification",
                "limit": 3
            }
            
            start = time.time()
            response = requests.post(
                f"{self.base_url}/huggingface/search",
                json=payload,
                timeout=TIMEOUT
            )
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                
                self.print_test("HF Model Search", "PASS", 
                              f"Found {len(models)} models for 'sentiment-analysis'", latency)
                if models:
                    print(f"      └─ Top model: {models[0].get('modelId', 'N/A')}")
                return True
            else:
                self.print_test("HF Model Search", "FAIL", f"Status: {response.status_code}", latency)
                return False
        except Exception as e:
            self.print_test("HF Model Search", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_huggingface_inference(self) -> bool:
        """Test 2b: HuggingFace Inference"""
        self.print_header("TEST 2b: HuggingFace Hub - Inference")
        try:
            payload = {
                "model_id": "distilbert-base-uncased-finetuned-sst-2-english",
                "input_text": "This AGI platform is absolutely amazing!",
                "task": "text-classification"
            }
            
            start = time.time()
            response = requests.post(
                f"{self.base_url}/huggingface/inference",
                json=payload,
                timeout=TIMEOUT
            )
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                self.print_test("HF Inference", "PASS", 
                              f"Result: {str(data)[:60]}...", latency)
                return True
            else:
                self.print_test("HF Inference", "FAIL", f"Status: {response.status_code}", latency)
                return False
        except Exception as e:
            self.print_test("HF Inference", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_anomaly_detection(self) -> bool:
        """Test 3: Isolation Forest Anomaly Detection"""
        self.print_header("TEST 3: Isolation Forest - Anomaly Detection")
        try:
            # Normal data with a few anomalies
            payload = {
                "data": [
                    {"x": 10, "y": 20}, {"x": 12, "y": 22}, {"x": 11, "y": 21}, {"x": 13, "y": 23},  # Normal
                    {"x": 100, "y": 200},  # Anomaly
                    {"x": 14, "y": 24}, {"x": 15, "y": 25}, {"x": 13, "y": 22},  # Normal
                    {"x": 200, "y": 300},  # Anomaly
                    {"x": 12, "y": 23}, {"x": 11, "y": 20}  # Normal
                ],
                "tenant_id": "test_tenant_smoke"
            }
            
            start = time.time()
            response = requests.post(
                f"{self.base_url}/anomaly/isolation-forest",
                json=payload,
                timeout=TIMEOUT
            )
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                predictions = data.get('predictions', [])
                anomalies = [i for i, p in enumerate(predictions) if p == -1]
                
                self.print_test("Anomaly Detection", "PASS", 
                              f"Detected {len(anomalies)} anomalies out of {len(predictions)} points", latency)
                print(f"      └─ Anomaly indices: {anomalies}")
                return True
            else:
                self.print_test("Anomaly Detection", "FAIL", f"Status: {response.status_code}", latency)
                return False
        except Exception as e:
            self.print_test("Anomaly Detection", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_hybrid_recommendations(self) -> bool:
        """Test 4: Hybrid Recommendation System"""
        self.print_header("TEST 4: Hybrid Recommendations (FAISS + Neo4j + Behavioral)")
        try:
            payload = {
                "user_id": "test_user_smoke",
                "tenant_id": "test_tenant_smoke",
                "context": {
                    "recent_views": ["product_1", "product_2"],
                    "preferences": ["electronics", "gadgets"]
                },
                "limit": 5
            }
            
            start = time.time()
            response = requests.post(
                f"{self.base_url}/recommend/products",
                json=payload,
                timeout=TIMEOUT
            )
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get('recommendations', [])
                
                self.print_test("Hybrid Recommendations", "PASS", 
                              f"Generated {len(recommendations)} recommendations", latency)
                if recommendations:
                    print(f"      └─ Top recommendation: {recommendations[0].get('item_id')} (score: {recommendations[0].get('score', 0):.3f})")
                    print(f"      └─ Reasoning: {recommendations[0].get('reasoning', 'N/A')[:60]}...")
                return True
            else:
                self.print_test("Hybrid Recommendations", "FAIL", f"Status: {response.status_code}", latency)
                return False
        except Exception as e:
            self.print_test("Hybrid Recommendations", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_swarm_optimization(self) -> bool:
        """Test 5: Swarm Intelligence"""
        self.print_header("TEST 5: Swarm Intelligence - Task Coordination")
        try:
            payload = {
                "goal": "Optimize task execution across distributed workers",
                "context": {
                    "tasks": [
                        {"id": "task_1", "priority": 5, "duration": 10},
                        {"id": "task_2", "priority": 8, "duration": 5},
                        {"id": "task_3", "priority": 3, "duration": 15}
                    ],
                    "workers": 2
                }
            }
            
            start = time.time()
            response = requests.post(
                f"{self.base_url}/swarm/coordinate",
                json=payload,
                timeout=TIMEOUT
            )
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                self.print_test("Swarm Coordination", "PASS", 
                              f"Status: {data.get('status')}", latency)
                return True
            else:
                self.print_test("Swarm Optimization", "FAIL", f"Status: {response.status_code}", latency)
                return False
        except Exception as e:
            self.print_test("Swarm Optimization", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_autonomous_agents(self) -> bool:
        """Test 6: Autonomous Agents"""
        self.print_header("TEST 6: Autonomous Agents - Observe & Status")
        try:
            # Test agent observation
            payload = {
                "observation": {
                    "event": "system_alert",
                    "details": "CPU usage spike detected",
                    "severity": "medium"
                },
                "agent_roles": ["learner", "healer"]
            }
            
            start = time.time()
            response = requests.post(
                f"{self.base_url}/agents/observe",
                json=payload,
                timeout=TIMEOUT
            )
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                self.print_test("Agent Observation", "PASS", 
                              f"Status: {data.get('status')}, Agents: {data.get('n_agents', 0)}", latency)
            else:
                self.print_test("Agent Observation", "FAIL", f"Status: {response.status_code}", latency)
                return False
            
            # Get agent status
            start = time.time()
            response = requests.get(
                f"{self.base_url}/agents/status",
                timeout=TIMEOUT
            )
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.print_test("Agent Status", "PASS", 
                              f"Total agents: {data.get('n_agents', 0)}", latency)
                return True
            else:
                self.print_test("Agent Status", "FAIL", f"Status: {response.status_code}", latency)
                return False
            
        except Exception as e:
            self.print_test("Autonomous Agents", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_agi_framework(self) -> bool:
        """Test 7: AGI Framework"""
        self.print_header("TEST 7: AGI Framework - Reasoning, Planning, Execution")
        try:
            payload = {
                "problem": "Optimize system resource allocation for peak performance",
                "reasoning_method": "chain_of_thought",
                "context": {
                    "current_cpu": 75,
                    "current_memory": 60,
                    "target_latency": 100
                }
            }
            
            start = time.time()
            response = requests.post(
                f"{self.base_url}/agi/process",
                json=payload,
                timeout=TIMEOUT
            )
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                self.print_test("AGI Processing", "PASS", 
                              f"Status: {data.get('status')}, Method: {data.get('reasoning_method')}", latency)
                return True
            else:
                self.print_test("AGI Processing", "FAIL", f"Status: {response.status_code}", latency)
                return False
        except Exception as e:
            self.print_test("AGI Processing", "FAIL", f"Error: {str(e)}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        avg_latency = sum(r['latency_ms'] for r in self.results) / total_tests if total_tests > 0 else 0
        
        self.print_header("TEST SUMMARY")
        print(f"Total Tests: {total_tests}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.ENDC}")
        print(f"{Colors.RED}Failed: {failed}{Colors.ENDC}")
        print(f"Success Rate: {(passed/total_tests*100):.1f}%")
        print(f"Average Latency: {avg_latency:.2f}ms")
        print(f"Total Duration: {(time.time() - self.start_time):.2f}s")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "success_rate": passed/total_tests*100 if total_tests > 0 else 0,
                "average_latency_ms": avg_latency,
                "total_duration_seconds": time.time() - self.start_time
            },
            "detailed_results": self.results
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Execute all smoke tests"""
        self.start_time = time.time()
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}")
        print("╔════════════════════════════════════════════════════════════╗")
        print("║   OMNI ENTERPRISE ULTRA MAX - AGI SMOKE TEST SUITE        ║")
        print("║   Comprehensive Testing of All Deployed AGI Services      ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}")
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Run all tests
        self.test_health()
        self.test_lstm_forecasting()
        self.test_huggingface_search()
        self.test_huggingface_inference()
        self.test_anomaly_detection()
        self.test_hybrid_recommendations()
        self.test_swarm_optimization()
        self.test_autonomous_agents()
        self.test_agi_framework()
        
        # Generate report
        report = self.generate_report()
        
        # Save report to file
        report_filename = f"smoke_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{Colors.GREEN}Report saved to: {report_filename}{Colors.ENDC}")
        
        return report

def main():
    runner = SmokeTestRunner(BASE_URL)
    report = runner.run_all_tests()
    
    # Exit with appropriate code
    if report['summary']['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
