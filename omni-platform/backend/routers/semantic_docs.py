from fastapi import APIRouter, HTTPException, Response, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Dict, Any, Optional
import json
import os
from datetime import datetime

from utils.semantic_api_generator import SemanticAPIGenerator
from .access_controller import require_api_key

router = APIRouter()

# Cache za dokumentacijo
_documentation_cache: Optional[Dict[str, Any]] = None
_cache_timestamp: Optional[datetime] = None
CACHE_DURATION_MINUTES = 30

def get_semantic_generator():
    """Pridobi semantic generator z dostopom do FastAPI app"""
    from main import app  # Import tukaj, da se izognemo circular import
    return SemanticAPIGenerator(app)

def get_cached_documentation() -> Dict[str, Any]:
    """Pridobi cached dokumentacijo ali generiraj novo"""
    global _documentation_cache, _cache_timestamp
    
    now = datetime.utcnow()
    
    # Preveri, če je cache zastarel
    if (_documentation_cache is None or 
        _cache_timestamp is None or 
        (now - _cache_timestamp).total_seconds() > CACHE_DURATION_MINUTES * 60):
        
        # Generiraj novo dokumentacijo
        generator = get_semantic_generator()
        _documentation_cache = generator.generate_semantic_documentation()
        _cache_timestamp = now
    
    return _documentation_cache

@router.get("/semantic/jsonld", 
           summary="JSON-LD API Documentation",
           description="Pridobi API dokumentacijo v JSON-LD formatu za semantic web aplikacije",
           response_class=JSONResponse,
           tags=["Semantic Documentation"])
