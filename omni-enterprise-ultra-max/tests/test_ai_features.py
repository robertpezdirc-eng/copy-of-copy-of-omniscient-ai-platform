"""
Tests for Multi-LLM Router, Enhanced RAG, and Autonomous Agents
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import numpy as np


# Multi-LLM Router Tests
class TestMultiLLMRouter:
    """Test Multi-LLM Router functionality"""
    
    def test_router_initialization(self):
        """Test router initializes with all providers"""
        from services.ai.multi_llm_router import MultiLLMRouter
        
        router = MultiLLMRouter()
        
        assert "openai" in router.providers
        assert "anthropic" in router.providers
        assert "gemini" in router.providers
        assert "ollama" in router.providers
        
        assert router.providers["openai"].cost_per_1k_tokens == 0.03
        assert router.providers["ollama"].cost_per_1k_tokens == 0.0
    
    def test_select_provider_cost_optimized(self):
        """Test cost-optimized routing selects cheapest provider"""
        from services.ai.multi_llm_router import MultiLLMRouter, RoutingStrategy
        
        router = MultiLLMRouter()
        
        # Set all providers as available for testing
        for provider in router.providers.values():
            provider.is_available = True
        
        selected = router.select_provider(
            strategy=RoutingStrategy.COST_OPTIMIZED,
            required_tokens=1000
        )
        
        # Should select Ollama (free) or Gemini (cheapest paid)
        assert selected in ["ollama", "gemini"]
    
    def test_select_provider_speed_optimized(self):
        """Test speed-optimized routing selects fastest provider"""
        from services.ai.multi_llm_router import MultiLLMRouter, RoutingStrategy
        
        router = MultiLLMRouter()
        
        for provider in router.providers.values():
            provider.is_available = True
        
        selected = router.select_provider(
            strategy=RoutingStrategy.SPEED_OPTIMIZED,
            required_tokens=1000
        )
        
        # Should select Ollama (fastest)
        assert selected == "ollama"
    
    def test_select_provider_quality_optimized(self):
        """Test quality-optimized routing selects best quality"""
        from services.ai.multi_llm_router import MultiLLMRouter, RoutingStrategy
        
        router = MultiLLMRouter()
        
        for provider in router.providers.values():
            provider.is_available = True
        
        selected = router.select_provider(
            strategy=RoutingStrategy.QUALITY_OPTIMIZED,
            required_tokens=1000
        )
        
        # Should select OpenAI (highest quality score)
        assert selected == "openai"
    
    @pytest.mark.asyncio
    async def test_complete_with_mock_openai(self):
        """Test completion with mocked OpenAI"""
        from services.ai.multi_llm_router import MultiLLMRouter
        
        router = MultiLLMRouter()
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        
        with patch.object(router, 'openai_client') as mock_client:
            mock_client.chat.completions.create.return_value = mock_response
            router.providers["openai"].is_available = True
            
            result = await router.complete(
                prompt="Test prompt",
                provider="openai",
                max_tokens=100
            )
            
            assert result["content"] == "Test response"
            assert result["provider"] == "openai"
            assert "latency_ms" in result
            assert "estimated_cost" in result
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        from services.ai.multi_llm_router import MultiLLMRouter
        
        router = MultiLLMRouter()
        stats = router.get_stats()
        
        assert "total_requests" in stats
        assert "provider_usage" in stats
        assert "provider_availability" in stats
        assert len(stats["provider_usage"]) == 4  # 4 providers


# Enhanced RAG Tests
class TestEnhancedRAG:
    """Test Enhanced RAG Service"""
    
    def test_rag_initialization(self):
        """Test RAG service initializes correctly"""
        from services.ai.enhanced_rag_service import EnhancedRAGService
        
        rag = EnhancedRAGService()
        
        assert rag.embedding_model_name == "all-MiniLM-L6-v2"
        assert rag.embedding_dim > 0
        assert len(rag.documents) == 0
    
    def test_embed_text(self):
        """Test text embedding generation"""
        from services.ai.enhanced_rag_service import EnhancedRAGService
        
        rag = EnhancedRAGService()
        
        embedding = rag.embed_text("Test document")
        
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) == rag.embedding_dim
        assert embedding.dtype == np.float32
    
    def test_ingest_documents(self):
        """Test document ingestion"""
        from services.ai.enhanced_rag_service import EnhancedRAGService
        
        rag = EnhancedRAGService()
        
        documents = [
            {
                "content": "Machine learning is a subset of AI",
                "metadata": {"category": "ml", "topic": "intro"}
            },
            {
                "content": "Deep learning uses neural networks",
                "metadata": {"category": "dl", "topic": "neural"}
            }
        ]
        
        result = rag.ingest_documents(documents, tenant_id="test-tenant")
        
        assert result["status"] == "success"
        assert result["documents_ingested"] == 2
        assert result["tenant_id"] == "test-tenant"
        assert len(rag.documents) == 2
    
    def test_search(self):
        """Test semantic search"""
        from services.ai.enhanced_rag_service import EnhancedRAGService
        
        rag = EnhancedRAGService()
        
        # Ingest test documents
        documents = [
            {"content": "Python is a programming language", "metadata": {}},
            {"content": "JavaScript is used for web development", "metadata": {}},
            {"content": "Python has extensive data science libraries", "metadata": {}}
        ]
        
        rag.ingest_documents(documents)
        
        # Search for Python-related content
        results = rag.search("Python programming", top_k=2)
        
        assert len(results) > 0
        assert all(hasattr(r, 'score') for r in results)
        assert all(hasattr(r, 'citation_id') for r in results)
    
    def test_tenant_isolation(self):
        """Test tenant document isolation"""
        from services.ai.enhanced_rag_service import EnhancedRAGService
        
        rag = EnhancedRAGService()
        
        # Ingest for tenant A
        rag.ingest_documents(
            [{"content": "Tenant A document", "metadata": {}}],
            tenant_id="tenant-a"
        )
        
        # Ingest for tenant B
        rag.ingest_documents(
            [{"content": "Tenant B document", "metadata": {}}],
            tenant_id="tenant-b"
        )
        
        # Search with tenant filter
        results_a = rag.search("document", tenant_id="tenant-a")
        results_b = rag.search("document", tenant_id="tenant-b")
        
        assert len(results_a) == 1
        assert len(results_b) == 1
        assert results_a[0].document.tenant_id == "tenant-a"
        assert results_b[0].document.tenant_id == "tenant-b"
    
    def test_clear_tenant_documents(self):
        """Test clearing tenant documents"""
        from services.ai.enhanced_rag_service import EnhancedRAGService
        
        rag = EnhancedRAGService()
        
        # Add documents for tenant
        rag.ingest_documents(
            [
                {"content": "Doc 1", "metadata": {}},
                {"content": "Doc 2", "metadata": {}}
            ],
            tenant_id="test-tenant"
        )
        
        initial_count = len(rag.documents)
        
        # Clear tenant documents
        removed = rag.clear_tenant_documents("test-tenant")
        
        assert removed == 2
        assert len(rag.documents) == initial_count - 2
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        from services.ai.enhanced_rag_service import EnhancedRAGService
        
        rag = EnhancedRAGService()
        
        rag.ingest_documents(
            [{"content": "Test", "metadata": {}}],
            tenant_id="test"
        )
        
        stats = rag.get_stats()
        
        assert stats["total_documents"] == 1
        assert "embedding_model" in stats
        assert "tenant_document_counts" in stats


# Autonomous Agent Tests
class TestAutonomousAgent:
    """Test Autonomous Agent"""
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        from services.ai.autonomous_agent import AutonomousAgent
        
        agent = AutonomousAgent(name="TestAgent")
        
        assert agent.name == "TestAgent"
        assert len(agent.executions) == 0
        assert len(agent.improvement_suggestions) == 0
    
    @pytest.mark.asyncio
    async def test_web_search(self):
        """Test web search capability"""
        from services.ai.autonomous_agent import AutonomousAgent
        
        agent = AutonomousAgent()
        
        if not agent.web_search_available:
            pytest.skip("Web search not available")
        
        result = await agent._web_search("Python programming")
        
        assert "status" in result
        # Result may be success or error depending on network
    
    @pytest.mark.asyncio
    async def test_generate_code_mock(self):
        """Test code generation with mock LLM"""
        from services.ai.autonomous_agent import AutonomousAgent
        
        agent = AutonomousAgent()
        
        mock_response = {
            "content": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)",
            "provider": "mock"
        }
        
        with patch.object(agent, 'llm_router') as mock_router:
            mock_router.complete = AsyncMock(return_value=mock_response)
            agent.llm_available = True
            
            result = await agent._generate_code("factorial function")
            
            assert result["status"] == "success"
            assert "code" in result
            assert "def factorial" in result["code"]
    
    @pytest.mark.asyncio
    async def test_self_heal(self):
        """Test self-healing capability"""
        from services.ai.autonomous_agent import AutonomousAgent, AgentExecution, AgentState
        
        agent = AutonomousAgent()
        
        failed_step = {"action": "test", "parameters": {}}
        error = Exception("Test error")
        
        execution = AgentExecution(
            execution_id="test",
            task="test task",
            state=AgentState.THINKING
        )
        
        mock_response = {
            "content": '{"can_heal": true, "modified_step": {"action": "test_fixed"}, "reasoning": "Fixed"}',
            "provider": "mock"
        }
        
        with patch.object(agent, 'llm_router') as mock_router:
            mock_router.complete = AsyncMock(return_value=mock_response)
            agent.llm_available = True
            
            result = await agent._self_heal(failed_step, error, execution)
            
            assert result.get("healed") == True
            assert "modified_step" in result
    
    def test_get_improvement_suggestions(self):
        """Test getting improvement suggestions"""
        from services.ai.autonomous_agent import AutonomousAgent
        
        agent = AutonomousAgent()
        
        # Add mock suggestions
        agent.improvement_suggestions = [
            {
                "title": "Optimize cache",
                "category": "performance",
                "priority": "high",
                "description": "Cache optimization",
                "implementation": "Add Redis",
                "timestamp": "2024-01-01",
                "status": "pending"
            },
            {
                "title": "Add MFA",
                "category": "security",
                "priority": "high",
                "description": "Multi-factor auth",
                "implementation": "TOTP",
                "timestamp": "2024-01-01",
                "status": "pending"
            }
        ]
        
        # Get all suggestions
        all_suggestions = agent.get_improvement_suggestions()
        assert len(all_suggestions) == 2
        
        # Filter by category
        perf_suggestions = agent.get_improvement_suggestions(category="performance")
        assert len(perf_suggestions) == 1
        assert perf_suggestions[0]["category"] == "performance"
        
        # Filter by priority
        high_priority = agent.get_improvement_suggestions(priority="high")
        assert len(high_priority) == 2
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        from services.ai.autonomous_agent import AutonomousAgent
        
        agent = AutonomousAgent()
        stats = agent.get_stats()
        
        assert "agent_name" in stats
        assert "total_executions" in stats
        assert "success_rate" in stats
        assert "capabilities" in stats
        assert isinstance(stats["capabilities"], dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
