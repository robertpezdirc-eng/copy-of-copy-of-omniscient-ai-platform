"""
Sentry Integration for Error Tracking and Performance Monitoring
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastAPIIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import os
from typing import Optional, Dict, Any
from utils.structured_logging import get_logger

logger = get_logger(__name__)


def init_sentry(
    dsn: Optional[str] = None,
    environment: str = "production",
    release: Optional[str] = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1
):
    """
    Initialize Sentry SDK
    
    Args:
        dsn: Sentry DSN (if not provided, uses SENTRY_DSN env var)
        environment: Environment name (production, staging, development)
        release: Release version (if not provided, uses GIT_SHA env var)
        traces_sample_rate: Percentage of transactions to sample (0.0 to 1.0)
        profiles_sample_rate: Percentage of profiles to sample (0.0 to 1.0)
    """
    dsn = dsn or os.getenv("SENTRY_DSN")
    
    if not dsn:
        logger.warning("Sentry DSN not configured, error tracking disabled")
        return
    
    release = release or os.getenv("GIT_SHA", "unknown")
    
    # Configure integrations
    integrations = [
        FastAPIIntegration(),
        AsyncioIntegration(),
        LoggingIntegration(
            level=None,  # Capture all log levels
            event_level=None  # Don't send logs as events (we use structured logging)
        )
    ]
    
    try:
        sentry_sdk.init(
            dsn=dsn,
            integrations=integrations,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            environment=environment,
            release=f"ai-worker@{release}",
            send_default_pii=False,  # Don't send PII
            attach_stacktrace=True,
            max_breadcrumbs=50,
            before_send=before_send_event,
            before_send_transaction=before_send_transaction,
        )
        
        logger.info(
            "Sentry initialized",
            environment=environment,
            release=release,
            traces_sample_rate=traces_sample_rate
        )
        
    except Exception as e:
        logger.error("Failed to initialize Sentry", error=e)


def before_send_event(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter and modify events before sending to Sentry
    
    Args:
        event: Sentry event dictionary
        hint: Additional context
        
    Returns:
        Modified event or None to drop the event
    """
    # Drop health check errors
    if "request" in event and event["request"].get("url", "").endswith("/health"):
        return None
    
    # Add custom context
    if "tags" not in event:
        event["tags"] = {}
    
    event["tags"]["service"] = "ai-worker"
    
    return event


def before_send_transaction(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter transactions before sending to Sentry
    
    Args:
        event: Sentry transaction dictionary
        hint: Additional context
        
    Returns:
        Modified transaction or None to drop
    """
    # Drop health check transactions
    if event.get("transaction", "").endswith("/health"):
        return None
    
    return event


def capture_exception(error: Exception, **context):
    """
    Capture exception with additional context
    
    Args:
        error: Exception to capture
        **context: Additional context fields
    """
    with sentry_sdk.push_scope() as scope:
        # Add context
        for key, value in context.items():
            scope.set_context(key, value if isinstance(value, dict) else {"value": value})
        
        sentry_sdk.capture_exception(error)
        
        logger.error(
            "Exception captured by Sentry",
            error=error,
            **context
        )


def capture_message(message: str, level: str = "info", **context):
    """
    Capture message with context
    
    Args:
        message: Message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **context: Additional context
    """
    with sentry_sdk.push_scope() as scope:
        for key, value in context.items():
            scope.set_context(key, value if isinstance(value, dict) else {"value": value})
        
        sentry_sdk.capture_message(message, level=level)


def set_user_context(user_id: str, tenant_id: str = None, **extra):
    """
    Set user context for current scope
    
    Args:
        user_id: User ID
        tenant_id: Tenant ID
        **extra: Additional user fields
    """
    user_data = {"id": user_id}
    
    if tenant_id:
        user_data["tenant_id"] = tenant_id
    
    user_data.update(extra)
    
    sentry_sdk.set_user(user_data)


def set_transaction_context(
    transaction_name: str,
    operation: str,
    **tags
):
    """
    Set transaction context
    
    Args:
        transaction_name: Name of the transaction
        operation: Operation type (e.g., "http.request", "model.inference")
        **tags: Additional tags
    """
    with sentry_sdk.configure_scope() as scope:
        scope.set_transaction_name(transaction_name)
        
        for key, value in tags.items():
            scope.set_tag(key, value)


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    **data
):
    """
    Add breadcrumb to current scope
    
    Args:
        message: Breadcrumb message
        category: Category (e.g., "http", "db", "model")
        level: Severity level
        **data: Additional data
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data
    )


class SentryContextManager:
    """Context manager for Sentry transaction tracking"""
    
    def __init__(
        self,
        operation: str,
        name: str = None,
        **context
    ):
        self.operation = operation
        self.name = name or operation
        self.context = context
        self.transaction = None
    
    def __enter__(self):
        self.transaction = sentry_sdk.start_transaction(
            op=self.operation,
            name=self.name
        )
        
        # Add context
        with sentry_sdk.configure_scope() as scope:
            for key, value in self.context.items():
                scope.set_context(key, value if isinstance(value, dict) else {"value": value})
        
        return self.transaction
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            # Capture exception
            sentry_sdk.capture_exception(exc_val)
        
        if self.transaction:
            self.transaction.finish()


def track_transaction(operation: str, name: str = None, **context):
    """
    Decorator and context manager for tracking transactions
    
    Usage as context manager:
        with track_transaction("model.inference", name="lstm_forecast"):
            result = model.predict()
    
    Args:
        operation: Operation type
        name: Transaction name
        **context: Additional context
    """
    return SentryContextManager(operation, name, **context)
