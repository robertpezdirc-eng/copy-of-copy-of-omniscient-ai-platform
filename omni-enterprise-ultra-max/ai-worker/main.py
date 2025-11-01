from fastapi import FastAPI, Request, Response, HTTPException
"""
OMNI AI WORKER - Heavy AI microservice
Provides AI endpoints: forecasting, churn, recommendations, sentiment, anomalies
"""

import os
import uuid
from fastapi import FastAPI, Body, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from prometheus_client import CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import threading

# TIER 1: Production Essentials (import early, minimal cost)
from middleware.prometheus_metrics import (
    PrometheusMiddleware, 
    get_metrics,
    track_model_inference
)
from middleware.auth import AuthenticationMiddleware, limiter, get_tenant_id, create_api_key
from utils.structured_logging import (
    get_logger, 
    set_request_context, 
    clear_request_context,
    configure_root_logger,
    PerformanceLogger
)
from utils.sentry_integration import (
    init_sentry,
    capture_exception,
    set_user_context,
    track_transaction
)

# Configure logging
configure_root_logger(level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

# Initialize Sentry
init_sentry(
    environment=os.getenv("ENVIRONMENT", "production"),
    traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
)

app = FastAPI(title="OMNI AI Worker", version="1.0.0")

# Add TIER 1 middleware
app.add_middleware(PrometheusMiddleware)
app.add_middleware(AuthenticationMiddleware)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate services lazily at startup to reduce cold-start time
_predictive: Optional[Any] = None
_reco: Optional[Any] = None
_sentiment: Optional[Any] = None
_anomaly: Optional[Any] = None
_swarm: Optional[Any] = None

# New AGI services (lazy)
_lstm = None
_hf = None
_isolation_forest = None
_agent_coordinator = None
_agi_framework = None

# cache of FAISS indices per tenant
_faiss_cache: dict[str, Any] = {}

# Startup flag to track heavy initialization
_services_ready = False

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(
        "AI Worker starting - services will load in background",
        version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "production")
    )
    # Start background thread to load services
    thread = threading.Thread(target=_load_services_background, daemon=True)
    thread.start()

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():


def _load_services_background():
    """Load heavy ML services in background thread"""
    global _services_ready, _predictive, _reco, _sentiment, _anomaly, _swarm
    global _lstm, _hf, _isolation_forest, _agent_coordinator, _agi_framework

    logger.info("Loading heavy AI services (background thread)...")
    
    try:


def _ensure_services_loaded():
    """Check if services are ready, wait if necessary"""
    if not _services_ready:
        raise HTTPException(
            status_code=503,
            detail="AI services are still initializing. Please try again in a moment."
        )
        # Local services (copied or minimal versions)
        from services.ai.predictive_analytics import PredictiveAnalyticsService
        from services.ai.recommendation_engine import RecommendationEngine
        from services.ai.sentiment_analysis import SentimentAnalysisService
        from services.ai.anomaly_detection import AnomalyDetectionService
        from services.ai.swarm_intelligence import SwarmIntelligenceOrchestrator
        from services.ai.vector_index import TenantVectorIndex

        # New AGI services
        from services.ai.lstm_networks import get_lstm_service
        from services.ai.huggingface_hub import get_huggingface_service
        from services.ai.isolation_forest import get_isolation_forest_service
        from services.ai.autonomous_agents import get_agent_coordinator, AutonomousAgent, AgentRole
        from services.ai.agi_framework import get_agi_framework, ReasoningMethod
        
        if _predictive is None:
            _predictive = PredictiveAnalyticsService()
        if _reco is None:
            _reco = RecommendationEngine()
        if _sentiment is None:
            _sentiment = SentimentAnalysisService()
        if _anomaly is None:
            _anomaly = AnomalyDetectionService()
        if _swarm is None:
            _swarm = SwarmIntelligenceOrchestrator()

        # AGI services
        if _lstm is None:
            _lstm = get_lstm_service()
        if _hf is None:
            _hf = get_huggingface_service()
        if _isolation_forest is None:
            _isolation_forest = get_isolation_forest_service()
        if _agent_coordinator is None:
            _agent_coordinator = get_agent_coordinator()
        if _agi_framework is None:
            _agi_framework = get_agi_framework()
        
        _services_ready = True
        logger.info("All AI services loaded successfully")
    except Exception as e:
        # Log but don't crash - allow health checks to pass
        logger.error("Service initialization failed", error=e)
    logger.info("AI Worker shutting down")

