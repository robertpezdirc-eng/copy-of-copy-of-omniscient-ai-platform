"""Tests for Content Generation service."""

import pytest
from backend.services.advanced_ai.content_generation import ContentGenerationService


@pytest.fixture
def content_service():
    """Create a fresh content generation service instance."""
    return ContentGenerationService()


@pytest.mark.asyncio
async def test_generate_documentation_markdown(content_service):
    """Test generating markdown documentation."""
    code = """
def calculate_sum(a, b):
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
    """
    
    result = await content_service.generate_documentation(
        code_snippet=code,
        language="python",
        doc_format="markdown",
        include_examples=True,
    )
    
    assert result["format"] == "markdown"
    assert result["language"] == "python"
    assert "documentation" in result
    assert len(result["documentation"]) > 0
    assert "calculate_sum" in result["entities_found"]
    assert "Calculator" in result["entities_found"]
    assert result["confidence"] > 0.8


@pytest.mark.asyncio
async def test_generate_documentation_docstring(content_service):
    """Test generating Python docstrings."""
    code = """
def process_data(data):
    return data
    """
    
    result = await content_service.generate_documentation(
        code_snippet=code,
        language="python",
        doc_format="docstring",
        include_examples=False,
    )
    
    assert result["format"] == "docstring"
    assert '"""' in result["documentation"]
    assert "process_data" in result["entities_found"]


@pytest.mark.asyncio
async def test_generate_documentation_openapi(content_service):
    """Test generating OpenAPI specification."""
    code = """
def get_user(user_id):
    pass

def create_user(username, email):
    pass
    """
    
    result = await content_service.generate_documentation(
        code_snippet=code,
        language="python",
        doc_format="openapi",
    )
    
    assert result["format"] == "openapi"
    assert "openapi" in result["documentation"]
    assert "get_user" in result["entities_found"]
    assert "create_user" in result["entities_found"]


@pytest.mark.asyncio
async def test_generate_test_data(content_service):
    """Test generating test data from schema."""
    schema = {
        "id": "integer",
        "name": "string",
        "email": "email",
        "age": "integer",
        "active": "boolean",
    }
    
    result = await content_service.generate_test_data(
        schema=schema,
        count=5,
        seed=42,
    )
    
    assert result["count"] == 5
    assert len(result["data"]) == 5
    assert result["seed"] == 42
    
    # Check first record has all fields
    record = result["data"][0]
    assert "id" in record
    assert "name" in record
    assert "email" in record
    assert "age" in record
    assert "active" in record
    assert isinstance(record["active"], bool)
    assert "@" in record["email"]


@pytest.mark.asyncio
async def test_generate_test_data_reproducible(content_service):
    """Test that test data generation is reproducible with seed."""
    schema = {"id": "integer", "name": "string"}
    
    result1 = await content_service.generate_test_data(schema=schema, count=3, seed=123)
    result2 = await content_service.generate_test_data(schema=schema, count=3, seed=123)
    
    assert result1["data"] == result2["data"]


@pytest.mark.asyncio
async def test_suggest_features_from_usage_patterns(content_service):
    """Test feature suggestions based on usage patterns."""
    context = {
        "usage_patterns": {
            "api_calls_per_hour": 1500,
            "error_rate": 0.08,
        },
        "current_features": ["authentication", "api"],
        "user_feedback": ["This is slow", "Very confusing interface"],
    }
    
    result = await content_service.suggest_features(
        context=context,
        max_suggestions=5,
    )
    
    assert result["count"] > 0
    assert result["count"] <= 5
    assert len(result["suggestions"]) > 0
    
    # Check suggestion structure
    suggestion = result["suggestions"][0]
    assert "title" in suggestion
    assert "description" in suggestion
    assert "priority" in suggestion
    assert "effort" in suggestion
    assert "impact" in suggestion


@pytest.mark.asyncio
async def test_suggest_features_empty_context(content_service):
    """Test feature suggestions with minimal context."""
    context = {"current_features": []}
    
    result = await content_service.suggest_features(
        context=context,
        max_suggestions=3,
    )
    
    assert "suggestions" in result
    assert result["count"] >= 0


