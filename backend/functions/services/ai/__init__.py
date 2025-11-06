"""
AI Services Module
Advanced Machine Learning & Artificial Intelligence

Includes:
- Predictive Analytics (Prophet, LSTM, TensorFlow)
- Recommendation System (Collaborative + Content-based + Deep Learning)
- Sentiment Analysis (50+ languages, emotion detection)
- Anomaly Detection (PyOD, Isolation Forest)
- Swarm Intelligence (Multi-agent collaboration)
"""

from .predictive_analytics import PredictiveAnalyticsService
from .recommendation_engine import RecommendationEngine
from .sentiment_analysis import SentimentAnalysisService
from .anomaly_detection import AnomalyDetectionService
from .swarm_intelligence import SwarmIntelligenceOrchestrator

__all__ = [
    "PredictiveAnalyticsService",
    "RecommendationEngine",
    "SentimentAnalysisService",
    "AnomalyDetectionService",
    "SwarmIntelligenceOrchestrator"
]
