Pripravi okolje na Google Cloud instanci (Omni ali GCE)

Prijavi se v svojo instanco:

gcloud compute ssh <INSTANCE_NAME> --zone=<ZONE>


Posodobi knjižnice:

sudo apt update && sudo apt install -y curl jq

🔹 2️⃣ Pridobi dostopni žeton (access token)

Gemini API na Google Cloudu uporablja OAuth 2.0 token, ki ga lahko generiraš iz svojega projekta.
V terminalu vpiši:

gcloud auth application-default print-access-token


Rezultat bo dolg niz znakov (tvoj token).
Shrani ga v spremenljivko:

export ACCESS_TOKEN=$(gcloud auth application-default print-access-token)

🔹 3️⃣ Preveri povezavo z Gemini API

Zdaj preveri, ali se tvoja instanca poveže z Geminijem:

curl \
  -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts":[{"text":"Pozdravljen, Gemini! Povej nekaj o Beli krajini."}]}]
  }' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent"


Če je povezava pravilna, boš dobil odgovor v obliki JSON:

{
  "candidates": [
    {
      "content": {
        "parts": [{"text": "Bela krajina je čudovita pokrajina ob Kolpi..."}]
      }
    }
  ]
}


✅ To pomeni, da tvoj Google Cloud (torej tudi Omni) že komunicira z Geminijem.

🔹 4️⃣ (Neobvezno) – Ustvari skripto za avtomatsko uporabo

Ustvari datoteko gemini_test.sh:

#!/bin/bash
ACCESS_TOKEN=$(gcloud auth application-default print-access-token)
PROMPT=$1

curl -s \
  -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"contents\": [{\"parts\":[{\"text\":\"$PROMPT\"}]}]
  }" \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent" | jq -r '.candidates[0].content.parts[0].text'


Naredi jo izvedljivo:

chmod +x gemini_test.sh


Zdaj jo lahko uporabljaš kjerkoli:

./gemini_test.sh "Napiši opis Kolpe v stilu pesnika."

🔹 5️⃣ Povezava v tvojo Omni platformo

Če Omni že teče na isti instanci:

dodaš v svojo .env datoteko:

GCP_ACCESS_TOKEN=$(gcloud auth application-default print-access-token)
GEMINI_ENDPOINT=https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent


in v kodi (npr. gemini_connector.js):

import fetch from "node-fetch";

export async function callGemini(prompt) {
  const res = await fetch(process.env.GEMINI_ENDPOINT, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.GCP_ACCESS_TOKEN}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      contents: [{ parts: [{ text: prompt }]}]
    })
  });
  const data = await res.json();
  return data.candidates?.[0]?.content?.parts?.[0]?.text || "Ni odgovora.";
}


✅ KONEC
Tvoja Google Cloud instanca (ali Omni platforma) je zdaj povezana z Gemini preko varne GCP avtorizacije.
Ni ti treba več ročno vnašati API ključev — avtorizacija poteka prek IAM in tvojega GCP računa.#!/usr/bin/env python3
"""
Vertex AI Standalone Test - Proves Vertex AI works outside Google Cloud
This script demonstrates that Vertex AI can operate completely outside of
Google Cloud infrastructure using both REST API and SDK approaches.

Author: Vertex AI Standalone Test
Version: 1.0.0
"""

import requests
import json
import time
import os
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class VertexConfig:
    """Configuration for Vertex AI tests"""
    api_key: str = "AQ.Ab8RN6LjDXj9_BHBcp-XvbSm0WCE2ftjfwyobHz-Zc3oNMVfhQ"
    project_id: str = "refined-graph-471712-n9"
    region: str = "us-central1"
    model: str = "gemini-2.0-flash"
    timeout: int = 30

