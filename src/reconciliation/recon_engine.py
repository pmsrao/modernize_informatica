"""Reconciliation Engine - Core reconciliation orchestration."""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.reconciliation.data_comparator import DataComparator
from src.reconciliation.report_generator import ReconciliationReportGenerator
from src.utils.logger import get_logger
from src.graph.graph_store import GraphStore
from src.graph.graph_queries import GraphQueries

logger = get_logger(__name__)


class ReconciliationEngine:
    """Orchestrates reconciliation between Informatica source and Databricks target."""
    
    def __init__(self, graph_store: Optional[GraphStore] = None):
        """Initialize reconciliation engine.
        
        Args:
            graph_store: Optional GraphStore instance for accessing mapping metadata
        """
        self.graph_store = graph_store
        self.graph_queries = GraphQueries(graph_store) if graph_store else None
        self.data_comparator = DataComparator()
        self.report_generator = ReconciliationReportGenerator()
        logger.info("ReconciliationEngine initialized")
    
    def reconcile_mapping(self, 
                         mapping_name: str,
                         source_connection: Dict[str, Any],
                         target_connection: Dict[str, Any],
                         comparison_method: str = "count",
                         options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reconcile a single mapping between source and target.
        
        Args:
            mapping_name: Name of the mapping to reconcile
            source_connection: Source connection details (Informatica)
            target_connection: Target connection details (Databricks)
            comparison_method: Method to use ('count', 'hash', 'threshold', 'sampling')
            options: Optional comparison options (threshold, sample_size, etc.)
            
        Returns:
            Reconciliation results dictionary
        """
        logger.info(f"Starting reconciliation for mapping: {mapping_name}")
        
        # Get mapping metadata from graph if available
        mapping_metadata = None
        if self.graph_queries:
            try:
                mappings = self.graph_queries.get_all_mappings_with_metrics()
                mapping_metadata = next((m for m in mappings if m.get('name') == mapping_name), None)
            except Exception as e:
                logger.warning(f"Could not fetch mapping metadata: {e}")
        
        # Get source and target table information
        source_table = self._get_source_table_info(mapping_name, mapping_metadata, source_connection)
        target_table = self._get_target_table_info(mapping_name, mapping_metadata, target_connection)
        
        # Perform comparison based on method
        comparison_options = options or {}
        
        if comparison_method == "count":
            result = self.data_comparator.compare_counts(
                source_table, target_table, **comparison_options
            )
        elif comparison_method == "hash":
            result = self.data_comparator.compare_hash(
                source_table, target_table, **comparison_options
            )
        elif comparison_method == "threshold":
            result = self.data_comparator.compare_with_threshold(
                source_table, target_table, **comparison_options
            )
        elif comparison_method == "sampling":
            result = self.data_comparator.compare_samples(
                source_table, target_table, **comparison_options
            )
        else:
            raise ValueError(f"Unsupported comparison method: {comparison_method}")
        
        # Add metadata
        result['mapping_name'] = mapping_name
        result['comparison_method'] = comparison_method
        result['timestamp'] = datetime.now().isoformat()
        result['source_table'] = source_table.get('table_name')
        result['target_table'] = target_table.get('table_name')
        
        logger.info(f"Reconciliation complete for {mapping_name}: {result.get('status', 'unknown')}")
        return result
    
    def reconcile_workflow(self,
                          workflow_name: str,
                          source_connection: Dict[str, Any],
                          target_connection: Dict[str, Any],
                          comparison_method: str = "count",
                          options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reconcile all mappings in a workflow.
        
        Args:
            workflow_name: Name of the workflow
            source_connection: Source connection details
            target_connection: Target connection details
            comparison_method: Method to use
            options: Optional comparison options
            
        Returns:
            Workflow reconciliation results
        """
        logger.info(f"Starting workflow reconciliation: {workflow_name}")
        
        # Get workflow mappings
        mappings = []
        if self.graph_queries:
            try:
                # Get all workflows and find the one matching workflow_name
                all_workflows = self.graph_queries.get_all_workflows_with_metrics()
                workflow_info = next((w for w in all_workflows if w.get('name') == workflow_name), None)
                
                if workflow_info:
                    # Get sessions for this workflow
                    with self.graph_store.driver.session() as session:
                        result = session.run("""
                            MATCH (w:Workflow {name: $workflow_name})-[:CONTAINS]->(s:Session)-[:EXECUTES]->(m:Mapping)
                            RETURN DISTINCT m.name as mapping_name
                        """, workflow_name=workflow_name)
                        mappings = [record['mapping_name'] for record in result]
            except Exception as e:
                logger.warning(f"Could not fetch workflow mappings: {e}")
        
        if not mappings:
            logger.warning(f"No mappings found for workflow {workflow_name}")
            return {
                'workflow_name': workflow_name,
                'status': 'error',
                'error': 'No mappings found',
                'mappings': []
            }
        
        # Reconcile each mapping
        results = []
        for mapping_name in mappings:
            try:
                result = self.reconcile_mapping(
                    mapping_name, source_connection, target_connection,
                    comparison_method, options
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to reconcile {mapping_name}: {e}")
                results.append({
                    'mapping_name': mapping_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Aggregate workflow results
        total_mappings = len(results)
        passed = sum(1 for r in results if r.get('status') == 'match')
        failed = sum(1 for r in results if r.get('status') == 'mismatch')
        errors = sum(1 for r in results if r.get('status') == 'error')
        
        workflow_result = {
            'workflow_name': workflow_name,
            'status': 'complete' if errors == 0 else 'partial',
            'total_mappings': total_mappings,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'mappings': results,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Workflow reconciliation complete: {workflow_name} - {passed}/{total_mappings} passed")
        return workflow_result
    
    def reconcile_incremental(self,
                             mapping_name: str,
                             source_connection: Dict[str, Any],
                             target_connection: Dict[str, Any],
                             incremental_key: str,
                             start_value: Any,
                             end_value: Any,
                             comparison_method: str = "count",
                             options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reconcile incremental data (for phased migrations).
        
        Args:
            mapping_name: Name of the mapping
            source_connection: Source connection details
            target_connection: Target connection details
            incremental_key: Key column for incremental comparison
            start_value: Start value for incremental range
            end_value: End value for incremental range
            comparison_method: Method to use
            options: Optional comparison options
            
        Returns:
            Incremental reconciliation results
        """
        logger.info(f"Starting incremental reconciliation for {mapping_name}: {incremental_key} between {start_value} and {end_value}")
        
        # Add incremental filter to options
        incremental_options = options or {}
        incremental_options['incremental_key'] = incremental_key
        incremental_options['start_value'] = start_value
        incremental_options['end_value'] = end_value
        
        result = self.reconcile_mapping(
            mapping_name, source_connection, target_connection,
            comparison_method, incremental_options
        )
        
        result['incremental'] = True
        result['incremental_key'] = incremental_key
        result['start_value'] = start_value
        result['end_value'] = end_value
        
        return result
    
    def _get_source_table_info(self, 
                               mapping_name: str,
                               mapping_metadata: Optional[Dict[str, Any]],
                               connection: Dict[str, Any]) -> Dict[str, Any]:
        """Get source table information for reconciliation.
        
        Args:
            mapping_name: Mapping name
            mapping_metadata: Mapping metadata from graph
            connection: Connection details
            
        Returns:
            Source table information dictionary
        """
        # Try to get target table from metadata
        target_name = None
        if mapping_metadata:
            # Extract target table from mapping metadata
            # This would need to be implemented based on actual metadata structure
            pass
        
        # Default: use mapping name as table name hint
        if not target_name:
            target_name = mapping_name.replace('M_', '').replace('m_', '')
        
        return {
            'table_name': target_name,
            'connection': connection,
            'type': 'informatica'
        }
    
    def _get_target_table_info(self,
                               mapping_name: str,
                               mapping_metadata: Optional[Dict[str, Any]],
                               connection: Dict[str, Any]) -> Dict[str, Any]:
        """Get target table information for reconciliation.
        
        Args:
            mapping_name: Mapping name
            mapping_metadata: Mapping metadata from graph
            connection: Connection details
            
        Returns:
            Target table information dictionary
        """
        # Try to get target table from metadata
        target_name = None
        if mapping_metadata:
            # Extract target table from mapping metadata
            # This would need to be implemented based on actual metadata structure
            pass
        
        # Default: use mapping name as table name hint
        if not target_name:
            target_name = mapping_name.replace('M_', '').replace('m_', '')
        
        return {
            'table_name': target_name,
            'connection': connection,
            'type': 'databricks'
        }

