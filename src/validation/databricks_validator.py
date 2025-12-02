"""Databricks Validator - Validates generated code against Databricks syntax."""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import ast
import re

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabricksValidator:
    """Validates generated code against Databricks syntax and best practices."""
    
    # Databricks-specific functions and APIs
    DATABRICKS_FUNCTIONS = [
        'dbutils', 'spark', 'display', 'table', 'sql',
        'read', 'write', 'format', 'option', 'mode',
        'createOrReplaceTempView', 'createOrReplaceGlobalTempView',
        'spark.sql', 'spark.read', 'spark.write'
    ]
    
    # Unity Catalog functions
    UNITY_CATALOG_FUNCTIONS = [
        'catalog', 'schema', 'table', 'USE CATALOG', 'USE SCHEMA'
    ]
    
    # Databricks-specific imports
    DATABRICKS_IMPORTS = [
        'pyspark.sql', 'pyspark.sql.functions', 'delta', 'dlt'
    ]
    
    def __init__(self):
        """Initialize Databricks validator."""
        logger.info("DatabricksValidator initialized")
    
    def validate_pyspark_code(self, code: str) -> Dict[str, Any]:
        """Validate PySpark code for Databricks compatibility.
        
        Args:
            code: Generated PySpark code string
            
        Returns:
            Validation results dictionary
        """
        logger.info("Validating PySpark code for Databricks compatibility")
        
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'databricks_compatibility': True,
            'unity_catalog_compatible': False
        }
        
        # Check syntax
        try:
            ast.parse(code)
        except SyntaxError as e:
            results['valid'] = False
            results['errors'].append({
                'type': 'syntax_error',
                'line': e.lineno,
                'message': e.msg,
                'text': e.text
            })
            return results
        
        # Check for Databricks-specific functions
        databricks_functions_found = []
        for func in self.DATABRICKS_FUNCTIONS:
            if func in code:
                databricks_functions_found.append(func)
        
        if not databricks_functions_found:
            results['warnings'].append({
                'type': 'missing_databricks_functions',
                'message': 'No Databricks-specific functions detected. Code may need Databricks context.'
            })
        
        # Check for Unity Catalog usage
        unity_catalog_found = any(func in code for func in self.UNITY_CATALOG_FUNCTIONS)
        results['unity_catalog_compatible'] = unity_catalog_found
        
        if not unity_catalog_found:
            results['suggestions'].append({
                'type': 'unity_catalog',
                'message': 'Consider using Unity Catalog for table references (catalog.schema.table)'
            })
        
        # Check for Delta Lake usage
        delta_usage = 'delta' in code.lower() or 'DeltaTable' in code
        if not delta_usage:
            results['suggestions'].append({
                'type': 'delta_lake',
                'message': 'Consider using Delta Lake format for better performance and ACID transactions'
            })
        
        # Check for best practices
        self._check_best_practices(code, results)
        
        return results
    
    def validate_sql_code(self, code: str) -> Dict[str, Any]:
        """Validate SQL code for Databricks SQL compatibility.
        
        Args:
            code: Generated SQL code string
            
        Returns:
            Validation results dictionary
        """
        logger.info("Validating SQL code for Databricks SQL compatibility")
        
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'databricks_sql_compatible': True
        }
        
        # Basic SQL syntax checks
        if not code.strip():
            results['valid'] = False
            results['errors'].append({
                'type': 'empty_sql',
                'message': 'SQL code is empty'
            })
            return results
        
        # Check for Databricks SQL-specific syntax
        # Check for Unity Catalog references
        unity_catalog_pattern = r'\b\w+\.\w+\.\w+\b'  # catalog.schema.table
        if re.search(unity_catalog_pattern, code):
            results['suggestions'].append({
                'type': 'unity_catalog',
                'message': 'Unity Catalog references detected - good practice'
            })
        
        # Check for Delta-specific SQL
        if 'DELTA' in code.upper():
            results['suggestions'].append({
                'type': 'delta_lake',
                'message': 'Delta Lake syntax detected'
            })
        
        # Check for unsupported Informatica functions
        informatica_functions = ['IIF', 'DECODE', 'ISNULL', 'ISNULL2']
        found_informatica = [f for f in informatica_functions if f in code.upper()]
        if found_informatica:
            results['warnings'].append({
                'type': 'informatica_functions',
                'message': f'Informatica-specific functions found: {found_informatica}. May need translation.',
                'functions': found_informatica
            })
        
        return results
    
    def validate_against_unity_catalog(self, code: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate code against Unity Catalog schema.
        
        Args:
            code: Generated code string
            schema: Optional Unity Catalog schema definition
            
        Returns:
            Validation results dictionary
        """
        logger.info("Validating code against Unity Catalog schema")
        
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'schema_validation': {}
        }
        
        if not schema:
            results['warnings'].append({
                'type': 'no_schema',
                'message': 'No Unity Catalog schema provided - skipping schema validation'
            })
            return results
        
        # Extract table references from code
        table_refs = self._extract_table_references(code)
        
        # Validate table references against schema
        for table_ref in table_refs:
            if not self._validate_table_reference(table_ref, schema):
                results['errors'].append({
                    'type': 'invalid_table_reference',
                    'table': table_ref,
                    'message': f'Table reference {table_ref} not found in Unity Catalog schema'
                })
                results['valid'] = False
        
        return results
    
    def _check_best_practices(self, code: str, results: Dict[str, Any]):
        """Check code against Databricks best practices.
        
        Args:
            code: Code string
            results: Results dictionary to update
        """
        # Check for proper error handling
        if 'try:' not in code and 'except' not in code:
            results['suggestions'].append({
                'type': 'error_handling',
                'message': 'Consider adding error handling with try/except blocks'
            })
        
        # Check for proper partitioning
        if 'partitionBy' not in code and 'repartition' not in code:
            results['suggestions'].append({
                'type': 'partitioning',
                'message': 'Consider adding partitioning for better performance'
            })
        
        # Check for caching where appropriate
        if '.cache()' not in code and '.persist()' not in code:
            results['suggestions'].append({
                'type': 'caching',
                'message': 'Consider caching DataFrames that are reused multiple times'
            })
    
    def _extract_table_references(self, code: str) -> List[str]:
        """Extract table references from code.
        
        Args:
            code: Code string
            
        Returns:
            List of table references
        """
        # Simple pattern matching for table references
        # This could be enhanced with AST parsing
        patterns = [
            r'table\(["\']([^"\']+)["\']\)',
            r'spark\.table\(["\']([^"\']+)["\']\)',
            r'FROM\s+([\w\.]+)',
            r'JOIN\s+([\w\.]+)',
        ]
        
        table_refs = []
        for pattern in patterns:
            matches = re.findall(pattern, code, re.IGNORECASE)
            table_refs.extend(matches)
        
        return list(set(table_refs))
    
    def _validate_table_reference(self, table_ref: str, schema: Dict[str, Any]) -> bool:
        """Validate a table reference against Unity Catalog schema.
        
        Args:
            table_ref: Table reference string
            schema: Unity Catalog schema definition
            
        Returns:
            True if valid, False otherwise
        """
        # Placeholder - in real implementation, would check against Unity Catalog
        # For now, just check if it's a valid format
        parts = table_ref.split('.')
        return len(parts) <= 3  # catalog.schema.table format

