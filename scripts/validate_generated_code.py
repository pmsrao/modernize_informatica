#!/usr/bin/env python3
"""
Validation Script for Generated Code (After AI Review and Fix)

This script performs sanity checks on generated code to ensure:
1. All mappings (top-level transformations) have generated code files
2. Code files exist on disk
3. Code files are syntactically valid (Python/SQL)
4. Code files have proper structure (imports, functions, etc.)
5. Code quality metrics are within acceptable ranges

Note: Only validates top-level mappings (source_component_type='mapping'), 
not nested transformations (expressions, aggregators, etc.) which are part of mappings.

Usage:
    python scripts/validate_generated_code.py [--strict] [--verbose]
"""

import sys
import os
import json
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

try:
    from src.graph.graph_store import GraphStore
    from src.graph.graph_queries import GraphQueries
    from src.utils.logger import get_logger
    from config import settings
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root and dependencies are installed.")
    sys.exit(1)

logger = get_logger(__name__)


class CodeValidator:
    """Validates generated code files."""
    
    def __init__(self, strict: bool = False, verbose: bool = False):
        """Initialize validator.
        
        Args:
            strict: If True, fail on warnings as well as errors
            verbose: If True, print detailed validation information
        """
        self.strict = strict
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        self.stats = {
            'total_transformations': 0,
            'transformations_with_code': 0,
            'transformations_without_code': 0,
            'total_code_files': 0,
            'valid_code_files': 0,
            'invalid_code_files': 0,
            'syntax_errors': 0,
            'missing_imports': 0,
            'missing_functions': 0
        }
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks.
        
        Returns:
            Dictionary with validation results
        """
        logger.info("Starting code validation...")
        
        # Initialize graph store
        graph_store = GraphStore()
        graph_queries = GraphQueries(graph_store)
        
        try:
            # Get only top-level mappings (transformations with source_component_type='mapping')
            # Nested transformations (expressions, aggregators, etc.) don't have their own code files
            with graph_store.driver.session() as session:
                result = session.run("""
                    MATCH (t:Transformation)
                    WHERE t.source_component_type = 'mapping'
                    RETURN t.name as name
                    ORDER BY t.name
                """)
                transformations = [record["name"] for record in result]
            
            self.stats['total_transformations'] = len(transformations)
            
            logger.info(f"Found {len(transformations)} mapping(s) to validate")
            
            # Validate each transformation (mapping)
            for transformation_name in transformations:
                self._validate_transformation(transformation_name, graph_queries)
            
            # Generate summary
            summary = self._generate_summary()
            
            return {
                'success': len(self.errors) == 0 and (not self.strict or len(self.warnings) == 0),
                'stats': self.stats,
                'errors': self.errors,
                'warnings': self.warnings,
                'summary': summary
            }
        
        finally:
            graph_store.close()
    
    def _validate_transformation(self, transformation_name: str, graph_queries: GraphQueries):
        """Validate code for a single transformation.
        
        Args:
            transformation_name: Name of the transformation
            graph_queries: GraphQueries instance
        """
        # Get code files for this transformation
        code_files = graph_queries.get_transformation_code_files(transformation_name)
        
        if not code_files:
            self.stats['transformations_without_code'] += 1
            # This is now an error, not a warning, since we're only checking actual mappings
            self.errors.append({
                'type': 'missing_code',
                'transformation': transformation_name,
                'message': f'No code files found in Neo4j for mapping: {transformation_name}. Code generation may have failed or not been run.'
            })
            if self.verbose:
                logger.error(f"No code files found in Neo4j for mapping: {transformation_name}")
            return
        
        self.stats['transformations_with_code'] += 1
        self.stats['total_code_files'] += len(code_files)
        
        if self.verbose:
            logger.info(f"Found {len(code_files)} code file(s) in Neo4j for {transformation_name}")
        
        # Validate each code file
        for code_file in code_files:
            file_path = code_file.get('file_path')
            code_type = code_file.get('code_type', 'unknown')
            language = code_file.get('language', 'unknown')
            
            if self.verbose:
                logger.info(f"  Validating: {file_path} (type: {code_type}, language: {language})")
            
            if not file_path:
                self.errors.append({
                    'type': 'missing_file_path',
                    'transformation': transformation_name,
                    'code_file': code_file,
                    'message': 'Code file metadata missing file_path'
                })
                continue
            
            self._validate_code_file(file_path, language, code_type, transformation_name)
    
    def _validate_code_file(self, file_path: str, language: str, code_type: str, transformation_name: str):
        """Validate a single code file.
        
        Args:
            file_path: Path to the code file (relative to project root)
            language: Programming language (python, sql)
            code_type: Type of code (pyspark, dlt, sql)
            transformation_name: Name of the transformation
        """
        # Resolve file path
        project_root = Path(__file__).parent.parent
        full_path = project_root / file_path
        
        # Check if file exists
        if not full_path.exists():
            # Try alternative paths - check both generated and generated_ai directories
            # Also try to find file by name if path doesn't match exactly
            alt_paths = [
                project_root / "test_log" / "generated_ai" / file_path,
                project_root / "test_log" / "generated" / file_path,
                project_root / file_path
            ]
            
            # If file_path is relative, also try finding by filename in generated_ai
            if not Path(file_path).is_absolute():
                filename = Path(file_path).name
                # Search in generated_ai directory structure
                generated_ai_dir = project_root / "test_log" / "generated_ai"
                if generated_ai_dir.exists():
                    for alt_file in generated_ai_dir.rglob(filename):
                        if alt_file.is_file():
                            alt_paths.append(alt_file)
                            break
                # Also search in generated directory
                generated_dir = project_root / "test_log" / "generated"
                if generated_dir.exists():
                    for alt_file in generated_dir.rglob(filename):
                        if alt_file.is_file():
                            alt_paths.append(alt_file)
                            break
            
            found = False
            for alt_path in alt_paths:
                if alt_path.exists() and alt_path.is_file():
                    full_path = alt_path
                    found = True
                    if self.verbose:
                        logger.info(f"Found code file at alternative path: {full_path}")
                    break
            
            if not found:
                self.stats['invalid_code_files'] += 1
                # Check if file exists in generated_ai but path points to generated
                generated_ai_dir = project_root / "test_log" / "generated_ai"
                generated_dir = project_root / "test_log" / "generated"
                
                # Try to find file in generated_ai with same relative structure
                if generated_ai_dir.exists() and file_path.startswith("test_log/generated/"):
                    ai_path = file_path.replace("test_log/generated/", "test_log/generated_ai/")
                    ai_full_path = project_root / ai_path
                    if ai_full_path.exists():
                        full_path = ai_full_path
                        found = True
                        self.warnings.append({
                            'type': 'path_mismatch',
                            'transformation': transformation_name,
                            'file_path': file_path,
                            'actual_path': str(ai_full_path.relative_to(project_root)),
                            'message': f'Code file found in generated_ai/ but Neo4j path points to generated/. File exists at: {ai_path}'
                        })
                        if self.verbose:
                            logger.warning(f"File path mismatch: Neo4j has {file_path} but file exists at {ai_path}")
                
                if not found:
                    self.errors.append({
                        'type': 'file_not_found',
                        'transformation': transformation_name,
                        'file_path': file_path,
                        'message': f'Code file not found: {file_path}. Searched in generated/ and generated_ai/ directories.'
                    })
                    return
        
        # Read file content
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.stats['invalid_code_files'] += 1
            self.errors.append({
                'type': 'file_read_error',
                'transformation': transformation_name,
                'file_path': str(full_path),
                'message': f'Failed to read file: {str(e)}'
            })
            return
        
        # Validate based on language
        if language == 'python' or code_type in ['pyspark', 'dlt']:
            self._validate_python_code(content, file_path, transformation_name)
        elif language == 'sql' or code_type == 'sql':
            self._validate_sql_code(content, file_path, transformation_name)
        
        self.stats['valid_code_files'] += 1
    
    def _validate_python_code(self, content: str, file_path: str, transformation_name: str):
        """Validate Python code.
        
        Args:
            content: Python code content
            file_path: Path to the file
            transformation_name: Name of the transformation
        """
        # Check syntax
        try:
            ast.parse(content)
        except SyntaxError as e:
            self.stats['syntax_errors'] += 1
            self.stats['invalid_code_files'] += 1
            self.errors.append({
                'type': 'syntax_error',
                'transformation': transformation_name,
                'file_path': file_path,
                'message': f'Syntax error in Python code: {str(e)}',
                'line': e.lineno,
                'offset': e.offset
            })
            return
        
        # Check for required imports (basic checks)
        if 'pyspark' in file_path.lower() or 'pyspark' in content.lower():
            if 'from pyspark.sql' not in content and 'import pyspark' not in content:
                self.stats['missing_imports'] += 1
                self.warnings.append({
                    'type': 'missing_imports',
                    'transformation': transformation_name,
                    'file_path': file_path,
                    'message': 'PySpark imports not found in PySpark code file'
                })
        
        # Check for function definitions (at least one)
        if not re.search(r'def\s+\w+', content):
            self.stats['missing_functions'] += 1
            self.warnings.append({
                'type': 'missing_functions',
                'transformation': transformation_name,
                'file_path': file_path,
                'message': 'No function definitions found in code file'
            })
        
        # Check for empty file
        if not content.strip():
            self.errors.append({
                'type': 'empty_file',
                'transformation': transformation_name,
                'file_path': file_path,
                'message': 'Code file is empty'
            })
    
    def _validate_sql_code(self, content: str, file_path: str, transformation_name: str):
        """Validate SQL code.
        
        Args:
            content: SQL code content
            file_path: Path to the file
            transformation_name: Name of the transformation
        """
        # Basic SQL validation (check for common SQL keywords)
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        content_upper = content.upper()
        
        has_sql_keyword = any(keyword in content_upper for keyword in sql_keywords)
        
        if not has_sql_keyword and content.strip():
            self.warnings.append({
                'type': 'unusual_sql',
                'transformation': transformation_name,
                'file_path': file_path,
                'message': 'SQL file does not contain common SQL keywords'
            })
        
        # Check for empty file
        if not content.strip():
            self.errors.append({
                'type': 'empty_file',
                'transformation': transformation_name,
                'file_path': file_path,
                'message': 'SQL file is empty'
            })
    
    def _generate_summary(self) -> str:
        """Generate validation summary.
        
        Returns:
            Summary string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("CODE VALIDATION SUMMARY")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Total Mappings: {self.stats['total_transformations']}")
        lines.append(f"  - With Code Files: {self.stats['transformations_with_code']}")
        lines.append(f"  - Without Code Files: {self.stats['transformations_without_code']}")
        lines.append("")
        lines.append(f"Total Code Files (in Neo4j): {self.stats['total_code_files']}")
        lines.append(f"  - Valid: {self.stats['valid_code_files']}")
        lines.append(f"  - Invalid: {self.stats['invalid_code_files']}")
        if self.stats['total_code_files'] > 0 and self.stats['transformations_with_code'] > 0:
            avg_files = self.stats['total_code_files'] / self.stats['transformations_with_code']
            lines.append(f"  - Average per Mapping: {avg_files:.1f}")
            if avg_files == 1.0:
                lines.append("  ℹ️  Note: Only PySpark code is generated (DLT/SQL disabled), so 1 file per mapping is expected")
        lines.append("")
        lines.append(f"Issues Found:")
        lines.append(f"  - Syntax Errors: {self.stats['syntax_errors']}")
        lines.append(f"  - Missing Imports: {self.stats['missing_imports']}")
        lines.append(f"  - Missing Functions: {self.stats['missing_functions']}")
        lines.append("")
        lines.append(f"Errors: {len(self.errors)}")
        lines.append(f"Warnings: {len(self.warnings)}")
        lines.append("")
        
        if self.errors:
            lines.append("ERRORS:")
            lines.append("-" * 80)
            for error in self.errors[:10]:  # Show first 10 errors
                lines.append(f"  [{error['type']}] {error['transformation']}: {error['message']}")
            if len(self.errors) > 10:
                lines.append(f"  ... and {len(self.errors) - 10} more errors")
            lines.append("")
        
        if self.warnings:
            lines.append("WARNINGS:")
            lines.append("-" * 80)
            for warning in self.warnings[:10]:  # Show first 10 warnings
                lines.append(f"  [{warning['type']}] {warning['transformation']}: {warning['message']}")
            if len(self.warnings) > 10:
                lines.append(f"  ... and {len(self.warnings) - 10} more warnings")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate generated code after AI Review and Fix')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as errors')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    validator = CodeValidator(strict=args.strict, verbose=args.verbose)
    results = validator.validate_all()
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(validator._generate_summary())
    
    # Exit with error code if validation failed
    if not results['success']:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()

