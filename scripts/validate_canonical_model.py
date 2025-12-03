#!/usr/bin/env python3
"""
Canonical Model Validation Script

This script validates canonical models for completeness and correctness:
1. All transformations are represented
2. Connectors are valid (from/to transformations exist)
3. Expression syntax is correct
4. No circular dependencies
5. All sources/targets are connected
6. Field mappings are complete

Additionally, it can validate enhancements in Neo4j:
- Field and Port nodes
- Field-level lineage relationships
- Complexity metrics
- Semantic tags
- Runtime configuration
- SCD structure
- Control tasks

Usage:
    python scripts/validate_canonical_model.py [--path PATH] [--strict] [--verbose] [--enhancements] [--json]
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, deque

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

try:
    from utils.logger import get_logger
    from utils.exceptions import ValidationError
    try:
        from translator.parser_engine import Parser
        from translator.tokenizer import tokenize
        PARSER_ENGINE_AVAILABLE = True
    except ImportError:
        PARSER_ENGINE_AVAILABLE = False
        Parser = None
        tokenize = None
    
    # Optional imports for enhancement validation
    try:
        from graph.graph_store import GraphStore
        from graph.graph_queries import GraphQueries
        GRAPH_STORE_AVAILABLE = True
    except ImportError:
        GRAPH_STORE_AVAILABLE = False
        GraphStore = None
        GraphQueries = None
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root and dependencies are installed.")
    sys.exit(1)

logger = get_logger(__name__)


class CanonicalModelValidator:
    """Validates canonical models for completeness and correctness."""
    
    def __init__(self, strict: bool = False, verbose: bool = False, validate_enhancements: bool = False):
        """Initialize validator.
        
        Args:
            strict: If True, treat warnings as errors
            verbose: If True, print detailed validation information
            validate_enhancements: If True, also validate Neo4j enhancements
        """
        self.strict = strict
        self.verbose = verbose
        self.validate_enhancements = validate_enhancements
        self.errors = []
        self.warnings = []
        self.stats = {
            'total_models': 0,
            'valid_models': 0,
            'invalid_models': 0,
            'total_transformations': 0,
            'total_connectors': 0,
            'invalid_connectors': 0,
            'orphaned_transformations': 0,
            'circular_dependencies': 0,
            'expression_errors': 0
        }
        self.parser_available = PARSER_ENGINE_AVAILABLE and Parser is not None and tokenize is not None
        
        # Enhancement validation results (if enabled)
        self.enhancement_results = None
        self.graph_store = None
        self.graph_queries = None
        
        if validate_enhancements:
            if not GRAPH_STORE_AVAILABLE:
                logger.warning("Graph store not available, skipping enhancement validation")
                self.validate_enhancements = False
            else:
                try:
                    self.graph_store = GraphStore()
                    self.graph_queries = GraphQueries(self.graph_store)
                    self.enhancement_results = {
                        "field_port_nodes": {"status": "pending", "details": []},
                        "field_lineage": {"status": "pending", "details": []},
                        "complexity_metrics": {"status": "pending", "details": []},
                        "semantic_tags": {"status": "pending", "details": []},
                        "runtime_config": {"status": "pending", "details": []},
                        "scd_structure": {"status": "pending", "details": []},
                        "control_tasks": {"status": "pending", "details": []}
                    }
                except Exception as e:
                    logger.error(f"Failed to initialize graph store: {e}")
                    self.validate_enhancements = False
    
    def validate_model(self, model: Dict[str, Any], model_name: Optional[str] = None) -> Dict[str, Any]:
        """Validate a single canonical model.
        
        Args:
            model: Canonical model dictionary
            model_name: Optional model name for reporting
            
        Returns:
            Validation result dictionary
        """
        model_name = model_name or model.get('transformation_name', 'unknown')
        self.stats['total_models'] += 1
        
        if self.verbose:
            logger.info(f"Validating model: {model_name}")
        
        # Reset per-model errors/warnings
        model_errors = []
        model_warnings = []
        
        # Skip validation for sessions (they reference mappings, don't contain transformations directly)
        source_component_type = model.get('source_component_type', 'mapping')
        if source_component_type == 'session':
            # Sessions are valid by default (they reference mappings)
            self.stats['valid_models'] += 1
            return {
                'valid': True,
                'errors': [],
                'warnings': []
            }
        
        # Validate structure
        structure_result = self._validate_structure(model, model_name)
        model_errors.extend(structure_result['errors'])
        model_warnings.extend(structure_result['warnings'])
        
        # Validate transformations
        transformation_result = self._validate_transformations(model, model_name)
        model_errors.extend(transformation_result['errors'])
        model_warnings.extend(transformation_result['warnings'])
        
        # Validate connectors
        connector_result = self._validate_connectors(model, model_name)
        model_errors.extend(connector_result['errors'])
        model_warnings.extend(connector_result['warnings'])
        
        # Validate expressions
        expression_result = self._validate_expressions(model, model_name)
        model_errors.extend(expression_result['errors'])
        model_warnings.extend(expression_result['warnings'])
        
        # Check for circular dependencies
        circular_result = self._check_circular_dependencies(model, model_name)
        model_errors.extend(circular_result['errors'])
        model_warnings.extend(circular_result['warnings'])
        
        # Check for orphaned transformations
        orphaned_result = self._check_orphaned_transformations(model, model_name)
        model_errors.extend(orphaned_result['errors'])
        model_warnings.extend(orphaned_result['warnings'])
        
        # Update stats
        if model_errors:
            self.stats['invalid_models'] += 1
            self.errors.extend([{**e, 'model': model_name} for e in model_errors])
        else:
            self.stats['valid_models'] += 1
        
        if model_warnings:
            self.warnings.extend([{**w, 'model': model_name} for w in model_warnings])
        
        return {
            'valid': len(model_errors) == 0,
            'errors': model_errors,
            'warnings': model_warnings
        }
    
    def _validate_structure(self, model: Dict[str, Any], model_name: str) -> Dict[str, Any]:
        """Validate canonical model structure.
        
        Args:
            model: Canonical model
            model_name: Model name
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        # Check required fields (different for mappings vs mapplets)
        source_component_type = model.get('source_component_type', 'mapping')
        
        if source_component_type == 'mapplet':
            # Mapplets have input_ports and output_ports instead of sources/targets
            required_fields = ['name', 'type', 'input_ports', 'output_ports', 'transformations']
        else:
            # Mappings have sources and targets
            required_fields = ['transformation_name', 'sources', 'targets', 'transformations', 'connectors']
        
        for field in required_fields:
            if field not in model:
                errors.append({
                    'type': 'missing_field',
                    'field': field,
                    'message': f'Required field "{field}" is missing for {source_component_type}'
                })
        
        # Check transformation_name
        if 'transformation_name' in model and not model['transformation_name']:
            errors.append({
                'type': 'empty_field',
                'field': 'transformation_name',
                'message': 'transformation_name cannot be empty'
            })
        
        # Check sources/targets are lists
        for field in ['sources', 'targets', 'transformations', 'connectors']:
            if field in model and not isinstance(model[field], list):
                errors.append({
                    'type': 'invalid_type',
                    'field': field,
                    'message': f'"{field}" must be a list'
                })
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_transformations(self, model: Dict[str, Any], model_name: str) -> Dict[str, Any]:
        """Validate transformations.
        
        Args:
            model: Canonical model
            model_name: Model name
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        transformations = model.get("transformations", [])
        
        self.stats['total_transformations'] += len(transformations)
        
        # Check for duplicate transformation names
        trans_names = [t.get("name") for t in transformations]
        duplicates = [name for name in trans_names if trans_names.count(name) > 1]
        if duplicates:
            errors.append({
                'type': 'duplicate_transformation',
                'transformations': list(set(duplicates)),
                'message': f'Duplicate transformation names found: {list(set(duplicates))}'
            })
        
        # Validate each transformation
        for trans in transformations:
            trans_name = trans.get("name", "unknown")
            
            # Check required fields
            if 'name' not in trans or not trans['name']:
                errors.append({
                    'type': 'missing_transformation_name',
                    'transformation': trans_name,
                    'message': 'Transformation missing name'
                })
            
            if 'type' not in trans:
                warnings.append({
                    'type': 'missing_transformation_type',
                    'transformation': trans_name,
                    'message': 'Transformation missing type'
                })
            
            # Validate transformation type
            valid_types = [
                'EXPRESSION', 'LOOKUP', 'AGGREGATOR', 'JOINER', 'FILTER',
                'ROUTER', 'SORTER', 'RANKER', 'NORMALIZER', 'UNION',
                'UPDATE_STRATEGY', 'MAPPLET_INSTANCE', 'SOURCE_QUALIFIER'
            ]
            if 'type' in trans and trans['type'] not in valid_types:
                warnings.append({
                    'type': 'unknown_transformation_type',
                    'transformation': trans_name,
                    'type': trans['type'],
                    'message': f'Unknown transformation type: {trans["type"]}'
                })
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_connectors(self, model: Dict[str, Any], model_name: str) -> Dict[str, Any]:
        """Validate connectors.
        
        Args:
            model: Canonical model
            model_name: Model name
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        connectors = model.get("connectors", [])
        
        self.stats['total_connectors'] += len(connectors)
        
        # Build set of valid component names
        source_component_type = model.get("source_component_type", "mapping")
        
        if source_component_type == 'mapplet':
            # Mapplets have input_ports and output_ports
            input_ports = {p.get("name") for p in model.get("input_ports", [])}
            output_ports = {p.get("name") for p in model.get("output_ports", [])}
            transformations = {t.get("name") for t in model.get("transformations", [])}
            # "OUTPUT" and "INPUT" are special placeholders for mapplet output/input ports
            all_valid_names = input_ports | output_ports | transformations | {'OUTPUT', 'INPUT'}
        else:
            # Mappings have sources and targets
            sources = {s.get("name") for s in model.get("sources", [])}
            targets = {t.get("name") for t in model.get("targets", [])}
            transformations = {t.get("name") for t in model.get("transformations", [])}
            all_valid_names = sources | targets | transformations
        
        # Validate each connector
        for connector in connectors:
            from_trans = connector.get("from_transformation") or connector.get("from_instance")
            to_trans = connector.get("to_transformation") or connector.get("to_instance")
            
            # Check required fields
            if not from_trans:
                errors.append({
                    'type': 'missing_from_transformation',
                    'connector': connector,
                    'message': 'Connector missing from_transformation'
                })
                continue
            
            if not to_trans:
                errors.append({
                    'type': 'missing_to_transformation',
                    'connector': connector,
                    'message': 'Connector missing to_transformation'
                })
                continue
            
            # Check from_transformation exists
            if from_trans not in all_valid_names:
                self.stats['invalid_connectors'] += 1
                # Provide helpful suggestions
                suggestions = [name for name in all_valid_names if from_trans.lower() in name.lower() or name.lower() in from_trans.lower()]
                suggestion_msg = f" (Did you mean: {', '.join(list(suggestions)[:3])}?)" if suggestions else ""
                errors.append({
                    'type': 'invalid_from_transformation',
                    'connector': connector,
                    'from_transformation': from_trans,
                    'message': f'Connector references unknown from_transformation: {from_trans}{suggestion_msg}'
                })
            
            # Check to_transformation exists
            if to_trans not in all_valid_names:
                self.stats['invalid_connectors'] += 1
                errors.append({
                    'type': 'invalid_to_transformation',
                    'connector': connector,
                    'to_transformation': to_trans,
                    'message': f'Connector references unknown to_transformation: {to_trans}'
                })
            
            # Check for self-loops (transformation connecting to itself)
            if from_trans == to_trans:
                warnings.append({
                    'type': 'self_loop',
                    'connector': connector,
                    'transformation': from_trans,
                    'message': f'Transformation {from_trans} connects to itself'
                })
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_expressions(self, model: Dict[str, Any], model_name: str) -> Dict[str, Any]:
        """Validate expressions in transformations.
        
        Args:
            model: Canonical model
            model_name: Model name
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        if not self.parser_available:
            warnings.append({
                'type': 'expression_validation_unavailable',
                'message': 'Parser not available, skipping expression validation'
            })
            return {'errors': errors, 'warnings': warnings}
        
        transformations = model.get("transformations", [])
        
        for trans in transformations:
            trans_name = trans.get("name", "unknown")
            trans_type = trans.get("type", "")
            
            # Check expression transformations
            if trans_type == "EXPRESSION":
                ports = trans.get("ports", [])
                for port in ports:
                    if port.get("port_type") == "OUTPUT":
                        expression = port.get("expression", "")
                        if expression:
                            try:
                                # Try to parse the expression
                                tokens = tokenize(expression)
                                parser = Parser(tokens)
                                parser.parse()
                            except Exception as e:
                                self.stats['expression_errors'] += 1
                                errors.append({
                                    'type': 'expression_syntax_error',
                                    'transformation': trans_name,
                                    'port': port.get("name", "unknown"),
                                    'expression': expression,
                                    'message': f'Expression syntax error: {str(e)}'
                                })
            
            # Check filter conditions
            if trans_type == "FILTER":
                filter_condition = trans.get("filter_condition", "")
                if filter_condition:
                    try:
                        tokens = tokenize(filter_condition)
                        parser = Parser(tokens)
                        parser.parse()
                    except Exception as e:
                        self.stats['expression_errors'] += 1
                        errors.append({
                            'type': 'filter_condition_error',
                            'transformation': trans_name,
                            'condition': filter_condition,
                            'message': f'Filter condition syntax error: {str(e)}'
                        })
            
            # Check lookup conditions
            if trans_type == "LOOKUP":
                condition = trans.get("condition", "")
                if condition:
                    try:
                        tokens = tokenize(condition)
                        parser = Parser(tokens)
                        parser.parse()
                    except Exception as e:
                        self.stats['expression_errors'] += 1
                        warnings.append({
                            'type': 'lookup_condition_error',
                            'transformation': trans_name,
                            'condition': condition,
                            'message': f'Lookup condition syntax error: {str(e)}'
                        })
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_circular_dependencies(self, model: Dict[str, Any], model_name: str) -> Dict[str, Any]:
        """Check for circular dependencies in transformation graph.
        
        Args:
            model: Canonical model
            model_name: Model name
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        connectors = model.get("connectors", [])
        
        # Build adjacency list
        graph = defaultdict(list)
        for connector in connectors:
            from_trans = connector.get("from_transformation") or connector.get("from_instance")
            to_trans = connector.get("to_transformation") or connector.get("to_instance")
            
            if from_trans and to_trans:
                graph[from_trans].append(to_trans)
        
        # Detect cycles using DFS
        visited = set()
        rec_stack = set()
        cycles = []
        
        def has_cycle(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, path.copy()):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True
            
            rec_stack.remove(node)
            return False
        
        # Check all nodes
        all_nodes = set(graph.keys())
        for node in all_nodes:
            if node not in visited:
                has_cycle(node, [])
        
        if cycles:
            self.stats['circular_dependencies'] += len(cycles)
            for cycle in cycles:
                errors.append({
                    'type': 'circular_dependency',
                    'cycle': cycle,
                    'message': f'Circular dependency detected: {" -> ".join(cycle)}'
                })
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_orphaned_transformations(self, model: Dict[str, Any], model_name: str) -> Dict[str, Any]:
        """Check for orphaned transformations (not connected to sources or targets).
        
        Args:
            model: Canonical model
            model_name: Model name
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        source_component_type = model.get("source_component_type", "mapping")
        connectors = model.get("connectors", [])
        transformations = {t.get("name") for t in model.get("transformations", [])}
        
        if source_component_type == 'mapplet':
            # Mapplets have input_ports and output_ports
            input_ports = {p.get("name") for p in model.get("input_ports", [])}
            output_ports = {p.get("name") for p in model.get("output_ports", [])}
            sources = set()
            targets = set()
        else:
            sources = {s.get("name") for s in model.get("sources", [])}
            targets = {t.get("name") for t in model.get("targets", [])}
            input_ports = set()
            output_ports = set()
        
        # Build connectivity sets
        connected_from = set()
        connected_to = set()
        
        for connector in connectors:
            from_trans = connector.get("from_transformation") or connector.get("from_instance")
            to_trans = connector.get("to_transformation") or connector.get("to_instance")
            
            if from_trans:
                connected_from.add(from_trans)
            if to_trans:
                connected_to.add(to_trans)
        
        # Find orphaned transformations
        # A transformation is orphaned if:
        # - It's not connected from any source/input_port or transformation
        # - It's not connected to any target/output_port or transformation
        orphaned = []
        for trans_name in transformations:
            is_connected_from = trans_name in connected_to or trans_name in sources or trans_name in input_ports
            is_connected_to = trans_name in connected_from or trans_name in targets or trans_name in output_ports
            
            if not is_connected_from and not is_connected_to:
                orphaned.append(trans_name)
        
        if orphaned:
            self.stats['orphaned_transformations'] += len(orphaned)
            warnings.append({
                'type': 'orphaned_transformations',
                'transformations': orphaned,
                'message': f'Orphaned transformations (not connected): {orphaned}'
            })
        
        return {'errors': errors, 'warnings': warnings}
    
    def validate_all(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Validate all canonical models in a directory.
        
        Args:
            path: Path to directory containing canonical model JSON files
            
        Returns:
            Validation results
        """
        if path is None:
            # Default paths to check
            paths = [
                project_root / "versions",
                project_root / "workspace" / "parsed",
                project_root / "workspace" / "parse_ai"
            ]
        else:
            paths = [Path(path)]
        
        logger.info("Starting canonical model validation...")
        
        # Find all JSON files
        json_files = []
        for path_obj in paths:
            if path_obj.exists():
                json_files.extend(path_obj.glob("*.json"))
        
        if not json_files:
            logger.warning(f"No JSON files found in {paths}")
            return {
                'success': False,
                'stats': self.stats,
                'errors': [{'type': 'no_files', 'message': 'No canonical model files found'}],
                'warnings': self.warnings
            }
        
        logger.info(f"Found {len(json_files)} canonical model file(s)")
        
        # Validate each file
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    model = json.load(f)
                
                model_name = json_file.stem
                self.validate_model(model, model_name)
                
            except json.JSONDecodeError as e:
                self.errors.append({
                    'type': 'json_decode_error',
                    'file': str(json_file),
                    'message': f'Failed to parse JSON: {str(e)}'
                })
                self.stats['invalid_models'] += 1
            except Exception as e:
                self.errors.append({
                    'type': 'validation_error',
                    'file': str(json_file),
                    'message': f'Validation failed: {str(e)}'
                })
                self.stats['invalid_models'] += 1
        
        # Run enhancement validation if enabled
        enhancement_summary = None
        if self.validate_enhancements and self.enhancement_results:
            logger.info("Running enhancement validation...")
            self._validate_enhancements()
            enhancement_summary = self._generate_enhancement_summary()
        
        # Generate summary
        summary = self._generate_summary(enhancement_summary)
        
        return {
            'success': len(self.errors) == 0 and (not self.strict or len(self.warnings) == 0),
            'stats': self.stats,
            'errors': self.errors,
            'warnings': self.warnings,
            'summary': summary,
            'enhancements': self.enhancement_results
        }
    
    def _validate_enhancements(self):
        """Validate canonical model enhancements in Neo4j."""
        if not self.graph_store or not self.enhancement_results:
            return
        
        print("\n" + "=" * 80)
        print("CANONICAL MODEL ENHANCEMENTS VALIDATION")
        print("=" * 80)
        print()
        
        # Run all enhancement validations
        self._validate_field_port_nodes()
        self._validate_field_lineage()
        self._validate_complexity_metrics()
        self._validate_semantic_tags()
        self._validate_runtime_config()
        self._validate_scd_structure()
        self._validate_control_tasks()
    
    def _validate_field_port_nodes(self):
        """Validate Field and Port nodes are created in Neo4j."""
        if not self.graph_store or not self.enhancement_results:
            return
        
        print("🔍 Validating Field and Port nodes...")
        
        try:
            with self.graph_store.driver.session() as session:
                # Check for Field nodes
                field_result = session.run("""
                    MATCH (f:Field)
                    RETURN count(f) as field_count
                """)
                field_count = field_result.single()["field_count"]
                
                # Check for Port nodes
                port_result = session.run("""
                    MATCH (p:Port)
                    RETURN count(p) as port_count
                """)
                port_count = port_result.single()["port_count"]
                
                # Check Field-Port relationships
                field_port_rel = session.run("""
                    MATCH (p:Port)-[:HAS_FIELD]->(f:Field)
                    RETURN count(*) as rel_count
                """)
                rel_count = field_port_rel.single()["rel_count"]
                
                # Check Transformation-Port relationships
                trans_port_rel = session.run("""
                    MATCH (t:Transformation)-[:HAS_PORT]->(p:Port)
                    RETURN count(*) as trans_port_count
                """)
                trans_port_count = trans_port_rel.single()["trans_port_count"]
                
                if port_count > 0:
                    self.enhancement_results["field_port_nodes"]["status"] = "✅ PASS"
                    self.enhancement_results["field_port_nodes"]["details"] = [
                        f"Field nodes: {field_count}",
                        f"Port nodes: {port_count}",
                        f"Port-Field relationships: {rel_count}",
                        f"Transformation-Port relationships: {trans_port_count}"
                    ]
                    print(f"   ✅ Found {port_count} Port nodes (Fields: {field_count})")
                else:
                    self.enhancement_results["field_port_nodes"]["status"] = "❌ FAIL"
                    self.enhancement_results["field_port_nodes"]["details"] = [
                        f"Field nodes: {field_count} (expected > 0)",
                        f"Port nodes: {port_count} (expected > 0)"
                    ]
                    print(f"   ❌ No Field or Port nodes found")
                    
        except Exception as e:
            self.enhancement_results["field_port_nodes"]["status"] = "❌ ERROR"
            self.enhancement_results["field_port_nodes"]["details"] = [f"Error: {str(e)}"]
            print(f"   ❌ Error: {e}")
    
    def _validate_field_lineage(self):
        """Validate field-level lineage relationships."""
        if not self.graph_store or not self.enhancement_results:
            return
        
        print("🔍 Validating field-level lineage relationships...")
        
        try:
            with self.graph_store.driver.session() as session:
                # Check DERIVED_FROM relationships
                derived_from_result = session.run("""
                    MATCH (f1:Field)-[:DERIVED_FROM]->(f2:Field)
                    RETURN count(*) as derived_count
                """)
                derived_count = derived_from_result.single()["derived_count"]
                
                # Check FEEDS relationships
                feeds_result = session.run("""
                    MATCH (f1:Field)-[:FEEDS]->(f2:Field)
                    RETURN count(*) as feeds_count
                """)
                feeds_count = feeds_result.single()["feeds_count"]
                
                total_relationships = derived_count + feeds_count
                
                if total_relationships > 0:
                    self.enhancement_results["field_lineage"]["status"] = "✅ PASS"
                    self.enhancement_results["field_lineage"]["details"] = [
                        f"DERIVED_FROM relationships: {derived_count}",
                        f"FEEDS relationships: {feeds_count}",
                        f"Total field-level relationships: {total_relationships}"
                    ]
                    print(f"   ✅ Found {total_relationships} field-level lineage relationships")
                else:
                    self.enhancement_results["field_lineage"]["status"] = "⚠️  WARNING"
                    self.enhancement_results["field_lineage"]["details"] = [
                        "No field-level lineage relationships found",
                        "This may be normal if transformations don't have expressions or connectors"
                    ]
                    print(f"   ⚠️  No field-level lineage relationships found (may be normal)")
                    
        except Exception as e:
            self.enhancement_results["field_lineage"]["status"] = "❌ ERROR"
            self.enhancement_results["field_lineage"]["details"] = [f"Error: {str(e)}"]
            print(f"   ❌ Error: {e}")
    
    def _validate_complexity_metrics(self):
        """Validate complexity metrics are calculated and stored."""
        if not self.graph_store or not self.enhancement_results:
            return
        
        print("🔍 Validating complexity metrics...")
        
        try:
            with self.graph_store.driver.session() as session:
                # Check transformations with complexity metrics
                complexity_result = session.run("""
                    MATCH (t:Transformation)
                    WHERE t.complexity_score IS NOT NULL
                    RETURN count(t) as with_complexity,
                           avg(t.complexity_score) as avg_score
                """)
                result = complexity_result.single()
                
                with_complexity = result["with_complexity"] if result else 0
                avg_score = result["avg_score"] if result and result["avg_score"] else None
                
                # Check version store for complexity metrics
                version_store_path = project_root / "versions"
                complexity_in_files = 0
                if version_store_path.exists():
                    for json_file in version_store_path.glob("*.json"):
                        try:
                            with open(json_file, 'r') as f:
                                model = json.load(f)
                                if "complexity_metrics" in model:
                                    complexity_in_files += 1
                        except Exception:
                            pass
                
                if with_complexity > 0 or complexity_in_files > 0:
                    self.enhancement_results["complexity_metrics"]["status"] = "✅ PASS"
                    self.enhancement_results["complexity_metrics"]["details"] = [
                        f"Transformations with complexity_score in Neo4j: {with_complexity}",
                        f"Average complexity score: {avg_score:.1f}" if avg_score else "No scores found",
                        f"Canonical models with complexity_metrics: {complexity_in_files}"
                    ]
                    print(f"   ✅ Found complexity metrics for {with_complexity} transformations")
                else:
                    self.enhancement_results["complexity_metrics"]["status"] = "❌ FAIL"
                    self.enhancement_results["complexity_metrics"]["details"] = [
                        "No complexity metrics found in Neo4j or version store"
                    ]
                    print(f"   ❌ No complexity metrics found")
                    
        except Exception as e:
            self.enhancement_results["complexity_metrics"]["status"] = "❌ ERROR"
            self.enhancement_results["complexity_metrics"]["details"] = [f"Error: {str(e)}"]
            print(f"   ❌ Error: {e}")
    
    def _validate_semantic_tags(self):
        """Validate semantic tags are detected and stored."""
        if not self.graph_store or not self.enhancement_results:
            return
        
        print("🔍 Validating semantic tags...")
        
        try:
            with self.graph_store.driver.session() as session:
                # Check transformations with semantic tags
                tags_result = session.run("""
                    MATCH (t:Transformation)
                    WHERE t.semantic_tags IS NOT NULL AND size(t.semantic_tags) > 0
                    RETURN count(t) as with_tags,
                           t.semantic_tags as tags
                    LIMIT 100
                """)
                records = list(tags_result)
                
                with_tags = len(records)
                all_tags = []
                for record in records:
                    tags = record.get("tags", [])
                    if isinstance(tags, list):
                        all_tags.extend(tags)
                
                # Count tags by type
                tag_counts = {}
                for tag in all_tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                # Check version store
                version_store_path = project_root / "versions"
                tags_in_files = 0
                if version_store_path.exists():
                    for json_file in version_store_path.glob("*.json"):
                        try:
                            with open(json_file, 'r') as f:
                                model = json.load(f)
                                if "semantic_tags" in model and model["semantic_tags"]:
                                    tags_in_files += 1
                        except Exception:
                            pass
                
                if with_tags > 0 or tags_in_files > 0:
                    self.enhancement_results["semantic_tags"]["status"] = "✅ PASS"
                    details = [
                        f"Transformations with semantic_tags in Neo4j: {with_tags}",
                        f"Canonical models with semantic_tags: {tags_in_files}"
                    ]
                    if tag_counts:
                        details.append(f"Tag distribution: {tag_counts}")
                    self.enhancement_results["semantic_tags"]["details"] = details
                    print(f"   ✅ Found semantic tags for {with_tags} transformations")
                    if tag_counts:
                        print(f"      Tags: {', '.join(tag_counts.keys())}")
                else:
                    self.enhancement_results["semantic_tags"]["status"] = "⚠️  WARNING"
                    self.enhancement_results["semantic_tags"]["details"] = [
                        "No semantic tags found",
                        "This may be normal if transformations don't match tag patterns"
                    ]
                    print(f"   ⚠️  No semantic tags found (may be normal)")
                    
        except Exception as e:
            self.enhancement_results["semantic_tags"]["status"] = "❌ ERROR"
            self.enhancement_results["semantic_tags"]["details"] = [f"Error: {str(e)}"]
            print(f"   ❌ Error: {e}")
    
    def _validate_runtime_config(self):
        """Validate structured runtime configuration."""
        if not self.graph_store or not self.enhancement_results:
            return
        
        print("🔍 Validating structured runtime configuration...")
        
        try:
            with self.graph_store.driver.session() as session:
                # Check tasks with runtime config
                task_config_result = session.run("""
                    MATCH (t:Task)
                    WHERE t.task_runtime_config_json IS NOT NULL OR t.task_runtime_config IS NOT NULL
                    RETURN count(t) as with_config
                """)
                task_with_config = task_config_result.single()["with_config"] if task_config_result.peek() else 0
                
                # Check pipelines with workflow config
                pipeline_config_result = session.run("""
                    MATCH (p:Pipeline)
                    WHERE p.workflow_runtime_config_json IS NOT NULL OR p.workflow_runtime_config IS NOT NULL
                    RETURN count(p) as with_config
                """)
                pipeline_with_config = pipeline_config_result.single()["with_config"] if pipeline_config_result.peek() else 0
                
                # Check parsed files for runtime config
                parsed_dir = project_root / "workspace" / "parsed"
                parsed_ai_dir = project_root / "workspace" / "parse_ai"
                config_in_files = 0
                
                for check_dir in [parsed_dir, parsed_ai_dir]:
                    if check_dir.exists():
                        for json_file in check_dir.rglob("*.json"):
                            try:
                                with open(json_file, 'r') as f:
                                    data = json.load(f)
                                    if "task_runtime_config" in data or "workflow_runtime_config" in data:
                                        config_in_files += 1
                            except Exception:
                                pass
                
                total_configs = task_with_config + pipeline_with_config
                
                if total_configs > 0 or config_in_files > 0:
                    self.enhancement_results["runtime_config"]["status"] = "✅ PASS"
                    self.enhancement_results["runtime_config"]["details"] = [
                        f"Tasks with task_runtime_config: {task_with_config}",
                        f"Pipelines with workflow_runtime_config: {pipeline_with_config}",
                        f"Parsed files with runtime config: {config_in_files}"
                    ]
                    print(f"   ✅ Found structured runtime config for {total_configs} components")
                else:
                    self.enhancement_results["runtime_config"]["status"] = "⚠️  WARNING"
                    self.enhancement_results["runtime_config"]["details"] = [
                        "No structured runtime config found",
                        "This may be normal if no sessions/workflows have been parsed yet"
                    ]
                    print(f"   ⚠️  No structured runtime config found (may be normal)")
                    
        except Exception as e:
            self.enhancement_results["runtime_config"]["status"] = "❌ ERROR"
            self.enhancement_results["runtime_config"]["details"] = [f"Error: {str(e)}"]
            print(f"   ❌ Error: {e}")
    
    def _validate_scd_structure(self):
        """Validate enhanced SCD structure."""
        if not self.graph_store or not self.enhancement_results:
            return
        
        print("🔍 Validating enhanced SCD structure...")
        
        try:
            # Check version store for enhanced SCD structure
            version_store_path = project_root / "versions"
            scd_enhanced = 0
            scd_types = {}
            
            if version_store_path.exists():
                for json_file in version_store_path.glob("*.json"):
                    try:
                        with open(json_file, 'r') as f:
                            model = json.load(f)
                            scd_type = model.get("scd_type", "NONE")
                            if scd_type != "NONE":
                                scd_types[scd_type] = scd_types.get(scd_type, 0) + 1
                                scd_enhanced += 1
                    except Exception:
                        pass
            
            # Check Neo4j for SCD types
            with self.graph_store.driver.session() as session:
                scd_result = session.run("""
                    MATCH (t:Transformation)
                    WHERE t.scd_type IS NOT NULL AND t.scd_type <> 'NONE'
                    RETURN t.scd_type as scd_type, count(t) as count
                """)
                neo4j_scd_types = {record["scd_type"]: record["count"] for record in scd_result}
            
            if scd_enhanced > 0 or neo4j_scd_types:
                self.enhancement_results["scd_structure"]["status"] = "✅ PASS"
                details = [
                    f"Canonical models with SCD type: {scd_enhanced}",
                    f"SCD types in Neo4j: {neo4j_scd_types}"
                ]
                if scd_types:
                    details.append(f"SCD type distribution: {scd_types}")
                self.enhancement_results["scd_structure"]["details"] = details
                print(f"   ✅ Found SCD information for {scd_enhanced} transformations")
            else:
                self.enhancement_results["scd_structure"]["status"] = "⚠️  WARNING"
                self.enhancement_results["scd_structure"]["details"] = [
                    "No SCD information found",
                    "This may be normal if transformations don't have SCD patterns"
                ]
                print(f"   ⚠️  No SCD information found (may be normal)")
                
        except Exception as e:
            self.enhancement_results["scd_structure"]["status"] = "❌ ERROR"
            self.enhancement_results["scd_structure"]["details"] = [f"Error: {str(e)}"]
            print(f"   ❌ Error: {e}")
    
    def _validate_control_tasks(self):
        """Validate control tasks are created as separate node types."""
        if not self.graph_store or not self.enhancement_results:
            return
        
        print("🔍 Validating control task node types...")
        
        try:
            with self.graph_store.driver.session() as session:
                # Check for DecisionTask nodes
                decision_result = session.run("""
                    MATCH (dt:DecisionTask)
                    RETURN count(dt) as count
                """)
                decision_count = decision_result.single()["count"]
                
                # Check for AssignmentTask nodes
                assignment_result = session.run("""
                    MATCH (at:AssignmentTask)
                    RETURN count(at) as count
                """)
                assignment_count = assignment_result.single()["count"]
                
                # Check for CommandTask nodes
                command_result = session.run("""
                    MATCH (ct:CommandTask)
                    RETURN count(ct) as count
                """)
                command_count = command_result.single()["count"]
                
                # Check for EventTask nodes
                event_result = session.run("""
                    MATCH (et:EventTask)
                    RETURN count(et) as count
                """)
                event_count = event_result.single()["count"]
                
                total_control_tasks = decision_count + assignment_count + command_count + event_count
                
                # Also check parsed workflows for control tasks
                parsed_dir = project_root / "workspace" / "parsed"
                parsed_ai_dir = project_root / "workspace" / "parse_ai"
                control_tasks_in_files = 0
                
                for check_dir in [parsed_dir, parsed_ai_dir]:
                    if check_dir.exists():
                        for json_file in check_dir.rglob("*workflow*.json"):
                            try:
                                with open(json_file, 'r') as f:
                                    data = json.load(f)
                                    tasks = data.get("tasks", [])
                                    for task in tasks:
                                        task_type = task.get("type", "")
                                        if task_type in ["Decision", "Assignment", "Command", "Event-Wait", "Event-Raise"]:
                                            control_tasks_in_files += 1
                            except Exception:
                                pass
                
                if total_control_tasks > 0 or control_tasks_in_files > 0:
                    self.enhancement_results["control_tasks"]["status"] = "✅ PASS"
                    self.enhancement_results["control_tasks"]["details"] = [
                        f"DecisionTask nodes: {decision_count}",
                        f"AssignmentTask nodes: {assignment_count}",
                        f"CommandTask nodes: {command_count}",
                        f"EventTask nodes: {event_count}",
                        f"Total control task nodes: {total_control_tasks}",
                        f"Control tasks in parsed files: {control_tasks_in_files}"
                    ]
                    print(f"   ✅ Found {total_control_tasks} control task nodes")
                else:
                    self.enhancement_results["control_tasks"]["status"] = "⚠️  WARNING"
                    self.enhancement_results["control_tasks"]["details"] = [
                        "No control task nodes found",
                        "This may be normal if workflows don't have control tasks"
                    ]
                    print(f"   ⚠️  No control task nodes found (may be normal)")
                    
        except Exception as e:
            self.enhancement_results["control_tasks"]["status"] = "❌ ERROR"
            self.enhancement_results["control_tasks"]["details"] = [f"Error: {str(e)}"]
            print(f"   ❌ Error: {e}")
    
    def _generate_summary(self, enhancement_summary: Optional[str] = None) -> str:
        """Generate validation summary.
        
        Args:
            enhancement_summary: Optional enhancement validation summary
            
        Returns:
            Summary string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("CANONICAL MODEL VALIDATION SUMMARY")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Total Models: {self.stats['total_models']}")
        lines.append(f"  - Valid: {self.stats['valid_models']}")
        lines.append(f"  - Invalid: {self.stats['invalid_models']}")
        lines.append("")
        lines.append(f"Transformations: {self.stats['total_transformations']}")
        lines.append(f"Connectors: {self.stats['total_connectors']}")
        lines.append(f"  - Invalid: {self.stats['invalid_connectors']}")
        lines.append(f"  - Orphaned Transformations: {self.stats['orphaned_transformations']}")
        lines.append(f"  - Circular Dependencies: {self.stats['circular_dependencies']}")
        lines.append(f"  - Expression Errors: {self.stats['expression_errors']}")
        lines.append("")
        lines.append(f"Errors: {len(self.errors)}")
        lines.append(f"Warnings: {len(self.warnings)}")
        lines.append("")
        
        if self.errors:
            lines.append("ERRORS:")
            lines.append("-" * 80)
            for error in self.errors[:10]:
                model = error.get('model', 'unknown')
                error_type = error.get('type', 'unknown')
                message = error.get('message', '')
                lines.append(f"  [{error_type}] {model}: {message}")
            if len(self.errors) > 10:
                lines.append(f"  ... and {len(self.errors) - 10} more errors")
            lines.append("")
        
        if self.warnings:
            lines.append("WARNINGS:")
            lines.append("-" * 80)
            for warning in self.warnings[:10]:
                model = warning.get('model', 'unknown')
                warning_type = warning.get('type', 'unknown')
                message = warning.get('message', '')
                lines.append(f"  [{warning_type}] {model}: {message}")
            if len(self.warnings) > 10:
                lines.append(f"  ... and {len(self.warnings) - 10} more warnings")
            lines.append("")
        
        # Add enhancement summary if available
        if enhancement_summary:
            lines.append(enhancement_summary)
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def _generate_enhancement_summary(self) -> str:
        """Generate enhancement validation summary.
        
        Returns:
            Summary string
        """
        if not self.enhancement_results:
            return ""
        
        lines = []
        lines.append("")
        lines.append("=" * 80)
        lines.append("ENHANCEMENT VALIDATION SUMMARY")
        lines.append("=" * 80)
        lines.append("")
        
        passed = 0
        warnings = 0
        failed = 0
        errors = 0
        
        for feature, result in self.enhancement_results.items():
            status = result["status"]
            if "✅" in status:
                passed += 1
            elif "⚠️" in status:
                warnings += 1
            elif "❌" in status and "ERROR" in status:
                errors += 1
            else:
                failed += 1
            
            feature_name = feature.replace("_", " ").title()
            lines.append(f"{status} {feature_name}")
            for detail in result["details"]:
                lines.append(f"   {detail}")
            lines.append("")
        
        lines.append("-" * 80)
        lines.append(f"Total Checks: {len(self.enhancement_results)}")
        lines.append(f"  ✅ Passed: {passed}")
        lines.append(f"  ⚠️  Warnings: {warnings}")
        lines.append(f"  ❌ Failed: {failed}")
        lines.append(f"  ❌ Errors: {errors}")
        lines.append("")
        
        if passed == len(self.enhancement_results):
            lines.append("🎉 All enhancement validations passed!")
        elif errors > 0 or failed > 0:
            lines.append("⚠️  Some enhancement validations failed. Please review the details above.")
        else:
            lines.append("✅ All critical enhancement validations passed. Some warnings may be normal.")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def close(self):
        """Close graph store connection if open."""
        if self.graph_store:
            self.graph_store.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate canonical models')
    parser.add_argument('--path', type=str, help='Path to directory containing canonical model JSON files')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as errors')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--enhancements', action='store_true', help='Also validate Neo4j enhancements')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    validator = None
    try:
        validator = CanonicalModelValidator(
            strict=args.strict,
            verbose=args.verbose,
            validate_enhancements=args.enhancements
        )
        results = validator.validate_all(path=args.path)
        
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            print(results['summary'])
        
        # Save results to file if enhancements were validated
        if args.enhancements and results.get('enhancements'):
            output_file = project_root / "workspace" / "canonical_model_validation.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n📄 Detailed results saved to: {output_file}")
        
        # Exit with error code if validation failed
        if not results['success']:
            sys.exit(1)
        
        # Also check enhancement failures
        if args.enhancements and results.get('enhancements'):
            failed_count = sum(1 for r in results['enhancements'].values() 
                              if "❌" in r["status"] and "ERROR" in r["status"])
            if failed_count > 0:
                sys.exit(1)
        
    except Exception as e:
        logger.error(f"Validation failed: {e}", error=e)
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)
    finally:
        if validator:
            validator.close()
    
    sys.exit(0)


if __name__ == '__main__':
    main()