@pytest.mark.asyncio
async def test_generate_api_examples(content_service):
    """Test generating API examples in multiple languages."""
    result = await content_service.generate_api_examples(
        endpoint="/api/v1/users",
        method="POST",
        parameters={"name": "John", "email": "john@example.com"},
    )
    
    assert result["endpoint"] == "/api/v1/users"
    assert result["method"] == "POST"
    assert "examples" in result
    
    # Check all language examples are present
    assert "curl" in result["examples"]
    assert "python" in result["examples"]
    assert "javascript" in result["examples"]
    assert "go" in result["examples"]
    
    # Check curl example contains expected elements
    curl_example = result["examples"]["curl"]
    assert "curl" in curl_example
    assert "/api/v1/users" in curl_example
    assert "POST" in curl_example
    
    # Check python example
    python_example = result["examples"]["python"]
    assert "import requests" in python_example
    assert "requests.post" in python_example


@pytest.mark.asyncio
async def test_generate_api_examples_get_request(content_service):
    """Test generating API examples for GET request."""
    result = await content_service.generate_api_examples(
        endpoint="/api/v1/users/123",
        method="GET",
        parameters=None,
    )
    
    assert result["method"] == "GET"
    assert "curl" in result["examples"]


@pytest.mark.asyncio
async def test_get_generation_stats(content_service):
    """Test getting generation statistics."""
    # Generate some content first
    await content_service.generate_documentation(
        code_snippet="def test(): pass",
        language="python",
    )
    await content_service.generate_test_data(
        schema={"id": "integer"},
        count=5,
    )
    
    stats = await content_service.get_generation_stats()
    
    assert "total_generations" in stats
    assert stats["total_generations"] >= 2
    assert "by_type" in stats
    assert "documentation" in stats["by_type"]
    assert "test_data" in stats["by_type"]
    assert stats["by_type"]["documentation"] >= 1
    assert stats["by_type"]["test_data"] >= 1


@pytest.mark.asyncio
async def test_documentation_entity_extraction(content_service):
    """Test that entity extraction works correctly."""
    code = """
class UserManager:
    def add_user(self, user):
        pass
    
    def remove_user(self, user_id):
        pass

def validate_email(email):
    return "@" in email
    """
    
    result = await content_service.generate_documentation(
        code_snippet=code,
        language="python",
    )
    
    entities = result["entities_found"]
    assert "UserManager" in entities
    assert "add_user" in entities
    assert "remove_user" in entities
    assert "validate_email" in entities


@pytest.mark.asyncio
async def test_test_data_all_types(content_service):
    """Test generating test data with all supported types."""
    schema = {
        "str_field": "string",
        "int_field": "integer",
        "float_field": "float",
        "bool_field": "boolean",
        "email_field": "email",
        "uuid_field": "uuid",
        "timestamp_field": "timestamp",
    }
    
    result = await content_service.generate_test_data(schema=schema, count=2)
    
    assert len(result["data"]) == 2
    record = result["data"][0]
    
    assert isinstance(record["str_field"], str)
    assert isinstance(record["int_field"], int)
    assert isinstance(record["float_field"], float)
    assert isinstance(record["bool_field"], bool)
    assert "@" in record["email_field"]
    # UUID check (basic)
    assert len(record["uuid_field"]) > 20
    # Timestamp check
    assert "T" in record["timestamp_field"] or ":" in record["timestamp_field"]


@pytest.mark.asyncio
async def test_feature_suggestions_priority_ranking(content_service):
    """Test that feature suggestions are ranked by priority."""
    context = {
        "usage_patterns": {
            "api_calls_per_hour": 2000,
            "error_rate": 0.10,
        },
    }
    
    result = await content_service.suggest_features(context=context, max_suggestions=10)
    
    if len(result["suggestions"]) > 1:
        # Check that suggestions are sorted by priority (descending)
        priorities = [s["priority"] for s in result["suggestions"]]
        assert priorities == sorted(priorities, reverse=True)
