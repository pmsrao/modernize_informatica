"""Version Store — Production Implementation"""
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.utils.logger import get_logger
from src.utils.exceptions import ValidationError

logger = get_logger(__name__)


class VersionStore:
    """Stores and retrieves canonical models and parsed data."""
    
    def __init__(self, path: str = "./versions", 
                 graph_store: Optional[object] = None,
                 graph_first: bool = False):
        """Initialize version store.
        
        Args:
            path: Directory path for storing versions (fallback/export)
            graph_store: Optional GraphStore instance for graph storage
            graph_first: Whether to use graph as primary storage
        """
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.graph_store = graph_store
        self.graph_first = graph_first
        
        if graph_first and not graph_store:
            raise ValueError("graph_store required when graph_first=True")
        
        logger.info(f"Version store initialized at: {self.path}, graph_first={graph_first}")

    def save(self, name: str, model: Dict[str, Any]) -> str:
        """Save model to version store (graph-first or JSON-first).
        
        Args:
            name: Model name/identifier
            model: Model data to save
            
        Returns:
            Path to saved file or mapping name
        """
        if self.graph_first:
            # Save to graph first
            if self.graph_store:
                try:
                    # Determine component type and save accordingly
                    source_component_type = model.get("source_component_type", "")
                    if source_component_type == "mapplet":
                        self.graph_store.save_reusable_transformation(model)
                    elif source_component_type == "mapping" or "transformation_name" in model:
                        self.graph_store.save_transformation(model)
                    else:
                        # Try to save as transformation by default
                        self.graph_store.save_transformation(model)
                    logger.debug(f"Model saved to graph: {name}")
                except Exception as e:
                    logger.error(f"Failed to save to graph: {name}", error=e)
                    raise ValidationError(f"Failed to save to graph: {str(e)}", field="name")
            # Export to JSON for compatibility
            return self._save_json(name, model)
        else:
            # Save to JSON first
            json_path = self._save_json(name, model)
            # Sync to graph if enabled
            if self.graph_store:
                try:
                    # Determine component type and save accordingly
                    source_component_type = model.get("source_component_type", "")
                    if source_component_type == "mapplet":
                        self.graph_store.save_reusable_transformation(model)
                    elif source_component_type == "mapping" or "transformation_name" in model:
                        self.graph_store.save_transformation(model)
                    else:
                        # Try to save as transformation by default
                        self.graph_store.save_transformation(model)
                    logger.debug(f"Model synced to graph: {name}")
                except Exception as e:
                    logger.warning(f"Failed to sync to graph: {str(e)}")
            return json_path
    
    def _save_json(self, name: str, model: Dict[str, Any]) -> str:
        """Save model to JSON file.
        
        Args:
            name: Model name/identifier
            model: Model data to save
            
        Returns:
            Path to saved file
        """
        # Sanitize name for filesystem
        safe_name = name.replace("/", "_").replace("\\", "_")
        file_path = self.path / f"{safe_name}.json"
        
        try:
            with open(file_path, "w") as f:
                json.dump(model, f, indent=2)
            logger.debug(f"Model saved to JSON: {name} -> {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Failed to save model: {name}", error=e)
            raise ValidationError(f"Failed to save model: {str(e)}", field="name")

    def load(self, name: str) -> Optional[Dict[str, Any]]:
        """Load model from version store (graph-first or JSON-first).
        
        Args:
            name: Model name/identifier
            
        Returns:
            Model data or None if not found
        """
        if self.graph_first:
            # Load from graph first
            if self.graph_store:
                try:
                    model = self.graph_store.load_transformation(name)
                    if model:
                        logger.debug(f"Model loaded from graph: {name}")
                        return model
                except Exception as e:
                    logger.warning(f"Failed to load from graph: {str(e)}")
            # Fall back to JSON
            return self._load_json(name)
        else:
            # Load from JSON first
            return self._load_json(name)
    
    def _load_json(self, name: str) -> Optional[Dict[str, Any]]:
        """Load model from JSON file.
        
        Args:
            name: Model name/identifier
            
        Returns:
            Model data or None if not found
        """
        # Sanitize name for filesystem
        safe_name = name.replace("/", "_").replace("\\", "_")
        file_path = self.path / f"{safe_name}.json"
        
        if not file_path.exists():
            logger.warning(f"Model not found: {name} at {file_path}")
            return None
        
        try:
            with open(file_path, "r") as f:
                model = json.load(f)
            logger.debug(f"Model loaded from JSON: {name} from {file_path}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {name}", error=e)
            raise ValidationError(f"Failed to load model: {str(e)}", field="name")
    
    def list_all(self) -> list:
        """List all stored models.
        
        Returns:
            List of model names
        """
        if self.graph_first and self.graph_store:
            # List from graph
            try:
                models = self.graph_store.list_all_mappings()
                logger.debug(f"Listed {len(models)} models from graph")
                return models
            except Exception as e:
                logger.warning(f"Failed to list from graph: {str(e)}, falling back to JSON")
        
        # List from JSON
        models = []
        for file_path in self.path.glob("*.json"):
            model_name = file_path.stem
            models.append(model_name)
        logger.debug(f"Listed {len(models)} models from JSON")
        return models
    
    def delete(self, name: str) -> bool:
        """Delete model from version store.
        
        Args:
            name: Model name/identifier
            
        Returns:
            True if deleted, False if not found
        """
        deleted = False
        
        if self.graph_first and self.graph_store:
            # Delete from graph
            try:
                deleted = self.graph_store.delete_mapping(name)
                if deleted:
                    logger.info(f"Model deleted from graph: {name}")
            except Exception as e:
                logger.warning(f"Failed to delete from graph: {str(e)}")
        
        # Delete from JSON
        safe_name = name.replace("/", "_").replace("\\", "_")
        file_path = self.path / f"{safe_name}.json"
        
        if file_path.exists():
            try:
                file_path.unlink()
                deleted = True
                logger.info(f"Model deleted from JSON: {name}")
            except Exception as e:
                logger.error(f"Failed to delete model from JSON: {name}", error=e)
        
        return deleted
