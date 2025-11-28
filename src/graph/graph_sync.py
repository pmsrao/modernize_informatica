"""Graph Sync — Keep graph and JSON in sync."""
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.graph.graph_store import GraphStore
from src.versioning.version_store import VersionStore
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GraphSync:
    """Synchronizes JSON and graph storage."""
    
    def __init__(self, version_store: VersionStore, graph_store: GraphStore):
        """Initialize sync manager.
        
        Args:
            version_store: VersionStore instance
            graph_store: GraphStore instance
        """
        self.version_store = version_store
        self.graph_store = graph_store
        logger.info("GraphSync initialized")
    
    def sync_all(self) -> Dict[str, Any]:
        """Sync all JSON models to graph.
        
        Returns:
            Sync results
        """
        logger.info("Starting full sync from JSON to graph")
        
        results = {
            "synced": 0,
            "failed": 0,
            "errors": []
        }
        
        for model_name in self.version_store.list_all():
            try:
                model = self.version_store.load(model_name)
                if model:
                    self.graph_store.save_mapping(model)
                    results["synced"] += 1
                    logger.debug(f"Synced: {model_name}")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{model_name}: {str(e)}")
                logger.error(f"Failed to sync {model_name}: {str(e)}")
        
        logger.info(f"Sync completed: {results['synced']} synced, {results['failed']} failed")
        return results
    
    def sync_mapping(self, mapping_name: str) -> bool:
        """Sync a single mapping from JSON to graph.
        
        Args:
            mapping_name: Mapping name to sync
            
        Returns:
            True if synced successfully, False otherwise
        """
        try:
            model = self.version_store.load(mapping_name)
            if model:
                self.graph_store.save_mapping(model)
                logger.info(f"Synced mapping: {mapping_name}")
                return True
            else:
                logger.warning(f"Mapping not found in JSON: {mapping_name}")
                return False
        except Exception as e:
            logger.error(f"Failed to sync mapping {mapping_name}: {str(e)}")
            return False
    
    def verify_sync(self, mapping_name: str) -> bool:
        """Verify that JSON and graph are in sync for a mapping.
        
        Args:
            mapping_name: Mapping name to verify
            
        Returns:
            True if in sync, False otherwise
        """
        json_model = self.version_store.load(mapping_name)
        graph_model = self.graph_store.load_mapping(mapping_name)
        
        if json_model is None and graph_model is None:
            return True  # Both missing (consistent)
        
        if json_model is None or graph_model is None:
            return False  # One missing (out of sync)
        
        # Compare key fields
        return (
            json_model.get("mapping_name") == graph_model.get("mapping_name") and
            len(json_model.get("transformations", [])) == len(graph_model.get("transformations", [])) and
            len(json_model.get("sources", [])) == len(graph_model.get("sources", [])) and
            len(json_model.get("targets", [])) == len(graph_model.get("targets", []))
        )
    
    def verify_all(self) -> Dict[str, Any]:
        """Verify all mappings are in sync.
        
        Returns:
            Verification results
        """
        logger.info("Starting verification of all mappings")
        
        results = {
            "total": 0,
            "in_sync": 0,
            "out_of_sync": 0,
            "missing_in_json": 0,
            "missing_in_graph": 0,
            "errors": []
        }
        
        # Get all JSON mappings
        json_mappings = set(self.version_store.list_all())
        
        # Get all graph mappings
        try:
            graph_mappings = set(self.graph_store.list_all_mappings())
        except Exception as e:
            logger.error(f"Failed to list graph mappings: {str(e)}")
            graph_mappings = set()
        
        # Check all JSON mappings
        for mapping_name in json_mappings:
            results["total"] += 1
            try:
                if self.verify_sync(mapping_name):
                    results["in_sync"] += 1
                else:
                    results["out_of_sync"] += 1
            except Exception as e:
                results["errors"].append(f"{mapping_name}: {str(e)}")
        
        # Check for mappings in graph but not in JSON
        missing_in_json = graph_mappings - json_mappings
        results["missing_in_json"] = len(missing_in_json)
        
        # Check for mappings in JSON but not in graph
        missing_in_graph = json_mappings - graph_mappings
        results["missing_in_graph"] = len(missing_in_graph)
        
        logger.info(f"Verification completed: {results['in_sync']}/{results['total']} in sync")
        return results

