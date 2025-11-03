"""
Developer Platform & API Management Routes
Provides SDK generation, API documentation, developer portal, sandbox environment, and API versioning
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

router = APIRouter(prefix="/api/v1/developer-platform", tags=["Developer Platform"])


class SDKLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUBY = "ruby"
    PHP = "php"
    CSHARP = "csharp"
    SWIFT = "swift"
    KOTLIN = "kotlin"


class DocFormat(str, Enum):
    OPENAPI = "openapi"
    SWAGGER = "swagger"
    POSTMAN = "postman"
    RAML = "raml"
    GRAPHQL_SCHEMA = "graphql_schema"


# ==================== SDK Generation ====================

@router.post("/sdk/generate")
async def generate_sdk(
    language: SDKLanguage,
    api_spec_url: str,
    package_name: Optional[str] = None,
    include_examples: bool = True
):
    """
    Generate SDK for specified programming language
    Auto-generates from OpenAPI specification
    """
    return {
        "sdk_id": f"sdk-{hash(language + api_spec_url) % 1000000}",
        "language": language,
        "package_name": package_name or f"omni-api-{language}",
        "version": "1.0.0",
        "generated_at": datetime.utcnow().isoformat(),
        "status": "completed",
        "download_url": f"/sdks/{language}/omni-api-{language}-1.0.0.zip",
        "documentation_url": f"/docs/sdks/{language}",
        "features": [
            "Type-safe API clients",
            "Automatic request/response serialization",
            "Built-in error handling",
            "Rate limiting support",
            "Retry logic with exponential backoff",
            "Request/response logging",
            "Authentication helpers"
        ],
        "examples_included": include_examples,
        "size_bytes": 245000,
        "installation": self._get_installation_command(language, package_name or f"omni-api-{language}")
    }


def _get_installation_command(language: SDKLanguage, package_name: str) -> Dict[str, str]:
    commands = {
        "python": f"pip install {package_name}",
        "javascript": f"npm install {package_name}",
        "typescript": f"npm install {package_name}",
        "java": f"<dependency>\n  <groupId>com.omni</groupId>\n  <artifactId>{package_name}</artifactId>\n  <version>1.0.0</version>\n</dependency>",
        "go": f"go get github.com/omni/{package_name}",
        "ruby": f"gem install {package_name}",
        "php": f"composer require omni/{package_name}",
        "csharp": f"dotnet add package {package_name}",
        "swift": f"pod '{package_name}'",
        "kotlin": f"implementation 'com.omni:{package_name}:1.0.0'"
    }
    return {
        "command": commands.get(language, ""),
        "package_manager": ["pip", "npm", "npm", "maven", "go", "gem", "composer", "nuget", "cocoapods", "gradle"][
            list(SDKLanguage).index(language)
        ]
    }


@router.get("/sdk/list")
async def list_sdks():
    """
    List all available SDKs
    """
    sdks = [
        {
            "language": lang,
            "version": "1.0.0",
            "downloads": 1000 + i * 250,
            "last_updated": (datetime.utcnow() - timedelta(days=i * 5)).isoformat(),
            "status": "stable",
            "documentation_url": f"/docs/sdks/{lang}",
            "download_url": f"/sdks/{lang}/omni-api-{lang}-1.0.0.zip"
        }
        for i, lang in enumerate(SDKLanguage)
    ]
    
    return {
        "sdks": sdks,
        "total": len(sdks),
        "most_popular": "python",
        "total_downloads": sum(sdk["downloads"] for sdk in sdks)
    }


# ==================== API Documentation ====================

@router.get("/docs/generate")
async def generate_documentation(
    format: DocFormat = DocFormat.OPENAPI,
    include_examples: bool = True,
    include_schemas: bool = True
):
    """
    Generate API documentation in various formats
    """
    return {
        "doc_id": f"doc-{hash(format) % 100000}",
        "format": format,
        "version": "3.0.0",
        "generated_at": datetime.utcnow().isoformat(),
        "endpoints_documented": 355,
        "schemas_included": 180 if include_schemas else 0,
        "examples_included": include_examples,
        "download_url": f"/docs/api-{format}.json",
        "preview_url": f"/docs/preview/{format}",
        "size_kb": 1250
    }


@router.get("/docs/interactive")
async def get_interactive_docs():
    """
    Get interactive API documentation (Swagger UI / ReDoc)
    """
    return {
        "swagger_ui_url": "/api/docs",
        "redoc_url": "/api/redoc",
        "features": [
            "Try it out functionality",
            "Request/response examples",
            "Authentication testing",
            "Schema browser",
            "Code generation",
            "Download OpenAPI spec"
        ],
        "total_endpoints": 355,
        "categories": 22,
        "auth_methods": ["API Key", "OAuth 2.0", "JWT Bearer"],
        "rate_limits_documented": True
    }


# ==================== Developer Portal ====================

@router.post("/portal/register")
async def register_developer(
    email: str,
    company: str,
    use_case: str
):
    """
    Register for developer portal access
    """
    return {
        "developer_id": f"dev-{hash(email) % 1000000}",
        "email": email,
        "company": company,
        "use_case": use_case,
        "status": "pending_verification",
        "verification_email_sent": True,
        "registered_at": datetime.utcnow().isoformat(),
        "portal_url": "https://developers.omni.com",
        "next_steps": [
            "Verify your email address",
            "Complete your profile",
            "Generate API keys",
            "Explore documentation"
        ]
    }


@router.get("/portal/dashboard/{developer_id}")
async def get_developer_dashboard(developer_id: str):
    """
    Get developer portal dashboard
    """
    return {
        "developer_id": developer_id,
        "profile": {
            "name": "John Developer",
            "email": "john@company.com",
            "company": "TechStart Inc",
            "member_since": "2024-01-01T00:00:00Z",
            "tier": "professional"
        },
        "api_keys": [
            {
                "key_id": "key-12345",
                "name": "Production",
                "prefix": "pk_live_",
                "created": "2024-01-10",
                "last_used": "2024-01-20",
                "status": "active"
            },
            {
                "key_id": "key-12346",
                "name": "Development",
                "prefix": "pk_test_",
                "created": "2024-01-05",
                "last_used": "2024-01-20",
                "status": "active"
            }
        ],
        "usage": {
            "api_calls_today": 1245,
            "api_calls_month": 42500,
            "quota_limit": 100000,
            "quota_remaining": 57500,
            "bandwidth_gb": 12.5,
            "error_rate": 0.5
        },
        "recent_activity": [
            {
                "timestamp": "2024-01-20T15:30:00Z",
                "endpoint": "/api/v1/ai-assistants/chat",
                "status": 200,
                "latency_ms": 245
            },
            {
                "timestamp": "2024-01-20T15:29:00Z",
                "endpoint": "/api/v1/tenants/list",
                "status": 200,
                "latency_ms": 120
            }
        ],
        "notifications": [
            {
                "type": "rate_limit_warning",
                "message": "Approaching 80% of monthly quota",
                "timestamp": "2024-01-20T10:00:00Z"
            }
        ]
    }


# ==================== Sandbox Environment ====================

@router.post("/sandbox/create")
async def create_sandbox(developer_id: str, name: str):
    """
    Create isolated sandbox environment for testing
    """
    return {
        "sandbox_id": f"sandbox-{hash(developer_id + name) % 1000000}",
        "name": name,
        "developer_id": developer_id,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "api_endpoint": f"https://sandbox-{hash(name) % 10000}.api.omni.com",
        "test_api_key": f"sk_test_{hash(name) % 1000000}",
        "features": [
            "Full API access",
            "Mock data pre-loaded",
            "No rate limits",
            "Webhook testing",
            "Request logging",
            "Auto-reset daily"
        ],
        "pre_loaded_data": {
            "users": 100,
            "transactions": 500,
            "api_calls": 1000
        },
        "dashboard_url": f"https://sandbox-{hash(name) % 10000}.dashboard.omni.com"
    }


@router.get("/sandbox/{sandbox_id}")
async def get_sandbox(sandbox_id: str):
    """
    Get sandbox environment details
    """
    return {
        "sandbox_id": sandbox_id,
        "name": "Testing Environment",
        "status": "active",
        "created_at": "2024-01-15T00:00:00Z",
        "expires_at": "2024-02-14T00:00:00Z",
        "api_endpoint": f"https://sandbox-{hash(sandbox_id) % 10000}.api.omni.com",
        "usage": {
            "api_calls": 2450,
            "storage_mb": 125,
            "last_activity": datetime.utcnow().isoformat()
        },
        "test_data": {
            "users": 100,
            "transactions": 500,
            "can_reset": True,
            "last_reset": "2024-01-20T00:00:00Z"
        },
        "logs_available": True,
        "webhook_endpoint": f"https://sandbox-{hash(sandbox_id) % 10000}.webhooks.omni.com"
    }


@router.post("/sandbox/{sandbox_id}/reset")
async def reset_sandbox(sandbox_id: str):
    """
    Reset sandbox to initial state
    """
    return {
        "sandbox_id": sandbox_id,
        "status": "reset",
        "reset_at": datetime.utcnow().isoformat(),
        "actions_taken": [
            "Cleared all test data",
            "Restored initial dataset",
            "Reset API call counters",
            "Cleared logs"
        ],
        "ready_for_testing": True
    }


# ==================== API Versioning ====================

@router.get("/versions")
async def list_api_versions():
    """
    List all API versions
    """
    return {
        "versions": [
            {
                "version": "v3",
                "status": "current",
                "release_date": "2024-01-01",
                "deprecation_date": None,
                "sunset_date": None,
                "endpoints": 355,
                "breaking_changes": [],
                "documentation": "/docs/v3"
            },
            {
                "version": "v2",
                "status": "supported",
                "release_date": "2023-06-01",
                "deprecation_date": "2024-06-01",
                "sunset_date": "2024-12-01",
                "endpoints": 280,
                "breaking_changes": ["Removed legacy auth endpoints"],
                "documentation": "/docs/v2",
                "migration_guide": "/docs/migration/v2-to-v3"
            },
            {
                "version": "v1",
                "status": "deprecated",
                "release_date": "2023-01-01",
                "deprecation_date": "2023-06-01",
                "sunset_date": "2024-01-01",
                "endpoints": 150,
                "breaking_changes": ["Complete API redesign in v2"],
                "documentation": "/docs/v1",
                "migration_guide": "/docs/migration/v1-to-v2"
            }
        ],
        "current_version": "v3",
        "recommended_version": "v3",
        "deprecation_policy": "12 months notice before sunset"
    }


@router.get("/versions/{version}/changelog")
async def get_version_changelog(version: str):
    """
    Get detailed changelog for API version
    """
    return {
        "version": version,
        "changes": [
            {
                "date": "2024-01-15",
                "type": "feature",
                "title": "Added ML Platform endpoints",
                "description": "30 new endpoints for model training and serving",
                "breaking": False
            },
            {
                "date": "2024-01-10",
                "type": "enhancement",
                "title": "Improved rate limiting",
                "description": "Dynamic rate limits based on tier",
                "breaking": False
            },
            {
                "date": "2024-01-05",
                "type": "fix",
                "title": "Fixed pagination on list endpoints",
                "description": "Cursor-based pagination now works correctly",
                "breaking": False
            },
            {
                "date": "2024-01-01",
                "type": "breaking",
                "title": "New authentication flow",
                "description": "OAuth 2.0 is now required for all endpoints",
                "breaking": True,
                "migration_guide": "/docs/auth-migration"
            }
        ],
        "total_changes": 45,
        "breaking_changes": 2,
        "deprecated_features": 5
    }


# ==================== Code Examples ====================

@router.get("/examples/{language}")
async def get_code_examples(
    language: SDKLanguage,
    category: Optional[str] = None
):
    """
    Get code examples for specific language
    """
    examples = {
        "authentication": {
            "title": "Authentication",
            "description": "How to authenticate API requests",
            "code": _get_auth_example(language)
        },
        "create_resource": {
            "title": "Create Resource",
            "description": "Create a new resource via API",
            "code": _get_create_example(language)
        },
        "list_resources": {
            "title": "List Resources",
            "description": "List resources with pagination",
            "code": _get_list_example(language)
        },
        "error_handling": {
            "title": "Error Handling",
            "description": "Proper error handling and retries",
            "code": _get_error_handling_example(language)
        }
    }
    
    return {
        "language": language,
        "examples": examples if not category else {category: examples.get(category)},
        "total_examples": len(examples),
        "playground_url": f"/playground/{language}"
    }


def _get_auth_example(language: SDKLanguage) -> str:
    examples = {
        "python": """
