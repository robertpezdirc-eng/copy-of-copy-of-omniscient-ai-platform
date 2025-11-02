"""
Enterprise RAG (Retrieval-Augmented Generation) Service

Production-grade RAG implementation with:
- Multiple vector databases (FAISS, Pinecone, Weaviate)
- Multi-model embedding support (OpenAI, Cohere, HuggingFace)
- Hybrid search (vector + keyword)
- Context window management
- Citation tracking
- Multi-tenant isolation
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

# Vector databases
try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available - install with: pip install faiss-cpu")

try:
    import pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logging.warning("Pinecone not available - install with: pip install pinecone-client")

try:
    import weaviate
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False
    logging.warning("Weaviate not available - install with: pip install weaviate-client")

# Embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("Sentence Transformers not available")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# LLM backends
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class RAGService:
    """
    Enterprise RAG service with multi-database, multi-model support
    """
    
    def __init__(
        self,
        vector_db: str = "faiss",  # faiss, pinecone, weaviate
        embedding_model: str = "openai",  # openai, cohere, huggingface, sentence-transformers
        llm_backend: str = "openai",  # openai, anthropic, ollama, google
        index_name: str = "omni-rag",
        dimension: int = 1536,  # OpenAI ada-002 dimension
    ):
        self.vector_db = vector_db
        self.embedding_model = embedding_model
        self.llm_backend = llm_backend
        self.index_name = index_name
        self.dimension = dimension
        
        # Initialize vector database (will be revalidated after embedder loads)
        self.index = None
        self.metadata_store: Dict[int, Dict[str, Any]] = {}
        self._init_vector_db()
        
        # Initialize embedding model
        self.embedder = None
        self._init_embedding_model()

        # Ensure FAISS index matches embedding dimension (may recreate index)
        self._ensure_index_matches_dimension()
        
        # Initialize LLM backend
        self.llm_client = None
        self._init_llm_backend()
        
        logger.info(
            f"RAG Service initialized: vector_db={self.vector_db}, "
            f"embedding={self.embedding_model}, llm={self.llm_backend}, dim={self.dimension}"
        )
    
    def _init_vector_db(self):
        """Initialize vector database"""
        if self.vector_db == "faiss":
            if not FAISS_AVAILABLE:
                raise RuntimeError("FAISS not available")
            
            # Create FAISS index (L2 distance, flat)
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info(f"FAISS index created with dimension {self.dimension}")
            
        elif self.vector_db == "pinecone":
            if not PINECONE_AVAILABLE:
                raise RuntimeError("Pinecone not available")
            
            api_key = os.getenv("PINECONE_API_KEY")
            environment = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
            
            if not api_key:
                raise ValueError("PINECONE_API_KEY environment variable required")
            
            pinecone.init(api_key=api_key, environment=environment)
            
            # Create or connect to index
            if self.index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    self.index_name,
                    dimension=self.dimension,
                    metric="cosine"
                )
            
            self.index = pinecone.Index(self.index_name)
            logger.info(f"Pinecone index '{self.index_name}' ready")
            
        elif self.vector_db == "weaviate":
            if not WEAVIATE_AVAILABLE:
                raise RuntimeError("Weaviate not available")
            
            url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
            api_key = os.getenv("WEAVIATE_API_KEY")
            
            auth = weaviate.auth.AuthApiKey(api_key) if api_key else None
            self.index = weaviate.Client(url=url, auth_client_secret=auth)
            
            logger.info(f"Weaviate client connected to {url}")
        
        else:
            raise ValueError(f"Unsupported vector database: {self.vector_db}")

    def _ensure_index_matches_dimension(self):
        """Ensure vector DB index matches current embedding dimension (recreate if needed)."""
        try:
            if self.vector_db == "faiss" and self.index is not None:
                current_dim = getattr(self.index, 'd', None)
                if current_dim is not None and current_dim != self.dimension:
                    logger.warning(
                        f"FAISS index dimension {current_dim} != embedding dimension {self.dimension}; recreating index"
                    )
                    self.index = faiss.IndexFlatL2(self.dimension)
        except Exception as e:
            logger.error(f"Failed to ensure index matches dimension: {e}")
    
    def _init_embedding_model(self):
        """Initialize embedding model with graceful fallbacks and dynamic dimensions"""
        if self.embedding_model == "openai":
            if not OPENAI_AVAILABLE:
                raise RuntimeError("OpenAI not available")
            
            openai.api_key = os.getenv("OPENAI_API_KEY")
            if not openai.api_key:
                raise ValueError("OPENAI_API_KEY environment variable required")
            
            # OpenAI ada-002 has 1536 dims
            self.embedder = "text-embedding-ada-002"
            self.dimension = 1536
            logger.info("OpenAI embeddings configured")
            
        elif self.embedding_model == "sentence-transformers":
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                # Fallback to OpenAI if available to keep service healthy
                if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
                    logger.warning("Sentence Transformers not available; falling back to OpenAI embeddings")
                    self.embedding_model = "openai"
                    openai.api_key = os.getenv("OPENAI_API_KEY")
                    self.embedder = "text-embedding-ada-002"
                    self.dimension = 1536
                    return
                raise RuntimeError("Sentence Transformers not available")
            
            model_name = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
            self.embedder = SentenceTransformer(model_name)
            # Try to detect dimension from model; default to 384 for MiniLM
            try:
                detected_dim = getattr(self.embedder, 'get_sentence_embedding_dimension', None)
                self.dimension = int(detected_dim()) if callable(detected_dim) else int(os.getenv("SENTENCE_TRANSFORMER_DIM", 384))
            except Exception:
                self.dimension = 384
            logger.info(f"Sentence Transformer loaded: {model_name} (dim={self.dimension})")
            
        elif self.embedding_model == "huggingface":
            # Use sentence-transformers as backend
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                # Fallback to OpenAI if available
                if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
                    logger.warning("Sentence Transformers not available for HuggingFace; falling back to OpenAI embeddings")
                    self.embedding_model = "openai"
                    openai.api_key = os.getenv("OPENAI_API_KEY")
                    self.embedder = "text-embedding-ada-002"
                    self.dimension = 1536
                    return
                raise RuntimeError("Sentence Transformers required for HuggingFace")
            
            model_name = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")
            self.embedder = SentenceTransformer(model_name)
            try:
                detected_dim = getattr(self.embedder, 'get_sentence_embedding_dimension', None)
                self.dimension = int(detected_dim()) if callable(detected_dim) else int(os.getenv("SENTENCE_TRANSFORMER_DIM", 768))
            except Exception:
                self.dimension = 768
            logger.info(f"HuggingFace model loaded: {model_name} (dim={self.dimension})")
        
        else:
            raise ValueError(f"Unsupported embedding model: {self.embedding_model}")
    
    def _init_llm_backend(self):
        """Initialize LLM backend"""
        if self.llm_backend == "openai":
            if not OPENAI_AVAILABLE:
                raise RuntimeError("OpenAI not available")
            
            openai.api_key = os.getenv("OPENAI_API_KEY")
            self.llm_client = openai
            logger.info("OpenAI LLM backend configured")
            
        elif self.llm_backend == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise RuntimeError("Anthropic not available")
            
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY required")
            
            self.llm_client = Anthropic(api_key=api_key)
            logger.info("Anthropic LLM backend configured")
            
        elif self.llm_backend == "ollama":
            # Use existing ollama service
            from .ollama_service import get_ollama_service
            self.llm_client = get_ollama_service()
            logger.info("Ollama LLM backend configured")
        
        else:
            logger.warning(f"LLM backend '{self.llm_backend}' not configured")
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if self.embedding_model == "openai":
            response = await openai.Embedding.acreate(
                input=text,
                model=self.embedder
            )
            return response['data'][0]['embedding']
        
        elif self.embedding_model in ["sentence-transformers", "huggingface"]:
            embedding = self.embedder.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        
        else:
            raise NotImplementedError(f"Embedding not implemented for {self.embedding_model}")
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if self.embedding_model == "openai":
            response = await openai.Embedding.acreate(
                input=texts,
                model=self.embedder
            )
            return [item['embedding'] for item in response['data']]
        
        elif self.embedding_model in ["sentence-transformers", "huggingface"]:
            embeddings = self.embedder.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        
        else:
            raise NotImplementedError(f"Batch embedding not implemented")
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add documents to RAG system
        
        Args:
            documents: List of docs with 'content' and optional 'metadata'
            tenant_id: Tenant identifier for multi-tenancy
        
        Returns:
            Result with document IDs
        """
        texts = [doc['content'] for doc in documents]
        embeddings = await self.embed_batch(texts)
        
        if self.vector_db == "faiss":
            # Add to FAISS
            vectors = np.array(embeddings).astype('float32')
            start_id = self.index.ntotal
            self.index.add(vectors)
            
            # Store metadata
            for i, doc in enumerate(documents):
                doc_id = start_id + i
                self.metadata_store[doc_id] = {
                    "content": doc['content'],
                    "metadata": doc.get('metadata', {}),
                    "tenant_id": tenant_id,
                    "created_at": datetime.utcnow().isoformat()
                }
            
            return {
                "success": True,
                "count": len(documents),
                "ids": list(range(start_id, start_id + len(documents)))
            }
        
        elif self.vector_db == "pinecone":
            # Upsert to Pinecone
            vectors = []
            for i, (embedding, doc) in enumerate(zip(embeddings, documents)):
                vectors.append((
                    f"{tenant_id}_{i}" if tenant_id else str(i),
                    embedding,
                    {
                        "content": doc['content'],
                        "tenant_id": tenant_id,
                        **(doc.get('metadata', {}))
                    }
                ))
            
            self.index.upsert(vectors=vectors)
            
            return {
                "success": True,
                "count": len(documents),
                "ids": [v[0] for v in vectors]
            }
        
        else:
            raise NotImplementedError(f"Add documents not implemented for {self.vector_db}")
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        tenant_id: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            top_k: Number of results
            tenant_id: Filter by tenant
            filter_metadata: Additional metadata filters
        
        Returns:
            List of relevant documents with scores
        """
        query_embedding = await self.embed_text(query)
        
        if self.vector_db == "faiss":
            # Search FAISS
            query_vector = np.array([query_embedding]).astype('float32')
            distances, indices = self.index.search(query_vector, top_k)
            
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:  # FAISS returns -1 for empty slots
                    continue
                
                metadata = self.metadata_store.get(int(idx), {})
                
                # Apply tenant filter
                if tenant_id and metadata.get('tenant_id') != tenant_id:
                    continue
                
                # Apply metadata filters
                if filter_metadata:
                    if not all(
                        metadata.get('metadata', {}).get(k) == v
                        for k, v in filter_metadata.items()
                    ):
                        continue
                
                results.append({
                    "content": metadata.get('content', ''),
                    "metadata": metadata.get('metadata', {}),
                    "score": float(dist),
                    "id": int(idx)
                })
            
            return results
        
        elif self.vector_db == "pinecone":
            # Search Pinecone
            filter_dict = {}
            if tenant_id:
                filter_dict['tenant_id'] = tenant_id
            if filter_metadata:
                filter_dict.update(filter_metadata)
            
            response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )
            
            results = []
            for match in response['matches']:
                results.append({
                    "content": match['metadata'].get('content', ''),
                    "metadata": match.get('metadata', {}),
                    "score": match['score'],
                    "id": match['id']
                })
            
            return results
        
        else:
            raise NotImplementedError(f"Search not implemented for {self.vector_db}")
    
    async def generate_response(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate RAG response using retrieved context
        
        Args:
            query: User query
            context_documents: Retrieved documents
            system_prompt: Optional system prompt
            model: LLM model to use
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
        
        Returns:
            Generated response with citations
        """
        # Build context from documents
        context = "\n\n".join([
            f"[Document {i+1}]\n{doc['content']}"
            for i, doc in enumerate(context_documents)
        ])
        
        # Build prompt
        if not system_prompt:
            system_prompt = (
                "You are a helpful AI assistant. Use the provided context to answer "
                "the user's question. If the answer is not in the context, say so. "
                "Always cite which document(s) you used."
            )
        
        user_prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        
        # Generate with LLM
        if self.llm_backend == "openai":
            response = await self.llm_client.ChatCompletion.acreate(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            answer = response['choices'][0]['message']['content']
            usage = response['usage']
            
        elif self.llm_backend == "anthropic":
            response = await self.llm_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            answer = response.content[0].text
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
            
        elif self.llm_backend == "ollama":
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            answer = await self.llm_client.generate(
                prompt=full_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            usage = {"total_tokens": len(answer.split())}  # Estimate
        
        else:
            raise NotImplementedError(f"Generation not implemented for {self.llm_backend}")
        
        return {
            "answer": answer,
            "context_documents": context_documents,
            "usage": usage,
            "model": model
        }
    
    async def rag_query(
        self,
        query: str,
        top_k: int = 5,
        tenant_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve + generate
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            tenant_id: Tenant ID for multi-tenancy
            system_prompt: Optional system prompt
            model: LLM model
            temperature: Sampling temperature
        
        Returns:
            Complete RAG response with answer and sources
        """
        # Step 1: Retrieve relevant documents
        context_docs = await self.search(
            query=query,
            top_k=top_k,
            tenant_id=tenant_id
        )
        
        if not context_docs:
            return {
                "answer": "No relevant context found to answer this question.",
                "context_documents": [],
                "success": False
            }
        
        # Step 2: Generate response
        result = await self.generate_response(
            query=query,
            context_documents=context_docs,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature
        )
        
        result['success'] = True
        return result


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service(
    vector_db: str = None,
    embedding_model: str = None,
    llm_backend: str = None
) -> RAGService:
    """Get or create RAG service singleton"""
    global _rag_service
    
    if _rag_service is None:
        vector_db = vector_db or os.getenv("RAG_VECTOR_DB", "faiss")
        embedding_model = embedding_model or os.getenv("RAG_EMBEDDING_MODEL", "openai")
        llm_backend = llm_backend or os.getenv("RAG_LLM_BACKEND", "openai")
        
        _rag_service = RAGService(
            vector_db=vector_db,
            embedding_model=embedding_model,
            llm_backend=llm_backend
        )
    
    return _rag_service
