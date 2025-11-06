"""
Anomaly Detection Service
Real-time anomaly detection using PyOD and Isolation Forest
"""

import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class AnomalyDetectionService:
    def __init__(self):
        self._model = None
    
    async def detect(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect anomalies in metrics.
        metrics: list of {metric, value, timestamp}
        """
        try:
            if not metrics:
                return {"anomalies": [], "count": 0}
            
            X = np.array([[m.get("value", 0)] for m in metrics], dtype=float)
            
            labels = await self._predict_labels(X)
            anomalies = []
            for i, m in enumerate(metrics):
                if labels[i] == 1:  # 1 = anomaly
                    anomalies.append({
                        "metric": m.get("metric", "unknown"),
                        "value": m.get("value", 0),
                        "timestamp": m.get("timestamp"),
                        "severity": self._estimate_severity(m.get("value", 0), X)
                    })
            
            return {"anomalies": anomalies, "count": len(anomalies)}
        except Exception as e:
            logger.error(f"Anomaly detection error: {str(e)}")
            return {"anomalies": [], "count": 0}
    
    async def _predict_labels(self, X: np.ndarray):
        try:
            if self._model is None:
                from pyod.models.iforest import IForest
                self._model = IForest(contamination=0.05, random_state=42)
                # Fit with a bootstrap baseline (simple approach; replace with rolling window)
                baseline = np.random.normal(loc=np.mean(X), scale=max(np.std(X), 1e-6), size=(max(100, len(X)), 1))
                self._model.fit(baseline)
            
            preds = self._model.predict(X)  # 1 for outliers
            return preds
        except Exception as e:
            logger.warning(f"PyOD unavailable, fallback to z-score: {e}")
            # Fallback: simple z-score
            z = (X - np.mean(X)) / (np.std(X) + 1e-8)
            return (np.abs(z) > 3).astype(int).reshape(-1)
    
    def _estimate_severity(self, value: float, X: np.ndarray) -> str:
        mean = float(np.mean(X))
        std = float(np.std(X) + 1e-8)
        z = abs((value - mean) / std)
        if z > 4:
            return "critical"
        if z > 3:
            return "high"
        if z > 2:
            return "medium"
        return "low"


# Singleton
_anomaly_service = None

def get_anomaly_service() -> AnomalyDetectionService:
    global _anomaly_service
    if _anomaly_service is None:
        _anomaly_service = AnomalyDetectionService()
    return _anomaly_service
