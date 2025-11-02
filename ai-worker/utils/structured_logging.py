"""
Structured Logging with Context
JSON logging with request_id and tenant_id tracking
"""

import logging
import json
from datetime import datetime
from contextvars import ContextVar
from typing import Dict, Any, Optional
import traceback
import sys

# Context variables for request tracing
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
tenant_id_var: ContextVar[str] = ContextVar('tenant_id', default='')
user_id_var: ContextVar[str] = ContextVar('user_id', default='')


class StructuredLogger:
    """Structured JSON logger with context tracking"""
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Add structured handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _build_log(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """Build structured log entry"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": message,
            "service": "ai-worker",
            "request_id": request_id_var.get() or None,
            "tenant_id": tenant_id_var.get() or None,
            "user_id": user_id_var.get() or None,
        }
        
        # Add custom fields
        if kwargs:
            log_entry["context"] = kwargs
        
        # Remove None values
        return {k: v for k, v in log_entry.items() if v is not None}
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        log_entry = self._build_log("DEBUG", message, **kwargs)
        self.logger.debug(json.dumps(log_entry))
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        log_entry = self._build_log("INFO", message, **kwargs)
        self.logger.info(json.dumps(log_entry))
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        log_entry = self._build_log("WARNING", message, **kwargs)
        self.logger.warning(json.dumps(log_entry))
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception"""
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)
            kwargs["stack_trace"] = traceback.format_exc()
        
        log_entry = self._build_log("ERROR", message, **kwargs)
        self.logger.error(json.dumps(log_entry))
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log critical message"""
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)
            kwargs["stack_trace"] = traceback.format_exc()
        
        log_entry = self._build_log("CRITICAL", message, **kwargs)
        self.logger.critical(json.dumps(log_entry))


class StructuredFormatter(logging.Formatter):
    """Formatter that passes through structured JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        # If message is already JSON, return as-is
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except (json.JSONDecodeError, ValueError):
            # Not JSON, wrap it
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "message": record.getMessage(),
                "service": "ai-worker",
                "logger": record.name,
            }
            
            # Add exception info if present
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            
            return json.dumps(log_entry)


def set_request_context(request_id: str, tenant_id: str = "", user_id: str = ""):
    """Set context variables for current request"""
    request_id_var.set(request_id)
    if tenant_id:
        tenant_id_var.set(tenant_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context():
    """Clear context variables"""
    request_id_var.set("")
    tenant_id_var.set("")
    user_id_var.set("")


def get_logger(name: str) -> StructuredLogger:
    """Get or create structured logger"""
    return StructuredLogger(name)


# Performance logging helper
class PerformanceLogger:
    """Track and log performance metrics"""
    
    def __init__(self, logger: StructuredLogger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.info(f"{self.operation} started")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (datetime.utcnow() - self.start_time).total_seconds() * 1000
        
        if exc_type:
            self.logger.error(
                f"{self.operation} failed",
                error=exc_val,
                duration_ms=duration_ms
            )
        else:
            self.logger.info(
                f"{self.operation} completed",
                duration_ms=duration_ms
            )


# Configure root logger to use structured format
def configure_root_logger(level: str = "INFO"):
    """Configure root logger with structured format"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
