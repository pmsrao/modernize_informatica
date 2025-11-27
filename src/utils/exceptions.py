"""Custom exception hierarchy for modernization errors."""


class ModernizationError(Exception):
    """Base exception for all modernization errors."""
    
    def __init__(self, message: str, error_code: str = None):
        """Initialize modernization error.
        
        Args:
            message: Error message
            error_code: Optional error code for categorization
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class ParsingError(ModernizationError):
    """Raised when XML parsing fails."""
    
    def __init__(self, message: str, file_path: str = None, line_number: int = None):
        """Initialize parsing error.
        
        Args:
            message: Error message
            file_path: Path to file that failed to parse
            line_number: Line number where error occurred
        """
        super().__init__(message, error_code="PARSING_ERROR")
        self.file_path = file_path
        self.line_number = line_number


class TranslationError(ModernizationError):
    """Raised when expression translation fails."""
    
    def __init__(self, message: str, expression: str = None):
        """Initialize translation error.
        
        Args:
            message: Error message
            expression: Expression that failed to translate
        """
        super().__init__(message, error_code="TRANSLATION_ERROR")
        self.expression = expression


class GenerationError(ModernizationError):
    """Raised when code generation fails."""
    
    def __init__(self, message: str, generator_type: str = None):
        """Initialize generation error.
        
        Args:
            message: Error message
            generator_type: Type of generator that failed
        """
        super().__init__(message, error_code="GENERATION_ERROR")
        self.generator_type = generator_type


class ValidationError(ModernizationError):
    """Raised when validation fails."""
    
    def __init__(self, message: str, field: str = None):
        """Initialize validation error.
        
        Args:
            message: Error message
            field: Field that failed validation
        """
        super().__init__(message, error_code="VALIDATION_ERROR")
        self.field = field


class UnsupportedTransformationError(ModernizationError):
    """Raised when unsupported transformation is encountered."""
    
    def __init__(self, transformation_type: str):
        """Initialize unsupported transformation error.
        
        Args:
            transformation_type: Type of transformation that is unsupported
        """
        message = f"Unsupported transformation type: {transformation_type}"
        super().__init__(message, error_code="UNSUPPORTED_TRANSFORMATION")
        self.transformation_type = transformation_type


class ConfigurationError(ModernizationError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: str = None):
        """Initialize configuration error.
        
        Args:
            message: Error message
            config_key: Configuration key that is missing or invalid
        """
        super().__init__(message, error_code="CONFIGURATION_ERROR")
        self.config_key = config_key

