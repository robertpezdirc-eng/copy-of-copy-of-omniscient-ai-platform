import os
import time
from typing import Dict, Any, Optional

class PriceFeed:
    """
    Poenostavljen cenovni vir. Poskusi prebrati cene iz okolja, sicer uporabi privzete.
    Privzete cene (na 1k tokens):
    - openai.gpt-4: 0.05 USD
    - google.gemini-ultra: 0.03 USD
    """
    def __init__(self) -> None:
        self.last_updated = 0.0
        self.cache: Optional[Dict[str, Any]] = None

    def get_current_prices(self, window: str = "weekly") -> Dict[str, Any]:
        # Preberi iz env, če na voljo
        openai_price = os.environ.get("OPENAI_PRICE_USD")
        google_price = os.environ.get("GOOGLE_PRICE_USD")
        if openai_price and google_price:
            data = {
                "window": window,
                "providers": {
                    "openai": {"gpt-4": float(openai_price)},
                    "gemini": {"ultra": float(google_price)},
                },
                "timestamp": time.time(),
            }
            self.cache = data
            self.last_updated = data["timestamp"]
            return data
        # Fallback privzete cene
        data = {
            "window": window,
            "providers": {
                "openai": {"gpt-4": 0.05},
                "gemini": {"ultra": 0.03},
            },
            "timestamp": time.time(),
        }
        self.cache = data
        self.last_updated = data["timestamp"]
        return data