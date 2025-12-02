"""Error Categorizer - Categorizes and handles errors with recovery mechanisms."""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.utils.logger import get_logger
from src.utils.exceptions import (
    ParsingError, TranslationError, GenerationError, ValidationError, ModernizationError
)

logger = get_logger(__name__)


class ErrorCategory(Enum):
    """Error categories based on Lakebridge and industry best practices."""
    # Analysis errors - Issues during analysis phase
    ANALYSIS_ERROR = "analysis_error"
    ANALYSIS_TIMEOUT = "analysis_timeout"
    ANALYSIS_INVALID_INPUT = "analysis_invalid_input"
    
    # Parsing errors - Issues during XML/input parsing
    PARSING_ERROR = "parsing_error"
    PARSING_SYNTAX_ERROR = "parsing_syntax_error"
    PARSING_MALFORMED_XML = "parsing_malformed_xml"
    PARSING_MISSING_ELEMENT = "parsing_missing_element"
    PARSING_UNSUPPORTED_FORMAT = "parsing_unsupported_format"
    
    # Validation errors - Issues during validation phase
    VALIDATION_ERROR = "validation_error"
    VALIDATION_SCHEMA_ERROR = "validation_schema_error"
    VALIDATION_DATA_QUALITY_ERROR = "validation_data_quality_error"
    VALIDATION_SYNTAX_ERROR = "validation_syntax_error"
    
    # Generation errors - Issues during code generation
    GENERATION_ERROR = "generation_error"
    GENERATION_TEMPLATE_ERROR = "generation_template_error"
    GENERATION_TRANSLATION_ERROR = "generation_translation_error"
    GENERATION_UNSUPPORTED_FEATURE = "generation_unsupported_feature"
    
    # Translation errors - Issues during expression/transformation translation
    TRANSLATION_ERROR = "translation_error"
    TRANSLATION_UNSUPPORTED_FUNCTION = "translation_unsupported_function"
    TRANSLATION_SYNTAX_ERROR = "translation_syntax_error"
    TRANSLATION_TYPE_ERROR = "translation_type_error"
    
    # System errors - Infrastructure/system issues
    SYSTEM_ERROR = "system_error"
    SYSTEM_CONNECTION_ERROR = "system_connection_error"
    SYSTEM_TIMEOUT = "system_timeout"
    SYSTEM_RESOURCE_ERROR = "system_resource_error"
    
    # Configuration errors - Configuration/parameter issues
    CONFIGURATION_ERROR = "configuration_error"
    CONFIGURATION_MISSING = "configuration_missing"
    CONFIGURATION_INVALID = "configuration_invalid"
    
    # Unknown errors - Unclassified errors
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"  # System cannot continue
    HIGH = "high"          # Major functionality affected
    MEDIUM = "medium"      # Some functionality affected
    LOW = "low"            # Minor issue, can continue
    INFO = "info"          # Informational, not an error


