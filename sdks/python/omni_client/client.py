"""
Omni Client - Main client class for interacting with Omni API
"""

import time
from typing import Optional, Dict, Any, List
import httpx

from .exceptions import OmniAPIError, OmniAuthError, OmniRateLimitError


class OmniClient:
    """
    Official Python client for Omni Enterprise Ultra Max Platform
    
    Example:
        >>> from omni_client import OmniClient
        >>> client = OmniClient(api_key="your-api-key")
        >>> predictions = client.intelligence.predict_revenue(user_id="123")
        >>> print(predictions)
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.omni-platform.com",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize Omni client
        
        Args:
            api_key: Your Omni API key
            base_url: Base URL of the Omni API (default: production)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._get_headers()
        )
        
        # Initialize service clients
        self.intelligence = IntelligenceService(self)
        self.ai = AIService(self)
        self.analytics = AnalyticsService(self)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"omni-python-sdk/1.0.0"
        }
    
    def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            **kwargs: Additional request parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            OmniAuthError: Authentication failed
            OmniRateLimitError: Rate limit exceeded
            OmniAPIError: Other API errors
        """
        url = f"{self.base_url}{path}"
        
        for attempt in range(self.max_retries):
            try:
                response = self._client.request(method, path, **kwargs)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("X-RateLimit-Reset", 60))
                    raise OmniRateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after}s",
                        retry_after=retry_after
                    )
                
                # Handle authentication errors
                if response.status_code == 401:
                    raise OmniAuthError("Invalid or expired API key")
                
                # Handle other errors
                if response.status_code >= 400:
                    error_msg = response.json().get("detail", "Unknown error")
                    raise OmniAPIError(f"API error: {error_msg}", status_code=response.status_code)
                
                return response.json()
                
            except (httpx.RequestError, httpx.TimeoutException) as e:
                if attempt == self.max_retries - 1:
                    raise OmniAPIError(f"Request failed after {self.max_retries} attempts: {str(e)}")
                
                # Exponential backoff
                time.sleep(self.retry_delay * (2 ** attempt))
        
        raise OmniAPIError("Max retries exceeded")
    
    def close(self):
        """Close the HTTP client"""
        self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class IntelligenceService:
    """AI Intelligence service endpoints"""
    
    def __init__(self, client: OmniClient):
        self.client = client
    
    def predict_revenue(self, user_id: Optional[str] = None, **params) -> Dict[str, Any]:
        """
        Get revenue predictions
        
        Args:
            user_id: Optional user ID for personalized predictions
            **params: Additional prediction parameters
            
        Returns:
            Revenue prediction results
        """
        data = {"user_id": user_id, **params} if user_id else params
        return self.client._request("GET", "/api/intelligence/predictions/revenue", json=data)
    
    def get_business_insights(self, timeframe: str = "30d") -> Dict[str, Any]:
        """
        Get business insights
        
        Args:
            timeframe: Time period for insights (e.g., "7d", "30d", "90d")
            
        Returns:
            Business insights and recommendations
        """
        return self.client._request("GET", f"/api/intelligence/insights/business?timeframe={timeframe}")
    
    def detect_anomalies(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect anomalies in data
        
        Args:
            data: List of data points to analyze
            
        Returns:
            Anomaly detection results
        """
        return self.client._request("POST", "/api/intelligence/anomaly-detection", json={"data": data})
    
    def predict_churn(self, user_id: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict customer churn probability
        
        Args:
            user_id: User ID to analyze
            features: User features for prediction
            
        Returns:
            Churn prediction with probability score
        """
        return self.client._request(
            "POST",
            "/api/intelligence/predict/churn",
            json={"user_id": user_id, "features": features}
        )


class AIService:
    """AI service endpoints"""
    
    def __init__(self, client: OmniClient):
        self.client = client
    
    def analyze_text(self, text: str, analysis_type: str = "sentiment") -> Dict[str, Any]:
        """
        Analyze text with AI
        
        Args:
            text: Text to analyze
            analysis_type: Type of analysis (sentiment, entities, summary)
            
        Returns:
            Text analysis results
        """
        return self.client._request(
            "POST",
            "/api/ai/analyze/text",
            json={"text": text, "analysis_type": analysis_type}
        )
    
    def get_models(self) -> List[Dict[str, Any]]:
        """
        Get available AI models
        
        Returns:
            List of available models
        """
        return self.client._request("GET", "/api/advanced-ai/models")
    
    def get_model_details(self, model_name: str) -> Dict[str, Any]:
        """
        Get details for a specific model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model details and capabilities
        """
        return self.client._request("GET", f"/api/advanced-ai/models/{model_name}")


class AnalyticsService:
    """Analytics service endpoints"""
    
    def __init__(self, client: OmniClient):
        self.client = client
    
    def get_dashboard(self, dashboard_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get analytics dashboard data
        
        Args:
            dashboard_id: Optional specific dashboard ID
            
        Returns:
            Dashboard data and metrics
        """
        params = {"id": dashboard_id} if dashboard_id else {}
        return self.client._request("GET", "/api/analytics/dashboard", params=params)
    
    def get_metrics(self, metric_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get real-time metrics
        
        Args:
            metric_names: Optional list of specific metrics to retrieve
            
        Returns:
            Current metric values
        """
        params = {"metrics": ",".join(metric_names)} if metric_names else {}
        return self.client._request("GET", "/api/analytics/metrics", params=params)
    
    def get_dashboard_types(self) -> List[Dict[str, Any]]:
        """
        Get available dashboard types
        
        Returns:
            List of dashboard types and templates
        """
        return self.client._request("GET", "/api/v1/dashboards/types")