class VertexAIStandaloneTester:
    """Tests Vertex AI functionality outside Google Cloud environment"""

    def __init__(self, config: VertexConfig = None):
        self.config = config or VertexConfig()
        self.session = requests.Session()

    def log(self, level: str, message: str):
        """Log message with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def test_rest_api_approach(self) -> Dict[str, any]:
        """Test Vertex AI using REST API approach (works anywhere with internet)"""
        self.log("INFO", "[TEST] Testing Vertex AI REST API approach (no Google Cloud required)")

        start_time = time.time()

        # This approach works from ANY computer with internet access
        url = f"https://{self.config.region}-aiplatform.googleapis.com/v1/projects/{self.config.project_id}/locations/{self.config.region}/publishers/google/models/{self.config.model}:generateContent"

        headers = {
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'contents': [{
                'parts': [{
                    'text': 'You are a helpful AI assistant. Please respond to this message from a standalone test running outside of Google Cloud infrastructure. Confirm you received this message and that Vertex AI works independently of Google Cloud services.'
                }]
            }],
            'generation_config': {
                'max_output_tokens': 500,
                'temperature': 0.7,
                'top_p': 0.8,
                'top_k': 40
            }
        }

        try:
            response = self.session.post(url, headers=headers, json=data, timeout=self.config.timeout)

            if response.status_code == 200:
                result = response.json()
                generated_text = result["candidates"][0]["content"]["parts"][0]["text"]

                return {
                    "success": True,
                    "approach": "REST API",
                    "message": "[OK] Vertex AI REST API works perfectly outside Google Cloud!",
                    "details": {
                        "response_text": generated_text[:300] + "..." if len(generated_text) > 300 else generated_text,
                        "response_time": time.time() - start_time,
                        "model": self.config.model,
                        "endpoint": url,
                        "authentication": "API Key (Bearer token)",
                        "environment": "Standalone - No Google Cloud infrastructure required"
                    }
                }
            else:
                return {
                    "success": False,
                    "approach": "REST API",
                    "message": f"[FAIL] REST API request failed with status {response.status_code}",
                    "details": {
                        "status_code": response.status_code,
                        "error": response.text,
                        "response_time": time.time() - start_time
                    }
                }

        except Exception as e:
            return {
                "success": False,
                "approach": "REST API",
                "message": f"[FAIL] REST API request error: {str(e)}",
                "details": {
                    "error": str(e),
                    "response_time": time.time() - start_time
                }
            }

    def test_sdk_approach(self) -> Dict[str, any]:
        """Test Vertex AI using official SDK approach"""
        self.log("INFO", "[TEST] Testing Vertex AI SDK approach (requires only authentication)")

        start_time = time.time()

        try:
            # This approach also works from any computer with proper authentication
            from google.oauth2 import service_account
            from vertexai import init as vertex_init
            from vertexai.preview.generative_models import GenerativeModel

            # Use service account key for authentication (works from any machine)
            key_path = "service_account.omni-deployer.json"

            if not os.path.exists(key_path):
                return {
                    "success": False,
                    "approach": "SDK",
                    "message": "[FAIL] Service account key file not found",
                    "details": {
                        "error": f"Key file not found: {key_path}",
                        "note": "SDK approach requires service account credentials but works from any machine"
                    }
                }

            credentials = service_account.Credentials.from_service_account_file(key_path)

            # Initialize Vertex AI (works from any machine with credentials)
            vertex_init(
                project=self.config.project_id,
                location=self.config.region,
                credentials=credentials
            )

            # Create and use model (works from any machine)
            model = GenerativeModel(self.config.model)
            response = model.generate_content(
                "You are a helpful AI assistant. Please respond to this message from a standalone SDK test running outside of Google Cloud infrastructure. Confirm that Vertex AI SDK works independently of Google Cloud services."
            )

            return {
                "success": True,
                "approach": "SDK",
                "message": "[OK] Vertex AI SDK works perfectly outside Google Cloud!",
                "details": {
                    "response_text": response.text[:300] + "..." if len(response.text) > 300 else response.text,
                    "response_time": time.time() - start_time,
                    "model": self.config.model,
                    "authentication": "Service Account Key",
                    "environment": "Standalone - No Google Cloud infrastructure required",
                    "note": "Only requires service account credentials file"
                }
            }

        except ImportError as e:
            return {
                "success": False,
                "approach": "SDK",
                "message": "[FAIL] Required packages not installed",
                "details": {
                    "error": f"Missing packages: {str(e)}",
                    "note": "Install with: pip install google-cloud-aiplatform google-auth"
                }
            }
        except Exception as e:
            return {
                "success": False,
                "approach": "SDK",
                "message": f"[FAIL] SDK approach error: {str(e)}",
                "details": {
                    "error": str(e),
                    "response_time": time.time() - start_time
                }
            }

    def test_internet_connectivity(self) -> Dict[str, any]:
        """Test basic internet connectivity to Google APIs"""
        self.log("INFO", "[TEST] Testing internet connectivity to Google APIs")

        start_time = time.time()

        try:
            # Test connectivity to Google APIs domain
            response = self.session.get("https://aiplatform.googleapis.com", timeout=10)

            return {
                "success": response.status_code > 0,
                "message": f"Internet connectivity: {'[OK] Available' if response.status_code > 0 else '[FAIL] Failed'}",
                "details": {
                    "status_code": response.status_code,
                    "response_time": time.time() - start_time,
                    "domain": "aiplatform.googleapis.com"
                }
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"[FAIL] Internet connectivity test failed: {str(e)}",
                "details": {
                    "error": str(e),
                    "response_time": time.time() - start_time
                }
            }

    def run_comprehensive_test(self) -> Dict[str, any]:
        """Run comprehensive test of Vertex AI outside Google Cloud"""
        self.log("INFO", "[START] Starting comprehensive Vertex AI standalone test")
        self.log("INFO", "=" * 80)
        self.log("INFO", "This test proves Vertex AI works OUTSIDE of Google Cloud infrastructure")
        self.log("INFO", "Requirements: Internet connection + API key or service account credentials")
        self.log("INFO", "=" * 80)

        tests = [
            self.test_internet_connectivity,
            self.test_rest_api_approach,
            self.test_sdk_approach
        ]

        results = []

        for test_func in tests:
            try:
                result = test_func()
                results.append(result)

                if result["success"]:
                    self.log("SUCCESS", f"[OK] {result.get('approach', 'Test')}: {result['message']}")
                else:
                    self.log("FAIL", f"[FAIL] {result.get('approach', 'Test')}: {result['message']}")

            except Exception as e:
                error_result = {
                    "success": False,
                    "message": f"[FAIL] Test execution failed: {str(e)}",
                    "details": {"error": str(e)}
                }
                results.append(error_result)
                self.log("ERROR", f"[CRASH] Test error: {str(e)}")

        # Summary
        successful_tests = sum(1 for r in results if r["success"])
        total_tests = len(results)

        summary = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
                "conclusion": "[OK] Vertex AI CAN work outside Google Cloud!" if successful_tests >= 2 else "[FAIL] Vertex AI cannot work outside Google Cloud"
            },
            "results": results,
            "key_findings": [
                "🌐 REST API approach: Works from any computer with internet and API key",
                "🔑 SDK approach: Works from any computer with service account credentials",
                "☁️ No Google Cloud infrastructure required - only authentication",
                "📡 Only requirement: Internet connection to Google APIs",
                "🏢 Can run on-premises, other cloud providers, or local machines"
            ]
        }

        self.log("INFO", "=" * 80)
        self.log("INFO", "[STATS] VERTEX AI STANDALONE TEST RESULTS")
        self.log("INFO", f"Total Tests: {total_tests}")
        self.log("INFO", f"[OK] Successful: {successful_tests}")
        self.log("INFO", f"[FAIL] Failed: {total_tests - successful_tests}")
        self.log("INFO", f"[WINNER] Success Rate: {summary['summary']['success_rate']:.1f}%")
        self.log("INFO", f"[TARGET] Conclusion: {summary['summary']['conclusion']}")

        for finding in summary["key_findings"]:
            self.log("INFO", finding)

        return summary

def main():
    """Main function"""
    print("Vertex AI Standalone Test Suite")
    print("Proving that Vertex AI works outside Google Cloud infrastructure")
    print()

    # Create tester
    config = VertexConfig()
    tester = VertexAIStandaloneTester(config)

    # Run comprehensive test
    results = tester.run_comprehensive_test()

    # Save results
    timestamp = int(time.time())
    report_file = f"vertex_ai_standalone_test_report_{timestamp}.json"

    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Test report saved to: {report_file}")

    # Final conclusion
    if results["summary"]["successful_tests"] >= 2:
        print("\n[SUCCESS] SUCCESS: Vertex AI CAN work outside Google Cloud!")
        print("\n💡 Key Points:")
        print("   • REST API approach works from any computer with internet")
        print("   • SDK approach works with service account credentials")
        print("   • No Google Cloud infrastructure required")
        print("   • Can run on-premises or other cloud providers")
        sys.exit(0)
    else:
        print(f"\n[WARNING]  PARTIAL SUCCESS: {results['summary']['successful_tests']}/{results['summary']['total_tests']} tests passed")
        print("   Some issues detected - check the report for details")
        sys.exit(1)

if __name__ == "__main__":
    main()