async def get_jsonld_documentation():
    """
    Vrne API dokumentacijo v JSON-LD formatu.
    
    JSON-LD je W3C standard za strukturirane podatke,
    ki omogoča strojno berljivost in semantic web integracije.
    """
    try:
        docs = get_cached_documentation()
        return JSONResponse(
            content=docs["jsonld"],
            headers={
                "Content-Type": "application/ld+json",
                "Cache-Control": f"public, max-age={CACHE_DURATION_MINUTES * 60}",
                "X-Generated-At": docs["generated_at"],
                "X-Standards": "JSON-LD, Schema.org, W3C"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Napaka pri generiranju JSON-LD dokumentacije: {str(e)}")

@router.get("/semantic/hydra",
           summary="Hydra API Documentation", 
           description="Pridobi API dokumentacijo v Hydra formatu za RESTful web services",
           response_class=JSONResponse,
           tags=["Semantic Documentation"])
async def get_hydra_documentation():
    """
    Vrne API dokumentacijo v Hydra formatu.
    
    Hydra je W3C Community Group specification za opisovanje
    RESTful web API-jev z RDF vocabularies.
    """
    try:
        docs = get_cached_documentation()
        return JSONResponse(
            content=docs["hydra"],
            headers={
                "Content-Type": "application/ld+json",
                "Cache-Control": f"public, max-age={CACHE_DURATION_MINUTES * 60}",
                "X-Generated-At": docs["generated_at"],
                "X-Standards": "Hydra, RDF, W3C"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Napaka pri generiranju Hydra dokumentacije: {str(e)}")

@router.get("/semantic/turtle",
           summary="RDF Turtle API Documentation",
           description="Pridobi API dokumentacijo v RDF/Turtle formatu",
           response_class=PlainTextResponse,
           tags=["Semantic Documentation"])
async def get_turtle_documentation():
    """
    Vrne API dokumentacijo v RDF/Turtle formatu.
    
    Turtle je W3C standard za serijalizacijo RDF grafov
    v človeku berljivi obliki.
    """
    try:
        docs = get_cached_documentation()
        return PlainTextResponse(
            content=docs["turtle"],
            headers={
                "Content-Type": "text/turtle",
                "Cache-Control": f"public, max-age={CACHE_DURATION_MINUTES * 60}",
                "X-Generated-At": docs["generated_at"],
                "X-Standards": "RDF, Turtle, W3C"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Napaka pri generiranju Turtle dokumentacije: {str(e)}")

@router.get("/semantic/openapi-enhanced",
           summary="Enhanced OpenAPI Documentation",
           description="Pridobi razširjeno OpenAPI dokumentacijo s semantičnimi anotacijami",
           response_class=JSONResponse,
           tags=["Semantic Documentation"])
async def get_enhanced_openapi():
    """
    Vrne razširjeno OpenAPI dokumentacijo s semantičnimi anotacijami.
    
    Vključuje dodatne metapodatke za semantic web kompatibilnost.
    """
    try:
        docs = get_cached_documentation()
        return JSONResponse(
            content=docs["openapi"],
            headers={
                "Content-Type": "application/json",
                "Cache-Control": f"public, max-age={CACHE_DURATION_MINUTES * 60}",
                "X-Generated-At": docs["generated_at"],
                "X-Standards": "OpenAPI 3.0, Schema.org"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Napaka pri generiranju razširjene OpenAPI dokumentacije: {str(e)}")

@router.get("/semantic/full",
           summary="Complete Semantic Documentation",
           description="Pridobi celotno semantično dokumentacijo v vseh formatih",
           response_class=JSONResponse,
           tags=["Semantic Documentation"])
async def get_full_semantic_documentation():
    """
    Vrne celotno semantično dokumentacijo v vseh podprtih formatih.
    
    Vključuje JSON-LD, Hydra, Turtle, OpenAPI in dodatne metapodatke.
    """
    try:
        docs = get_cached_documentation()
        return JSONResponse(
            content=docs,
            headers={
                "Content-Type": "application/json",
                "Cache-Control": f"public, max-age={CACHE_DURATION_MINUTES * 60}",
                "X-Generated-At": docs["generated_at"],
                "X-Standards": "JSON-LD, Hydra, RDF, Turtle, OpenAPI, Schema.org, W3C"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Napaka pri generiranju celotne dokumentacije: {str(e)}")

@router.get("/semantic/ontology",
           summary="OmniscientAI Ontology",
           description="Pridobi OmniscientAI ontologijo v RDF/Turtle formatu",
           response_class=PlainTextResponse,
           tags=["Semantic Documentation"])
async def get_omniscient_ontology():
    """
    Vrne OmniscientAI ontologijo, ki definira koncepte in relacije
    uporabljene v API dokumentaciji.
    """
    
    ontology_turtle = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix schema: <https://schema.org/> .
@prefix omni: <https://omniscient-ai.com/ontology/> .

# OmniscientAI Ontology
omni: a owl:Ontology ;
    rdfs:label "OmniscientAI Ontology" ;
    rdfs:comment "Ontologija za OmniscientAI platformo in API" ;
    owl:versionInfo "1.0.0" .

# AI Agent koncepti
omni:AIAgent a owl:Class ;
    rdfs:label "AI Agent" ;
    rdfs:comment "Inteligentni agent z zmožnostmi strojnega učenja" ;
    rdfs:subClassOf schema:SoftwareApplication .

omni:MachineLearning a owl:Class ;
    rdfs:label "Machine Learning" ;
    rdfs:comment "Strojno učenje in povezane funkcionalnosti" ;
    rdfs:subClassOf schema:ComputerLanguage .

omni:Policy a owl:Class ;
    rdfs:label "Policy" ;
    rdfs:comment "Politika za reinforcement learning" ;
    rdfs:subClassOf schema:Algorithm .

omni:Feedback a owl:Class ;
    rdfs:label "Feedback" ;
    rdfs:comment "Povratne informacije za učenje" ;
    rdfs:subClassOf schema:Thing .

# Senzorski podatki
omni:SensorReading a owl:Class ;
    rdfs:label "Sensor Reading" ;
    rdfs:comment "Odčitek senzorja" ;
    rdfs:subClassOf schema:Observation .

omni:DataStream a owl:Class ;
    rdfs:label "Data Stream" ;
    rdfs:comment "Tok podatkov v realnem času" ;
    rdfs:subClassOf schema:DataFeed .

# ML modeli
omni:MLModel a owl:Class ;
    rdfs:label "ML Model" ;
    rdfs:comment "Model strojnega učenja" ;
    rdfs:subClassOf schema:SoftwareApplication .

# API koncepti
omni:RequestBody a owl:Class ;
    rdfs:label "Request Body" ;
    rdfs:comment "Telo HTTP zahteve" ;
    rdfs:subClassOf schema:Thing .

omni:Response a owl:Class ;
    rdfs:label "Response" ;
    rdfs:comment "HTTP odgovor" ;
    rdfs:subClassOf schema:Thing .

omni:ResponseBody a owl:Class ;
    rdfs:label "Response Body" ;
    rdfs:comment "Telo HTTP odgovora" ;
    rdfs:subClassOf schema:Thing .

omni:Error a owl:Class ;
    rdfs:label "Error" ;
    rdfs:comment "Napaka v sistemu" ;
    rdfs:subClassOf schema:Thing .

# Konteksti
omni:GeneralAPI a owl:Class ;
    rdfs:label "General API" ;
    rdfs:comment "Splošni API kontekst" .

omni:Authentication a owl:Class ;
    rdfs:label "Authentication" ;
    rdfs:comment "Avtentikacija in avtorizacija" .

omni:FileManagement a owl:Class ;
    rdfs:label "File Management" ;
    rdfs:comment "Upravljanje datotek" .

omni:BillingService a owl:Class ;
    rdfs:label "Billing Service" ;
    rdfs:comment "Storitve obračunavanja" .

omni:Monitoring a owl:Class ;
    rdfs:label "Monitoring" ;
    rdfs:comment "Nadzor sistema" .

omni:SensorData a owl:Class ;
    rdfs:label "Sensor Data" ;
    rdfs:comment "Senzorski podatki" .
"""
    
    return PlainTextResponse(
        content=ontology_turtle,
        headers={
            "Content-Type": "text/turtle",
            "Cache-Control": f"public, max-age={CACHE_DURATION_MINUTES * 60}",
            "X-Standards": "RDF, OWL, Turtle, W3C"
        }
    )

@router.post("/semantic/refresh",
            summary="Refresh Documentation Cache",
            description="Osveži cache dokumentacije (zahteva API ključ)",
            tags=["Semantic Documentation"])
async def refresh_documentation_cache(auth: Dict[str, Any] = Depends(require_api_key)):
    """
    Osveži cache dokumentacije.
    
    Uporabno po spremembah API-ja ali za prisilno osvežitev.
    """
    global _documentation_cache, _cache_timestamp
    
    try:
        # Počisti cache
        _documentation_cache = None
        _cache_timestamp = None
        
        # Generiraj novo dokumentacijo
        docs = get_cached_documentation()
        
        return {
            "message": "Cache dokumentacije je bil uspešno osvežen",
            "generated_at": docs["generated_at"],
            "cache_cleared": True,
            "formats_available": ["jsonld", "hydra", "turtle", "openapi", "full"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Napaka pri osvežitvi cache: {str(e)}")

@router.get("/semantic/stats",
           summary="Documentation Statistics",
           description="Pridobi statistike o generirani dokumentaciji",
           tags=["Semantic Documentation"])
async def get_documentation_stats():
    """
    Vrne statistike o generirani dokumentaciji.
    """
    try:
        docs = get_cached_documentation()
        
        # Preštej operacije po metodah
        method_counts = {}
        for operation in docs["semantic_api"]["operations"]:
            method = operation["method"]
            method_counts[method] = method_counts.get(method, 0) + 1
        
        # Preštej sheme
        schema_count = len(docs["semantic_api"]["schemas"])
        
        # Preštej kontekste
        contexts = set()
        for operation in docs["semantic_api"]["operations"]:
            if operation.get("context"):
                contexts.add(operation["context"])
        
        return {
            "generated_at": docs["generated_at"],
            "cache_timestamp": _cache_timestamp.isoformat() if _cache_timestamp else None,
            "api_info": {
                "name": docs["semantic_api"]["name"],
                "version": docs["semantic_api"]["version"],
                "base_url": docs["semantic_api"]["base_url"]
            },
            "statistics": {
                "total_operations": len(docs["semantic_api"]["operations"]),
                "operations_by_method": method_counts,
                "total_schemas": schema_count,
                "unique_contexts": len(contexts),
                "contexts": list(contexts)
            },
            "formats": {
                "jsonld_size": len(json.dumps(docs["jsonld"])),
                "hydra_size": len(json.dumps(docs["hydra"])),
                "turtle_size": len(docs["turtle"]),
                "openapi_size": len(json.dumps(docs["openapi"]))
            },
            "standards_compliance": docs["generator"]["standards"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Napaka pri pridobivanju statistik: {str(e)}")

@router.get("/semantic/validate",
           summary="Validate Semantic Documentation",
           description="Preveri veljavnost generirane semantične dokumentacije",
           tags=["Semantic Documentation"])
async def validate_semantic_documentation():
    """
    Preveri veljavnost generirane semantične dokumentacije
    glede na W3C standarde in Schema.org specifikacije.
    """
    try:
        docs = get_cached_documentation()
        
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks_performed": []
        }
        
        # Preveri JSON-LD strukturo
        jsonld = docs["jsonld"]
        validation_results["checks_performed"].append("JSON-LD structure validation")
        
        if "@context" not in jsonld:
            validation_results["errors"].append("JSON-LD manjka @context")
            validation_results["valid"] = False
        
        if "@type" not in jsonld:
            validation_results["errors"].append("JSON-LD manjka @type")
            validation_results["valid"] = False
        
        # Preveri Hydra strukturo
        hydra = docs["hydra"]
        validation_results["checks_performed"].append("Hydra structure validation")
        
        if "@type" not in hydra or hydra["@type"] != "ApiDocumentation":
            validation_results["errors"].append("Hydra mora imeti @type: ApiDocumentation")
            validation_results["valid"] = False
        
        # Preveri Turtle sintakso (osnovno)
        turtle = docs["turtle"]
        validation_results["checks_performed"].append("Turtle syntax validation")
        
        if not turtle.strip().startswith("@prefix"):
            validation_results["warnings"].append("Turtle dokumentacija naj bi se začela s @prefix deklaracijami")
        
        # Preveri OpenAPI strukturo
        openapi = docs["openapi"]
        validation_results["checks_performed"].append("OpenAPI structure validation")
        
        if "openapi" not in openapi:
            validation_results["errors"].append("OpenAPI manjka verzija specifikacije")
            validation_results["valid"] = False
        
        if "info" not in openapi:
            validation_results["errors"].append("OpenAPI manjka info objekt")
            validation_results["valid"] = False
        
        # Preveri semantične anotacije
        validation_results["checks_performed"].append("Semantic annotations validation")
        
        semantic_api = docs["semantic_api"]
        operations_with_context = sum(1 for op in semantic_api["operations"] if op.get("context"))
        
        if operations_with_context < len(semantic_api["operations"]) * 0.8:
            validation_results["warnings"].append("Manj kot 80% operacij ima definiran semantični kontekst")
        
        return {
            "validation_results": validation_results,
            "generated_at": docs["generated_at"],
            "standards_checked": ["JSON-LD", "Hydra", "RDF/Turtle", "OpenAPI", "Schema.org"],
            "summary": {
                "total_checks": len(validation_results["checks_performed"]),
                "errors_found": len(validation_results["errors"]),
                "warnings_found": len(validation_results["warnings"]),
                "overall_valid": validation_results["valid"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Napaka pri validaciji dokumentacije: {str(e)}")