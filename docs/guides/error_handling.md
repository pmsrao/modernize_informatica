# Error Handling Guide

## Overview

The Informatica Modernization Accelerator includes comprehensive error categorization and recovery mechanisms inspired by industry best practices and Lakebridge's error handling approach.

---

## Error Categorization

### Error Categories

Errors are categorized into the following types:

#### Analysis Errors
- `ANALYSIS_ERROR` - General analysis errors
- `ANALYSIS_TIMEOUT` - Analysis operation timeout
- `ANALYSIS_INVALID_INPUT` - Invalid input during analysis

#### Parsing Errors
- `PARSING_ERROR` - General parsing errors
- `PARSING_SYNTAX_ERROR` - XML syntax errors
- `PARSING_MALFORMED_XML` - Malformed XML structure
- `PARSING_MISSING_ELEMENT` - Missing required XML elements
- `PARSING_UNSUPPORTED_FORMAT` - Unsupported file format

#### Validation Errors
- `VALIDATION_ERROR` - General validation errors
- `VALIDATION_SCHEMA_ERROR` - Schema validation failures
- `VALIDATION_DATA_QUALITY_ERROR` - Data quality issues
- `VALIDATION_SYNTAX_ERROR` - Syntax validation errors

#### Generation Errors
- `GENERATION_ERROR` - General code generation errors
- `GENERATION_TEMPLATE_ERROR` - Template rendering errors
- `GENERATION_TRANSLATION_ERROR` - Translation errors during generation
- `GENERATION_UNSUPPORTED_FEATURE` - Unsupported features

#### Translation Errors
- `TRANSLATION_ERROR` - General translation errors
- `TRANSLATION_UNSUPPORTED_FUNCTION` - Unsupported Informatica functions
- `TRANSLATION_SYNTAX_ERROR` - Syntax errors in expressions
- `TRANSLATION_TYPE_ERROR` - Type mismatch errors

#### System Errors
- `SYSTEM_ERROR` - General system errors
- `SYSTEM_CONNECTION_ERROR` - Connection failures
- `SYSTEM_TIMEOUT` - Operation timeouts
- `SYSTEM_RESOURCE_ERROR` - Resource exhaustion

#### Configuration Errors
- `CONFIGURATION_ERROR` - General configuration errors
- `CONFIGURATION_MISSING` - Missing configuration
- `CONFIGURATION_INVALID` - Invalid configuration values

### Error Severity Levels

- **CRITICAL** - System cannot continue
- **HIGH** - Major functionality affected
- **MEDIUM** - Some functionality affected
- **LOW** - Minor issue, can continue
- **INFO** - Informational, not an error

---

## Using Error Categorization

### Basic Usage

```python
from utils.error_categorizer import ErrorCategorizer

categorizer = ErrorCategorizer()

try:
    # Your code here
    result = some_operation()
except Exception as e:
    error_details = categorizer.categorize_error(e, context={'phase': 'parsing'})
    
    print(f"Category: {error_details['category']}")
    print(f"Severity: {error_details['severity']}")
    print(f"Recovery Strategy: {error_details['recovery_strategy']['strategy']}")
    
    # Get recovery suggestions
    for suggestion in error_details['recovery_strategy']['suggestions']:
        print(f"  - {suggestion}")
```

### Error Reporting

```python
# Format error as report
report = categorizer.format_error_report(error_details)
print(report)

# Get error statistics
errors = [error_details1, error_details2, ...]
stats = categorizer.get_error_statistics(errors)
print(f"Total errors: {stats['total']}")
print(f"Critical errors: {stats['critical']}")
print(f"Recoverable errors: {stats['recoverable']}")
```

---

## Error Recovery

### Automatic Retry

```python
from utils.error_recovery import ErrorRecovery, retry_on_error

recovery = ErrorRecovery()

# Retry with backoff
result = recovery.retry_with_backoff(
    func=some_function,
    arg1=value1,
    arg2=value2
)
```

### Using Decorators

