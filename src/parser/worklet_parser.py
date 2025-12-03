"""Worklet Parser - Production Grade (Simplified)"""
import lxml.etree as ET
from utils.logger import get_logger

logger = get_logger(__name__)

class WorkletParser:
    def __init__(self, path):
        self.tree = ET.parse(path)
        self.root = self.tree.getroot()

    def parse(self):
        """Parse worklet XML and extract worklet structure with tasks.
        
        Returns:
            Dictionary with worklet name and tasks (sessions, etc.)
        """
        # The root element should be WORKLET, or find it
        wk = self.root if self.root.tag == "WORKLET" else self.root.find(".//WORKLET")
        
        if wk is None:
            logger.warning(f"WORKLET element not found in XML file")
            return {}
        
        worklet_name = wk.get("NAME", "unknown")
        logger.debug(f"Parsing worklet: {worklet_name}")
        
        # Extract all TASKINSTANCE elements (these are sessions or other tasks)
        tasks = []
        for t in wk.findall(".//TASKINSTANCE"):
            task_name = t.get("NAME", "")
            task_type = t.get("TASKTYPE", "")
            if task_name:
                tasks.append({
                    "name": task_name,
                    "type": task_type
                })
        
        logger.debug(f"Extracted {len(tasks)} task(s) from worklet {worklet_name}")
        return {
            "name": worklet_name,
            "source_component_type": "worklet",
            "tasks": tasks
        }
