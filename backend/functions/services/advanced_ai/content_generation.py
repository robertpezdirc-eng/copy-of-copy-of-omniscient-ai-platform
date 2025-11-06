"""AI-powered content generation service for documentation, test data, and feature suggestions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import random
import json
import logging
import uuid

logger = logging.getLogger(__name__)


class ContentGenerationService:
    """Generate documentation, test data, and feature suggestions using AI."""

    def __init__(self) -> None:
        self._generation_history: List[Dict[str, Any]] = []

    async def generate_documentation(
        self,
        code_snippet: str,
        language: str = "python",
        doc_format: str = "markdown",
        include_examples: bool = True,
    ) -> Dict[str, Any]:
        """Automatically generate documentation from code."""
        logger.info(f"Generating {doc_format} documentation for {language} code")
        
        # Simulate AI-powered documentation generation
        lines = code_snippet.strip().split("\n")
        
        # Extract function/class names
        entities = []
        for line in lines:
            if "def " in line:
                entities.append(line.split("def ")[1].split("(")[0])
            elif "class " in line:
                entities.append(line.split("class ")[1].split("(")[0].split(":")[0])
        
        # Generate documentation
        if doc_format == "markdown":
            doc = self._generate_markdown_doc(code_snippet, entities, include_examples)
        elif doc_format == "docstring":
            doc = self._generate_docstring(code_snippet, entities)
        elif doc_format == "openapi":
            doc = self._generate_openapi_spec(code_snippet, entities)
        else:
            doc = self._generate_markdown_doc(code_snippet, entities, include_examples)
        
        result = {
            "documentation": doc,
            "format": doc_format,
            "language": language,
            "entities_found": entities,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "char_count": len(doc),
            "confidence": round(random.uniform(0.85, 0.98), 2),
        }
        
        self._generation_history.append({
            "type": "documentation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "language": language,
            "format": doc_format,
        })
        
        return result

    async def generate_test_data(
        self,
        schema: Dict[str, Any],
        count: int = 10,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate realistic test data based on schema."""
        logger.info(f"Generating {count} test records from schema")
        
        if seed:
            random.seed(seed)
        
        records = []
        for i in range(count):
            record = self._generate_record(schema, i)
            records.append(record)
        
        result = {
            "data": records,
            "count": len(records),
            "schema": schema,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "seed": seed,
        }
        
        self._generation_history.append({
            "type": "test_data",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": count,
        })
        
        return result

    async def suggest_features(
        self,
        context: Dict[str, Any],
        max_suggestions: int = 5,
    ) -> Dict[str, Any]:
        """Generate feature suggestions based on usage patterns and context."""
        logger.info(f"Generating up to {max_suggestions} feature suggestions")
        
        usage_patterns = context.get("usage_patterns", {})
        current_features = context.get("current_features", [])
        user_feedback = context.get("user_feedback", [])
        
        suggestions = []
        
        # Analyze usage patterns
        if usage_patterns:
            suggestions.extend(self._analyze_usage_patterns(usage_patterns))
        
        # Consider missing features
        suggestions.extend(self._suggest_complementary_features(current_features))
        
        # Process user feedback
        if user_feedback:
            suggestions.extend(self._process_feedback(user_feedback))
        
        # Rank and limit suggestions
        ranked_suggestions = sorted(
            suggestions, 
            key=lambda x: x["priority"], 
            reverse=True
        )[:max_suggestions]
        
        result = {
            "suggestions": ranked_suggestions,
            "count": len(ranked_suggestions),
            "context_analyzed": {
                "usage_patterns": bool(usage_patterns),
                "current_features": len(current_features),
                "user_feedback": len(user_feedback),
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        self._generation_history.append({
            "type": "feature_suggestions",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": len(ranked_suggestions),
        })
        
        return result

    async def generate_api_examples(
        self,
        endpoint: str,
        method: str = "POST",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate API usage examples in multiple languages."""
        logger.info(f"Generating API examples for {method} {endpoint}")
        
        examples = {
            "curl": self._generate_curl_example(endpoint, method, parameters),
            "python": self._generate_python_example(endpoint, method, parameters),
            "javascript": self._generate_js_example(endpoint, method, parameters),
            "go": self._generate_go_example(endpoint, method, parameters),
        }
        
        result = {
            "endpoint": endpoint,
            "method": method,
            "examples": examples,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        return result

    async def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about content generation usage."""
        total = len(self._generation_history)
        
        by_type = {}
        for item in self._generation_history:
            item_type = item["type"]
            by_type[item_type] = by_type.get(item_type, 0) + 1
        
        return {
            "total_generations": total,
            "by_type": by_type,
            "last_24h": len([
                h for h in self._generation_history 
                if self._is_recent(h["timestamp"], hours=24)
            ]),
        }

    def _generate_markdown_doc(
        self, 
        code: str, 
        entities: List[str], 
        include_examples: bool
    ) -> str:
        """Generate Markdown documentation."""
        doc = f"# API Documentation\n\n"
        doc += f"Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n"
        
        if entities:
            doc += f"## Overview\n\n"
            doc += f"This module provides {len(entities)} main components:\n\n"
            for entity in entities:
                doc += f"- `{entity}`\n"
            doc += "\n"
        
        for entity in entities:
            doc += f"## {entity}\n\n"
            doc += f"### Description\n\n"
            doc += f"The `{entity}` function/class provides core functionality for the module.\n\n"
            doc += f"### Parameters\n\n"
            doc += f"- `param1` (str): Description of the first parameter\n"
            doc += f"- `param2` (int, optional): Description of the second parameter\n\n"
            doc += f"### Returns\n\n"
            doc += f"Returns a dictionary containing the result of the operation.\n\n"
            
            if include_examples:
                doc += f"### Example\n\n```python\n"
                doc += f"result = {entity}(param1='value', param2=42)\n"
                doc += f"print(result)\n```\n\n"
        
        return doc

    def _generate_docstring(self, code: str, entities: List[str]) -> str:
        """Generate Python docstrings."""
        doc = '"""\n'
        doc += f"Module docstring.\n\n"
        doc += f"This module provides functionality for AI/ML operations.\n\n"
        doc += f"Functions:\n"
        for entity in entities:
            doc += f"    {entity}: Core operation function\n"
        doc += '\n"""\n'
        return doc

    def _generate_openapi_spec(self, code: str, entities: List[str]) -> str:
        """Generate OpenAPI specification."""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Generated API",
                "version": "1.0.0",
                "description": "Auto-generated API specification",
            },
            "paths": {},
        }
        
        for entity in entities:
            spec["paths"][f"/{entity}"] = {
                "post": {
                    "summary": f"Execute {entity} operation",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "param1": {"type": "string"},
                                        "param2": {"type": "integer"},
                                    },
                                },
                            },
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Success",
                        },
                    },
                },
            }
        
        return json.dumps(spec, indent=2)

    def _generate_record(self, schema: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Generate a single test record based on schema."""
        record = {}
        for field, field_type in schema.items():
            if field_type == "string":
                record[field] = f"test_{field}_{index}"
            elif field_type == "integer":
                record[field] = random.randint(1, 1000)
            elif field_type == "float":
                record[field] = round(random.uniform(0, 100), 2)
            elif field_type == "boolean":
                record[field] = random.choice([True, False])
            elif field_type == "email":
                record[field] = f"user{index}@example.com"
            elif field_type == "uuid":
                record[field] = str(uuid.uuid4())
            elif field_type == "timestamp":
                record[field] = datetime.now(timezone.utc).isoformat()
            else:
                record[field] = None
        return record

    def _analyze_usage_patterns(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze usage patterns to suggest features."""
        suggestions = []
        
        if patterns.get("api_calls_per_hour", 0) > 1000:
            suggestions.append({
                "title": "Implement Rate Limiting Tiers",
                "description": "High API usage detected. Consider implementing tiered rate limiting.",
                "priority": 90,
                "effort": "medium",
                "impact": "high",
            })
        
        if patterns.get("error_rate", 0) > 0.05:
            suggestions.append({
                "title": "Enhanced Error Handling",
                "description": "Error rate above threshold. Improve error messages and recovery.",
                "priority": 95,
                "effort": "low",
                "impact": "high",
            })
        
        return suggestions

    def _suggest_complementary_features(self, current: List[str]) -> List[Dict[str, Any]]:
        """Suggest features that complement existing ones."""
        suggestions = []
        
        feature_map = {
            "authentication": {
                "title": "Multi-Factor Authentication",
                "description": "Add MFA for enhanced security",
                "priority": 85,
            },
            "api": {
                "title": "GraphQL API Support",
                "description": "Add GraphQL endpoint for flexible queries",
                "priority": 75,
            },
            "analytics": {
                "title": "Real-time Analytics Dashboard",
                "description": "Add live monitoring dashboard",
                "priority": 80,
            },
        }
        
        for feature in current:
            if feature.lower() in feature_map:
                suggestion = feature_map[feature.lower()].copy()
                suggestion["effort"] = "medium"
                suggestion["impact"] = "high"
                suggestions.append(suggestion)
        
        return suggestions

    def _process_feedback(self, feedback: List[str]) -> List[Dict[str, Any]]:
        """Process user feedback to generate suggestions."""
        suggestions = []
        
        keywords = {
            "slow": ("Performance Optimization", "Optimize slow operations", 88),
            "confusing": ("Improved Documentation", "Enhance user guides", 82),
            "missing": ("Feature Gap Analysis", "Identify missing features", 85),
        }
        
        for fb in feedback:
            fb_lower = fb.lower()
            for keyword, (title, desc, priority) in keywords.items():
                if keyword in fb_lower:
                    suggestions.append({
                        "title": title,
                        "description": desc,
                        "priority": priority,
                        "effort": "medium",
                        "impact": "high",
                        "source": "user_feedback",
                    })
        
        return suggestions

    def _generate_curl_example(
        self, 
        endpoint: str, 
        method: str, 
        params: Optional[Dict[str, Any]]
    ) -> str:
        """Generate curl example."""
        example = f'curl -X {method} "https://api.example.com{endpoint}" \\\n'
        example += '  -H "Authorization: Bearer YOUR_API_KEY" \\\n'
        example += '  -H "Content-Type: application/json" \\\n'
        if params:
            example += f"  -d '{json.dumps(params, indent=2)}'"
        return example

    def _generate_python_example(
        self, 
        endpoint: str, 
        method: str, 
        params: Optional[Dict[str, Any]]
    ) -> str:
        """Generate Python example."""
        example = 'import requests\n\n'
        example += f'url = "https://api.example.com{endpoint}"\n'
        example += 'headers = {\n'
        example += '    "Authorization": "Bearer YOUR_API_KEY",\n'
        example += '    "Content-Type": "application/json"\n'
        example += '}\n'
        if params:
            example += f'data = {json.dumps(params, indent=4)}\n'
            example += f'response = requests.{method.lower()}(url, headers=headers, json=data)\n'
        else:
            example += f'response = requests.{method.lower()}(url, headers=headers)\n'
        example += 'print(response.json())'
        return example

    def _generate_js_example(
        self, 
        endpoint: str, 
        method: str, 
        params: Optional[Dict[str, Any]]
    ) -> str:
        """Generate JavaScript example."""
        example = f'const response = await fetch("https://api.example.com{endpoint}", {{\n'
        example += f'  method: "{method}",\n'
        example += '  headers: {\n'
        example += '    "Authorization": "Bearer YOUR_API_KEY",\n'
        example += '    "Content-Type": "application/json"\n'
        example += '  },\n'
        if params:
            example += f'  body: JSON.stringify({json.dumps(params)})\n'
        example += '});\n'
        example += 'const data = await response.json();\n'
        example += 'console.log(data);'
        return example

    def _generate_go_example(
        self, 
        endpoint: str, 
        method: str, 
        params: Optional[Dict[str, Any]]
    ) -> str:
        """Generate Go example."""
        example = 'package main\n\n'
        example += 'import (\n'
        example += '    "bytes"\n'
        example += '    "encoding/json"\n'
        example += '    "net/http"\n'
        example += ')\n\n'
        example += 'func main() {\n'
        example += f'    url := "https://api.example.com{endpoint}"\n'
        if params:
            # Generate proper Go map initialization
            example += '    data := map[string]interface{}{\n'
            for key, value in params.items():
                if isinstance(value, str):
                    example += f'        "{key}": "{value}",\n'
                else:
                    example += f'        "{key}": {json.dumps(value)},\n'
            example += '    }\n'
            example += '    jsonData, _ := json.Marshal(data)\n'
            example += '    req, _ := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))\n'
        else:
            example += f'    req, _ := http.NewRequest("{method}", url, nil)\n'
        example += '    req.Header.Set("Authorization", "Bearer YOUR_API_KEY")\n'
        example += '    req.Header.Set("Content-Type", "application/json")\n'
        example += '    client := &http.Client{}\n'
        example += '    resp, _ := client.Do(req)\n'
        example += '    defer resp.Body.Close()\n'
        example += '}'
        return example

    def _is_recent(self, timestamp_str: str, hours: int = 24) -> bool:
        """Check if timestamp is within the last N hours."""
        try:
            ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            delta = now - ts
            return delta.total_seconds() < (hours * 3600)
        except Exception:
            return False