class PredictionRequest(BaseModel):
    user_id: str
    context: Dict[str, Any] = {}


class RevenueForecastRequest(BaseModel):
    tenant_id: Optional[str] = Field(default="default")
    historical_data: Optional[List[Dict[str, Any]]] = None
    forecast_days: Optional[int] = 30


class SwarmTask(BaseModel):
    goal: str
    context: Dict[str, Any] = {}

class UpsertItemsRequest(BaseModel):
    tenant_id: str
    items: List[Dict[str, Any]]  # [{id, text}]

class VectorQueryRequest(BaseModel):
    tenant_id: str
    text: str
    top_k: int = 5


@app.get("/health")
async def health():
    """Health check endpoint - responds immediately, reports service status"""
    return {
        "status": "ok",
        "service": "ai-worker",
        "time": datetime.now(timezone.utc).isoformat(),
        "services_ready": _services_ready
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint - no authentication required"""
    return Response(content=get_metrics(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "OMNI AI Worker",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "metrics": "/metrics",
        "health": "/health",
        "authentication": "Required - use X-API-Key header (except for public endpoints)",
        "endpoints": {
            "lstm": "/predict/revenue-lstm",
            "huggingface": "/huggingface/*",
            "anomaly": "/anomaly/isolation-forest",
            "recommendations": "/recommend/products",
            "swarm": "/swarm/coordinate",
            "agents": "/agents/*",
            "agi": "/agi/*"
        }
    }


@app.post("/predict/revenue")
async def predict_revenue(payload: RevenueForecastRequest):
    _ensure_services_loaded()
    if payload.historical_data:
        return await _predictive.predict_revenue(
            tenant_id=payload.tenant_id or "default",
            historical_data=payload.historical_data,
            forecast_days=payload.forecast_days or 30
        )
    return {"error": "historical_data required"}


@app.post("/predict/churn")
    _ensure_services_loaded()
async def predict_churn(payload: PredictionRequest):
    return await _predictive.predict_churn(
        tenant_id=str(payload.context.get("tenant_id", "default")),
        user_id=payload.user_id,
        user_features=payload.context
    )


@app.post("/recommend/products")
    _ensure_services_loaded()
async def recommend_products(payload: PredictionRequest):
    recs = await _reco.recommend_products(
        tenant_id=str(payload.context.get("tenant_id", "default")),
        user_id=payload.user_id,
        user_context=payload.context
    )
    return {"recommendations": recs}


@app.post("/recommend/features")
    _ensure_services_loaded()
    _ensure_services_loaded()
async def recommend_features(payload: PredictionRequest):
    feats = await _reco.recommend_features(
        tenant_id=str(payload.context.get("tenant_id", "default")),
        user_id=payload.user_id,
        current_usage=payload.context
    )
    return {"unused_features": feats}


@app.get("/anomaly/detect")
async def anomaly_detect():
    now = datetime.now(timezone.utc)
    metrics = [
        {"metric": "api_response_time_ms", "value": 120 + (i % 10) * 3, "timestamp": (now).isoformat()}
        for i in range(60)
    ]
    metrics[3]["value"] = 780
    return await _anomaly.detect(metrics)


@app.post("/sentiment/analyze")
    _ensure_services_loaded()
async def sentiment_analyze(text: str = Body(..., embed=True)):
    return await _sentiment.analyze(text)


@app.post("/swarm/coordinate")
    _ensure_services_loaded()
async def swarm_coordinate(task: SwarmTask):
    return await _swarm.coordinate({"goal": task.goal, "context": task.context})


@app.post("/faiss/upsert")
    _ensure_services_loaded()
async def faiss_upsert(req: UpsertItemsRequest):
    idx = _faiss_cache.get(req.tenant_id)
    if not idx:
        idx = TenantVectorIndex(req.tenant_id)
        _faiss_cache[req.tenant_id] = idx
    idx.upsert(req.items)
    return {"status": "ok", "count": len(req.items)}


@app.post("/faiss/query")
    _ensure_services_loaded()
async def faiss_query(req: VectorQueryRequest):
    idx = _faiss_cache.get(req.tenant_id)
    if not idx:
        idx = TenantVectorIndex(req.tenant_id)
        _faiss_cache[req.tenant_id] = idx
    results = idx.query(req.text, top_k=req.top_k)
    return {"results": [{"id": rid, "score": score} for rid, score in results]}


# ========== NEW AGI ENDPOINTS ==========

class LSTMForecastRequest(BaseModel):
    tenant_id: str = "default"
    time_series: List[float]
    forecast_steps: int = 30
    sequence_length: int = 10


@app.post("/predict/revenue-lstm")
    _ensure_services_loaded()
@limiter.limit("100/minute")
async def predict_revenue_lstm(request: Request, payload: LSTMForecastRequest):
    """
    LSTM-based time series forecasting
    Alternative to Prophet with attention mechanism
    """
    # Set request context
    request_id = str(uuid.uuid4())
    tenant_id = get_tenant_id(request)
    set_request_context(request_id, tenant_id)
    
    logger.info(
        "LSTM forecast requested",
        tenant_id=tenant_id,
        forecast_steps=payload.forecast_steps,
        data_points=len(payload.time_series)
    )
    
    try:
        # Track metrics
        with track_model_inference("lstm", tenant_id):
            # Ensure service uses requested sequence length
            try:
                _lstm.seq_length = payload.sequence_length
            except Exception:
                pass

            # Train LSTM
            train_result = await _lstm.train(
                payload.time_series,
                epochs=50,
                learning_rate=0.001
            )
            
            # Generate predictions
            predictions = await _lstm.predict(
                payload.time_series,
                forecast_periods=payload.forecast_steps
            )
            
            result = {
                "status": "success",
                "model": "LSTM with attention",
                "tenant_id": tenant_id,
                "request_id": request_id,
                "forecast": predictions.get("predictions", []),
                "confidence_intervals": predictions.get("confidence_intervals"),
                "training": {
                    "final_loss": train_result.get("final_loss"),
                    "epochs": train_result.get("epochs")
                }
            }
            
            logger.info("LSTM forecast completed", final_loss=result["training"]["final_loss"])
            return result
    
    except Exception as e:
        logger.error("LSTM forecast failed", error=e)
        capture_exception(e, tenant_id=tenant_id, model_type="lstm")
        return {"status": "error", "message": str(e), "request_id": request_id}
    finally:
        clear_request_context()


class HuggingFaceInferenceRequest(BaseModel):
    model_id: str
    input_text: str
    task: str = "text-classification"


@app.post("/huggingface/inference")
async def huggingface_inference(payload: HuggingFaceInferenceRequest):
    _ensure_services_loaded()
    """
    Run inference using HuggingFace models
    Supports: text-classification, text-generation, summarization, translation
    """
    result = await _hf.run_inference(
        model_id=payload.model_id,
        input_text=payload.input_text,
        task=payload.task
    )
    return result


class HuggingFaceSearchRequest(BaseModel):
    query: Optional[str] = None
    task: Optional[str] = None
    limit: int = 10


@app.post("/huggingface/search")
async def huggingface_search(payload: HuggingFaceSearchRequest):
    _ensure_services_loaded()
    """Search HuggingFace Hub for models"""
    results = await _hf.search_models(
        task=payload.task,
        query=payload.query,
        limit=payload.limit
    )
    return {"models": results}


class IsolationForestRequest(BaseModel):
    tenant_id: str = "default"
    data: List[Dict[str, float]]
    feature_names: Optional[List[str]] = None
    contamination: float = 0.1


@app.post("/anomaly/isolation-forest")
    _ensure_services_loaded()
async def anomaly_isolation_forest(payload: IsolationForestRequest):
    """
    Advanced anomaly detection using Isolation Forest
    Unsupervised outlier detection with contamination tuning
    """
    # Create new instance with specified contamination
    from services.ai.isolation_forest import IsolationForestService
    detector = IsolationForestService(contamination=payload.contamination)
    
    result = detector.detect_anomalies(
        data=payload.data,
        feature_names=payload.feature_names
    )
    
    return result


class AgentObservationRequest(BaseModel):
    observation: Dict[str, Any]
    agent_roles: Optional[List[str]] = None


@app.post("/agents/observe")
    _ensure_services_loaded()
async def agents_observe(payload: AgentObservationRequest):
    """
    Process observation with autonomous agents
    Agents reason, plan, and execute actions
    """
    await _agent_coordinator.process_observation(payload.observation)
    
    return {
        "status": "success",
        "message": "Observation processed by agents",
        "n_agents": len(_agent_coordinator.agents)
    }


@app.get("/agents/status")
    _ensure_services_loaded()
async def agents_status():
    """Get status of all registered agents"""
    agents_info = []
    for agent_id, agent in _agent_coordinator.agents.items():
        agents_info.append({
            "agent_id": agent_id,
            "role": agent.role.value,
            "is_active": agent.is_active,
            "capabilities": agent.capabilities,
            "n_tasks": len(agent.task_history),
            "n_short_term_memories": len(agent.memory.short_term),
            "n_episodic_memories": len(agent.memory.episodic)
        })
    
    return {
        "n_agents": len(agents_info),
        "agents": agents_info
    }


@app.post("/agents/register")
    _ensure_services_loaded()
async def agents_register(
    agent_id: str = Body(...),
    role: str = Body(...),
    capabilities: List[str] = Body(...)
):
    """Register a new autonomous agent"""
    agent_role = AgentRole(role)
    agent = AutonomousAgent(agent_id, agent_role, capabilities)
    agent.is_active = True
    _agent_coordinator.register_agent(agent)
    
    return {
        "status": "success",
        "agent_id": agent_id,
        "role": role
    }


# ========== AGI FRAMEWORK ENDPOINTS ==========

class AGIProcessRequest(BaseModel):
    problem: str
    context: Dict[str, Any] = {}
    reasoning_method: str = "chain_of_thought"


@app.post("/agi/process")
async def agi_process(payload: AGIProcessRequest):
    _ensure_services_loaded()
    """
    Full AGI processing pipeline: Reasoning → Planning → Execution
    
    Supports multiple reasoning methods:
    - chain_of_thought: Step-by-step reasoning
    - react: Reason + Act in loops
    - tree_of_thought: Multiple reasoning paths
    """
    try:
        # Convert reasoning method
        method_map = {
            "chain_of_thought": ReasoningMethod.CHAIN_OF_THOUGHT,
            "react": ReasoningMethod.REACT,
            "tree_of_thought": ReasoningMethod.TREE_OF_THOUGHT
        }
        method = method_map.get(payload.reasoning_method, ReasoningMethod.CHAIN_OF_THOUGHT)
        
        # Process with AGI framework
        result = await _agi_framework.process(
            problem=payload.problem,
            context=payload.context,
            reasoning_method=method
        )
        
        return {
            "status": "success",
            "problem": payload.problem,
            "reasoning_method": payload.reasoning_method,
            "execution_result": {
                "plan_id": result.plan_id,
                "success": result.success,
                "steps_completed": result.steps_completed,
                "total_steps": result.total_steps,
                "duration": result.duration,
                "errors": result.errors,
                "output": result.output
            }
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/agi/reasoning/history")
    _ensure_services_loaded()
async def agi_reasoning_history(limit: int = 10):
    """Get AGI reasoning history"""
    history = _agi_framework.reasoning.reasoning_history[-limit:]
    return {
        "n_total": len(_agi_framework.reasoning.reasoning_history),
        "history": history
    }


@app.get("/agi/execution/history")
async def agi_execution_history(limit: int = 10):
    """Get AGI execution history"""
    history = _agi_framework.execution.execution_history[-limit:]
    return {
        "n_total": len(_agi_framework.execution.execution_history),
        "history": [
            {
                "plan_id": r.plan_id,
                "success": r.success,
                "steps_completed": r.steps_completed,
                "total_steps": r.total_steps,
                "duration": r.duration,
                "errors": r.errors
            }
            for r in history
        ]
    }


