"""Workflow Parser - Production Grade"""
import lxml.etree as ET
from utils.logger import get_logger
from utils.exceptions import ParsingError

logger = get_logger(__name__)


class WorkflowParser:
    """Parser for Informatica Workflow XML files."""
    
    def __init__(self, path):
        """Initialize parser with XML file path.
        
        Args:
            path: Path to workflow XML file
        """
        try:
            self.tree = ET.parse(path)
            self.root = self.tree.getroot()
            logger.info(f"Initializing workflow parser for file: {path}")
        except Exception as e:
            logger.error(f"Failed to parse XML file: {path}", error=e)
            raise ParsingError(f"Failed to parse XML file: {path}") from e

    def parse(self):
        """Parse workflow XML and extract workflow structure.
        
        Returns:
            Dictionary with workflow name, tasks, and links
        """
        try:
            # The root element is WORKFLOW, or find it
            wf = self.root if self.root.tag == "WORKFLOW" else self.root.find(".//WORKFLOW")
            
            if wf is None:
                raise ParsingError("WORKFLOW element not found in XML")
            
            workflow_name = wf.get("NAME", "Unknown")
            logger.info(f"Parsing workflow: {workflow_name}")
            
            tasks = []
            links = []
            
            # Parse TASKINSTANCE elements
            for t in wf.findall(".//TASKINSTANCE"):
                task_name = t.get("NAME", "")
                task_type = t.get("TASKTYPE", "")
                worklet_name = t.get("WORKLETNAME", "")
                
                task = {
                    "name": task_name,
                    "type": task_type,
                    "worklet_name": worklet_name if worklet_name else None
                }
                
                # Parse attributes
                attributes = {}
                for attr in t.findall(".//ATTRIBUTE"):
                    attr_name = attr.get("NAME", "")
                    attr_value = attr.get("VALUE", "")
                    attributes[attr_name] = attr_value
                
                if attributes:
                    task["attributes"] = attributes
                
                tasks.append(task)
            
            # Parse CONNECTOR elements (links between tasks)
            for conn in wf.findall(".//CONNECTOR"):
                from_instance = conn.get("FROMINSTANCE", "")
                from_link = conn.get("FROMLINK", "")
                to_instance = conn.get("TOINSTANCE", "")
                to_link = conn.get("TOLINK", "")
                
                link = {
                    "from": from_instance,
                    "to": to_instance,
                    "from_link": from_link,
                    "to_link": to_link
                }
                links.append(link)
            
            # Also check for LINK elements (alternative format)
            for link_elem in wf.findall(".//LINK"):
                from_task = link_elem.get("FROMTASK", "")
                to_task = link_elem.get("TOTASK", "")
                condition = link_elem.get("CONDITION", "")
                
                link = {
                    "from": from_task,
                    "to": to_task,
                    "condition": condition if condition else None
                }
                links.append(link)
            
            result = {
                "name": workflow_name,
                "tasks": tasks,
                "links": links
            }
            
            logger.info(f"Successfully parsed workflow: {workflow_name} - {len(tasks)} tasks, {len(links)} links")
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing workflow", error=e)
            raise ParsingError(f"Failed to parse workflow: {str(e)}") from e