```python
from utils.error_recovery import retry_on_error, skip_on_error

@retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
def risky_operation():
    # This will automatically retry on error
    return some_operation()

@skip_on_error(default_value=None)
def optional_operation():
    # This will return None if error occurs
    return some_operation()
```

### Skip on Error

```python
# Skip operation on error, return default value
result = recovery.skip_on_error(
    func=optional_function,
    default_value={},
    arg1=value1
)
```

### Use Defaults on Error

```python
# Use defaults for missing elements
result = recovery.use_defaults_on_error(
    func=parse_with_defaults,
    defaults={'field1': 'default1', 'field2': 'default2'},
    data=data
)
```

---

## Enhanced Error Logging

### Using Enhanced Logger

The logger automatically categorizes errors when logging:

```python
from utils.logger import get_logger

logger = get_logger(__name__)

try:
    result = some_operation()
except Exception as e:
    # Logger automatically categorizes the error
    logger.error("Operation failed", error=e, context={'phase': 'generation'})
```

### Error Logging Output

When an error is logged, it includes:
- Error category
- Error severity
- Recovery strategy
- Recovery suggestions
- Full traceback

Example log output:
```
ERROR | Category: parsing_malformed_xml | Severity: high | Recovery: fix_xml
Recovery suggestions:
  - Validate XML file format
  - Check for unclosed tags or invalid characters
  - Use XML validator tool
```

---

## Recovery Strategies

### Available Strategies

1. **retry_with_backoff** - Retry operation with exponential backoff
2. **fix_xml** - Fix XML format issues
3. **use_defaults** - Use default values for missing elements
4. **manual_translation** - Requires manual translation
5. **manual_implementation** - Requires manual implementation
6. **fix_data** - Fix data quality issues

### Strategy Properties

Each strategy includes:
- `can_retry` - Whether operation can be retried
- `can_skip` - Whether operation can be skipped
- `auto_recovery` - Whether automatic recovery is possible
- `suggestions` - List of recovery suggestions

---

## Best Practices

### 1. Categorize Errors Early

```python
try:
    result = operation()
except Exception as e:
    error_details = categorizer.categorize_error(e, context)
    # Handle based on category
```

### 2. Use Appropriate Recovery Strategy

```python
recovery = error_details['recovery_strategy']
if recovery['can_retry']:
    # Retry operation
elif recovery['can_skip']:
    # Skip operation
else:
    # Manual review required
```

### 3. Log Errors with Context

```python
logger.error(
    "Operation failed",
    error=error,
    context={
        'phase': 'parsing',
        'file': file_path,
        'mapping': mapping_name
    }
)
```

### 4. Collect Error Statistics

```python
errors = []
try:
    process_files()
except Exception as e:
    errors.append(categorizer.categorize_error(e))

stats = categorizer.get_error_statistics(errors)
# Review statistics to identify patterns
```

---

## Integration Examples

### In Parsers

```python
from utils.error_categorizer import ErrorCategorizer
from utils.error_recovery import skip_on_error

categorizer = ErrorCategorizer()

@skip_on_error(default_value=None)
def parse_mapping(xml_file):
    try:
        return parse_xml(xml_file)
    except Exception as e:
        error_details = categorizer.categorize_error(
            e,
            context={'phase': 'parsing', 'file': xml_file}
        )
        logger.error("Parsing failed", error=e, context=error_details)
        raise
```

### In Code Generators

```python
from utils.error_recovery import retry_on_error

@retry_on_error(max_retries=3)
def generate_code(canonical_model):
    try:
        return generator.generate(canonical_model)
    except Exception as e:
        error_details = categorizer.categorize_error(
            e,
            context={'phase': 'generation', 'mapping': canonical_model.get('mapping_name')}
        )
        if error_details['recovery_strategy']['can_skip']:
            logger.warning("Skipping code generation", error=e)
            return None
        raise
```

---

## Related Documentation

- [Migration Guide](migration_guide.md) - Migration best practices
- [Testing and Validation](testing_validation.md) - Testing error scenarios
- [API Documentation](api/api_frontend.md) - API error handling

---

*Last Updated: December 2, 2025*

