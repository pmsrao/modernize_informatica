"""Version Store — Production Implementation"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from utils.logger import get_logger
from utils.exceptions import ValidationError

logger = get_logger(__name__)


class VersionStore:
    """Stores and retrieves canonical models and parsed data."""
    
    def __init__(self, path: str = "./versions"):
        """Initialize version store.
        
        Args:
            path: Directory path for storing versions
        """
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Version store initialized at: {self.path}")

    def save(self, name: str, model: Dict[str, Any]) -> str:
        """Save model to version store.
        
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
            logger.debug(f"Model saved: {name} -> {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Failed to save model: {name}", error=e)
            raise ValidationError(f"Failed to save model: {str(e)}", field="name")

    def load(self, name: str) -> Optional[Dict[str, Any]]:
        """Load model from version store.
        
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
            logger.debug(f"Model loaded: {name} from {file_path}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {name}", error=e)
            raise ValidationError(f"Failed to load model: {str(e)}", field="name")
    
    def list_all(self) -> list:
        """List all stored models.
        
        Returns:
            List of model names
        """
        models = []
        for file_path in self.path.glob("*.json"):
            model_name = file_path.stem
            models.append(model_name)
        logger.debug(f"Listed {len(models)} models")
        return models
    
    def delete(self, name: str) -> bool:
        """Delete model from version store.
        
        Args:
            name: Model name/identifier
            
        Returns:
            True if deleted, False if not found
        """
        safe_name = name.replace("/", "_").replace("\\", "_")
        file_path = self.path / f"{safe_name}.json"
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            logger.info(f"Model deleted: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete model: {name}", error=e)
            return False
