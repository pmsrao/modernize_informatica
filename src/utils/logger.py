"""Structured logging infrastructure for the modernization accelerator."""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
from config import settings


class StructuredLogger:
    """Structured logger with JSON and text formatting support."""
    
    def __init__(self, name: str, log_file: Optional[str] = None):
        """Initialize structured logger.
        
        Args:
            name: Logger name (typically module name)
            log_file: Optional file path for file logging
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        if settings.log_format == "json":
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
        self.logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file or settings.log_file:
            log_path = Path(log_file or settings.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(JSONFormatter())
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message.
        
        Args:
            message: Error message
            error: Optional exception object
            **kwargs: Additional context
        """
        log_data = kwargs.copy()
        if error:
            log_data['error'] = str(error)
            log_data['error_type'] = type(error).__name__
            if hasattr(error, '__traceback__'):
                import traceback
                log_data['traceback'] = traceback.format_exc()
        
        self._log(logging.ERROR, message, **log_data)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal log method."""
        if settings.log_format == "json":
            log_data = self._format_json_message(message, **kwargs)
            self.logger.log(level, json.dumps(log_data))
        else:
            # Text format - append kwargs as context
            context = f" | {kwargs}" if kwargs else ""
            self.logger.log(level, f"{message}{context}")
    
    def _format_json_message(self, message: str, **kwargs) -> Dict[str, Any]:
        """Format message as JSON structure."""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            **kwargs
        }


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            import traceback
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


# Module-level logger instance
def get_logger(name: str = "modernizer") -> StructuredLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)


# Default logger
logger = get_logger("modernizer")


def get_enhanced_logger(name: str = "modernizer") -> StructuredLogger:
    """Get enhanced logger with error categorization support.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        StructuredLogger instance with error categorization
    """
    return StructuredLogger(name)
