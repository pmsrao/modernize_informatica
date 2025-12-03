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
    from graph.graph_store import GraphStore
    from graph.graph_queries import GraphQueries
    from utils.logger import get_logger
    from config import settings
    # Import canonical model validator
    try:
        from scripts.validate_canonical_model import CanonicalModelValidator
        CANONICAL_VALIDATOR_AVAILABLE = True
    except ImportError:
        CANONICAL_VALIDATOR_AVAILABLE = False
        CanonicalModelValidator = None
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root and dependencies are installed.")
    sys.exit(1)

logger = get_logger(__name__)


class CodeValidator:
    """Validates generated code files."""
    
    def __init__(self, strict: bool = False, verbose: bool = False, validate_canonical: bool = True):
        """Initialize validator.
        
        Args:
            strict: If True, fail on warnings as well as errors
            verbose: If True, print detailed validation information
            validate_canonical: If True, also validate canonical models
        """
        self.strict = strict
        self.verbose = verbose
        self.validate_canonical = validate_canonical and CANONICAL_VALIDATOR_AVAILABLE
        self.errors = []
        self.warnings = []
        self.canonical_errors = []
        self.canonical_warnings = []
        self.stats = {
            'total_transformations': 0,
            'transformations_with_code': 0,
            'transformations_without_code': 0,
            'total_code_files': 0,
            'valid_code_files': 0,
            'invalid_code_files': 0,
            'syntax_errors': 0,
            'missing_imports': 0,
            'missing_functions': 0,
            'canonical_models_validated': 0,
            'canonical_models_invalid': 0
        }
    
    def validate_transformation_completeness(self, transformation_name: str, code_content: str, model: Dict[str, Any]) -> List[str]:
        """Validate that all transformations are represented in generated code.
        
        Args:
            transformation_name: Name of the transformation
            code_content: Generated code content
            model: Canonical model
            
        Returns:
            List of errors found
        """
        errors = []
        transformations = model.get("transformations", [])
        
        # Check that key transformations are mentioned in code
        for trans in transformations:
            trans_name = trans.get("name", "")
            trans_type = trans.get("type", "")
            
            # Skip sources and targets (they're handled differently)
            if trans_type in ["SOURCE", "TARGET"]:
                continue
            
            # Check if transformation name appears in code (as variable, comment, or function)
            if trans_name and trans_name not in code_content:
                # Allow some flexibility - check if similar name exists
                similar_names = [name for name in code_content.split() if trans_name.lower() in name.lower() or name.lower() in trans_name.lower()]
                if not similar_names:
                    errors.append(f"Transformation '{trans_name}' (type: {trans_type}) not found in generated code")
        
        return errors
    
    def validate_connector_completeness(self, transformation_name: str, code_content: str, model: Dict[str, Any]) -> List[str]:
        """Validate that connectors are represented in code.
        
        Args:
            transformation_name: Name of the transformation
            code_content: Generated code content
            model: Canonical model
            
        Returns:
            List of errors found
        """
        errors = []
        connectors = model.get("connectors", [])
        
        # Check that connectors are represented (as joins, selects, etc.)
        # This is a basic check - more sophisticated analysis would parse the code AST
        for conn in connectors:
            from_trans = conn.get("from_transformation", "")
            to_trans = conn.get("to_transformation", "")
            
            # Skip OUTPUT/INPUT connectors (handled specially)
            if to_trans == "OUTPUT" or from_trans == "INPUT":
                continue
            
            # Check if both transformations are mentioned in code
            if from_trans and from_trans not in code_content:
                errors.append(f"Source transformation '{from_trans}' from connector not found in code")
            if to_trans and to_trans not in code_content:
                errors.append(f"Target transformation '{to_trans}' from connector not found in code")
        
        return errors
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks.
        
        Returns:
            Dictionary with validation results
        """
        logger.info("Starting code validation...")
        
        # Initialize graph store (store as instance variable for completeness checks)
        self.graph_store = GraphStore()
        graph_store = self.graph_store
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
            
            # Validate canonical models if enabled
            if self.validate_canonical:
                self._validate_canonical_models(graph_store, transformations)
            
            # Generate summary
            summary = self._generate_summary()
            
            # Combine errors and warnings
            all_errors = self.errors + self.canonical_errors
            all_warnings = self.warnings + self.canonical_warnings
            
            return {
                'success': len(all_errors) == 0 and (not self.strict or len(all_warnings) == 0),
                'stats': self.stats,
                'errors': all_errors,
                'warnings': all_warnings,
                'canonical_errors': self.canonical_errors,
                'canonical_warnings': self.canonical_warnings,
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
                project_root / "workspace" / "generated_ai" / file_path,
                project_root / "workspace" / "generated" / file_path,
                project_root / file_path
            ]
            
            # If file_path is relative, also try finding by filename in generated_ai
            if not Path(file_path).is_absolute():
                filename = Path(file_path).name
                # Search in generated_ai directory structure
                generated_ai_dir = project_root / "workspace" / "generated_ai"
                if generated_ai_dir.exists():
                    for alt_file in generated_ai_dir.rglob(filename):
                        if alt_file.is_file():
                            alt_paths.append(alt_file)
                            break
                # Also search in generated directory
                generated_dir = project_root / "workspace" / "generated"
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
                generated_ai_dir = project_root / "workspace" / "generated_ai"
                generated_dir = project_root / "workspace" / "generated"
                
                # Try to find file in generated_ai with same relative structure
                if generated_ai_dir.exists() and file_path.startswith("workspace/generated/"):
                    ai_path = file_path.replace("workspace/generated/", "workspace/generated_ai/")
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
        
        # Validate completeness (check transformations and connectors are represented)
        try:
            model = graph_store.load_transformation(transformation_name)
            if model:
                # Check transformation completeness
                trans_errors = self.validate_transformation_completeness(transformation_name, content, model)
                for error in trans_errors:
                    self.warnings.append({
                        'type': 'transformation_missing',
                        'transformation': transformation_name,
                        'file_path': file_path,
                        'message': error
                    })
                
                # Check connector completeness
                conn_errors = self.validate_connector_completeness(transformation_name, content, model)
                for error in conn_errors:
                    self.warnings.append({
                        'type': 'connector_missing',
                        'transformation': transformation_name,
                        'file_path': file_path,
                        'message': error
                    })
        except Exception as e:
            if self.verbose:
                logger.debug(f"Could not load model for completeness check: {e}")
        
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
    
    def _validate_canonical_models(self, graph_store: GraphStore, transformation_names: List[str]):
        """Validate canonical models for transformations.
        
        Args:
            graph_store: GraphStore instance
            transformation_names: List of transformation names to validate
        """
        if not self.validate_canonical or not CanonicalModelValidator:
            return
        
        logger.info("Validating canonical models...")
        canonical_validator = CanonicalModelValidator(strict=self.strict, verbose=self.verbose)
        
        # Load canonical models from version store or graph
        from versioning.version_store import VersionStore
        version_store = VersionStore(path=settings.version_store_path)
        
        for transformation_name in transformation_names:
            try:
                # Try to load from version store
                model = version_store.load(transformation_name)
                
                if not model:
                    # Try loading from graph
                    try:
                        model = graph_store.load_transformation(transformation_name)
                    except Exception:
                        pass
                
                if model:
                    self.stats['canonical_models_validated'] += 1
                    result = canonical_validator.validate_model(model, transformation_name)
                    
                    if not result['valid']:
                        self.stats['canonical_models_invalid'] += 1
                        self.canonical_errors.extend(result['errors'])
                    
                    if result['warnings']:
                        self.canonical_warnings.extend(result['warnings'])
                else:
                    self.warnings.append({
                        'type': 'canonical_model_not_found',
                        'transformation': transformation_name,
                        'message': f'Canonical model not found for {transformation_name}'
                    })
            except Exception as e:
                self.warnings.append({
                    'type': 'canonical_validation_error',
                    'transformation': transformation_name,
                    'message': f'Failed to validate canonical model: {str(e)}'
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
        if self.validate_canonical:
            lines.append(f"Canonical Model Validation:")
            lines.append(f"  - Models Validated: {self.stats['canonical_models_validated']}")
            lines.append(f"  - Invalid Models: {self.stats['canonical_models_invalid']}")
            lines.append("")
        lines.append(f"Errors: {len(self.errors) + len(self.canonical_errors)}")
        lines.append(f"  - Code Errors: {len(self.errors)}")
        if self.validate_canonical:
            lines.append(f"  - Canonical Model Errors: {len(self.canonical_errors)}")
        lines.append(f"Warnings: {len(self.warnings) + len(self.canonical_warnings)}")
        lines.append(f"  - Code Warnings: {len(self.warnings)}")
        if self.validate_canonical:
            lines.append(f"  - Canonical Model Warnings: {len(self.canonical_warnings)}")
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
    parser.add_argument('--no-canonical', action='store_true', help='Skip canonical model validation')
    
    args = parser.parse_args()
    
    validator = CodeValidator(
        strict=args.strict, 
        verbose=args.verbose,
        validate_canonical=not args.no_canonical
    )
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

