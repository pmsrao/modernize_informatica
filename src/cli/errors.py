"""CLI Error Classes — Custom exceptions for CLI."""
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.utils.exceptions import ModernizationError


class CLIError(ModernizationError):
    """Base exception for CLI errors."""
    pass


class ValidationError(CLIError):
    """Validation error in CLI input."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        """Initialize validation error.
        
        Args:
            message: Error message
            field: Optional field name that failed validation
        """
        super().__init__(message)
        self.field = field


class ConfigurationError(CLIError):
    """Configuration file or setting error."""
    
    def __init__(self, message: str, config_path: Optional[str] = None):
        """Initialize configuration error.
        
        Args:
            message: Error message
            config_path: Optional path to configuration file
        """
        super().__init__(message)
        self.config_path = config_path


class NetworkError(CLIError):
    """Network/API connection error."""
    
    def __init__(self, message: str, url: Optional[str] = None):
        """Initialize network error.
        
        Args:
            message: Error message
            url: Optional URL that failed
        """
        super().__init__(message)
        self.url = url


class ParsingError(CLIError):
    """File parsing error."""
    
    def __init__(self, message: str, file_path: Optional[str] = None):
        """Initialize parsing error.
        
        Args:
            message: Error message
            file_path: Optional path to file that failed parsing
        """
        super().__init__(message)
        self.file_path = file_path


class GraphStoreError(CLIError):
    """Graph store operation error."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        """Initialize graph store error.
        
        Args:
            message: Error message
            operation: Optional operation that failed
        """
        super().__init__(message)
        self.operation = operation