from omni_api import OmniClient

client = OmniClient(api_key='your_api_key')
response = client.auth.verify()
print(response)
        """,
        "javascript": """
const { OmniClient } = require('omni-api');

const client = new OmniClient({ apiKey: 'your_api_key' });
const response = await client.auth.verify();
console.log(response);
        """,
        "go": """
package main

import "github.com/omni/omni-api-go"

func main() {
    client := omni.NewClient("your_api_key")
    response, err := client.Auth.Verify()
    if err != nil {
        panic(err)
    }
    fmt.Println(response)
}
        """
    }
    return examples.get(language, "# Example not available for this language")


def _get_create_example(language: SDKLanguage) -> str:
    return f"# Create example for {language}\n# Coming soon..."


def _get_list_example(language: SDKLanguage) -> str:
    return f"# List example for {language}\n# Coming soon..."


def _get_error_handling_example(language: SDKLanguage) -> str:
    return f"# Error handling example for {language}\n# Coming soon..."


# ==================== Webhooks ====================

@router.post("/webhooks/register")
async def register_webhook(
    developer_id: str,
    url: str,
    events: List[str],
    secret: Optional[str] = None
):
    """
    Register webhook endpoint
    """
    return {
        "webhook_id": f"wh-{hash(developer_id + url) % 1000000}",
        "developer_id": developer_id,
        "url": url,
        "events": events,
        "secret": secret or f"whsec_{hash(url) % 1000000}",
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "deliveries": 0,
        "failures": 0,
        "last_delivery": None
    }


@router.get("/webhooks/{webhook_id}/deliveries")
async def get_webhook_deliveries(
    webhook_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """
    Get webhook delivery history
    """
    deliveries = [
        {
            "delivery_id": f"del-{10000 + i}",
            "event_type": "customer.created",
            "delivered_at": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
            "status": "success" if i % 5 != 0 else "failed",
            "response_code": 200 if i % 5 != 0 else 500,
            "latency_ms": 145 + i * 10,
            "retries": 0 if i % 5 != 0 else 3
        }
        for i in range(20)
    ]
    
    return {
        "webhook_id": webhook_id,
        "deliveries": deliveries[:per_page],
        "total": 20,
        "page": page,
        "per_page": per_page,
        "statistics": {
            "total_deliveries": 2450,
            "successful": 2385,
            "failed": 65,
            "success_rate": 97.3,
            "avg_latency_ms": 185
        }
    }


# ==================== API Analytics ====================

@router.get("/analytics/usage")
async def get_api_usage_analytics(
    developer_id: str,
    days: int = Query(30, ge=1, le=365)
):
    """
    Get detailed API usage analytics
    """
    return {
        "developer_id": developer_id,
        "period_days": days,
        "total_requests": 125000,
        "successful_requests": 122500,
        "failed_requests": 2500,
        "success_rate": 98.0,
        "avg_latency_ms": 185,
        "p50_latency_ms": 150,
        "p95_latency_ms": 320,
        "p99_latency_ms": 485,
        "by_endpoint": [
            {
                "endpoint": "/api/v1/ai-assistants/chat",
                "calls": 45000,
                "percent": 36.0,
                "avg_latency": 250,
                "error_rate": 0.5
            },
            {
                "endpoint": "/api/v1/tenants/list",
                "calls": 28000,
                "percent": 22.4,
                "avg_latency": 120,
                "error_rate": 0.2
            },
            {
                "endpoint": "/api/v1/analytics/metrics",
                "calls": 18000,
                "percent": 14.4,
                "avg_latency": 180,
                "error_rate": 1.0
            }
        ],
        "by_status_code": {
            "200": 110000,
            "201": 12500,
            "400": 1200,
            "401": 500,
            "429": 300,
            "500": 500
        },
        "bandwidth": {
            "total_gb": 125.5,
            "requests_gb": 45.2,
            "responses_gb": 80.3
        },
        "quota": {
            "limit": 150000,
            "used": 125000,
            "remaining": 25000,
            "reset_date": (datetime.utcnow() + timedelta(days=10)).isoformat()
        }
    }


@router.get("/analytics/errors")
async def get_error_analytics(
    developer_id: str,
    days: int = Query(7, ge=1, le=30)
):
    """
    Get error analytics and debugging information
    """
    return {
        "developer_id": developer_id,
        "period_days": days,
        "total_errors": 2500,
        "error_rate": 2.0,
        "by_type": {
            "4xx_client_errors": 2000,
            "5xx_server_errors": 500
        },
        "top_errors": [
            {
                "status_code": 400,
                "message": "Invalid request body",
                "count": 850,
                "endpoints": ["/api/v1/ai-assistants/chat", "/api/v1/tenants/create"],
                "fix_suggestion": "Validate request body against schema before sending"
            },
            {
                "status_code": 401,
                "message": "Invalid API key",
                "count": 500,
                "endpoints": ["*"],
                "fix_suggestion": "Ensure API key is correctly set in Authorization header"
            },
            {
                "status_code": 429,
                "message": "Rate limit exceeded",
                "count": 300,
                "endpoints": ["/api/v1/analytics/metrics"],
                "fix_suggestion": "Implement exponential backoff or upgrade tier"
            }
        ],
        "recent_errors": [
            {
                "timestamp": "2024-01-20T15:30:00Z",
                "endpoint": "/api/v1/ai-assistants/chat",
                "status": 400,
                "error": "Invalid request body",
                "request_id": "req-12345"
            }
        ]
    }
