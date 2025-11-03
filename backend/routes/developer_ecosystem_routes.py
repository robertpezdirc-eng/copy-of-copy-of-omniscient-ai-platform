"""
Developer Ecosystem Routes
Provides SDK management, API documentation, and developer resources
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel, Field

router = APIRouter()


class SDKInfo(BaseModel):
    """SDK information model"""
    name: str
    language: str
    version: str
    download_url: str
    documentation_url: str
    repository_url: str
    last_updated: str


class APIEndpoint(BaseModel):
    """API endpoint documentation"""
    method: str
    path: str
    description: str
    parameters: List[dict] = Field(default_factory=list)
    example_request: Optional[dict] = None
    example_response: Optional[dict] = None


@router.get("/sdk", response_model=List[SDKInfo], tags=["Developer Ecosystem"])
async def list_sdks(
    language: Optional[str] = Query(default=None, description="Filter by programming language")
):
    """
    Get list of available SDKs for different programming languages
    
    - **language**: Filter by language (python, javascript, java, go, etc.)
    """
    sdks = [
        SDKInfo(
            name="omni-python-sdk",
            language="python",
            version="2.0.0",
            download_url="https://pypi.org/project/omni-sdk/",
            documentation_url="https://docs.omni-ultra.com/sdk/python",
            repository_url="https://github.com/omni-ultra/python-sdk",
            last_updated="2024-10-15T10:30:00Z"
        ),
        SDKInfo(
            name="omni-javascript-sdk",
            language="javascript",
            version="2.0.1",
            download_url="https://npmjs.com/package/@omni/sdk",
            documentation_url="https://docs.omni-ultra.com/sdk/javascript",
            repository_url="https://github.com/omni-ultra/javascript-sdk",
            last_updated="2024-10-20T14:45:00Z"
        ),
        SDKInfo(
            name="omni-go-sdk",
            language="go",
            version="2.0.0",
            download_url="https://pkg.go.dev/github.com/omni-ultra/go-sdk",
            documentation_url="https://docs.omni-ultra.com/sdk/go",
            repository_url="https://github.com/omni-ultra/go-sdk",
            last_updated="2024-10-10T09:15:00Z"
        ),
        SDKInfo(
            name="omni-java-sdk",
            language="java",
            version="2.0.0",
            download_url="https://search.maven.org/artifact/com.omni/omni-sdk",
            documentation_url="https://docs.omni-ultra.com/sdk/java",
            repository_url="https://github.com/omni-ultra/java-sdk",
            last_updated="2024-10-12T16:00:00Z"
        )
    ]
    
    if language:
        sdks = [sdk for sdk in sdks if sdk.language.lower() == language.lower()]
    
    return sdks


@router.get("/sdk/{language}/latest", response_model=SDKInfo, tags=["Developer Ecosystem"])
async def get_latest_sdk(language: str):
    """Get the latest version of SDK for specified language"""
    sdks = {
        "python": SDKInfo(
            name="omni-python-sdk",
            language="python",
            version="2.0.0",
            download_url="https://pypi.org/project/omni-sdk/",
            documentation_url="https://docs.omni-ultra.com/sdk/python",
            repository_url="https://github.com/omni-ultra/python-sdk",
            last_updated="2024-10-15T10:30:00Z"
        ),
        "javascript": SDKInfo(
            name="omni-javascript-sdk",
            language="javascript",
            version="2.0.1",
            download_url="https://npmjs.com/package/@omni/sdk",
            documentation_url="https://docs.omni-ultra.com/sdk/javascript",
            repository_url="https://github.com/omni-ultra/javascript-sdk",
            last_updated="2024-10-20T14:45:00Z"
        )
    }
    
    if language.lower() not in sdks:
        raise HTTPException(status_code=404, detail=f"SDK for language '{language}' not found")
    
    return sdks[language.lower()]


@router.get("/docs/endpoints", response_model=List[APIEndpoint], tags=["Developer Ecosystem"])
async def list_api_endpoints(
    tag: Optional[str] = Query(default=None, description="Filter by tag/category")
):
    """Get list of available API endpoints with documentation"""
    endpoints = [
        APIEndpoint(
            method="GET",
            path="/api/v1/ai/chat",
            description="Send a chat completion request to the AI",
            parameters=[
                {"name": "message", "type": "string", "required": True, "description": "User message"},
                {"name": "model", "type": "string", "required": False, "description": "AI model to use"}
            ],
            example_request={"message": "Hello, how are you?", "model": "gpt-4"},
            example_response={"response": "I'm doing well, thank you!"}
        ),
        APIEndpoint(
            method="POST",
            path="/api/v1/ai/embeddings",
            description="Generate embeddings for text",
            parameters=[
                {"name": "text", "type": "string", "required": True, "description": "Text to embed"}
            ],
            example_request={"text": "Sample text for embedding"},
            example_response={"embeddings": [0.1, 0.2, 0.3]}
        )
    ]
    
    return endpoints


@router.get("/quickstart", tags=["Developer Ecosystem"])
async def get_quickstart_guide():
    """Get quick start guide for developers"""
    return {
        "title": "Omni Enterprise Ultra Max - Quick Start Guide",
        "steps": [
            {
                "step": 1,
                "title": "Get API Key",
                "description": "Sign up at https://platform.omni-ultra.com and get your API key"
            },
            {
                "step": 2,
                "title": "Install SDK",
                "description": "Install the SDK for your preferred language",
                "examples": {
                    "python": "pip install omni-sdk",
                    "javascript": "npm install @omni/sdk",
                    "go": "go get github.com/omni-ultra/go-sdk"
                }
            },
            {
                "step": 3,
                "title": "Make Your First Request",
                "description": "Initialize the client and make your first API call",
                "examples": {
                    "python": "from omni import Client\nclient = Client(api_key='your-key')\nresponse = client.ai.chat('Hello!')",
                    "javascript": "import { OmniClient } from '@omni/sdk';\nconst client = new OmniClient('your-key');\nconst response = await client.ai.chat('Hello!');"
                }
            }
        ],
        "resources": {
            "documentation": "https://docs.omni-ultra.com",
            "api_reference": "https://docs.omni-ultra.com/api",
            "examples": "https://github.com/omni-ultra/examples",
            "support": "https://support.omni-ultra.com"
        }
    }


@router.get("/changelog", tags=["Developer Ecosystem"])
async def get_changelog():
    """Get API changelog and version history"""
    return {
        "versions": [
            {
                "version": "2.0.0",
                "release_date": "2024-10-01",
                "changes": [
                    "Added multi-modal AI support",
                    "Improved RAG performance by 40%",
                    "New GDPR compliance endpoints"
                ],
                "breaking_changes": [
                    "Deprecated v1 authentication endpoints"
                ]
            },
            {
                "version": "1.9.0",
                "release_date": "2024-09-15",
                "changes": [
                    "Enhanced analytics capabilities",
                    "Added webhook support",
                    "Improved error handling"
                ],
                "breaking_changes": []
            }
        ]
    }
