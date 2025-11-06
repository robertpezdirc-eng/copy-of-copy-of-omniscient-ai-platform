"""
Enhanced RAG (Retrieval-Augmented Generation) API Routes

Advanced RAG with FAISS indexing, semantic search, and citation tracking
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rag-enhanced", tags=["Enhanced RAG"])


# Pydantic Models
class DocumentInput(BaseModel):
    id: Optional[str] = Field(None, description="Optional document ID")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class IngestDocumentsRequest(BaseModel):
    documents: List[DocumentInput] = Field(..., description="Documents to ingest")
    tenant_id: Optional[str] = Field(None, description="Tenant ID for multi-tenancy")


class IngestDocumentsResponse(BaseModel):
    status: str
    documents_ingested: int
    document_ids: List[str]
    total_documents: int
    tenant_id: Optional[str]


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    top_k: int = Field(5, ge=1, le=50, description="Number of results")
    tenant_id: Optional[str] = Field(None, description="Tenant ID filter")
    filter_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")


class SearchResultResponse(BaseModel):
    document_id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    rank: int
    citation_id: str


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultResponse]
    num_results: int


class RAGQueryRequest(BaseModel):
    query: str = Field(..., description="User question")
    top_k: int = Field(5, ge=1, le=20, description="Number of context documents")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    llm_provider: str = Field("openai", description="LLM provider (openai, anthropic, gemini, ollama)")
    temperature: float = Field(0.7, ge=0, le=2, description="Sampling temperature")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")


class CitationResponse(BaseModel):
    id: str
    score: float
    metadata: Dict[str, Any]


class SourceResponse(BaseModel):
    document_id: str
    content_preview: str
    metadata: Dict[str, Any]
    score: float


class RAGQueryResponse(BaseModel):
    answer: str
    citations: List[CitationResponse]
    sources: List[SourceResponse]
    confidence: float
    query_id: str
    generation_info: Dict[str, Any]
    num_context_docs: int


class RAGStatsResponse(BaseModel):
    total_documents: int
    index_size: int
    embedding_model: str
    embedding_dimension: int
    tenant_document_counts: Dict[str, int]
    total_queries: int
    index_path: str


# Routes
@router.post("/ingest", response_model=IngestDocumentsResponse)
async def ingest_documents(request: IngestDocumentsRequest):
    """
    Ingest documents into the RAG system with FAISS indexing
    
    Documents are:
    - Embedded using sentence transformers (all-MiniLM-L6-v2)
    - Indexed in FAISS for fast similarity search
    - Stored with metadata for filtering
    - Isolated by tenant for multi-tenancy
    
    **Example:**
    ```json
    {
        "documents": [
            {
                "content": "The Omni Enterprise platform provides advanced AI capabilities...",
                "metadata": {"category": "documentation", "version": "1.0"}
            }
        ],
        "tenant_id": "acme-corp"
    }
    ```
    """
    try:
        from services.ai.enhanced_rag_service import get_enhanced_rag_service
        
        rag_service = get_enhanced_rag_service()
        
        # Convert to dict format
        docs_data = [
            {
                "id": doc.id,
                "content": doc.content,
                "metadata": doc.metadata
            }
            for doc in request.documents
        ]
        
        result = rag_service.ingest_documents(
            documents=docs_data,
            tenant_id=request.tenant_id
        )
        
        return IngestDocumentsResponse(**result)
        
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Semantic search for relevant documents using FAISS
    
    Uses sentence transformers to find semantically similar documents.
    Results are ranked by cosine similarity.
    
    **Features:**
    - Semantic similarity (not just keyword matching)
    - Multi-tenant filtering
    - Metadata filtering
    - Citation IDs for referencing
    
    **Example:**
    ```json
    {
        "query": "How does the monitoring system work?",
        "top_k": 5,
        "tenant_id": "acme-corp"
    }
    ```
    """
    try:
        from services.ai.enhanced_rag_service import get_enhanced_rag_service
        
        rag_service = get_enhanced_rag_service()
        
        results = rag_service.search(
            query=request.query,
            top_k=request.top_k,
            tenant_id=request.tenant_id,
            filter_metadata=request.filter_metadata
        )
        
        search_results = [
            SearchResultResponse(
                document_id=r.document.id,
                content=r.document.content,
                metadata=r.document.metadata,
                score=r.score,
                rank=r.rank,
                citation_id=r.citation_id
            )
            for r in results
        ]
        
        return SearchResponse(
            query=request.query,
            results=search_results,
            num_results=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """
    RAG query: semantic search + LLM generation with citations
    
    **Process:**
    1. Search for relevant documents using FAISS
    2. Build context with citations ([1], [2], etc.)
    3. Generate answer using Multi-LLM Router
    4. Return answer with sources and confidence score
    
    **Features:**
    - Automatic citation tracking
    - Source attribution
    - Confidence scoring
    - Multi-LLM support
    - Cost and latency metrics
    
    **Example:**
    ```json
    {
        "query": "What security features are available?",
        "top_k": 5,
        "llm_provider": "anthropic",
        "temperature": 0.7
    }
    ```
    """
    try:
        from services.ai.enhanced_rag_service import get_enhanced_rag_service
        
        rag_service = get_enhanced_rag_service()
        
        result = rag_service.generate_answer(
            query=request.query,
            top_k=request.top_k,
            tenant_id=request.tenant_id,
            llm_provider=request.llm_provider,
            temperature=request.temperature,
            system_prompt=request.system_prompt
        )
        
        return RAGQueryResponse(**result)
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=RAGStatsResponse)
async def get_stats():
    """
    Get RAG system statistics
    
    Returns:
    - Total documents indexed
    - Document counts per tenant
    - Embedding model information
    - Query statistics
    """
    try:
        from services.ai.enhanced_rag_service import get_enhanced_rag_service
        
        rag_service = get_enhanced_rag_service()
        stats = rag_service.get_stats()
        
        return RAGStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tenant/{tenant_id}")
async def clear_tenant_documents(tenant_id: str):
    """
    Clear all documents for a tenant
    
    Removes all documents and embeddings for the specified tenant.
    Useful for:
    - Data cleanup
    - GDPR compliance
    - Tenant offboarding
    """
    try:
        from services.ai.enhanced_rag_service import get_enhanced_rag_service
        
        rag_service = get_enhanced_rag_service()
        count = rag_service.clear_tenant_documents(tenant_id)
        
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "documents_removed": count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear tenant documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    RAG system health check
    
    Verifies:
    - FAISS index is initialized
    - Sentence transformer model is loaded
    - Index can be queried
    """
    try:
        from services.ai.enhanced_rag_service import get_enhanced_rag_service
        
        rag_service = get_enhanced_rag_service()
        
        return {
            "status": "healthy",
            "faiss_available": rag_service.faiss is not None,
            "embedding_model_available": rag_service.embedding_model is not None,
            "total_documents": len(rag_service.documents),
            "embedding_model": rag_service.embedding_model_name,
            "embedding_dimension": rag_service.embedding_dim
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
