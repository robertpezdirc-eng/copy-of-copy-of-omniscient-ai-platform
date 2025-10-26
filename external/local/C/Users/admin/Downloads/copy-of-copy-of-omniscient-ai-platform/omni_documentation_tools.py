#!/usr/bin/env python3
"""
OMNI Platform Documentation Tools
Comprehensive documentation and knowledge management tools

This module provides professional-grade documentation tools for:
- Wiki management and content organization
- Knowledge base creation and maintenance
- Automated document generation
- Tutorial and guide creation
- Changelog management and versioning
- API documentation generation

Author: OMNI Platform Documentation Tools
Version: 3.0.0
"""

import asyncio
import json
import time
import os
import sys
import logging
import threading
import subprocess
import re
import markdown
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
import shutil

class DocumentationType(Enum):
    """Documentation content types"""
    WIKI = "wiki"
    TUTORIAL = "tutorial"
    GUIDE = "guide"
    API_DOC = "api_doc"
    CHANGELOG = "changelog"
    KNOWLEDGE_BASE = "knowledge_base"

class ContentStatus(Enum):
    """Content status levels"""
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"

@dataclass
class DocumentationPage:
    """Documentation page structure"""
    page_id: str
    title: str
    content: str
    content_type: DocumentationType
    status: ContentStatus
    author: str
    created_at: float
    updated_at: float
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class KnowledgeEntry:
    """Knowledge base entry"""
    entry_id: str
    question: str
    answer: str
    category: str
    tags: List[str]
    confidence: float
    created_at: float
    updated_at: float
    usage_count: int = 0

