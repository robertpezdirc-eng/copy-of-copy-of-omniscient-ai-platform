"""
Isolation Forest for Advanced Anomaly Detection
Unsupervised outlier detection using tree-based ensemble
"""

from typing import List, Dict, Any, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    import joblib
    
    class IsolationForestService:
        """
        Advanced anomaly detection using Isolation Forest
        
        Isolation Forest isolates anomalies by randomly selecting features
        and split values. Anomalies are easier to isolate (shorter paths).
        """
        
        def __init__(
            self,
            contamination: float = 0.1,
            n_estimators: int = 100,
            max_samples: int = 256,
            random_state: int = 42
        ):
            """
            Initialize Isolation Forest detector
            
            Args:
                contamination: Expected proportion of outliers (0.1 = 10%)
                n_estimators: Number of trees
                max_samples: Samples per tree
                random_state: Random seed
            """
            self.contamination = contamination
            self.model = IsolationForest(
                contamination=contamination,
                n_estimators=n_estimators,
                max_samples=max_samples,
                random_state=random_state,
                n_jobs=-1  # Use all CPUs
            )
            self.scaler = StandardScaler()
            self.is_fitted = False
        
        def fit(self, X: np.ndarray) -> Dict[str, Any]:
            """
            Fit Isolation Forest on training data
            
            Args:
                X: Training data (n_samples, n_features)
            
            Returns:
                Fitting results
            """
            try:
                # Standardize features
                X_scaled = self.scaler.fit_transform(X)
                
                # Fit model
                self.model.fit(X_scaled)
                self.is_fitted = True
                
                # Get anomaly scores
                scores = self.model.score_samples(X_scaled)
                
                return {
                    "status": "success",
                    "n_samples": len(X),
                    "n_features": X.shape[1],
                    "contamination": self.contamination,
                    "mean_score": float(np.mean(scores)),
                    "std_score": float(np.std(scores))
                }
            
            except Exception as e:
                logger.error(f"Isolation Forest fitting failed: {e}")
                return {"status": "error", "message": str(e)}
        
        def predict(
            self,
            X: np.ndarray,
            return_scores: bool = True
        ) -> Dict[str, Any]:
            """
            Predict anomalies in new data
            
            Args:
                X: Data to predict (n_samples, n_features)
                return_scores: Include anomaly scores
            
            Returns:
                Predictions and scores
            """
            try:
                if not self.is_fitted:
                    return {
                        "status": "error",
                        "message": "Model not fitted. Call fit() first."
                    }
                
                # Standardize
                X_scaled = self.scaler.transform(X)
                
                # Predict (-1 = anomaly, 1 = normal)
                predictions = self.model.predict(X_scaled)
                
                # Anomaly scores (lower = more anomalous)
                scores = self.model.score_samples(X_scaled)
                
                # Decision function (signed distance to separating hyperplane)
                decision_scores = self.model.decision_function(X_scaled)
                
                # Identify anomalies
                anomaly_indices = np.where(predictions == -1)[0].tolist()
                
                results = {
                    "n_samples": len(X),
                    "n_anomalies": len(anomaly_indices),
                    "anomaly_rate": len(anomaly_indices) / len(X) if len(X) > 0 else 0,
                    "anomaly_indices": anomaly_indices
                }
                
                if return_scores:
                    results["anomaly_scores"] = scores.tolist()
                    results["decision_scores"] = decision_scores.tolist()
                    results["predictions"] = predictions.tolist()
                
                return results
            
            except Exception as e:
                logger.error(f"Isolation Forest prediction failed: {e}")
                return {"status": "error", "message": str(e)}
        
        def detect_anomalies(
            self,
            data: List[Dict[str, float]],
            feature_names: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """
            High-level anomaly detection with automatic fitting
            
            Args:
                data: List of data points as dicts
                feature_names: Feature names to extract
            
            Returns:
                Anomaly detection results
            """
            try:
                # Convert to numpy array
                if feature_names:
                    X = np.array([[d.get(f, 0) for f in feature_names] for d in data])
                else:
                    # Use all numeric values
                    feature_names = list(data[0].keys())
                    X = np.array([[d.get(f, 0) for f in feature_names] for d in data])
                
                # Fit and predict
                fit_result = self.fit(X)
                if fit_result.get("status") == "error":
                    return fit_result
                
                predict_result = self.predict(X, return_scores=True)
                
                # Build detailed results
                anomalies = []
                for idx in predict_result["anomaly_indices"]:
                    anomalies.append({
                        "index": idx,
                        "data": data[idx],
                        "anomaly_score": predict_result["anomaly_scores"][idx],
                        "decision_score": predict_result["decision_scores"][idx],
                        "severity": self._classify_severity(
                            predict_result["anomaly_scores"][idx]
                        )
                    })
                
                return {
                    "status": "success",
                    "n_samples": len(data),
                    "n_anomalies": len(anomalies),
                    "anomaly_rate": predict_result["anomaly_rate"],
                    "contamination": self.contamination,
                    "feature_names": feature_names,
                    "anomalies": anomalies,
                    "fit_info": fit_result
                }
            
            except Exception as e:
                logger.error(f"Anomaly detection failed: {e}")
                return {"status": "error", "message": str(e)}
        
        def _classify_severity(self, score: float) -> str:
            """
            Classify anomaly severity based on score
            
            Args:
                score: Anomaly score (lower = more anomalous)
            
            Returns:
                Severity level
            """
            if score < -0.5:
                return "critical"
            elif score < -0.3:
                return "high"
            elif score < -0.1:
                return "medium"
            else:
                return "low"
        
        def save_model(self, filepath: str) -> bool:
            """
            Save fitted model to disk
            
            Args:
                filepath: Path to save model
            
            Returns:
                Success status
            """
            try:
                if not self.is_fitted:
                    logger.warning("Model not fitted, nothing to save")
                    return False
                
                joblib.dump({
                    "model": self.model,
                    "scaler": self.scaler,
                    "contamination": self.contamination,
                    "is_fitted": self.is_fitted
                }, filepath)
                
                logger.info(f"Model saved to {filepath}")
                return True
            
            except Exception as e:
                logger.error(f"Model save failed: {e}")
                return False
        
        def load_model(self, filepath: str) -> bool:
            """
            Load fitted model from disk
            
            Args:
                filepath: Path to load model from
            
            Returns:
                Success status
            """
            try:
                data = joblib.load(filepath)
                
                self.model = data["model"]
                self.scaler = data["scaler"]
                self.contamination = data["contamination"]
                self.is_fitted = data["is_fitted"]
                
                logger.info(f"Model loaded from {filepath}")
                return True
            
            except Exception as e:
                logger.error(f"Model load failed: {e}")
                return False
    
    # Singleton instance
    _isolation_forest = IsolationForestService()
    
    def get_isolation_forest_service() -> IsolationForestService:
        return _isolation_forest
    
except ImportError as e:
    logger.warning(f"scikit-learn not available: {e}")
    
    # Dummy service
    class IsolationForestService:
        def fit(self, X):
            return {"status": "error", "message": "scikit-learn not installed"}
        
        def predict(self, X, return_scores=True):
            return {"status": "error", "message": "scikit-learn not installed"}
        
        def detect_anomalies(self, data, feature_names=None):
            return {"status": "error", "message": "scikit-learn not installed"}
        
        def save_model(self, filepath):
            return False
        
        def load_model(self, filepath):
            return False
    
    def get_isolation_forest_service() -> IsolationForestService:
        return IsolationForestService()