class ErrorCategorizer:
    """Categorizes errors and provides recovery mechanisms."""
    
    def __init__(self):
        """Initialize error categorizer."""
        self.error_mappings = self._build_error_mappings()
        self.recovery_strategies = self._build_recovery_strategies()
        logger.info("ErrorCategorizer initialized")
    
    def categorize_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Categorize an error with full context.
        
        Args:
            error: Exception instance
            context: Optional context dictionary
            
        Returns:
            Categorized error dictionary
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Determine category
        category = self._determine_category(error, context)
        
        # Determine severity
        severity = self._determine_severity(category, error, context)
        
        # Get recovery strategy
        recovery = self._get_recovery_strategy(category, error, context)
        
        # Build error details
        error_details = {
            'category': category.value,
            'severity': severity.value,
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {},
            'recovery_strategy': recovery,
            'timestamp': self._get_timestamp(),
            'traceback': self._get_traceback(error)
        }
        
        logger.error(f"Error categorized: {category.value} ({severity.value}) - {error_message}")
        
        return error_details
    
    def _determine_category(self, error: Exception, context: Optional[Dict[str, Any]]) -> ErrorCategory:
        """Determine error category based on error type and context.
        
        Args:
            error: Exception instance
            context: Optional context
            
        Returns:
            ErrorCategory enum
        """
        error_type = type(error)
        
        # Map exception types to categories
        if isinstance(error, ParsingError):
            if 'malformed' in str(error).lower() or 'xml' in str(error).lower():
                return ErrorCategory.PARSING_MALFORMED_XML
            elif 'missing' in str(error).lower():
                return ErrorCategory.PARSING_MISSING_ELEMENT
            elif 'unsupported' in str(error).lower():
                return ErrorCategory.PARSING_UNSUPPORTED_FORMAT
            else:
                return ErrorCategory.PARSING_ERROR
        
        elif isinstance(error, TranslationError):
            if 'function' in str(error).lower() or 'unsupported' in str(error).lower():
                return ErrorCategory.TRANSLATION_UNSUPPORTED_FUNCTION
            elif 'syntax' in str(error).lower():
                return ErrorCategory.TRANSLATION_SYNTAX_ERROR
            elif 'type' in str(error).lower():
                return ErrorCategory.TRANSLATION_TYPE_ERROR
            else:
                return ErrorCategory.TRANSLATION_ERROR
        
        elif isinstance(error, GenerationError):
            if 'template' in str(error).lower():
                return ErrorCategory.GENERATION_TEMPLATE_ERROR
            elif 'translation' in str(error).lower():
                return ErrorCategory.GENERATION_TRANSLATION_ERROR
            elif 'unsupported' in str(error).lower():
                return ErrorCategory.GENERATION_UNSUPPORTED_FEATURE
            else:
                return ErrorCategory.GENERATION_ERROR
        
        elif isinstance(error, ValidationError):
            if 'schema' in str(error).lower():
                return ErrorCategory.VALIDATION_SCHEMA_ERROR
            elif 'quality' in str(error).lower() or 'data' in str(error).lower():
                return ErrorCategory.VALIDATION_DATA_QUALITY_ERROR
            elif 'syntax' in str(error).lower():
                return ErrorCategory.VALIDATION_SYNTAX_ERROR
            else:
                return ErrorCategory.VALIDATION_ERROR
        
        # Check context for additional hints
        if context:
            phase = context.get('phase', '').lower()
            if 'parsing' in phase:
                return ErrorCategory.PARSING_ERROR
            elif 'translation' in phase or 'transformation' in phase:
                return ErrorCategory.TRANSLATION_ERROR
            elif 'generation' in phase:
                return ErrorCategory.GENERATION_ERROR
            elif 'validation' in phase:
                return ErrorCategory.VALIDATION_ERROR
        
        # Check error message for patterns
        error_msg_lower = str(error).lower()
        if 'timeout' in error_msg_lower:
            if 'analysis' in error_msg_lower:
                return ErrorCategory.ANALYSIS_TIMEOUT
            return ErrorCategory.SYSTEM_TIMEOUT
        elif 'connection' in error_msg_lower or 'connect' in error_msg_lower:
            return ErrorCategory.SYSTEM_CONNECTION_ERROR
        elif 'config' in error_msg_lower or 'configuration' in error_msg_lower:
            return ErrorCategory.CONFIGURATION_ERROR
        elif 'resource' in error_msg_lower or 'memory' in error_msg_lower:
            return ErrorCategory.SYSTEM_RESOURCE_ERROR
        
        return ErrorCategory.UNKNOWN_ERROR
    
    def _determine_severity(self, category: ErrorCategory, error: Exception, context: Optional[Dict[str, Any]]) -> ErrorSeverity:
        """Determine error severity.
        
        Args:
            category: Error category
            error: Exception instance
            context: Optional context
            
        Returns:
            ErrorSeverity enum
        """
        # Critical errors
        if category in [
            ErrorCategory.SYSTEM_ERROR,
            ErrorCategory.SYSTEM_CONNECTION_ERROR,
            ErrorCategory.SYSTEM_RESOURCE_ERROR
        ]:
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if category in [
            ErrorCategory.PARSING_MALFORMED_XML,
            ErrorCategory.GENERATION_ERROR,
            ErrorCategory.TRANSLATION_ERROR,
            ErrorCategory.VALIDATION_SCHEMA_ERROR
        ]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category in [
            ErrorCategory.PARSING_ERROR,
            ErrorCategory.VALIDATION_ERROR,
            ErrorCategory.GENERATION_UNSUPPORTED_FEATURE,
            ErrorCategory.TRANSLATION_UNSUPPORTED_FUNCTION
        ]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors
        if category in [
            ErrorCategory.PARSING_MISSING_ELEMENT,
            ErrorCategory.VALIDATION_DATA_QUALITY_ERROR
        ]:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _get_recovery_strategy(self, category: ErrorCategory, error: Exception, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get recovery strategy for error category.
        
        Args:
            category: Error category
            error: Exception instance
            context: Optional context
            
        Returns:
            Recovery strategy dictionary
        """
        strategy = self.recovery_strategies.get(category, {})
        
        # Add context-specific recovery suggestions
        suggestions = strategy.get('suggestions', [])
        
        # Add specific suggestions based on error message
        error_msg = str(error).lower()
        if 'timeout' in error_msg:
            suggestions.append("Consider increasing timeout settings or optimizing query performance")
        if 'memory' in error_msg or 'resource' in error_msg:
            suggestions.append("Consider processing in smaller batches or increasing available resources")
        if 'connection' in error_msg:
            suggestions.append("Check network connectivity and service availability")
        
        return {
            'strategy': strategy.get('strategy', 'manual_review'),
            'can_retry': strategy.get('can_retry', False),
            'can_skip': strategy.get('can_skip', False),
            'suggestions': suggestions,
            'auto_recovery': strategy.get('auto_recovery', False)
        }
    
    def _build_error_mappings(self) -> Dict[str, ErrorCategory]:
        """Build error type to category mappings.
        
        Returns:
            Dictionary mapping error types to categories
        """
        return {
            'ParsingError': ErrorCategory.PARSING_ERROR,
            'TranslationError': ErrorCategory.TRANSLATION_ERROR,
            'GenerationError': ErrorCategory.GENERATION_ERROR,
            'ValidationError': ErrorCategory.VALIDATION_ERROR,
            'ModernizationError': ErrorCategory.SYSTEM_ERROR,
            'ConnectionError': ErrorCategory.SYSTEM_CONNECTION_ERROR,
            'TimeoutError': ErrorCategory.SYSTEM_TIMEOUT,
            'ValueError': ErrorCategory.VALIDATION_ERROR,
            'TypeError': ErrorCategory.TRANSLATION_TYPE_ERROR,
            'KeyError': ErrorCategory.PARSING_MISSING_ELEMENT,
            'FileNotFoundError': ErrorCategory.CONFIGURATION_ERROR
        }
    
    def _build_recovery_strategies(self) -> Dict[ErrorCategory, Dict[str, Any]]:
        """Build recovery strategies for each error category.
        
        Returns:
            Dictionary of recovery strategies
        """
        return {
            ErrorCategory.PARSING_MALFORMED_XML: {
                'strategy': 'fix_xml',
                'can_retry': False,
                'can_skip': True,
                'suggestions': [
                    'Validate XML file format',
                    'Check for unclosed tags or invalid characters',
                    'Use XML validator tool'
                ],
                'auto_recovery': False
            },
            ErrorCategory.PARSING_MISSING_ELEMENT: {
                'strategy': 'use_defaults',
                'can_retry': False,
                'can_skip': True,
                'suggestions': [
                    'Check if element is optional',
                    'Use default values if available',
                    'Review mapping requirements'
                ],
                'auto_recovery': True
            },
            ErrorCategory.TRANSLATION_UNSUPPORTED_FUNCTION: {
                'strategy': 'manual_translation',
                'can_retry': False,
                'can_skip': True,
                'suggestions': [
                    'Review function documentation',
                    'Find equivalent function in target platform',
                    'Implement custom translation logic'
                ],
                'auto_recovery': False
            },
            ErrorCategory.GENERATION_UNSUPPORTED_FEATURE: {
                'strategy': 'manual_implementation',
                'can_retry': False,
                'can_skip': True,
                'suggestions': [
                    'Review feature requirements',
                    'Implement manually in target code',
                    'Consider alternative approach'
                ],
                'auto_recovery': False
            },
            ErrorCategory.SYSTEM_TIMEOUT: {
                'strategy': 'retry_with_backoff',
                'can_retry': True,
                'can_skip': False,
                'suggestions': [
                    'Increase timeout settings',
                    'Optimize query performance',
                    'Process in smaller batches'
                ],
                'auto_recovery': True
            },
            ErrorCategory.SYSTEM_CONNECTION_ERROR: {
                'strategy': 'retry_with_backoff',
                'can_retry': True,
                'can_skip': False,
                'suggestions': [
                    'Check network connectivity',
                    'Verify service is running',
                    'Check firewall settings'
                ],
                'auto_recovery': True
            },
            ErrorCategory.VALIDATION_DATA_QUALITY_ERROR: {
                'strategy': 'fix_data',
                'can_retry': False,
                'can_skip': True,
                'suggestions': [
                    'Review data quality rules',
                    'Clean or transform data',
                    'Adjust quality thresholds'
                ],
                'auto_recovery': False
            }
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp.
        
        Returns:
            ISO format timestamp string
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_traceback(self, error: Exception) -> List[str]:
        """Get traceback as list of strings.
        
        Args:
            error: Exception instance
            
        Returns:
            List of traceback lines
        """
        try:
            return traceback.format_exception(type(error), error, error.__traceback__)
        except Exception:
            return [str(error)]
    
    def format_error_report(self, error_details: Dict[str, Any]) -> str:
        """Format error details as human-readable report.
        
        Args:
            error_details: Categorized error dictionary
            
        Returns:
            Formatted error report string
        """
        report = []
        report.append("=" * 60)
        report.append("ERROR REPORT")
        report.append("=" * 60)
        report.append(f"Category: {error_details['category']}")
        report.append(f"Severity: {error_details['severity']}")
        report.append(f"Error Type: {error_details['error_type']}")
        report.append(f"Message: {error_details['error_message']}")
        report.append("")
        report.append("Recovery Strategy:")
        recovery = error_details['recovery_strategy']
        report.append(f"  Strategy: {recovery['strategy']}")
        report.append(f"  Can Retry: {recovery['can_retry']}")
        report.append(f"  Can Skip: {recovery['can_skip']}")
        report.append(f"  Auto Recovery: {recovery['auto_recovery']}")
        if recovery['suggestions']:
            report.append("  Suggestions:")
            for suggestion in recovery['suggestions']:
                report.append(f"    - {suggestion}")
        report.append("")
        if error_details.get('traceback'):
            report.append("Traceback:")
            report.extend(error_details['traceback'])
        
        return "\n".join(report)
    
    def get_error_statistics(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics from a list of errors.
        
        Args:
            errors: List of categorized error dictionaries
            
        Returns:
            Error statistics dictionary
        """
        if not errors:
            return {
                'total': 0,
                'by_category': {},
                'by_severity': {},
                'recoverable': 0,
                'critical': 0
            }
        
        stats = {
            'total': len(errors),
            'by_category': {},
            'by_severity': {},
            'recoverable': 0,
            'critical': 0
        }
        
        for error in errors:
            category = error.get('category', 'unknown')
            severity = error.get('severity', 'unknown')
            recovery = error.get('recovery_strategy', {})
            
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
            
            if recovery.get('can_retry') or recovery.get('can_skip'):
                stats['recoverable'] += 1
            
            if severity == 'critical':
                stats['critical'] += 1
        
        return stats

