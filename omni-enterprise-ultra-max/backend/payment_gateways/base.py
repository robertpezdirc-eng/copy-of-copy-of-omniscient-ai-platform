from abc import ABC, abstractmethod
from typing import Any, Dict


class PaymentGateway(ABC):
    """Abstract interface for payment gateways."""

    @abstractmethod
    def authorize(self, amount: float, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Send an authorize request. Return parsed JSON response."""
        raise NotImplementedError

    @abstractmethod
    def capture(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        """Send a capture request. Return parsed JSON response."""
        raise NotImplementedError
