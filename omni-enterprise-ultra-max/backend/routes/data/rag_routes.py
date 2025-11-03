"""
RAG (Retrieval-Augmented Generation) API Routes

Enterprise RAG endpoints with:
- Document ingestion
- Semantic search
- Question answering
- Multi-tenant support
- Citation tracking
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

router = APIRouter(prefix="/api/v1/rag", tags=["RAG"])
logger = logging.getLogger(__name__)


# Pydantic Models
class Document(BaseModel):
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class IngestRequest(BaseModel):
    documents: List[Document] = Field(..., description="Documents to ingest")
    tenant_id: Optional[str] = Field(None, description="Tenant ID for multi-tenancy")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    top_k: int = Field(5, ge=1, le=50, description="Number of results")
    tenant_id: Optional[str] = Field(None, description="Tenant ID filter")
    filter_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")


class RAGQueryRequest(BaseModel):
    query: str = Field(..., description="User question")
    top_k: int = Field(5, ge=1, le=20, description="Number of context documents")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    model: str = Field("gpt-4", description="LLM model to use")
    temperature: float = Field(0.7, ge=0, le=2, description="Sampling temperature")


class RAGStatusResponse(BaseModel):
    vector_db: str
    embedding_model: str
    llm_backend: str
    index_name: str
    total_documents: int
    available: bool


@router.post("/ingest")
async def ingest_documents(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    x_tenant_id: Optional[str] = Header(None)
):
    """
    Ingest documents into RAG system
    
    **Features:**
    - Automatic embedding generation
    - Multi-tenant isolation
    - Metadata storage
    - Background processing
    
    **Example:**
    ```json
    {
      "documents": [
        {
          "content": "Omni Platform supports RAG with multiple LLMs",
          "metadata": {"source": "docs", "page": 1}
        }
      ],
      "tenant_id": "acme-corp"
    }
    ```
    """
    try:
        from services.ai.rag_service import get_rag_service
        
        rag_service = get_rag_service()
        
        # Use tenant from header or request
        tenant_id = x_tenant_id or request.tenant_id
        
        result = await rag_service.add_documents(
            documents=[doc.dict() for doc in request.documents],
            tenant_id=tenant_id
        )
        
        logger.info(
            f"Ingested {result['count']} documents "
            f"for tenant {tenant_id or 'default'}"
        )
        
        return {
            "success": True,
            "message": f"Ingested {result['count']} documents",
            "document_ids": result['ids'],
            "tenant_id": tenant_id
        }
    
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_documents(
    request: SearchRequest,
    x_tenant_id: Optional[str] = Header(None)
):
    """
    Semantic search across documents
    
    **Features:**
    - Vector similarity search
    - Metadata filtering
    - Multi-tenant support
    - Relevance scoring
    
    **Example:**
    ```json
    {
      "query": "How does RAG work?",
      "top_k": 5,
      "tenant_id": "acme-corp"
    }
    ```
    """
    try:
        from services.ai.rag_service import get_rag_service
        
        rag_service = get_rag_service()
        
        tenant_id = x_tenant_id or request.tenant_id
        
        results = await rag_service.search(
            query=request.query,
            top_k=request.top_k,
            tenant_id=tenant_id,
            filter_metadata=request.filter_metadata
        )
        
        return {
            "success": True,
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def rag_query(
    request: RAGQueryRequest,
    x_tenant_id: Optional[str] = Header(None)
):
    """
    RAG-powered question answering
    
    **Complete RAG pipeline:**
    1. Retrieve relevant documents
    2. Build context
    3. Generate answer with LLM
    4. Return answer with citations
    
    **Features:**
    - Multi-LLM support (OpenAI, Anthropic, Ollama)
    - Citation tracking
    - Custom system prompts
    - Multi-tenant isolation
    
    **Example:**
    ```json
    {
      "query": "What are the benefits of RAG?",
      "top_k": 5,
      "model": "gpt-4",
      "temperature": 0.7
    }
    ```
    """
    try:
        from services.ai.rag_service import get_rag_service
        
        rag_service = get_rag_service()
        
        tenant_id = x_tenant_id or request.tenant_id
        
        result = await rag_service.rag_query(
            query=request.query,
            top_k=request.top_k,
            tenant_id=tenant_id,
            system_prompt=request.system_prompt,
            model=request.model,
            temperature=request.temperature
        )
        
        return {
            "success": result.get('success', True),
            "query": request.query,
            "answer": result['answer'],
            "sources": result['context_documents'],
            "usage": result.get('usage', {}),
            "model": result.get('model', request.model)
        }
    
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def rag_status():
    """
    Get RAG system status
    
    **Returns:**
    - Vector database type
    - Embedding model
    - LLM backend
    - Document count
    - Availability
    """
    try:
        from services.ai.rag_service import get_rag_service
        
        rag_service = get_rag_service()
        
        # Get document count
        if rag_service.vector_db == "faiss":
            doc_count = rag_service.index.ntotal if rag_service.index else 0
        elif rag_service.vector_db == "pinecone":
            stats = rag_service.index.describe_index_stats()
            doc_count = stats.get('total_vector_count', 0)
        else:
            doc_count = 0
        
        return {
            "vector_db": rag_service.vector_db,
            "embedding_model": rag_service.embedding_model,
            "llm_backend": rag_service.llm_backend,
            "index_name": rag_service.index_name,
            "total_documents": doc_count,
            "available": True
        }
    
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "available": False,
            "error": str(e)
        }


@router.delete("/documents/{tenant_id}")
async def delete_tenant_documents(tenant_id: str):
    """
    Delete all documents for a tenant
    
    **⚠️ Warning:** This operation cannot be undone
    """
    try:
        from services.ai.rag_service import get_rag_service
        
        rag_service = get_rag_service()
        
        if rag_service.vector_db == "faiss":
            # FAISS doesn't support deletion - need to rebuild index
            # Remove from metadata store
            deleted_count = 0
            to_delete = []
            for doc_id, metadata in rag_service.metadata_store.items():
                if metadata.get('tenant_id') == tenant_id:
                    to_delete.append(doc_id)
            
            for doc_id in to_delete:
                del rag_service.metadata_store[doc_id]
                deleted_count += 1
            
            logger.warning(
                f"FAISS: Removed {deleted_count} documents from metadata. "
                f"Consider rebuilding index for tenant {tenant_id}"
            )
            
            return {
                "success": True,
                "message": f"Marked {deleted_count} documents for deletion",
                "note": "FAISS index needs rebuild to free space"
            }
        
        elif rag_service.vector_db == "pinecone":
            # Delete from Pinecone
            rag_service.index.delete(filter={"tenant_id": tenant_id})
            
            return {
                "success": True,
                "message": f"Deleted all documents for tenant {tenant_id}"
            }
        
        else:
            raise NotImplementedError(f"Deletion not implemented for {rag_service.vector_db}")
    
    except Exception as e:
        logger.error(f"Deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def rag_health():
    """
    RAG service health check
    
    **Returns:**
    - Service availability
    - Database connectivity
    - Embedding model status
    - LLM backend status
    """
    try:
        from services.ai.rag_service import get_rag_service
        
        rag_service = get_rag_service()
        
        checks = {
            "vector_db_available": rag_service.index is not None,
            "embedder_available": rag_service.embedder is not None,
            "llm_available": rag_service.llm_client is not None
        }
        
        all_healthy = all(checks.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "checks": checks,
            "vector_db": rag_service.vector_db,
            "embedding_model": rag_service.embedding_model,
            "llm_backend": rag_service.llm_backend
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
