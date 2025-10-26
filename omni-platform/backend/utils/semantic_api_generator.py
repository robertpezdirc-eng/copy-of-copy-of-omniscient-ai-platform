import os
import json
import inspect
from typing import Dict, Any, List, Optional, Union, get_type_hints
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
import re

@dataclass
class SemanticProperty:
    """Semantična lastnost"""
    name: str
    type: str
    description: str
    required: bool = False
    format: Optional[str] = None
    enum_values: Optional[List[str]] = None
    semantic_type: Optional[str] = None  # Schema.org tip
    context: Optional[str] = None

@dataclass
class SemanticOperation:
    """Semantična operacija"""
    operation_id: str
    method: str
    path: str
    summary: str
    description: str
    tags: List[str]
    parameters: List[SemanticProperty]
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = None
    semantic_action: Optional[str] = None  # Schema.org Action
    context: Optional[str] = None

@dataclass
class SemanticAPI:
    """Semantična API definicija"""
    name: str
    version: str
    description: str
    base_url: str
    operations: List[SemanticOperation]
    schemas: Dict[str, Dict[str, Any]]
    context: Dict[str, str]
    metadata: Dict[str, Any]

class SemanticAPIGenerator:
    """
    Generator semantične API dokumentacije.
    Ustvarja JSON-LD in W3C standards-compliant dokumentacijo.
    """
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.schema_org_context = {
            "@context": {
                "@vocab": "https://schema.org/",
                "api": "https://schema.org/WebAPI",
                "operation": "https://schema.org/Action",
                "parameter": "https://schema.org/PropertyValueSpecification",
                "response": "https://schema.org/Thing",
                "endpoint": "https://schema.org/EntryPoint",
                "method": "https://schema.org/httpMethod",
                "url": "https://schema.org/url",
                "name": "https://schema.org/name",
                "description": "https://schema.org/description",
                "version": "https://schema.org/version",
                "provider": "https://schema.org/provider",
                "documentation": "https://schema.org/documentation",
                "license": "https://schema.org/license",
                "termsOfService": "https://schema.org/termsOfService",
                "contact": "https://schema.org/contactPoint",
                "security": "https://schema.org/securityPolicy",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "owl": "http://www.w3.org/2002/07/owl#",
                "hydra": "http://www.w3.org/ns/hydra/core#",
                "omni": "https://omniscient-ai.com/ontology/"
            }
        }
        
        # Mapiranje HTTP metod na Schema.org Actions
        self.method_to_action = {
            "GET": "ReadAction",
            "POST": "CreateAction", 
            "PUT": "UpdateAction",
            "PATCH": "UpdateAction",
            "DELETE": "DeleteAction",
            "HEAD": "ReadAction",
            "OPTIONS": "ReadAction"
        }
        
        # Mapiranje Python tipov na Schema.org tipe
        self.type_mapping = {
            "str": "Text",
            "int": "Integer",
            "float": "Number",
            "bool": "Boolean",
            "list": "ItemList",
            "dict": "StructuredValue",
            "datetime": "DateTime",
            "date": "Date",
            "time": "Time",
            "uuid": "Text",
            "email": "Text",
            "url": "URL"
        }
    
    def generate_semantic_documentation(self) -> Dict[str, Any]:
        """Generiraj celotno semantično dokumentacijo"""
        
        # Pridobi OpenAPI spec
        openapi_spec = get_openapi(
            title=self.app.title,
            version=self.app.version,
            description=self.app.description,
            routes=self.app.routes,
        )
        
        # Ustvari semantično API strukturo
        semantic_api = self._create_semantic_api(openapi_spec)
        
        # Generiraj JSON-LD dokumentacijo
        jsonld_doc = self._generate_jsonld(semantic_api)
        
        # Generiraj Hydra dokumentacijo
        hydra_doc = self._generate_hydra(semantic_api)
        
        # Generiraj RDF/Turtle dokumentacijo
        turtle_doc = self._generate_turtle(semantic_api)
        
        return {
            "jsonld": jsonld_doc,
            "hydra": hydra_doc,
            "turtle": turtle_doc,
            "openapi": openapi_spec,
            "semantic_api": asdict(semantic_api),
            "generated_at": datetime.utcnow().isoformat(),
            "generator": {
                "name": "OmniscientAI Semantic API Generator",
                "version": "1.0.0",
                "standards": ["JSON-LD", "Schema.org", "Hydra", "RDF", "W3C"]
            }
        }
    
    def _create_semantic_api(self, openapi_spec: Dict[str, Any]) -> SemanticAPI:
        """Ustvari semantično API strukturo iz OpenAPI spec"""
        
        operations = []
        schemas = openapi_spec.get("components", {}).get("schemas", {})
        
        # Obdelaj vse poti
        for path, path_item in openapi_spec.get("paths", {}).items():
            for method, operation in path_item.items():
                if method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]:
                    semantic_op = self._create_semantic_operation(
                        path, method.upper(), operation, schemas
                    )
                    operations.append(semantic_op)
        
        # Ustvari kontekst
        context = self.schema_org_context["@context"].copy()
        context.update({
            "omni": "https://omniscient-ai.com/ontology/",
            "ai": "https://schema.org/SoftwareApplication",
            "ml": "https://schema.org/ComputerLanguage",
            "rl": "https://schema.org/Algorithm"
        })
        
        return SemanticAPI(
            name=openapi_spec.get("info", {}).get("title", "OmniscientAI API"),
            version=openapi_spec.get("info", {}).get("version", "1.0.0"),
            description=openapi_spec.get("info", {}).get("description", ""),
            base_url=openapi_spec.get("servers", [{}])[0].get("url", ""),
            operations=operations,
            schemas=self._enhance_schemas_with_semantics(schemas),
            context=context,
            metadata={
                "license": openapi_spec.get("info", {}).get("license"),
                "contact": openapi_spec.get("info", {}).get("contact"),
                "terms_of_service": openapi_spec.get("info", {}).get("termsOfService"),
                "external_docs": openapi_spec.get("externalDocs"),
                "tags": openapi_spec.get("tags", [])
            }
        )
    
    def _create_semantic_operation(self, path: str, method: str, operation: Dict[str, Any], schemas: Dict[str, Any]) -> SemanticOperation:
        """Ustvari semantično operacijo"""
        
        # Določi semantično akcijo
        semantic_action = self.method_to_action.get(method, "Action")
        
        # Določi kontekst glede na pot
        context = self._determine_operation_context(path, operation)
        
        # Obdelaj parametre
        parameters = []
        for param in operation.get("parameters", []):
            semantic_prop = SemanticProperty(
                name=param["name"],
                type=self._map_type_to_semantic(param.get("schema", {}).get("type", "string")),
                description=param.get("description", ""),
                required=param.get("required", False),
                format=param.get("schema", {}).get("format"),
                semantic_type=self._determine_parameter_semantic_type(param["name"], param.get("schema", {}))
            )
            parameters.append(semantic_prop)
        
        # Obdelaj request body
        request_body = None
        if "requestBody" in operation:
            request_body = self._process_request_body(operation["requestBody"], schemas)
        
        # Obdelaj responses
        responses = {}
        for status_code, response in operation.get("responses", {}).items():
            responses[status_code] = self._process_response(response, schemas)
        
        return SemanticOperation(
            operation_id=operation.get("operationId", f"{method.lower()}_{path.replace('/', '_')}"),
            method=method,
            path=path,
            summary=operation.get("summary", ""),
            description=operation.get("description", ""),
            tags=operation.get("tags", []),
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            semantic_action=semantic_action,
            context=context
        )
    
    def _determine_operation_context(self, path: str, operation: Dict[str, Any]) -> str:
        """Določi kontekst operacije"""
        
        # Analiziraj pot za določitev konteksta
        if "/learning" in path or "/policy" in path:
            return "omni:MachineLearning"
        elif "/agent" in path:
            return "omni:AIAgent"
        elif "/sensor" in path or "/websocket" in path:
            return "omni:SensorData"
        elif "/files" in path:
            return "omni:FileManagement"
        elif "/auth" in path or "/access" in path:
            return "omni:Authentication"
        elif "/billing" in path:
            return "omni:BillingService"
        elif "/monitor" in path:
            return "omni:Monitoring"
        else:
            return "omni:GeneralAPI"
    
    def _determine_parameter_semantic_type(self, param_name: str, schema: Dict[str, Any]) -> str:
        """Določi semantični tip parametra"""
        
        param_lower = param_name.lower()
        
        if "id" in param_lower:
            return "Identifier"
        elif "email" in param_lower:
            return "email"
        elif "url" in param_lower:
            return "URL"
        elif "date" in param_lower or "time" in param_lower:
            return "DateTime"
        elif "name" in param_lower:
            return "name"
        elif "description" in param_lower:
            return "description"
        elif "version" in param_lower:
            return "version"
        elif "status" in param_lower:
            return "status"
        else:
            return self._map_type_to_semantic(schema.get("type", "string"))
    
    def _map_type_to_semantic(self, python_type: str) -> str:
        """Mapira Python tip na Schema.org tip"""
        return self.type_mapping.get(python_type, "Thing")
    
    def _enhance_schemas_with_semantics(self, schemas: Dict[str, Any]) -> Dict[str, Any]:
        """Izboljša sheme s semantičnimi informacijami"""
        
        enhanced_schemas = {}
        
        for schema_name, schema in schemas.items():
            enhanced_schema = schema.copy()
            
            # Dodaj semantični tip
            enhanced_schema["@type"] = self._determine_schema_semantic_type(schema_name, schema)
            
            # Izboljšaj lastnosti
            if "properties" in enhanced_schema:
                for prop_name, prop_schema in enhanced_schema["properties"].items():
                    prop_schema["@type"] = self._determine_parameter_semantic_type(prop_name, prop_schema)
            
            enhanced_schemas[schema_name] = enhanced_schema
        
        return enhanced_schemas
    
    def _determine_schema_semantic_type(self, schema_name: str, schema: Dict[str, Any]) -> str:
        """Določi semantični tip sheme"""
        
        name_lower = schema_name.lower()
        
        if "user" in name_lower:
            return "Person"
        elif "agent" in name_lower:
            return "omni:AIAgent"
        elif "sensor" in name_lower:
            return "omni:SensorReading"
        elif "stream" in name_lower:
            return "omni:DataStream"
        elif "model" in name_lower:
            return "omni:MLModel"
        elif "policy" in name_lower:
            return "omni:Policy"
        elif "feedback" in name_lower:
            return "omni:Feedback"
        elif "request" in name_lower:
            return "Action"
        elif "response" in name_lower:
            return "Thing"
        elif "error" in name_lower:
            return "omni:Error"
        else:
            return "StructuredValue"
    
    def _process_request_body(self, request_body: Dict[str, Any], schemas: Dict[str, Any]) -> Dict[str, Any]:
        """Obdelaj request body"""
        
        processed = {
            "description": request_body.get("description", ""),
            "required": request_body.get("required", False),
            "content": {}
        }
        
        for media_type, media_schema in request_body.get("content", {}).items():
            processed["content"][media_type] = {
                "schema": media_schema.get("schema", {}),
                "@type": "omni:RequestBody"
            }
        
        return processed
    
    def _process_response(self, response: Dict[str, Any], schemas: Dict[str, Any]) -> Dict[str, Any]:
        """Obdelaj response"""
        
        processed = {
            "description": response.get("description", ""),
            "content": {},
            "@type": "omni:Response"
        }
        
        for media_type, media_schema in response.get("content", {}).items():
            processed["content"][media_type] = {
                "schema": media_schema.get("schema", {}),
                "@type": "omni:ResponseBody"
            }
        
        return processed
    
    def _generate_jsonld(self, semantic_api: SemanticAPI) -> Dict[str, Any]:
        """Generiraj JSON-LD dokumentacijo"""
        
        jsonld = {
            "@context": semantic_api.context,
            "@type": "WebAPI",
            "@id": f"{semantic_api.base_url}#api",
            "name": semantic_api.name,
            "version": semantic_api.version,
            "description": semantic_api.description,
            "url": semantic_api.base_url,
            "provider": {
                "@type": "Organization",
                "name": "OmniscientAI",
                "url": "https://omniscient-ai.com"
            },
            "documentation": f"{semantic_api.base_url}/docs",
            "potentialAction": []
        }
        
        # Dodaj operacije kot potentialAction
        for operation in semantic_api.operations:
            action = {
                "@type": operation.semantic_action,
                "@id": f"{semantic_api.base_url}{operation.path}#{operation.operation_id}",
                "name": operation.summary or operation.operation_id,
                "description": operation.description,
                "target": {
                    "@type": "EntryPoint",
                    "httpMethod": operation.method,
                    "urlTemplate": f"{semantic_api.base_url}{operation.path}",
                    "contentType": "application/json"
                }
            }
            
            # Dodaj parametre
            if operation.parameters:
                action["object"] = []
                for param in operation.parameters:
                    action["object"].append({
                        "@type": "PropertyValueSpecification",
                        "name": param.name,
                        "description": param.description,
                        "valueRequired": param.required,
                        "valueType": param.semantic_type or param.type
                    })
            
            jsonld["potentialAction"].append(action)
        
        # Dodaj sheme
        jsonld["supportedClass"] = []
        for schema_name, schema in semantic_api.schemas.items():
            class_def = {
                "@type": "Class",
                "@id": f"omni:{schema_name}",
                "name": schema_name,
                "description": schema.get("description", ""),
                "supportedProperty": []
            }
            
            for prop_name, prop_schema in schema.get("properties", {}).items():
                class_def["supportedProperty"].append({
                    "@type": "SupportedProperty",
                    "property": {
                        "@type": "Property",
                        "@id": f"omni:{prop_name}",
                        "name": prop_name,
                        "description": prop_schema.get("description", "")
                    },
                    "required": prop_name in schema.get("required", []),
                    "readable": True,
                    "writable": True
                })
            
            jsonld["supportedClass"].append(class_def)
        
        return jsonld
    
    def _generate_hydra(self, semantic_api: SemanticAPI) -> Dict[str, Any]:
        """Generiraj Hydra API dokumentacijo"""
        
        hydra = {
            "@context": {
                "@vocab": "http://www.w3.org/ns/hydra/core#",
                "hydra": "http://www.w3.org/ns/hydra/core#",
                "schema": "https://schema.org/",
                "omni": "https://omniscient-ai.com/ontology/"
            },
            "@type": "ApiDocumentation",
            "@id": f"{semantic_api.base_url}#hydra",
            "title": semantic_api.name,
            "description": semantic_api.description,
            "entrypoint": semantic_api.base_url,
            "supportedClass": [],
            "supportedOperation": []
        }
        
        # Dodaj operacije
        for operation in semantic_api.operations:
            hydra_operation = {
                "@type": "Operation",
                "@id": f"omni:{operation.operation_id}",
                "title": operation.summary,
                "description": operation.description,
                "method": operation.method,
                "expects": None,
                "returns": None
            }
            
            # Dodaj expects (request body)
            if operation.request_body:
                hydra_operation["expects"] = {
                    "@type": "Class",
                    "title": f"{operation.operation_id}Request"
                }
            
            # Dodaj returns (response)
            if operation.responses:
                hydra_operation["returns"] = {
                    "@type": "Class", 
                    "title": f"{operation.operation_id}Response"
                }
            
            hydra["supportedOperation"].append(hydra_operation)
        
        return hydra
    
    def _generate_turtle(self, semantic_api: SemanticAPI) -> str:
        """Generiraj RDF/Turtle dokumentacijo"""
        
        turtle_lines = [
            "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
            "@prefix schema: <https://schema.org/> .",
            "@prefix hydra: <http://www.w3.org/ns/hydra/core#> .",
            "@prefix omni: <https://omniscient-ai.com/ontology/> .",
            "",
            f"<{semantic_api.base_url}#api> a schema:WebAPI ;",
            f'    schema:name "{semantic_api.name}" ;',
            f'    schema:version "{semantic_api.version}" ;',
            f'    schema:description "{semantic_api.description}" ;',
            f'    schema:url <{semantic_api.base_url}> ;',
            "    schema:provider [",
            "        a schema:Organization ;",
            '        schema:name "OmniscientAI" ;',
            '        schema:url <https://omniscient-ai.com>',
            "    ] ."
        ]
        
        # Dodaj operacije
        for operation in semantic_api.operations:
            turtle_lines.extend([
                "",
                f"<{semantic_api.base_url}{operation.path}#{operation.operation_id}> a schema:{operation.semantic_action} ;",
                f'    schema:name "{operation.summary or operation.operation_id}" ;',
                f'    schema:description "{operation.description}" ;',
                "    schema:target [",
                "        a schema:EntryPoint ;",
                f'        schema:httpMethod "{operation.method}" ;',
                f'        schema:urlTemplate "{semantic_api.base_url}{operation.path}"',
                "    ] ."
            ])
        
        return "\n".join(turtle_lines)
    
    def save_documentation(self, output_dir: str = "docs/semantic") -> Dict[str, str]:
        """Shrani dokumentacijo v datoteke"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Generiraj dokumentacijo
        docs = self.generate_semantic_documentation()
        
        # Shrani datoteke
        files_created = {}
        
        # JSON-LD
        jsonld_path = os.path.join(output_dir, "api.jsonld")
        with open(jsonld_path, "w", encoding="utf-8") as f:
            json.dump(docs["jsonld"], f, indent=2, ensure_ascii=False)
        files_created["jsonld"] = jsonld_path
        
        # Hydra
        hydra_path = os.path.join(output_dir, "api.hydra.json")
        with open(hydra_path, "w", encoding="utf-8") as f:
            json.dump(docs["hydra"], f, indent=2, ensure_ascii=False)
        files_created["hydra"] = hydra_path
        
        # Turtle
        turtle_path = os.path.join(output_dir, "api.ttl")
        with open(turtle_path, "w", encoding="utf-8") as f:
            f.write(docs["turtle"])
        files_created["turtle"] = turtle_path
        
        # OpenAPI (za primerjavo)
        openapi_path = os.path.join(output_dir, "openapi.json")
        with open(openapi_path, "w", encoding="utf-8") as f:
            json.dump(docs["openapi"], f, indent=2, ensure_ascii=False)
        files_created["openapi"] = openapi_path
        
        # Celotna dokumentacija
        full_path = os.path.join(output_dir, "semantic_docs.json")
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(docs, f, indent=2, ensure_ascii=False)
        files_created["full"] = full_path
        
        return files_created