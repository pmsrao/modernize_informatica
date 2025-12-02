"""Error Recovery - Automatic error recovery mechanisms."""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import time
from functools import wraps

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.utils.logger import get_logger
from src.utils.error_categorizer import ErrorCategorizer, ErrorCategory, ErrorSeverity

logger = get_logger(__name__)


class ErrorRecovery:
    """Provides automatic error recovery mechanisms."""
    
    def __init__(self, categorizer: Optional[ErrorCategorizer] = None):
        """Initialize error recovery.
        
        Args:
            categorizer: Optional ErrorCategorizer instance
        """
        self.categorizer = categorizer or ErrorCategorizer()
        self.max_retries = 3
        self.retry_delays = [1, 2, 5]  # Seconds between retries
        logger.info("ErrorRecovery initialized")
    
    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """Retry a function with exponential backoff.
        
        Args:
            func: Function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_details = self.categorizer.categorize_error(e, {'phase': 'retry', 'attempt': attempt + 1})
                recovery = error_details['recovery_strategy']
                
                if not recovery.get('can_retry', False):
                    logger.warning(f"Error not retryable: {error_details['category']}")
                    raise e
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    logger.info(f"Retry attempt {attempt + 1}/{self.max_retries} after {delay}s delay")
                    time.sleep(delay)
                else:
                    logger.error(f"All retry attempts exhausted for {error_details['category']}")
        
        raise last_error
    
    def skip_on_error(self, func: Callable, default_value: Any = None, *args, **kwargs) -> Any:
        """Execute function and skip on error, returning default value.
        
        Args:
            func: Function to execute
            default_value: Value to return on error
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or default value
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_details = self.categorizer.categorize_error(e, {'phase': 'skip_on_error'})
            recovery = error_details['recovery_strategy']
            
            if recovery.get('can_skip', False):
                logger.warning(f"Skipping error: {error_details['category']} - {error_details['error_message']}")
                return default_value
            else:
                logger.error(f"Error cannot be skipped: {error_details['category']}")
                raise e
    
    def use_defaults_on_error(self, func: Callable, defaults: Dict[str, Any], *args, **kwargs) -> Any:
        """Execute function and use defaults for missing elements.
        
        Args:
            func: Function to execute
            defaults: Dictionary of default values
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result with defaults applied
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_details = self.categorizer.categorize_error(e, {'phase': 'use_defaults'})
            
            if error_details['category'] == ErrorCategory.PARSING_MISSING_ELEMENT.value:
                logger.info(f"Using defaults for missing element: {error_details['error_message']}")
                return defaults
            else:
                raise e
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle an error with automatic recovery if possible.
        
        Args:
            error: Exception instance
            context: Optional context dictionary
            
        Returns:
            Error handling result dictionary
        """
        error_details = self.categorizer.categorize_error(error, context)
        recovery = error_details['recovery_strategy']
        
        result = {
            'error_details': error_details,
            'recovered': False,
            'recovery_action': None,
            'result': None
        }
        
        # Attempt auto-recovery if available
        if recovery.get('auto_recovery', False):
            try:
                if recovery['strategy'] == 'retry_with_backoff':
                    # This would need the original function to retry
                    result['recovery_action'] = 'retry_scheduled'
                elif recovery['strategy'] == 'use_defaults':
                    result['recovery_action'] = 'defaults_applied'
                    result['recovered'] = True
                else:
                    result['recovery_action'] = 'manual_review_required'
            except Exception as recovery_error:
                logger.error(f"Auto-recovery failed: {recovery_error}")
                result['recovery_action'] = 'recovery_failed'
        else:
            result['recovery_action'] = 'manual_review_required'
        
        return result


def retry_on_error(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for automatic retry on error.
    
    Args:
        max_retries: Maximum number of retries
        delay: Initial delay in seconds
        backoff: Backoff multiplier
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            recovery = ErrorRecovery()
            recovery.max_retries = max_retries
            recovery.retry_delays = [delay * (backoff ** i) for i in range(max_retries)]
            return recovery.retry_with_backoff(func, *args, **kwargs)
        return wrapper
    return decorator


def skip_on_error(default_value: Any = None):
    """Decorator to skip errors and return default value.
    
    Args:
        default_value: Value to return on error
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            recovery = ErrorRecovery()
            return recovery.skip_on_error(func, default_value, *args, **kwargs)
        return wrapper
    return decorator

