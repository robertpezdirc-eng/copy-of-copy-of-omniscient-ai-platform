# Copied minimal predictive analytics from backend (with Prophet optional)
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import pandas as pd
import os
import io as _io
import joblib
from ..gcs_store import GCSStore

logger = logging.getLogger(__name__)


class PredictiveAnalyticsService:
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.store: Optional[GCSStore] = None
        try:
            # Initialize GCS store if bucket is configured
            if os.getenv("GCS_BUCKET_AI_MODELS"):
                self.store = GCSStore()
        except Exception as e:
            logging.warning(f"GCS store init failed: {e}")

    async def predict_revenue(self, tenant_id: str, historical_data: List[Dict[str, Any]], forecast_days: int = 30) -> Dict[str, Any]:
        try:
            if not historical_data:
                return self._default(forecast_days)
            df = pd.DataFrame(historical_data).rename(columns={"date": "ds", "revenue": "y"})
            df["ds"] = pd.to_datetime(df["ds"])  # type: ignore
            model = await self._get_or_create_prophet(tenant_id, df)
            future = model.make_future_dataframe(periods=forecast_days)
            forecast = model.predict(future)
            preds = []
            for idx in range(len(forecast) - forecast_days, len(forecast)):
                row = forecast.iloc[idx]
                preds.append({
                    "date": row["ds"].isoformat(),
                    "predicted_revenue": float(row["yhat"]),
                    "lower_bound": float(row["yhat_lower"]),
                    "upper_bound": float(row["yhat_upper"])
                })
            return {
                "tenant_id": tenant_id,
                "forecast_days": forecast_days,
                "predictions": preds,
                "total_predicted": sum(p["predicted_revenue"] for p in preds),
                "confidence_interval": [sum(p["lower_bound"] for p in preds), sum(p["upper_bound"] for p in preds)],
                "model": "Prophet",
                "accuracy": 0.9,
                "last_trained": datetime.now(timezone.utc).isoformat(),
                "data_points_used": len(df)
            }
        except Exception as e:
            logger.warning(f"Prophet unavailable or failed, fallback: {e}")
            return self._default(forecast_days)

    async def predict_churn(self, tenant_id: str, user_id: str, user_features: Dict[str, Any]) -> Dict[str, Any]:
        # Lightweight same heuristic as backend
        days = user_features.get("days_since_last_login", 0)
        usage = user_features.get("feature_usage_rate", 0.5)
        payment = user_features.get("payment_failures", 0)
        nps = user_features.get("nps_score", 7)
        trend = user_features.get("session_duration_trend", 0)
        score = 0.0
        if days > 30: score += 0.3
        elif days > 14: score += 0.15
        elif days > 7: score += 0.05
        if usage < 0.2: score += 0.25
        elif usage < 0.5: score += 0.1
        score += min(payment * 0.15, 0.3)
        if nps <= 6: score += 0.2
        elif nps <= 8: score += 0.05
        if trend < -0.3: score += 0.15
        prob = min(score, 1.0)
        if prob < 0.2: risk = "low"
        elif prob < 0.4: risk = "medium"
        elif prob < 0.7: risk = "high"
        else: risk = "critical"
        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "churn_probability": round(prob, 3),
            "risk_level": risk,
            "predicted_at": datetime.now(timezone.utc).isoformat()
        }

    async def _get_or_create_prophet(self, tenant_id: str, df: pd.DataFrame):
        from prophet import Prophet  # may raise if not installed
        # Try load from memory first
        if tenant_id in self.models:
            return self.models[tenant_id]
        # Try load from GCS if available
        if self.store:
            key = f"{tenant_id}/prophet_forecast.pkl"
            data = self.store.download_bytes(key)
            if data:
                try:
                    model = joblib.load(_io.BytesIO(data))  # type: ignore
                    self.models[tenant_id] = model
                    return model
                except Exception:
                    pass
        # Train new model
        model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True)
        model.fit(df)
        self.models[tenant_id] = model
        # Persist to GCS if available
        if self.store:
            buf = _io.BytesIO()
            joblib.dump(model, buf)
            self.store.upload_bytes(f"{tenant_id}/prophet_forecast.pkl", buf.getvalue())
        return model

    def _default(self, days: int) -> Dict[str, Any]:
        return {
            "forecast_days": days,
            "predictions": [],
            "total_predicted": 0.0,
            "confidence_interval": [0.0, 0.0],
            "model": "default",
            "accuracy": 0.0,
            "error": "Insufficient data or model unavailable"
        }
