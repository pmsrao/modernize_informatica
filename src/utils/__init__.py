"""Utility modules."""
try:
    from src.utils.error_categorizer import ErrorCategorizer, ErrorCategory, ErrorSeverity
    from src.utils.error_recovery import ErrorRecovery, retry_on_error, skip_on_error
    
    __all__ = [
        "ErrorCategorizer",
        "ErrorCategory",
        "ErrorSeverity",
        "ErrorRecovery",
        "retry_on_error",
        "skip_on_error"
    ]
except ImportError:
    # Error categorization modules not available
    __all__ = []

