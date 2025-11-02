"""
Omni Client Exceptions
"""


class OmniAPIError(Exception):
    """Base exception for Omni API errors"""
    
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class OmniAuthError(OmniAPIError):
    """Authentication error - invalid or expired API key"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class OmniRateLimitError(OmniAPIError):
    """Rate limit exceeded error"""
    
    def __init__(self, message: str, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message, status_code=429)
