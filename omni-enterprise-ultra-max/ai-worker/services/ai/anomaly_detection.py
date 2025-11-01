import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class AnomalyDetectionService:
    def __init__(self):
        self._model = None

    async def detect(self, metrics: List[Dict[str, Any]]):
        try:
            if not metrics:
                return {"anomalies": [], "count": 0}
            X = np.array([[m.get("value", 0)] for m in metrics], dtype=float)
            labels = await self._predict(X)
            anomalies = []
            for i, m in enumerate(metrics):
                if labels[i] == 1:
                    anomalies.append({
                        "metric": m.get("metric","unknown"),
                        "value": m.get("value",0),
                        "timestamp": m.get("timestamp"),
                        "severity": self._severity(m.get("value",0), X)
                    })
            return {"anomalies": anomalies, "count": len(anomalies)}
        except Exception as e:
            logger.error(f"Anomaly detect error: {e}")
            return {"anomalies": [], "count": 0}

    async def _predict(self, X: np.ndarray):
        try:
            from pyod.models.iforest import IForest
            if self._model is None:
                self._model = IForest(contamination=0.05, random_state=42)
                baseline = np.random.default_rng(42).normal(loc=float(np.mean(X)), scale=float(max(np.std(X),1e-6)), size=(max(100,len(X)),1))
                self._model.fit(baseline)
            return self._model.predict(X)
        except Exception as e:
            logger.warning(f"PyOD unavailable, z-score fallback: {e}")
            z = (X - np.mean(X)) / (np.std(X) + 1e-8)
            return (np.abs(z) > 3).astype(int).reshape(-1)

    def _severity(self, value: float, X: np.ndarray) -> str:
        mean = float(np.mean(X)); std = float(np.std(X)+1e-8)
        z = abs((value-mean)/std)
        if z>4: return "critical"
        if z>3: return "high"
        if z>2: return "medium"
        return "low"
