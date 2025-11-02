"""
Omni Enterprise Ultra Max - Python SDK
Official Python client library for the Omni AI Platform
Version: 1.0.0
"""

from .client import OmniClient
from .exceptions import OmniAPIError, OmniAuthError, OmniRateLimitError

__version__ = "1.0.0"
__all__ = ["OmniClient", "OmniAPIError", "OmniAuthError", "OmniRateLimitError"]