class OmniWikiManager:
    """Wiki management and content organization tool"""

    def __init__(self):
        self.manager_name = "OMNI Wiki Manager"
        self.version = "3.0.0"
        self.start_time = time.time()
        self.wiki_pages: Dict[str, DocumentationPage] = {}
        self.wiki_structure: Dict[str, Any] = {}
        self.logger = self._setup_logging()

        # Wiki configuration
        self.config = {
            "wiki_path": "./wiki",
            "default_template": "# {title}\n\n{content}",
            "auto_save": True,
            "version_control": True,
            "search_index": True
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for wiki manager"""
        logger = logging.getLogger('OmniWikiManager')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.FileHandler('omni_wiki_manager.log', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def create_page(self, title: str, content: str, content_type: DocumentationType = DocumentationType.WIKI, author: str = "system") -> str:
        """Create new wiki page"""
        page_id = f"page_{int(time.time())}"

        page = DocumentationPage(
            page_id=page_id,
            title=title,
            content=content,
            content_type=content_type,
            status=ContentStatus.DRAFT,
            author=author,
            created_at=time.time(),
            updated_at=time.time(),
            tags=self._extract_tags_from_content(content)
        )

        self.wiki_pages[page_id] = page

        # Update wiki structure
        self._update_wiki_structure()

        self.logger.info(f"Created wiki page: {page_id} - {title}")
        return page_id

    def update_page(self, page_id: str, title: str = None, content: str = None, status: ContentStatus = None) -> bool:
        """Update existing wiki page"""
        try:
            if page_id not in self.wiki_pages:
                self.logger.error(f"Page not found: {page_id}")
                return False

            page = self.wiki_pages[page_id]

            if title is not None:
                page.title = title

            if content is not None:
                page.content = content
                page.tags = self._extract_tags_from_content(content)

            if status is not None:
                page.status = status

            page.updated_at = time.time()

            # Update wiki structure
            self._update_wiki_structure()

            self.logger.info(f"Updated wiki page: {page_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating page {page_id}: {e}")
            return False

    def _extract_tags_from_content(self, content: str) -> List[str]:
        """Extract tags from content"""
        tags = []

        # Look for hashtag patterns
        hashtag_pattern = r'#(\w+)'
        found_tags = re.findall(hashtag_pattern, content)

        # Look for common keywords
        keywords = [
            'installation', 'configuration', 'deployment', 'monitoring',
            'troubleshooting', 'api', 'security', 'performance', 'backup'
        ]

        content_lower = content.lower()
        for keyword in keywords:
            if keyword in content_lower:
                tags.append(keyword)

        # Combine and deduplicate
        all_tags = list(set(found_tags + tags))
        return all_tags[:10]  # Limit to 10 tags

    def _update_wiki_structure(self):
        """Update wiki navigation structure"""
        self.wiki_structure = {
            "pages": {},
            "categories": {},
            "tags": {},
            "last_updated": time.time()
        }

        # Organize pages by type and status
        for page_id, page in self.wiki_pages.items():
            page_info = {
                "page_id": page_id,
                "title": page.title,
                "status": page.status.value,
                "updated_at": page.updated_at,
                "tags": page.tags
            }

            self.wiki_structure["pages"][page_id] = page_info

            # Organize by content type
            content_type = page.content_type.value
            if content_type not in self.wiki_structure["categories"]:
                self.wiki_structure["categories"][content_type] = []
            self.wiki_structure["categories"][content_type].append(page_id)

            # Organize by tags
            for tag in page.tags:
                if tag not in self.wiki_structure["tags"]:
                    self.wiki_structure["tags"][tag] = []
                self.wiki_structure["tags"][tag].append(page_id)

    def search_wiki(self, query: str, content_type: DocumentationType = None) -> List[Dict[str, Any]]:
        """Search wiki content"""
        results = []

        try:
            query_lower = query.lower()

            for page_id, page in self.wiki_pages.items():
                # Skip if content type filter is specified and doesn't match
                if content_type and page.content_type != content_type:
                    continue

                # Search in title
                title_match = query_lower in page.title.lower()

                # Search in content
                content_match = query_lower in page.content.lower()

                # Search in tags
                tag_match = any(query_lower in tag.lower() for tag in page.tags)

                if title_match or content_match or tag_match:
                    # Calculate relevance score
                    relevance = 0
                    if title_match:
                        relevance += 3
                    if tag_match:
                        relevance += 2
                    if content_match:
                        relevance += 1

                    results.append({
                        "page_id": page_id,
                        "title": page.title,
                        "content_type": page.content_type.value,
                        "status": page.status.value,
                        "relevance": relevance,
                        "updated_at": page.updated_at,
                        "tags": page.tags
                    })

            # Sort by relevance
            results.sort(key=lambda x: x["relevance"], reverse=True)

        except Exception as e:
            self.logger.error(f"Error searching wiki: {e}")

        return results

    def get_wiki_statistics(self) -> Dict[str, Any]:
        """Get wiki statistics and analytics"""
        total_pages = len(self.wiki_pages)

        if total_pages == 0:
            return {
                "total_pages": 0,
                "pages_by_type": {},
                "pages_by_status": {},
                "total_tags": 0,
                "most_used_tags": []
            }

        # Count by content type
        pages_by_type = {}
        for page in self.wiki_pages.values():
            content_type = page.content_type.value
            pages_by_type[content_type] = pages_by_type.get(content_type, 0) + 1

        # Count by status
        pages_by_status = {}
        for page in self.wiki_pages.values():
            status = page.status.value
            pages_by_status[status] = pages_by_status.get(status, 0) + 1

        # Count tag usage
        tag_usage = {}
        for page in self.wiki_pages.values():
            for tag in page.tags:
                tag_usage[tag] = tag_usage.get(tag, 0) + 1

        # Most used tags
        most_used_tags = sorted(tag_usage.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_pages": total_pages,
            "pages_by_type": pages_by_type,
            "pages_by_status": pages_by_status,
            "total_tags": len(tag_usage),
            "most_used_tags": most_used_tags,
            "last_updated": time.time()
        }

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute wiki manager tool"""
        action = parameters.get("action", "create_page")

        if action == "create_page":
            title = parameters.get("title", "")
            content = parameters.get("content", "")
            content_type = parameters.get("content_type", "wiki")
            author = parameters.get("author", "system")

            if not title or not content:
                return {"status": "error", "message": "Title and content required"}

            try:
                doc_type = DocumentationType(content_type)
                page_id = self.create_page(title, content, doc_type, author)
                return {"status": "success", "page_id": page_id}
            except ValueError:
                return {"status": "error", "message": f"Invalid content type: {content_type}"}

        elif action == "update_page":
            page_id = parameters.get("page_id", "")
            title = parameters.get("title")
            content = parameters.get("content")
            status = parameters.get("status")

            if not page_id:
                return {"status": "error", "message": "Page ID required"}

            try:
                if status:
                    status_enum = ContentStatus(status)
                else:
                    status_enum = None

                success = self.update_page(page_id, title, content, status_enum)
                return {"status": "success" if success else "error", "message": "Page updated"}
            except ValueError:
                return {"status": "error", "message": f"Invalid status: {status}"}

        elif action == "search":
            query = parameters.get("query", "")
            content_type = parameters.get("content_type")

            if not query:
                return {"status": "error", "message": "Query required"}

            try:
                doc_type = DocumentationType(content_type) if content_type else None
                results = self.search_wiki(query, doc_type)
                return {"status": "success", "data": results}
            except ValueError:
                return {"status": "error", "message": f"Invalid content type: {content_type}"}

        elif action == "get_stats":
            stats = self.get_wiki_statistics()
            return {"status": "success", "data": stats}

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

class OmniKnowledgeBase:
    """Knowledge base creation and maintenance tool"""

    def __init__(self):
        self.kb_name = "OMNI Knowledge Base"
        self.version = "3.0.0"
        self.start_time = time.time()
        self.knowledge_entries: Dict[str, KnowledgeEntry] = {}
        self.categories: Dict[str, List[str]] = {}
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for knowledge base"""
        logger = logging.getLogger('OmniKnowledgeBase')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.FileHandler('omni_knowledge_base.log', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def add_knowledge_entry(self, question: str, answer: str, category: str, tags: List[str] = None) -> str:
        """Add new knowledge base entry"""
        entry_id = f"kb_{int(time.time())}"

        if tags is None:
            tags = []

        entry = KnowledgeEntry(
            entry_id=entry_id,
            question=question,
            answer=answer,
            category=category,
            tags=tags,
            confidence=0.8,  # Default confidence
            created_at=time.time(),
            updated_at=time.time(),
            usage_count=0
        )

        self.knowledge_entries[entry_id] = entry

        # Update categories
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(entry_id)

        self.logger.info(f"Added knowledge entry: {entry_id}")
        return entry_id

    def search_knowledge_base(self, query: str, category: str = None, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant entries"""
        results = []

        try:
            query_lower = query.lower()

            for entry_id, entry in self.knowledge_entries.items():
                # Skip if category filter is specified and doesn't match
                if category and entry.category != category:
                    continue

                # Skip if confidence is too low
                if entry.confidence < min_confidence:
                    continue

                # Search in question
                question_match = query_lower in entry.question.lower()

                # Search in answer
                answer_match = query_lower in entry.answer.lower()

                # Search in tags
                tag_match = any(query_lower in tag.lower() for tag in entry.tags)

                if question_match or answer_match or tag_match:
                    # Calculate relevance score
                    relevance = 0
                    if question_match:
                        relevance += 3
                    if tag_match:
                        relevance += 2
                    if answer_match:
                        relevance += 1

                    # Boost by usage count and confidence
                    relevance += entry.usage_count * 0.1
                    relevance += entry.confidence * 0.5

                    results.append({
                        "entry_id": entry_id,
                        "question": entry.question,
                        "answer": entry.answer,
                        "category": entry.category,
                        "confidence": entry.confidence,
                        "usage_count": entry.usage_count,
                        "relevance": relevance,
                        "tags": entry.tags
                    })

            # Sort by relevance
            results.sort(key=lambda x: x["relevance"], reverse=True)

        except Exception as e:
            self.logger.error(f"Error searching knowledge base: {e}")

        return results

    def update_entry_confidence(self, entry_id: str, confidence: float):
        """Update confidence score for knowledge entry"""
        if entry_id in self.knowledge_entries:
            self.knowledge_entries[entry_id].confidence = max(0.0, min(1.0, confidence))
            self.knowledge_entries[entry_id].updated_at = time.time()

    def get_knowledge_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        total_entries = len(self.knowledge_entries)

        if total_entries == 0:
            return {
                "total_entries": 0,
                "categories": {},
                "average_confidence": 0.0,
                "total_usage": 0
            }

        # Count by category
        categories = {}
        total_confidence = 0
        total_usage = 0

        for entry in self.knowledge_entries.values():
            categories[entry.category] = categories.get(entry.category, 0) + 1
            total_confidence += entry.confidence
            total_usage += entry.usage_count

        average_confidence = total_confidence / total_entries

        return {
            "total_entries": total_entries,
            "categories": categories,
            "average_confidence": average_confidence,
            "total_usage": total_usage,
            "high_confidence_entries": len([e for e in self.knowledge_entries.values() if e.confidence > 0.8])
        }

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge base tool"""
        action = parameters.get("action", "add_entry")

        if action == "add_entry":
            question = parameters.get("question", "")
            answer = parameters.get("answer", "")
            category = parameters.get("category", "general")
            tags = parameters.get("tags", [])

            if not question or not answer:
                return {"status": "error", "message": "Question and answer required"}

            entry_id = self.add_knowledge_entry(question, answer, category, tags)
            return {"status": "success", "entry_id": entry_id}

        elif action == "search":
            query = parameters.get("query", "")
            category = parameters.get("category")
            min_confidence = parameters.get("min_confidence", 0.0)

            if not query:
                return {"status": "error", "message": "Query required"}

            results = self.search_knowledge_base(query, category, min_confidence)
            return {"status": "success", "data": results}

        elif action == "get_stats":
            stats = self.get_knowledge_statistics()
            return {"status": "success", "data": stats}

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

class OmniDocumentGenerator:
    """Automated document generation tool"""

    def __init__(self):
        self.generator_name = "OMNI Document Generator"
        self.version = "3.0.0"
        self.start_time = time.time()
        self.templates: Dict[str, str] = {}
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for document generator"""
        logger = logging.getLogger('OmniDocumentGenerator')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.FileHandler('omni_document_generator.log', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def generate_api_documentation(self, code_path: str, output_format: str = "markdown") -> Dict[str, Any]:
        """Generate API documentation from code"""
        result = {
            "generated": False,
            "output_path": "",
            "endpoints_found": 0,
            "functions_documented": 0,
            "classes_documented": 0,
            "content": ""
        }

        try:
            # Analyze code for API endpoints and functions
            api_analysis = self._analyze_code_for_api(code_path)

            if output_format.lower() == "markdown":
                content = self._generate_markdown_api_docs(api_analysis)
            elif output_format.lower() == "html":
                content = self._generate_html_api_docs(api_analysis)
            else:
                content = self._generate_text_api_docs(api_analysis)

            # Save documentation
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_documentation_{timestamp}.{output_format.lower()}"
            output_path = os.path.join("./docs", filename)

            os.makedirs("./docs", exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            result.update({
                "generated": True,
                "output_path": output_path,
                "endpoints_found": api_analysis.get("endpoints", 0),
                "functions_documented": api_analysis.get("functions", 0),
                "classes_documented": api_analysis.get("classes", 0),
                "content": content
            })

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"API documentation generation failed: {e}")

        return result

    def _analyze_code_for_api(self, code_path: str) -> Dict[str, Any]:
        """Analyze code for API components"""
        analysis = {
            "endpoints": 0,
            "functions": 0,
            "classes": 0,
            "modules": []
        }

        try:
            if os.path.isfile(code_path):
                # Analyze single file
                module_analysis = self._analyze_python_file_for_api(code_path)
                analysis["modules"].append(module_analysis)

                analysis["functions"] += module_analysis.get("functions", 0)
                analysis["classes"] += module_analysis.get("classes", 0)

            elif os.path.isdir(code_path):
                # Analyze directory
                for root, dirs, files in os.walk(code_path):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            module_analysis = self._analyze_python_file_for_api(file_path)
                            analysis["modules"].append(module_analysis)

                            analysis["functions"] += module_analysis.get("functions", 0)
                            analysis["classes"] += module_analysis.get("classes", 0)

        except Exception as e:
            self.logger.error(f"Error analyzing code for API: {e}")

        return analysis

    def _analyze_python_file_for_api(self, file_path: str) -> Dict[str, Any]:
        """Analyze Python file for API components"""
        module_analysis = {
            "file_path": file_path,
            "functions": 0,
            "classes": 0,
            "function_details": [],
            "class_details": []
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST
            import ast
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    module_analysis["functions"] += 1

                    # Extract function information
                    func_info = {
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node) or "",
                        "line_number": node.lineno
                    }

                    module_analysis["function_details"].append(func_info)

                elif isinstance(node, ast.ClassDef):
                    module_analysis["classes"] += 1

                    # Extract class information
                    class_info = {
                        "name": node.name,
                        "methods": [],
                        "docstring": ast.get_docstring(node) or "",
                        "line_number": node.lineno
                    }

                    # Extract methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                "name": item.name,
                                "args": [arg.arg for arg in item.args.args],
                                "docstring": ast.get_docstring(item) or "",
                                "line_number": item.lineno
                            }
                            class_info["methods"].append(method_info)

                    module_analysis["class_details"].append(class_info)

        except Exception as e:
            self.logger.error(f"Error analyzing Python file {file_path}: {e}")

        return module_analysis

    def _generate_markdown_api_docs(self, analysis: Dict[str, Any]) -> str:
        """Generate Markdown API documentation"""
        content = ["# API Documentation", ""]

        for module in analysis.get("modules", []):
            file_path = module["file_path"]
            content.append(f"## Module: {os.path.basename(file_path)}")
            content.append("")

            # Document functions
            if module["function_details"]:
                content.append("### Functions")
                content.append("")

                for func in module["function_details"]:
                    content.append(f"#### `{func['name']}`")
                    content.append("")

                    if func["docstring"]:
                        content.append(f"{func['docstring']}")
                        content.append("")

                    args_str = ", ".join(func["args"])
                    content.append(f"**Parameters:** `{args_str}`")
                    content.append("")

            # Document classes
            if module["class_details"]:
                content.append("### Classes")
                content.append("")

                for cls in module["class_details"]:
                    content.append(f"#### `{cls['name']}`")
                    content.append("")

                    if cls["docstring"]:
                        content.append(f"{cls['docstring']}")
                        content.append("")

                    # Document methods
                    if cls["methods"]:
                        content.append("**Methods:**")
                        content.append("")

                        for method in cls["methods"]:
                            content.append(f"- `{method['name']}` - {method['docstring'][:50]}...")
                            if method["docstring"]:
                                content.append(f"  - {method['docstring']}")

                        content.append("")

            content.append("---")
            content.append("")

        return "\n".join(content)

    def _generate_html_api_docs(self, analysis: Dict[str, Any]) -> str:
        """Generate HTML API documentation"""
        content = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>API Documentation</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; }",
            "h1, h2, h3 { color: #333; }",
            "code { background-color: #f4f4f4; padding: 2px 4px; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>API Documentation</h1>"
        ]

        for module in analysis.get("modules", []):
            content.append(f"<h2>Module: {os.path.basename(module['file_path'])}</h2>")

            # Document functions
            if module["function_details"]:
                content.append("<h3>Functions</h3>")
                content.append("<ul>")

                for func in module["function_details"]:
                    content.append(f"<li><code>{func['name']}</code> - {func['docstring'][:100]}...</li>")

                content.append("</ul>")

            # Document classes
            if module["class_details"]:
                content.append("<h3>Classes</h3>")
                content.append("<ul>")

                for cls in module["class_details"]:
                    content.append(f"<li><code>{cls['name']}</code> - {cls['docstring'][:100]}...</li>")

                content.append("</ul>")

        content.extend([
            "</body>",
            "</html>"
        ])

        return "\n".join(content)

    def _generate_text_api_docs(self, analysis: Dict[str, Any]) -> str:
        """Generate plain text API documentation"""
        content = ["API Documentation", "=" * 50, ""]

        for module in analysis.get("modules", []):
            content.append(f"Module: {os.path.basename(module['file_path'])}")
            content.append("-" * 30)

            # Document functions
            if module["function_details"]:
                content.append("Functions:")
                for func in module["function_details"]:
                    content.append(f"  {func['name']} - {func['docstring'][:80]}...")

            # Document classes
            if module["class_details"]:
                content.append("Classes:")
                for cls in module["class_details"]:
                    content.append(f"  {cls['name']} - {cls['docstring'][:80]}...")

            content.append("")

        return "\n".join(content)

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute document generator tool"""
        action = parameters.get("action", "generate_api_docs")

        if action == "generate_api_docs":
            code_path = parameters.get("code_path", ".")
            output_format = parameters.get("output_format", "markdown")

            result = self.generate_api_documentation(code_path, output_format)
            return {"status": "success" if result["generated"] else "error", "data": result}

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

class OmniChangelogManager:
    """Changelog management and versioning tool"""

    def __init__(self):
        self.manager_name = "OMNI Changelog Manager"
        self.version = "3.0.0"
        self.start_time = time.time()
        self.changelog_entries: List[Dict[str, Any]] = []
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for changelog manager"""
        logger = logging.getLogger('OmniChangelogManager')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.FileHandler('omni_changelog_manager.log', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def add_changelog_entry(self, version: str, changes: List[str], change_type: str = "feature") -> bool:
        """Add new changelog entry"""
        try:
            entry = {
                "entry_id": f"changelog_{int(time.time())}",
                "version": version,
                "change_type": change_type,
                "changes": changes,
                "timestamp": time.time(),
                "author": "system"
            }

            self.changelog_entries.append(entry)

            # Sort by version (assuming semantic versioning)
            self.changelog_entries.sort(key=lambda x: self._version_to_tuple(x["version"]), reverse=True)

            self.logger.info(f"Added changelog entry for version {version}")
            return True

        except Exception as e:
            self.logger.error(f"Error adding changelog entry: {e}")
            return False

    def _version_to_tuple(self, version: str) -> Tuple[int, int, int]:
        """Convert version string to comparable tuple"""
        try:
            # Remove 'v' prefix if present
            version = version.lstrip('v')

            # Split by dots
            parts = version.split('.')
            if len(parts) >= 3:
                return (int(parts[0]), int(parts[1]), int(parts[2]))
            elif len(parts) >= 2:
                return (int(parts[0]), int(parts[1]), 0)
            else:
                return (int(parts[0]), 0, 0)
        except:
            return (0, 0, 0)

    def generate_changelog(self, output_format: str = "markdown") -> str:
        """Generate formatted changelog"""
        if output_format.lower() == "markdown":
            return self._generate_markdown_changelog()
        elif output_format.lower() == "html":
            return self._generate_html_changelog()
        else:
            return self._generate_text_changelog()

    def _generate_markdown_changelog(self) -> str:
        """Generate Markdown changelog"""
        content = ["# Changelog", ""]

        current_version = None

        for entry in self.changelog_entries:
            version = entry["version"]

            if version != current_version:
                content.append(f"## Version {version}")
                content.append("")
                current_version = version

            # Group changes by type
            changes_by_type = {}
            for change in entry["changes"]:
                # Determine change type from content
                if any(keyword in change.lower() for keyword in ["fix", "bug", "error", "issue"]):
                    change_type = "bug_fixes"
                elif any(keyword in change.lower() for keyword in ["add", "new", "feature"]):
                    change_type = "features"
                elif any(keyword in change.lower() for keyword in ["update", "improve", "enhance"]):
                    change_type = "improvements"
                else:
                    change_type = "other"

                if change_type not in changes_by_type:
                    changes_by_type[change_type] = []
                changes_by_type[change_type].append(change)

            # Add changes by type
            type_headers = {
                "features": "### Features",
                "improvements": "### Improvements",
                "bug_fixes": "### Bug Fixes",
                "other": "### Other Changes"
            }

            for change_type, changes in changes_by_type.items():
                if change_type in type_headers:
                    content.append(type_headers[change_type])
                    content.append("")

                    for change in changes:
                        content.append(f"- {change}")

                    content.append("")

        return "\n".join(content)

    def _generate_html_changelog(self) -> str:
        """Generate HTML changelog"""
        content = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Changelog</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; }",
            "h1, h2, h3 { color: #333; }",
            "ul { line-height: 1.6; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Changelog</h1>"
        ]

        current_version = None

        for entry in self.changelog_entries:
            version = entry["version"]

            if version != current_version:
                content.append(f"<h2>Version {version}</h2>")
                current_version = version

            content.append("<ul>")

            for change in entry["changes"]:
                content.append(f"<li>{change}</li>")

            content.append("</ul>")

        content.extend([
            "</body>",
            "</html>"
        ])

        return "\n".join(content)

    def _generate_text_changelog(self) -> str:
        """Generate plain text changelog"""
        content = ["Changelog", "=" * 30, ""]

        current_version = None

        for entry in self.changelog_entries:
            version = entry["version"]

            if version != current_version:
                content.append(f"Version {version}")
                content.append("-" * 20)
                current_version = version

            for change in entry["changes"]:
                content.append(f"  - {change}")

            content.append("")

        return "\n".join(content)

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute changelog manager tool"""
        action = parameters.get("action", "add_entry")

        if action == "add_entry":
            version = parameters.get("version", "")
            changes = parameters.get("changes", [])
            change_type = parameters.get("change_type", "feature")

            if not version or not changes:
                return {"status": "error", "message": "Version and changes required"}

            success = self.add_changelog_entry(version, changes, change_type)
            return {"status": "success" if success else "error", "message": "Changelog entry added"}

        elif action == "generate":
            output_format = parameters.get("output_format", "markdown")
            changelog = self.generate_changelog(output_format)
            return {"status": "success", "data": {"content": changelog, "format": output_format}}

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

# Global tool instances
omni_wiki_manager = OmniWikiManager()
omni_knowledge_base = OmniKnowledgeBase()
omni_document_generator = OmniDocumentGenerator()
omni_changelog_manager = OmniChangelogManager()

def main():
    """Main function to run documentation tools"""
    print("[OMNI] Documentation Tools - Knowledge & Content Management Suite")
    print("=" * 70)
    print("[WIKI] Wiki management and content organization")
    print("[KNOWLEDGE] Knowledge base creation and maintenance")
    print("[DOCS] Automated document generation")
    print("[CHANGELOG] Changelog management and versioning")
    print()

    try:
        # Demonstrate wiki manager
        print("[DEMO] Wiki Manager Demo:")

        # Create sample wiki pages
        pages = [
            {
                "title": "Getting Started with OMNI",
                "content": "# Getting Started\n\nThis is a guide to get started with the OMNI platform. #installation #guide",
                "content_type": DocumentationType.TUTORIAL
            },
            {
                "title": "API Reference",
                "content": "# API Reference\n\nComplete API documentation for developers. #api #documentation",
                "content_type": DocumentationType.API_DOC
            }
        ]

        for page in pages:
            page_id = omni_wiki_manager.create_page(
                page["title"],
                page["content"],
                page["content_type"]
            )
            print(f"  [PAGE] Created: {page['title']} (ID: {page_id})")

        # Search wiki
        search_results = omni_wiki_manager.search_wiki("API")
        print(f"  [SEARCH] Found {len(search_results)} results for 'API'")

        # Demonstrate knowledge base
        print("\n[DEMO] Knowledge Base Demo:")

        # Add knowledge entries
        kb_entries = [
            {
                "question": "How do I install the OMNI platform?",
                "answer": "You can install OMNI by running the setup script or using the installation wizard.",
                "category": "installation",
                "tags": ["installation", "setup", "getting-started"]
            },
            {
                "question": "How do I configure the API endpoints?",
                "answer": "API endpoints can be configured in the configuration file or through the web interface.",
                "category": "configuration",
                "tags": ["api", "configuration", "endpoints"]
            }
        ]

        for entry in kb_entries:
            entry_id = omni_knowledge_base.add_knowledge_entry(
                entry["question"],
                entry["answer"],
                entry["category"],
                entry["tags"]
            )
            print(f"  [KB] Added: {entry['question'][:50]}... (ID: {entry_id})")

        # Search knowledge base
        kb_results = omni_knowledge_base.search_knowledge_base("install")
        print(f"  [KB_SEARCH] Found {len(kb_results)} results for 'install'")

        # Demonstrate document generator
        print("\n[DEMO] Document Generator Demo:")

        # Generate API documentation
        doc_result = omni_document_generator.generate_api_documentation(".", "markdown")
        print(f"  [DOCS] Generated: {doc_result['generated']}")
        print(f"  [OUTPUT] File: {doc_result['output_path']}")
        print(f"  [FUNCTIONS] Documented: {doc_result['functions_documented']}")

        # Demonstrate changelog manager
        print("\n[DEMO] Changelog Manager Demo:")

        # Add changelog entries
        changelog_entries = [
            {
                "version": "3.0.0",
                "changes": [
                    "Added comprehensive assistance tools framework",
                    "Implemented operational monitoring and management tools",
                    "Added security and compliance tools",
                    "Enhanced API management capabilities"
                ],
                "change_type": "feature"
            },
            {
                "version": "2.9.0",
                "changes": [
                    "Fixed performance issues in deployment pipeline",
                    "Updated security protocols",
                    "Improved error handling"
                ],
                "change_type": "bug_fix"
            }
        ]

        for entry in changelog_entries:
            omni_changelog_manager.add_changelog_entry(
                entry["version"],
                entry["changes"],
                entry["change_type"]
            )
            print(f"  [CHANGELOG] Added entry for version {entry['version']}")

        # Generate changelog
        changelog = omni_changelog_manager.generate_changelog("markdown")
        print(f"  [CHANGELOG] Generated changelog with {len(changelog.split('##')) - 1} versions")

        print("\n[SUCCESS] Documentation Tools Demonstration Complete!")
        print("=" * 70)
        print("[READY] All documentation tools are ready for professional use")
        print("[WIKI] Wiki management: Active")
        print("[KNOWLEDGE] Knowledge base: Available")
        print("[DOCS] Document generation: Operational")
        print("[CHANGELOG] Version management: Ready")

        return {
            "status": "success",
            "tools_demo": {
                "wiki_manager": "Active",
                "knowledge_base": "Active",
                "document_generator": "Active",
                "changelog_manager": "Active"
            }
        }

    except Exception as e:
        print(f"\n[ERROR] Documentation tools demo failed: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    result = main()
    print(f"\n[SUCCESS] Documentation tools execution completed")