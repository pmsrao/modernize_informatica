
"""Session Parser - Production Grade (Simplified)"""
import lxml.etree as ET
from utils.logger import get_logger

logger = get_logger(__name__)

class SessionParser:
    def __init__(self, path):
        self.tree = ET.parse(path)
        self.root = self.tree.getroot()

    def parse(self):
        # Try root element first (if it's SESSION), then search
        sess = self.root if self.root.tag == "SESSION" else self.root.find(".//SESSION")
        if sess is None:
            logger.warning(f"SESSION element not found in XML file")
            return {}
        
        session_name = sess.get("NAME")
        mapping_name = sess.get("MAPPINGNAME")
        logger.debug(f"Parsed session: {session_name}, mapping: {mapping_name}")
        
        # Parse attributes
        attributes = {a.get("NAME"): a.get("VALUE") for a in sess.findall(".//ATTRIBUTE")}
        
        # Normalize runtime configuration
        try:
            from normalizer.runtime_config_normalizer import RuntimeConfigNormalizer
            normalizer = RuntimeConfigNormalizer()
            task_runtime_config = normalizer.normalize_task_config(attributes)
        except Exception as e:
            logger.warning(f"Failed to normalize task runtime config: {e}")
            task_runtime_config = {}
        
        return {
            "name": session_name,
            "source_component_type": "session",
            "mapping": mapping_name,
            "mapping_name": mapping_name,  # Add both for compatibility
            "transformation_name": mapping_name,  # Generic term
            "config": attributes,  # Keep raw config for backward compatibility
            "task_runtime_config": task_runtime_config  # Structured config
        }
