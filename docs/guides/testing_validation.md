# Testing and Validation Guide

## Overview

This guide covers testing and validation capabilities in the Informatica Modernization Accelerator, including test data validation, automated test generation, and integration testing.

---

## Test Data Validation

### TestDataValidator

The `TestDataValidator` provides comprehensive validation capabilities for testing generated code.

#### Validate Transformation Logic

Validate transformation logic against test data:

```python
from src.validation.test_data_validator import TestDataValidator

validator = TestDataValidator()

# Validate transformation logic
result = validator.validate_transformation_logic(
    canonical_model=canonical_model,
    test_data=input_test_data,
    expected_output=expected_output,
    code_type="pyspark"
)

# Check results
if result['valid']:
    print(f"Validation passed: {result['match_percentage']:.1f}% match")
else:
    print(f"Validation failed: {result['failed_tests']} tests failed")
    for error in result['errors']:
        print(f"  - {error['message']}")
```

#### Validate Schema Compatibility

Check schema compatibility between source and target:

```python
schema_result = validator.validate_schema_compatibility(
    source_schema=source_schema,
    target_schema=target_schema,
    canonical_model=canonical_model
)

if schema_result['valid']:
    print("Schema compatibility validated")
else:
    print("Schema issues found:")
    for error in schema_result['errors']:
        print(f"  - {error['message']}")
```

#### Validate Data Quality

Apply data quality rules:

```python
quality_result = validator.validate_data_quality(
    test_data=test_data,
    quality_rules=[
        {'type': 'not_null', 'field': 'customer_id'},
        {'type': 'unique', 'field': 'order_id'},
        {'type': 'range', 'field': 'amount', 'value': {'min': 0, 'max': 10000}}
    ]
)

print(f"Quality metrics: {quality_result['quality_metrics']}")
```

### Quality Rules

Supported quality rules:

- **not_null** - Ensures fields are not null
- **unique** - Ensures field values are unique
- **range** - Validates values are within specified range

---

## Automated Test Generation

### TestGenerator

The `TestGenerator` automatically generates pytest-compatible tests for generated code.

#### Generate PySpark Tests

```python
from src.generators.test_generator import TestGenerator

test_generator = TestGenerator()

# Generate PySpark tests
pyspark_tests = test_generator.generate_pyspark_tests(
    canonical_model=canonical_model,
    generated_code=generated_pyspark_code,
    test_data=optional_test_data  # Optional - will be generated if not provided
)

# Save to file
with open('test_mapping.py', 'w') as f:
    f.write(pyspark_tests)
```

#### Generate SQL Tests

```python
sql_tests = test_generator.generate_sql_tests(
    canonical_model=canonical_model,
    generated_sql=generated_sql_code,
    test_data=optional_test_data
)

with open('test_mapping_sql.py', 'w') as f:
    f.write(sql_tests)
```

#### Generate Integration Tests

```python
integration_tests = test_generator.generate_integration_tests(
    workflow_name="WF_Main",
    workflow_structure=workflow_structure,
    test_config={'max_execution_time': 300}
)

with open('test_workflow_integration.py', 'w') as f:
    f.write(integration_tests)
```

### Generated Test Structure

Generated tests include:

- **Schema validation** - Validates output schema matches expected schema
- **Transformation logic** - Tests transformation logic against test data
- **Null handling** - Tests null value handling
- **Data quality** - Tests data quality rules

Example test structure:

```python
class TestMappingName:
    """Test suite for mapping."""
    
    @pytest.fixture(scope="class")
    def spark(self):
        """Create Spark session for testing."""
        return SparkSession.builder...
    
    def test_schema_validation(self, spark, test_data):
        """Test that output schema matches expected schema."""
        ...
    
    def test_transformation_logic(self, spark, test_data):
        """Test transformation logic against test data."""
        ...
    
    def test_null_handling(self, spark):
        """Test null value handling."""
        ...
    
    def test_data_quality(self, spark, test_data):
        """Test data quality rules."""
        ...
```

---

## Integration Testing Framework

### IntegrationTestFramework

Run comprehensive integration test suites:

```python
from src.testing.integration_test_framework import IntegrationTestFramework

framework = IntegrationTestFramework(test_config={
    'report_format': 'html'  # or 'json'
})

test_suite = {
    'name': 'mapping_tests',
    'test_cases': [
        {
            'name': 'test_schema_validation',
            'type': 'validation',
            'canonical_model': canonical_model,
            'test_data': test_data,
            'expected_output': expected_output
        },
        {
            'name': 'test_performance',
            'type': 'performance',
            'code': generated_code,
            'max_execution_time': 300
        }
    ]
}

results = framework.run_test_suite(test_suite)

# Generate report
report = framework.generate_test_report(
    results=results,
    output_path=Path('test_report.html')
)
```

### Test Types

Supported test types:

- **unit** - Individual function/method tests
- **integration** - Multi-component tests
- **performance** - Execution time and throughput tests
- **validation** - Data validation tests

---

## API Usage

### Generate Tests

```bash
curl -X POST http://localhost:8000/api/v1/testing/generate-tests \
  -H "Content-Type: application/json" \
  -d '{
    "mapping_name": "M_CustomerLoad",
    "code_type": "pyspark",
    "generated_code": "...",
    "canonical_model": {...}
  }'
```

### Validate Test Data

```bash
curl -X POST http://localhost:8000/api/v1/testing/validate-test-data \
  -H "Content-Type: application/json" \
  -d '{
    "canonical_model": {...},
    "test_data": [...],
    "expected_output": [...]
  }'
```

### Run Integration Tests

```bash
curl -X POST http://localhost:8000/api/v1/testing/run-integration-tests \
  -H "Content-Type: application/json" \
  -d '{
    "test_suite": {...},
    "test_config": {...}
  }'
```

---

## Best Practices

1. **Generate Tests Early** - Generate tests alongside code generation
2. **Use Test Data Validation** - Validate test data before running tests
3. **Run Integration Tests** - Use integration tests for end-to-end validation
4. **Review Test Reports** - Regularly review test reports for quality metrics
5. **Customize Quality Rules** - Define custom quality rules for your use case

---

## Related Documentation

- [Testing Guide](testing/TESTING.md) - Main testing documentation
- [Test Flow Guide](testing/test_flow_guide.md) - Comprehensive testing instructions
- [Code Generators](modules/code_generators.md) - Code generation documentation

---

*Last Updated: December 2, 2025*

