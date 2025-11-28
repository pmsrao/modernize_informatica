"""Hierarchy Builder - Builds Informatica component hierarchy graph."""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.parser import WorkflowParser, WorkletParser, SessionParser, MappingParser
from src.api.file_manager import file_manager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HierarchyBuilder:
    """Builds Informatica component hierarchy from uploaded files."""
    
    def __init__(self):
        """Initialize hierarchy builder."""
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.worklets: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.mappings: Dict[str, Dict[str, Any]] = {}
        self.file_registry: Dict[str, str] = {}  # file_id -> file_path
    
    def build_hierarchy_from_files(self, file_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Build hierarchy from uploaded files.
        
        Args:
            file_ids: Optional list of file IDs to process. If None, processes all files.
            
        Returns:
            Hierarchy graph with nodes and edges
        """
        logger.info("Building Informatica hierarchy from files")
        
        # Get all files or specific files
        if file_ids:
            files_to_process = []
            for file_id in file_ids:
                metadata = file_manager.get_file_metadata(file_id)
                if metadata:
                    files_to_process.append(metadata)
        else:
            # Get all files
            all_files = file_manager.list_all_files()
            files_to_process = all_files
        
        # Process each file
        for file_meta in files_to_process:
            file_id = file_meta.get("file_id")
            file_path = file_meta.get("file_path")
            file_type = file_meta.get("file_type")
            
            if not file_path or not Path(file_path).exists():
                logger.warning(f"File not found: {file_path}")
                continue
            
            self.file_registry[file_id] = file_path
            
            try:
                if file_type == "workflow":
                    self._parse_workflow(file_id, file_path)
                elif file_type == "worklet":
                    self._parse_worklet(file_id, file_path)
                elif file_type == "session":
                    self._parse_session(file_id, file_path)
                elif file_type == "mapping":
                    self._parse_mapping(file_id, file_path)
            except Exception as e:
                logger.error(f"Failed to parse {file_type} {file_id}: {str(e)}")
        
        # Build relationships
        self._build_relationships()
        
        # Convert to graph format
        return self._to_graph_format()
    
    def _parse_workflow(self, file_id: str, file_path: str):
        """Parse workflow file."""
        try:
            parser = WorkflowParser(file_path)
            workflow_data = parser.parse()
            workflow_name = workflow_data.get("name", "unknown")
            
            self.workflows[workflow_name] = {
                "name": workflow_name,
                "file_id": file_id,
                "file_path": file_path,
                "tasks": workflow_data.get("tasks", []),
                "links": workflow_data.get("links", []),
                "worklets": []
            }
            
            # Extract worklet references
            for task in workflow_data.get("tasks", []):
                if task.get("worklet_name"):
                    self.workflows[workflow_name]["worklets"].append(task["worklet_name"])
            
            logger.debug(f"Parsed workflow: {workflow_name}")
        except Exception as e:
            logger.error(f"Failed to parse workflow {file_path}: {str(e)}")
    
    def _parse_worklet(self, file_id: str, file_path: str):
        """Parse worklet file."""
        try:
            parser = WorkletParser(file_path)
            worklet_data = parser.parse()
            worklet_name = worklet_data.get("name", "unknown")
            
            self.worklets[worklet_name] = {
                "name": worklet_name,
                "file_id": file_id,
                "file_path": file_path,
                "tasks": worklet_data.get("tasks", []),
                "sessions": []
            }
            
            # Extract session references from tasks
            for task in worklet_data.get("tasks", []):
                if task.get("type") == "Session":
                    self.worklets[worklet_name]["sessions"].append(task.get("name", ""))
            
            logger.debug(f"Parsed worklet: {worklet_name}")
        except Exception as e:
            logger.error(f"Failed to parse worklet {file_path}: {str(e)}")
    
    def _parse_session(self, file_id: str, file_path: str):
        """Parse session file."""
        try:
            parser = SessionParser(file_path)
            session_data = parser.parse()
            session_name = session_data.get("name", "unknown")
            mapping_name = session_data.get("mapping")
            
            self.sessions[session_name] = {
                "name": session_name,
                "file_id": file_id,
                "file_path": file_path,
                "mapping_name": mapping_name,
                "config": session_data.get("config", {})
            }
            
            logger.debug(f"Parsed session: {session_name} -> mapping: {mapping_name}")
        except Exception as e:
            logger.error(f"Failed to parse session {file_path}: {str(e)}")
    
    def _parse_mapping(self, file_id: str, file_path: str):
        """Parse mapping file."""
        try:
            parser = MappingParser(file_path)
            mapping_data = parser.parse()
            mapping_name = mapping_data.get("name", "unknown")
            
            self.mappings[mapping_name] = {
                "name": mapping_name,
                "file_id": file_id,
                "file_path": file_path,
                "sources": len(mapping_data.get("sources", [])),
                "targets": len(mapping_data.get("targets", [])),
                "transformations": len(mapping_data.get("transformations", []))
            }
            
            logger.debug(f"Parsed mapping: {mapping_name}")
        except Exception as e:
            logger.error(f"Failed to parse mapping {file_path}: {str(e)}")
    
    def _build_relationships(self):
        """Build relationships between components."""
        # Relationships are already captured during parsing
        # This method can be extended for additional relationship building
        pass
    
    def _to_graph_format(self) -> Dict[str, Any]:
        """Convert hierarchy to graph format for visualization.
        
        Returns:
            Dictionary with nodes and edges
        """
        nodes = []
        edges = []
        
        # Add workflow nodes
        for wf_name, wf_data in self.workflows.items():
            nodes.append({
                "id": f"workflow_{wf_name}",
                "type": "workflow",
                "label": wf_name,
                "data": {
                    "name": wf_name,
                    "file_id": wf_data.get("file_id"),
                    "tasks_count": len(wf_data.get("tasks", []))
                }
            })
            
            # Add edges to worklets
            for worklet_name in wf_data.get("worklets", []):
                if worklet_name in self.worklets:
                    edges.append({
                        "id": f"edge_{wf_name}_to_{worklet_name}",
                        "source": f"workflow_{wf_name}",
                        "target": f"worklet_{worklet_name}",
                        "type": "contains",
                        "label": "CONTAINS"
                    })
            
            # Add edges to sessions (direct sessions in workflow)
            for task in wf_data.get("tasks", []):
                if task.get("type") == "Session":
                    session_name = task.get("name", "")
                    if session_name in self.sessions:
                        edges.append({
                            "id": f"edge_{wf_name}_to_{session_name}",
                            "source": f"workflow_{wf_name}",
                            "target": f"session_{session_name}",
                            "type": "contains",
                            "label": "CONTAINS"
                        })
        
        # Add worklet nodes
        for wl_name, wl_data in self.worklets.items():
            nodes.append({
                "id": f"worklet_{wl_name}",
                "type": "worklet",
                "label": wl_name,
                "data": {
                    "name": wl_name,
                    "file_id": wl_data.get("file_id"),
                    "tasks_count": len(wl_data.get("tasks", []))
                }
            })
            
            # Add edges to sessions
            for session_name in wl_data.get("sessions", []):
                if session_name in self.sessions:
                    edges.append({
                        "id": f"edge_{wl_name}_to_{session_name}",
                        "source": f"worklet_{wl_name}",
                        "target": f"session_{session_name}",
                        "type": "contains",
                        "label": "CONTAINS"
                    })
        
        # Add session nodes
        for sess_name, sess_data in self.sessions.items():
            nodes.append({
                "id": f"session_{sess_name}",
                "type": "session",
                "label": sess_name,
                "data": {
                    "name": sess_name,
                    "file_id": sess_data.get("file_id"),
                    "mapping_name": sess_data.get("mapping_name")
                }
            })
            
            # Add edge to mapping
            mapping_name = sess_data.get("mapping_name")
            if mapping_name and mapping_name in self.mappings:
                edges.append({
                    "id": f"edge_{sess_name}_to_{mapping_name}",
                    "source": f"session_{sess_name}",
                    "target": f"mapping_{mapping_name}",
                    "type": "uses",
                    "label": "USES"
                })
        
        # Add mapping nodes
        for map_name, map_data in self.mappings.items():
            nodes.append({
                "id": f"mapping_{map_name}",
                "type": "mapping",
                "label": map_name,
                "data": {
                    "name": map_name,
                    "file_id": map_data.get("file_id"),
                    "sources_count": map_data.get("sources", 0),
                    "targets_count": map_data.get("targets", 0),
                    "transformations_count": map_data.get("transformations", 0)
                }
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "workflows": len(self.workflows),
                "worklets": len(self.worklets),
                "sessions": len(self.sessions),
                "mappings": len(self.mappings)
            }
        }

