"""Workflow Parser - Production Grade"""
import lxml.etree as ET
from typing import Dict, List, Any, Optional
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
            
            workflow = {
                "name": workflow_name,
                "source_component_type": "workflow",
                "type": "WORKFLOW",
                "tasks": [],
                "links": []
            }
            
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
                
                # Parse task-specific attributes based on type
                if task_type == "Command":
                    task.update(self._parse_command_task(t))
                elif task_type == "Email":
                    task.update(self._parse_email_task(t))
                elif task_type == "Timer":
                    task.update(self._parse_timer_task(t))
                elif task_type == "Decision":
                    task.update(self._parse_decision_task(t))
                elif task_type == "Event-Wait" or task_type == "Event-Raise":
                    task.update(self._parse_event_task(t))
                elif task_type == "Assignment":
                    task.update(self._parse_assignment_task(t))
                elif task_type == "Control":
                    task.update(self._parse_control_task(t))
                
                # Parse general attributes
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
            
            workflow["tasks"] = tasks
            workflow["links"] = links
            
            # Normalize workflow runtime configuration
            workflow_attributes = {}
            for attr in wf.findall(".//ATTRIBUTE"):
                attr_name = attr.get("NAME", "")
                attr_value = attr.get("VALUE", "")
                workflow_attributes[attr_name] = attr_value
            
            if workflow_attributes:
                try:
                    from src.normalizer.runtime_config_normalizer import RuntimeConfigNormalizer
                    normalizer = RuntimeConfigNormalizer()
                    workflow_runtime_config = normalizer.normalize_workflow_config(workflow_attributes, tasks)
                    workflow["workflow_runtime_config"] = workflow_runtime_config
                    workflow["attributes"] = workflow_attributes  # Keep raw for backward compatibility
                except Exception as e:
                    logger.warning(f"Failed to normalize workflow runtime config: {e}")
                    workflow["attributes"] = workflow_attributes
            
            logger.info(f"Successfully parsed workflow: {workflow_name} - {len(tasks)} tasks, {len(links)} links")
            
            return workflow
            
        except Exception as e:
            logger.error(f"Error parsing workflow", error=e)
            raise ParsingError(f"Failed to parse workflow: {str(e)}") from e
    
    def _parse_command_task(self, task_elem) -> Dict[str, Any]:
        """Parse Command task attributes."""
        from parser.xml_utils import get_text
        
        return {
            "command": get_text(task_elem, "COMMAND") or get_text(task_elem, "COMMANDSTRING"),
            "working_directory": get_text(task_elem, "WORKINGDIRECTORY") or get_text(task_elem, "WORKDIR"),
            "success_codes": get_text(task_elem, "SUCCESSCODES") or "0",
            "failure_codes": get_text(task_elem, "FAILURECODES") or "",
            "timeout": get_text(task_elem, "TIMEOUT") or None
        }
    
    def _parse_email_task(self, task_elem) -> Dict[str, Any]:
        """Parse Email task attributes."""
        from parser.xml_utils import get_text
        
        # Parse recipients
        recipients = []
        for recip in task_elem.findall(".//RECIPIENT"):
            recipients.append(recip.get("NAME", "") or get_text(recip, "NAME"))
        
        return {
            "recipients": recipients,
            "subject": get_text(task_elem, "SUBJECT"),
            "body": get_text(task_elem, "BODY") or get_text(task_elem, "MESSAGE"),
            "attachments": [att.get("NAME", "") for att in task_elem.findall(".//ATTACHMENT")],
            "mail_server": get_text(task_elem, "MAILSERVER") or get_text(task_elem, "SMTPHOST")
        }
    
    def _parse_timer_task(self, task_elem) -> Dict[str, Any]:
        """Parse Timer task attributes."""
        from parser.xml_utils import get_text
        
        wait_type = get_text(task_elem, "WAITTYPE") or "Duration"
        wait_value = get_text(task_elem, "WAITVALUE") or get_text(task_elem, "DURATION")
        
        return {
            "wait_type": wait_type,  # Duration, File, Event
            "wait_value": wait_value,  # Duration in seconds or file path or event name
            "file_path": get_text(task_elem, "FILEPATH") if wait_type == "File" else None,
            "event_name": get_text(task_elem, "EVENTNAME") if wait_type == "Event" else None
        }
    
    def _parse_decision_task(self, task_elem) -> Dict[str, Any]:
        """Parse Decision task attributes."""
        from parser.xml_utils import get_text
        
        # Parse decision branches
        branches = []
        for branch in task_elem.findall(".//BRANCH"):
            branches.append({
                "name": branch.get("NAME", ""),
                "condition": get_text(branch, "CONDITION"),
                "link": branch.get("LINK", "")
            })
        
        return {
            "condition": get_text(task_elem, "CONDITION"),
            "branches": branches,
            "default_branch": get_text(task_elem, "DEFAULTBRANCH")
        }
    
    def _parse_event_task(self, task_elem) -> Dict[str, Any]:
        """Parse Event task attributes (Event-Wait or Event-Raise)."""
        from parser.xml_utils import get_text
        
        task_type = task_elem.get("TASKTYPE", "")
        is_wait = "Wait" in task_type
        
        return {
            "event_type": "WAIT" if is_wait else "RAISE",
            "event_name": get_text(task_elem, "EVENTNAME") or get_text(task_elem, "NAME"),
            "wait_timeout": get_text(task_elem, "TIMEOUT") if is_wait else None
        }
    
    def _parse_assignment_task(self, task_elem) -> Dict[str, Any]:
        """Parse Assignment task attributes."""
        from parser.xml_utils import get_text
        
        # Parse variable assignments
        assignments = []
        for assign in task_elem.findall(".//ASSIGNMENT"):
            assignments.append({
                "variable": assign.get("VARIABLE", ""),
                "value": assign.get("VALUE", "") or get_text(assign, "VALUE"),
                "variable_type": assign.get("TYPE", "USER")  # USER, SYSTEM, etc.
            })
        
        return {
            "assignments": assignments
        }
    
    def _parse_control_task(self, task_elem) -> Dict[str, Any]:
        """Parse Control task attributes (Abort, Stop, etc.)."""
        from parser.xml_utils import get_text
        
        task_name = task_elem.get("NAME", "")
        control_type = "ABORT" if "Abort" in task_name else "STOP" if "Stop" in task_name else "CONTROL"
        
        return {
            "control_type": control_type,
            "error_message": get_text(task_elem, "ERRORMESSAGE") or get_text(task_elem, "MESSAGE")
        }
