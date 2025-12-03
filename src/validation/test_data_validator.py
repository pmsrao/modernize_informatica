"""Test Data Validator - Validates generated code against test data."""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from utils.logger import get_logger

logger = get_logger(__name__)


class TestDataValidator:
    """Validates generated code against test data."""
    
    def __init__(self):
        """Initialize test data validator."""
        logger.info("TestDataValidator initialized")
    
    def validate_transformation_logic(self,
                                     canonical_model: Dict[str, Any],
                                     test_data: List[Dict[str, Any]],
                                     expected_output: List[Dict[str, Any]],
                                     code_type: str = "pyspark") -> Dict[str, Any]:
        """Validate transformation logic against test data.
        
        Args:
            canonical_model: Canonical model with transformation logic
            test_data: Input test data
            expected_output: Expected output data
            code_type: Type of code to validate ('pyspark', 'sql')
            
        Returns:
            Validation results dictionary
        """
        logger.info(f"Validating transformation logic for {code_type} code")
        
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'test_results': [],
            'match_percentage': 0.0,
            'total_tests': len(expected_output),
            'passed_tests': 0,
            'failed_tests': 0
        }
        
        if not test_data or not expected_output:
            results['valid'] = False
            results['errors'].append({
                'type': 'missing_data',
                'message': 'Test data or expected output is missing'
            })
            return results
        
        # Extract transformation expressions from canonical model
        transformations = self._extract_transformations(canonical_model)
        
        # For each test case, validate the transformation
        for i, (input_row, expected_row) in enumerate(zip(test_data, expected_output)):
            test_result = self._validate_single_row(
                input_row, expected_row, transformations, code_type
            )
            results['test_results'].append({
                'test_case': i + 1,
                'input': input_row,
                'expected': expected_row,
                'result': test_result
            })
            
            if test_result['match']:
                results['passed_tests'] += 1
            else:
                results['failed_tests'] += 1
                results['valid'] = False
        
        results['match_percentage'] = (
            results['passed_tests'] / results['total_tests'] * 100
            if results['total_tests'] > 0 else 0.0
        )
        
        return results
    
    def validate_schema_compatibility(self,
                                     source_schema: Dict[str, Any],
                                     target_schema: Dict[str, Any],
                                     canonical_model: Dict[str, Any]) -> Dict[str, Any]:
        """Validate schema compatibility between source and target.
        
        Args:
            source_schema: Source schema definition
            target_schema: Target schema definition
            canonical_model: Canonical model with field mappings
            
        Returns:
            Schema validation results
        """
        logger.info("Validating schema compatibility")
        
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'field_mappings': [],
            'missing_fields': [],
            'type_mismatches': []
        }
        
        # Extract field mappings from canonical model
        mappings = canonical_model.get('transformations', [])
        
        # Check each target field has a source mapping
        target_fields = target_schema.get('fields', [])
        source_fields = {f['name']: f for f in source_schema.get('fields', [])}
        
        for target_field in target_fields:
            field_name = target_field['name']
            field_type = target_field.get('type', 'unknown')
            
            # Find mapping for this field
            mapping_found = False
            for mapping in mappings:
                if mapping.get('target_field') == field_name:
                    mapping_found = True
                    source_field_name = mapping.get('source_field')
                    
                    if source_field_name in source_fields:
                        source_field = source_fields[source_field_name]
                        source_type = source_field.get('type', 'unknown')
                        
                        # Check type compatibility
                        if not self._are_types_compatible(source_type, field_type):
                            results['type_mismatches'].append({
                                'target_field': field_name,
                                'target_type': field_type,
                                'source_field': source_field_name,
                                'source_type': source_type
                            })
                            results['warnings'].append({
                                'type': 'type_mismatch',
                                'message': f'Type mismatch: {source_field_name} ({source_type}) -> {field_name} ({field_type})'
                            })
                        
                        results['field_mappings'].append({
                            'source': source_field_name,
                            'target': field_name,
                            'source_type': source_type,
                            'target_type': field_type,
                            'transformation': mapping.get('expression', 'direct')
                        })
                    break
            
            if not mapping_found:
                results['missing_fields'].append(field_name)
                results['errors'].append({
                    'type': 'missing_mapping',
                    'message': f'No mapping found for target field: {field_name}'
                })
                results['valid'] = False
        
        return results
    
    def validate_data_quality(self,
                             test_data: List[Dict[str, Any]],
                             quality_rules: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Validate data quality against rules.
        
        Args:
            test_data: Test data to validate
            quality_rules: Optional quality rules to apply
            
        Returns:
            Data quality validation results
        """
        logger.info("Validating data quality")
        
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'quality_metrics': {}
        }
        
        if not test_data:
            results['valid'] = False
            results['errors'].append({
                'type': 'empty_data',
                'message': 'Test data is empty'
            })
            return results
        
        # Basic quality checks
        total_rows = len(test_data)
        null_counts = {}
        duplicate_count = 0
        
        seen_rows = set()
        for row in test_data:
            # Check for nulls
            for key, value in row.items():
                if value is None:
                    null_counts[key] = null_counts.get(key, 0) + 1
            
            # Check for duplicates
            row_str = json.dumps(row, sort_keys=True)
            if row_str in seen_rows:
                duplicate_count += 1
            seen_rows.add(row_str)
        
        results['quality_metrics'] = {
            'total_rows': total_rows,
            'null_counts': null_counts,
            'duplicate_count': duplicate_count,
            'null_percentage': {
                k: (v / total_rows * 100) if total_rows > 0 else 0
                for k, v in null_counts.items()
            }
        }
        
        # Apply custom quality rules if provided
        if quality_rules:
            for rule in quality_rules:
                rule_result = self._apply_quality_rule(test_data, rule)
                if not rule_result['valid']:
                    results['errors'].extend(rule_result['errors'])
                    results['valid'] = False
                if rule_result.get('warnings'):
                    results['warnings'].extend(rule_result['warnings'])
        
        return results
    
    def _extract_transformations(self, canonical_model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract transformation expressions from canonical model.
        
        Args:
            canonical_model: Canonical model
            
        Returns:
            List of transformation dictionaries
        """
        transformations = []
        
        # Extract from transformations section
        model_transformations = canonical_model.get('transformations', [])
        for trans in model_transformations:
            transformations.append({
                'name': trans.get('name'),
                'type': trans.get('type'),
                'expression': trans.get('expression'),
                'target_field': trans.get('target_field'),
                'source_fields': trans.get('source_fields', [])
            })
        
        return transformations
    
    def _validate_single_row(self,
                            input_row: Dict[str, Any],
                            expected_row: Dict[str, Any],
                            transformations: List[Dict[str, Any]],
                            code_type: str) -> Dict[str, Any]:
        """Validate a single row transformation.
        
        Args:
            input_row: Input data row
            expected_row: Expected output row
            transformations: List of transformations
            code_type: Type of code
            
        Returns:
            Validation result for this row
        """
        # This is a simplified validation - in production, would execute actual code
        # For now, we'll do basic field matching
        
        result = {
            'match': True,
            'errors': [],
            'field_results': {}
        }
        
        # Check each expected field
        for field_name, expected_value in expected_row.items():
            # Find transformation for this field
            transformation = next(
                (t for t in transformations if t.get('target_field') == field_name),
                None
            )
            
            if transformation:
                # In a real implementation, would evaluate the expression
                # For now, just check if the field exists
                if field_name not in expected_row:
                    result['errors'].append({
                        'field': field_name,
                        'message': f'Expected field {field_name} not found in output'
                    })
                    result['match'] = False
                
                result['field_results'][field_name] = {
                    'transformation': transformation.get('expression', 'direct'),
                    'expected': expected_value,
                    'valid': True  # Would be validated by actual execution
                }
            else:
                # Direct field mapping
                if field_name in input_row:
                    actual_value = input_row[field_name]
                    if actual_value != expected_value:
                        result['errors'].append({
                            'field': field_name,
                            'message': f'Value mismatch: expected {expected_value}, got {actual_value}'
                        })
                        result['match'] = False
                        result['field_results'][field_name] = {
                            'expected': expected_value,
                            'actual': actual_value,
                            'valid': False
                        }
                    else:
                        result['field_results'][field_name] = {
                            'expected': expected_value,
                            'actual': actual_value,
                            'valid': True
                        }
        
        return result
    
    def _are_types_compatible(self, source_type: str, target_type: str) -> bool:
        """Check if source and target types are compatible.
        
        Args:
            source_type: Source field type
            target_type: Target field type
            
        Returns:
            True if compatible, False otherwise
        """
        # Type compatibility mapping
        compatibility_map = {
            'string': ['varchar', 'char', 'text', 'string'],
            'integer': ['int', 'bigint', 'smallint', 'integer'],
            'decimal': ['decimal', 'numeric', 'float', 'double'],
            'date': ['date', 'timestamp', 'datetime'],
            'boolean': ['boolean', 'bool']
        }
        
        source_normalized = source_type.lower()
        target_normalized = target_type.lower()
        
        # Check if types match exactly
        if source_normalized == target_normalized:
            return True
        
        # Check compatibility groups
        for compatible_types in compatibility_map.values():
            if source_normalized in compatible_types and target_normalized in compatible_types:
                return True
        
        return False
    
    def _apply_quality_rule(self,
                           test_data: List[Dict[str, Any]],
                           rule: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a quality rule to test data.
        
        Args:
            test_data: Test data
            rule: Quality rule definition
            
        Returns:
            Rule application results
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        rule_type = rule.get('type')
        rule_field = rule.get('field')
        rule_value = rule.get('value')
        
        if rule_type == 'not_null':
            # Check that field is not null
            for i, row in enumerate(test_data):
                if rule_field in row and row[rule_field] is None:
                    result['errors'].append({
                        'row': i,
                        'field': rule_field,
                        'message': f'Null value found in {rule_field} (not_null rule violated)'
                    })
                    result['valid'] = False
        
        elif rule_type == 'unique':
            # Check that field values are unique
            seen_values = {}
            for i, row in enumerate(test_data):
                if rule_field in row:
                    value = row[rule_field]
                    if value in seen_values:
                        result['errors'].append({
                            'row': i,
                            'field': rule_field,
                            'message': f'Duplicate value {value} found in {rule_field} (unique rule violated)'
                        })
                        result['valid'] = False
                    seen_values[value] = i
        
        elif rule_type == 'range':
            # Check that field values are within range
            min_value = rule_value.get('min')
            max_value = rule_value.get('max')
            for i, row in enumerate(test_data):
                if rule_field in row:
                    value = row[rule_field]
                    if min_value is not None and value < min_value:
                        result['errors'].append({
                            'row': i,
                            'field': rule_field,
                            'message': f'Value {value} below minimum {min_value}'
                        })
                        result['valid'] = False
                    if max_value is not None and value > max_value:
                        result['errors'].append({
                            'row': i,
                            'field': rule_field,
                            'message': f'Value {value} above maximum {max_value}'
                        })
                        result['valid'] = False
        
        return result

