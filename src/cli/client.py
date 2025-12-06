"""Hybrid API Client for CLI - Supports both direct and HTTP modes."""
import os
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


def _clean_component_name(name: str) -> str:
    """Clean component name for file/directory naming.
    
    Removes:
    - Prefixes: 'wf_', 's_', 'm_', 'wlt_' (can be multiple, e.g., 's_m_')
    - Suffixes: '_enhanced', 'enhanced_'
    - Converts to lowercase and replaces spaces with underscores
    
    Args:
        name: Component name to clean
        
    Returns:
        Cleaned name
    """
    if not name:
        return name
    
    name_lower = name.lower().replace(" ", "_")
    
    # Remove prefixes (can be multiple, e.g., 's_m_' -> remove both)
    prefixes = ["wf_", "s_m_", "s_", "m_", "wlt_"]
    for prefix in prefixes:
        if name_lower.startswith(prefix):
            name_lower = name_lower[len(prefix):]
            # Continue to check for more prefixes (e.g., after removing 's_', check for 'm_')
            break
    
    # Remove 'enhanced_' prefix
    if name_lower.startswith("enhanced_"):
        name_lower = name_lower[9:]
    
    # Remove '_enhanced' suffix
    if name_lower.endswith("_enhanced"):
        name_lower = name_lower[:-9]
    
    return name_lower


class APIClient:
    """Unified API client supporting direct module calls and HTTP requests."""
    
    def __init__(self, api_url: Optional[str] = None, workspace_dir: str = "workspace"):
        """Initialize API client.
        
        Args:
            api_url: API URL for HTTP mode. If None, uses direct mode.
            workspace_dir: Workspace directory for file operations
        """
        self.mode = "http" if api_url else "direct"
        self.api_url = api_url.rstrip("/") if api_url else None
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Session management: track upload sessions
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._sessions_file = self.workspace_dir / ".sessions.json"
        self._load_sessions()
        
        # Initialize direct mode components
        if self.mode == "direct":
            self._init_direct_mode()
        else:
            logger.info(f"Using HTTP mode with API URL: {self.api_url}")
    
    def _init_direct_mode(self):
        """Initialize direct mode components."""
        try:
            from api.file_manager import file_manager
            from parser import MappingParser, WorkflowParser, SessionParser, WorkletParser, MappletParser
            from normalizer import MappingNormalizer
            from generators import PySparkGenerator, DLTGenerator, SQLGenerator, SpecGenerator, OrchestrationGenerator
            from generators.code_quality_checker import CodeQualityChecker
            from versioning.version_store import VersionStore
            from config import settings
            
            # Initialize graph store if enabled
            self.graph_store = None
            self.graph_queries = None
            if getattr(settings, 'enable_graph_store', False) or os.getenv('ENABLE_GRAPH_STORE', 'false').lower() == 'true':
                try:
                    from graph.graph_store import GraphStore
                    from graph.graph_queries import GraphQueries
                    self.graph_store = GraphStore()
                    self.graph_queries = GraphQueries(self.graph_store)
                except Exception as e:
                    logger.warning(f"Graph store not available: {e}")
            
            self.file_manager = file_manager
            self.parsers = {
                "mapping": MappingParser,
                "workflow": WorkflowParser,
                "session": SessionParser,
                "worklet": WorkletParser,
                "mapplet": MappletParser
            }
            self.normalizer = MappingNormalizer()
            self.generators = {
                "pyspark": PySparkGenerator(),
                "dlt": DLTGenerator(),
                "sql": SQLGenerator(),
                "spec": SpecGenerator(),
                "orchestration": OrchestrationGenerator()
            }
            self.quality_checker = CodeQualityChecker()
            
            # Initialize version store
            graph_first = getattr(settings, 'graph_first', False) or os.getenv('GRAPH_FIRST', 'false').lower() == 'true'
            self.version_store = VersionStore(
                path=str(self.workspace_dir / "versions"),
                graph_store=self.graph_store,
                graph_first=graph_first,
                parsed_dir=self.workspace_dir / "parsed"
            )
            
            # Initialize AI orchestrator
            try:
                from ai_agents import AgentOrchestrator
                self.agent_orchestrator = AgentOrchestrator()
            except ImportError:
                logger.warning("AI agents not available")
                self.agent_orchestrator = None
            
            logger.info("Initialized in direct mode")
        except ImportError as e:
            logger.error(f"Failed to initialize direct mode: {e}")
            raise
    
    def detect_file_type(self, file_path: str) -> str:
        """Detect Informatica file type from content/extension.
        
        Args:
            file_path: Path to XML file
            
        Returns:
            File type: 'mapping', 'workflow', 'session', 'worklet', 'mapplet'
        """
        file_path_obj = Path(file_path)
        filename_lower = file_path_obj.name.lower()
        
        # Check filename patterns
        if 'mapping' in filename_lower or 'm_' in filename_lower:
            return "mapping"
        elif 'workflow' in filename_lower or 'wf_' in filename_lower:
            return "workflow"
        elif 'session' in filename_lower or 's_' in filename_lower:
            return "session"
        elif 'worklet' in filename_lower:
            return "worklet"
        elif 'mapplet' in filename_lower or 'mpl_' in filename_lower:
            return "mapplet"
        
        # Check XML content
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Check root element
            root_tag = root.tag.upper()
            if root_tag == "MAPPING":
                return "mapping"
            elif root_tag == "WORKFLOW":
                return "workflow"
            elif root_tag == "SESSION":
                return "session"
            elif root_tag == "WORKLET":
                return "worklet"
            elif root_tag == "MAPPLET":
                return "mapplet"
        except Exception as e:
            logger.warning(f"Failed to parse XML for type detection: {e}")
        
        # Default to mapping
        return "mapping"
    
    def upload_file(self, file_path: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Upload a single file to workspace/staging.
        
        Args:
            file_path: Path to file to upload
            session_id: Optional session ID to group uploads
            
        Returns:
            Dictionary with file_id and session metadata
        """
        source_path = Path(file_path).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Use workspace/staging directory (like test_flow.py)
        staging_dir = self.workspace_dir / "staging"
        staging_dir.mkdir(parents=True, exist_ok=True)
        staging_dir = staging_dir.resolve()
        
        # Check if file is already in staging directory
        staging_path = staging_dir / source_path.name
        if source_path.resolve() == staging_path.resolve():
            # File is already in staging, use it directly
            logger.debug(f"File already in staging: {source_path}")
        else:
            # Copy file to staging
            import shutil
            shutil.copy2(source_path, staging_path)
        
        if self.mode == "http":
            with open(staging_path, 'rb') as f:
                files = {'file': (staging_path.name, f, 'application/xml')}
                response = requests.post(f"{self.api_url}/api/v1/upload", files=files)
                response.raise_for_status()
                result = response.json()
                
                file_id = result.get("file_id")
                if session_id:
                    if session_id not in self._sessions:
                        self._sessions[session_id] = {"file_ids": [], "created_at": datetime.now().isoformat()}
                    self._sessions[session_id]["file_ids"].append(file_id)
                    self._save_sessions()
                
                return {
                    "file_id": file_id,
                    "session_id": session_id,
                    "filename": result.get("filename"),
                    "file_size": result.get("file_size"),
                    "staging_path": str(staging_path)
                }
        else:
            # Direct mode - save via file_manager for API compatibility
            with open(staging_path, 'rb') as f:
                content = f.read()
            
            metadata = self.file_manager.save_uploaded_file(content, staging_path.name)
            file_id = metadata["file_id"]
            
            if session_id:
                if session_id not in self._sessions:
                    self._sessions[session_id] = {"file_ids": [], "created_at": datetime.now().isoformat()}
                if file_id not in self._sessions[session_id]["file_ids"]:
                    self._sessions[session_id]["file_ids"].append(file_id)
                self._save_sessions()
            
            return {
                "file_id": file_id,
                "session_id": session_id,
                "filename": metadata["filename"],
                "file_size": metadata["file_size"],
                "staging_path": str(staging_path)
            }
    
    def upload_directory(self, directory: str, recursive: bool = False, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Upload all files from a directory to workspace/staging.
        
        Args:
            directory: Directory path
            recursive: Whether to recurse into subdirectories
            session_id: Optional session ID (auto-generated if not provided)
            
        Returns:
            Dictionary with session_id, file_ids, and count
        """
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # Use workspace/staging directory (like test_flow.py)
        staging_dir = self.workspace_dir / "staging"
        staging_dir.mkdir(parents=True, exist_ok=True)
        
        file_ids = []
        uploaded_files = []
        file_paths = []
        
        # Find all XML files
        pattern = "**/*.xml" if recursive else "*.xml"
        xml_files = list(directory_path.glob(pattern))
        
        import shutil
        for xml_file in xml_files:
            try:
                xml_file_path = Path(xml_file).resolve()
                staging_path = staging_dir / xml_file.name
                
                # Only copy if source is different from destination
                if xml_file_path.resolve() != staging_path.resolve():
                    shutil.copy2(xml_file_path, staging_path)
                
                # Also save via file_manager for API compatibility
                result = self.upload_file(str(staging_path), session_id)
                file_ids.append(result["file_id"])
                uploaded_files.append(result["filename"])
                file_paths.append(str(staging_path))
            except Exception as e:
                logger.warning(f"Failed to upload {xml_file}: {e}")
        
        self._sessions[session_id] = {
            "file_ids": file_ids,
            "file_paths": file_paths,
            "staging_dir": str(staging_dir),
            "created_at": datetime.now().isoformat(),
            "files": uploaded_files
        }
        self._save_sessions()
        
        return {
            "session_id": session_id,
            "file_ids": file_ids,
            "count": len(file_ids),
            "files": uploaded_files,
            "staging_dir": str(staging_dir)
        }
    
    def _load_sessions(self):
        """Load sessions from disk."""
        if self._sessions_file.exists():
            try:
                import json
                with open(self._sessions_file, 'r') as f:
                    self._sessions = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load sessions: {e}")
                self._sessions = {}
        else:
            self._sessions = {}
    
    def _save_sessions(self):
        """Save sessions to disk."""
        try:
            import json
            self._sessions_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._sessions_file, 'w') as f:
                json.dump(self._sessions, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save sessions: {e}")
    
    def get_session_files(self, session_id: str) -> List[str]:
        """Get file IDs for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of file IDs
        """
        # Reload sessions in case they were updated
        self._load_sessions()
        
        if session_id in self._sessions:
            file_ids = self._sessions[session_id].get("file_ids", [])
            if file_ids:
                return file_ids
        
        # Fallback: if session not found but we're in direct mode,
        # try to get all recent files (uploaded in last hour) as a workaround
        # This handles cases where session wasn't saved properly
        if self.mode == "direct" and hasattr(self, 'file_manager'):
            try:
                from datetime import datetime, timedelta
                all_files = self.file_manager.list_all_files() if hasattr(self.file_manager, 'list_all_files') else []
                # Get files uploaded in the last hour (as a fallback)
                recent_cutoff = (datetime.now() - timedelta(hours=1)).isoformat()
                recent_files = [
                    f.get('file_id') for f in all_files
                    if f.get('uploaded_at', '') > recent_cutoff
                ]
                if recent_files:
                    logger.info(f"Session '{session_id}' not found, using {len(recent_files)} recent files as fallback")
                    return recent_files
            except Exception as e:
                logger.debug(f"Could not retrieve files from file_manager: {e}")
        
        return []
    
    def parse_file(self, file_type: Optional[str], file_id: Optional[str] = None, 
                   file_path: Optional[str] = None, enhance: bool = False) -> Dict[str, Any]:
        """Parse an Informatica file.
        
        Args:
            file_type: File type (mapping, workflow, etc.) or None for auto-detect
            file_id: File ID from upload
            file_path: File path (alternative to file_id)
            enhance: Whether to enhance with AI
            
        Returns:
            Parsed canonical model
        """
        # Resolve file path
        if file_id:
            if self.mode == "http":
                response = requests.get(f"{self.api_url}/api/v1/files/{file_id}")
                response.raise_for_status()
                file_info = response.json()
                file_path = file_info.get("file_path")
            else:
                file_path = self.file_manager.get_file_path(file_id)
        
        if not file_path or not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_id or file_path}")
        
        # Auto-detect type if not provided
        if not file_type:
            file_type = self.detect_file_type(file_path)
        
        if self.mode == "http":
            # HTTP mode
            parse_endpoint = f"/api/v1/parse/{file_type}"
            payload = {
                "file_path": file_path,
                "enhance_model": enhance
            }
            if file_id:
                payload["file_id"] = file_id
            
            response = requests.post(f"{self.api_url}{parse_endpoint}", json=payload)
            response.raise_for_status()
            return response.json()
        else:
            # Direct mode
            parser_class = self.parsers.get(file_type)
            if not parser_class:
                raise ValueError(f"Unknown file type: {file_type}")
            
            parser = parser_class(file_path)
            raw_data = parser.parse()
            
            # Normalize to canonical model
            if file_type == "mapping":
                canonical_model = self.normalizer.normalize(raw_data)
            else:
                canonical_model = raw_data  # Other types may not need normalization
            
            # Enhance if requested
            if enhance and self.agent_orchestrator:
                try:
                    enhanced = self.agent_orchestrator.enhance_canonical_model(canonical_model)
                    canonical_model = enhanced if enhanced else canonical_model
                except Exception as e:
                    logger.warning(f"AI enhancement failed: {e}")
            
            # Save to version store
            mapping_name = canonical_model.get("transformation_name") or canonical_model.get("name") or Path(file_path).stem
            self.version_store.save(mapping_name, canonical_model)
            
            # Save parsed JSON to workspace/parsed (like test_flow.py)
            parsed_dir = self.workspace_dir / "parsed"
            parsed_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine output filename based on file type
            if file_type == "mapplet":
                output_filename = f"{mapping_name}_mapplet.json"
            elif file_type == "mapping":
                output_filename = f"{mapping_name}_mapping.json"
            elif file_type == "workflow":
                output_filename = f"{mapping_name}_workflow.json"
            elif file_type == "session":
                output_filename = f"{mapping_name}_session.json"
            elif file_type == "worklet":
                output_filename = f"{mapping_name}_worklet.json"
            else:
                output_filename = f"{mapping_name}.json"
            
            output_path = parsed_dir / output_filename
            with open(output_path, 'w') as f:
                json.dump(canonical_model, f, indent=2, default=str)
            logger.info(f"Saved parsed model to: {output_path}")
            
            # Save to graph if enabled (like test_flow.py)
            if self.graph_store:
                try:
                    if file_type == "mapping":
                        self.graph_store.save_transformation(canonical_model)
                    elif file_type == "workflow":
                        self.graph_store.save_pipeline(canonical_model)
                        # Also save file metadata
                        from datetime import datetime
                        file_size = Path(file_path).stat().st_size if Path(file_path).exists() else None
                        self.graph_store.save_file_metadata(
                            component_type="Workflow",
                            component_name=mapping_name,
                            file_path=str(file_path),
                            filename=Path(file_path).name,
                            file_size=file_size,
                            parsed_at=datetime.now().isoformat()
                        )
                    elif file_type == "worklet":
                        # Worklets are saved as sub-pipelines, need workflow context
                        # For now, save without workflow context (will be linked later)
                        logger.debug(f"Worklet {mapping_name} parsed, will be linked to workflow during workflow parsing")
                    elif file_type == "session":
                        # Sessions are saved as tasks, need workflow context
                        # For now, save without workflow context (will be linked later)
                        logger.debug(f"Session {mapping_name} parsed, will be linked to workflow during workflow parsing")
                    elif file_type == "mapplet":
                        self.graph_store.save_reusable_transformation(canonical_model)
                except Exception as e:
                    logger.warning(f"Failed to save {file_type} to graph: {e}")
            
            return {
                "canonical_model": canonical_model,
                "mapping_name": mapping_name,
                "file_type": file_type,
                "output_path": str(output_path)
            }
    
    def parse_session(self, session_id: str, file_type: Optional[str] = None, enhance: bool = False) -> Dict[str, Any]:
        """Parse all files from a session.
        
        Uses workspace/staging directory (like test_flow.py) to find files.
        Falls back to checking session metadata if staging doesn't exist.
        
        Args:
            session_id: Session ID (used for logging, but files are read from workspace/staging)
            file_type: Optional file type filter (or None for all)
            enhance: Whether to enhance with AI
            
        Returns:
            Dictionary with parse results
        """
        # Reload sessions to check for stored file paths
        self._load_sessions()
        
        # Try workspace/staging directory first (like test_flow.py)
        staging_dir = self.workspace_dir / "staging"
        
        if staging_dir.exists() and any(staging_dir.glob("*.xml")):
            logger.info(f"Parsing files from workspace/staging for session: {session_id}")
            return self.parse_directory(str(staging_dir), file_type, recursive=False, enhance=enhance)
        
        # Fallback: check if session has file_paths stored
        if session_id in self._sessions:
            file_paths = self._sessions[session_id].get("file_paths", [])
            if file_paths:
                logger.info(f"Parsing {len(file_paths)} files from session: {session_id}")
                results = {
                    "session_id": session_id,
                    "parsed": [],
                    "failed": []
                }
                for file_path in file_paths:
                    if Path(file_path).exists():
                        try:
                            result = self.parse_file(file_type, file_path=file_path, enhance=enhance)
                            results["parsed"].append(result)
                        except Exception as e:
                            results["failed"].append({
                                "file": file_path,
                                "error": str(e)
                            })
                    else:
                        results["failed"].append({
                            "file": file_path,
                            "error": "File not found"
                        })
                return results
        
        # Last resort: check uploads directory
        from config import settings
        upload_dir = Path(getattr(settings, 'upload_dir', './uploads'))
        if upload_dir.exists() and any(upload_dir.glob("*.xml")):
            logger.info(f"Falling back to uploads directory for session: {session_id}")
            return self.parse_directory(str(upload_dir), file_type, recursive=False, enhance=enhance)
        
        raise FileNotFoundError(
            f"No files found for session '{session_id}'. "
            f"Please ensure files are uploaded to workspace/staging or run upload command first."
        )
    
    def parse_directory(self, directory: str, file_type: Optional[str] = None, 
                       recursive: bool = False, enhance: bool = False) -> Dict[str, Any]:
        """Parse all files from a directory (like test_flow.py).
        
        IMPORTANT: Parses mapplets FIRST so they're available when mappings reference them.
        Order: mapplets → mappings → workflows → sessions → worklets
        
        Args:
            directory: Directory path
            file_type: Optional file type filter (or None for auto-detect each)
            recursive: Whether to recurse into subdirectories
            enhance: Whether to enhance with AI
            
        Returns:
            Dictionary with parse results
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        pattern = "**/*.xml" if recursive else "*.xml"
        xml_files = list(directory_path.glob(pattern))
        
        # Sort files by type priority (like test_flow.py): mapplets first, then mappings, workflows, sessions, worklets
        def get_file_priority(file_path: Path) -> int:
            filename_lower = file_path.name.lower()
            if "mapplet" in filename_lower:
                return 0  # Parse mapplets first
            elif "mapping" in filename_lower:
                return 1
            elif "workflow" in filename_lower:
                return 2
            elif "session" in filename_lower:
                return 3
            elif "worklet" in filename_lower:
                return 4
            else:
                return 5  # Unknown types last
        
        xml_files.sort(key=get_file_priority)
        
        results = {
            "directory": str(directory),
            "parsed": [],
            "failed": []
        }
        
        for xml_file in xml_files:
            try:
                # Auto-detect type for each file if not specified
                detected_type = file_type or self.detect_file_type(str(xml_file))
                result = self.parse_file(detected_type, file_path=str(xml_file), enhance=enhance)
                results["parsed"].append(result)
            except Exception as e:
                results["failed"].append({
                    "file": str(xml_file),
                    "error": str(e)
                })
        
        # Build relationships in Neo4j (like test_flow.py second pass)
        if self.graph_store:
            # Use parsed directory, not source directory
            parsed_dir = Path(self.workspace_dir) / "parsed"
            if parsed_dir.exists():
                self._build_parse_relationships(str(parsed_dir))
            else:
                logger.warning(f"Parsed directory not found: {parsed_dir}, skipping relationship building")
        
        return results
    
    def _build_parse_relationships(self, parsed_dir: str):
        """Build relationships in Neo4j after parsing (like test_flow.py second pass).
        
        Reloads workflow files and links sessions/worklets to workflows.
        
        Args:
            parsed_dir: Directory with parsed JSON files
        """
        if not self.graph_store:
            return
        
        import glob
        import json
        
        logger.info(f"Building relationships in Neo4j from parsed directory: {parsed_dir}")
        
        try:
            # Reload workflow files to build relationships
            workflow_files = glob.glob(os.path.join(parsed_dir, "*_workflow.json"))
            logger.info(f"Found {len(workflow_files)} workflow file(s) in {parsed_dir}")
            
            for workflow_file in workflow_files:
                try:
                    logger.info(f"Processing workflow file: {workflow_file}")
                    with open(workflow_file, 'r') as f:
                        workflow_data = json.load(f)
                    
                    workflow_name = workflow_data.get("name")
                    if not workflow_name:
                        logger.warning(f"Workflow file {workflow_file} has no name, skipping")
                        continue
                    
                    logger.info(f"Processing workflow: {workflow_name}")
                    # Process tasks to link sessions/worklets to workflow
                    tasks = workflow_data.get("tasks", [])
                    logger.info(f"Found {len(tasks)} task(s) in workflow {workflow_name}")
                    for task in tasks:
                        task_name = task.get("name", "")
                        task_type = task.get("type", "")
                        
                        if task_type == "Session" or "Session" in task_type:
                            # Ensure session exists and link to workflow
                            try:
                                # Try to load session data to get mapping name
                                session_file = os.path.join(parsed_dir, f"{task_name}_session.json")
                                session_data = {"name": task_name, "type": task_type, "source_component_type": "session"}
                                mapping_name = None
                                
                                if os.path.exists(session_file):
                                    with open(session_file, 'r') as f:
                                        loaded_session = json.load(f)
                                        session_data["config"] = loaded_session.get("config", {})
                                        session_data["task_runtime_config"] = loaded_session.get("task_runtime_config", {})
                                        
                                        # Try multiple sources for mapping name
                                        mapping_name = (loaded_session.get("mapping") or 
                                                      loaded_session.get("mapping_name") or
                                                      loaded_session.get("transformation_name"))
                                        
                                        # If still not found, check config
                                        if not mapping_name and session_data.get("config"):
                                            mapping_name = session_data["config"].get("Mapping Name")
                                        
                                        # If still not found, check task_runtime_config
                                        if not mapping_name and session_data.get("task_runtime_config"):
                                            other_attrs = session_data["task_runtime_config"].get("other_attributes", {})
                                            mapping_name = other_attrs.get("Mapping Name")
                                
                                # If mapping name not found in session file, try task attributes from workflow
                                if not mapping_name:
                                    task_attrs = task.get("attributes", {})
                                    mapping_name = task_attrs.get("Mapping Name")
                                
                                # If still not found, try name pattern matching
                                if not mapping_name:
                                    if task_name.startswith("S_M_"):
                                        mapping_name = "M_" + task_name[4:]
                                    elif task_name.startswith("S_"):
                                        mapping_name = "M_" + task_name[2:]
                                
                                if mapping_name:
                                    session_data["mapping_name"] = mapping_name
                                    session_data["transformation_name"] = mapping_name
                                    logger.info(f"Found mapping name for session {task_name}: {mapping_name}")
                                else:
                                    logger.warning(f"Could not determine mapping name for session {task_name}")
                                
                                # Save/update session and link to workflow
                                logger.info(f"Saving task {task_name} with transformation_name={mapping_name} to workflow {workflow_name}")
                                self.graph_store.save_task(session_data, workflow_name)
                                logger.info(f"Linked task {task_name} to workflow {workflow_name}")
                            except Exception as e:
                                logger.warning(f"Could not link session {task_name} to workflow {workflow_name}: {e}")
                        
                        elif task_type == "Worklet" or "Worklet" in task_type:
                            worklet_name = task.get("worklet_name") or task_name
                            try:
                                # Try to load worklet data if available
                                worklet_file = os.path.join(parsed_dir, f"{worklet_name}_worklet.json")
                                worklet_data = {}
                                if os.path.exists(worklet_file):
                                    with open(worklet_file, 'r') as f:
                                        worklet_data = json.load(f)
                                
                                # Ensure worklet has a name
                                if not worklet_data.get("name"):
                                    worklet_data["name"] = worklet_name
                                
                                # Save/update worklet and link to workflow
                                # Pass parsed_dir so _create_sub_pipeline_tx can extract mapping names from session files
                                self.graph_store.save_sub_pipeline(worklet_data, workflow_name, parsed_dir)
                                logger.info(f"Linked worklet {worklet_name} to workflow {workflow_name}")
                            except Exception as e:
                                logger.warning(f"Could not link worklet {worklet_name} to workflow {workflow_name}: {e}")
                    
                    logger.debug(f"Built relationships for workflow: {workflow_name}")
                except Exception as e:
                    logger.warning(f"Failed to build relationships for workflow: {e}")
            
            logger.info("Relationship building complete")
        except Exception as e:
            logger.warning(f"Relationship building failed: {e}")
    
    def enhance_model(self, mapping_name: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Enhance canonical model with AI.
        
        Args:
            mapping_name: Mapping name or ID
            output_dir: Output directory (default: workspace/parse_ai)
            
        Returns:
            Enhanced canonical model
        """
        if not self.agent_orchestrator:
            raise RuntimeError("AI orchestrator not available")
        
        # Use workspace/parse_ai directory (like test_flow.py)
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = self.workspace_dir / "parse_ai"
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Try to load from workspace/parsed first, then version store
        parsed_dir = self.workspace_dir / "parsed"
        canonical_model = None
        
        # Try loading from parsed JSON file
        if parsed_dir.exists():
            import glob
            mapping_files = glob.glob(str(parsed_dir / f"*{mapping_name}*.json"))
            if mapping_files:
                with open(mapping_files[0], 'r') as f:
                    canonical_model = json.load(f)
        
        # Fallback to version store
        if not canonical_model:
            canonical_model = self.version_store.load(mapping_name)
        
        if not canonical_model:
            raise ValueError(f"Canonical model not found: {mapping_name}")
        
        # Enhance (try enhance_model first, fallback to enhance_canonical_model)
        try:
            enhanced = self.agent_orchestrator.enhance_model(canonical_model, use_llm=True)
        except (AttributeError, TypeError):
            # Fallback to old method name
            enhanced = self.agent_orchestrator.enhance_canonical_model(canonical_model)
        
        if not enhanced:
            enhanced = canonical_model
        
        # Save enhanced model to workspace/parse_ai
        mapping_name_clean = mapping_name.replace("M_", "").replace(" ", "_")
        output_file = output_path / f"{mapping_name_clean}_enhanced.json"
        with open(output_file, 'w') as f:
            json.dump(enhanced, f, indent=2, default=str)
        
        # Save to version store
        self.version_store.save(mapping_name, enhanced)
        
        # Save to graph store if enabled (canonical model gets pushed after enhance)
        if self.graph_store:
            try:
                # Determine file type from model
                file_type = "mapping"
                if "_mapplet" in str(output_file):
                    file_type = "mapplet"
                elif "_workflow" in str(output_file):
                    file_type = "workflow"
                
                if file_type == "mapping":
                    self.graph_store.save_transformation(enhanced)
                elif file_type == "mapplet":
                    self.graph_store.save_reusable_transformation(enhanced)
            except Exception as e:
                logger.warning(f"Failed to save enhanced model to graph: {e}")
        
        return {
            "mapping_name": mapping_name,
            "enhanced": True,
            "output_file": str(output_file)
        }
    
    def enhance_session(self, session_id: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Enhance all models in a session.
        
        Reads parsed JSON files from workspace/parsed/ directory (like test_flow.py).
        
        Args:
            session_id: Session ID
            output_dir: Output directory (default: workspace/parse_ai)
            
        Returns:
            Dictionary with enhancement results
        """
        # Use workspace/parsed directory (like test_flow.py)
        parsed_dir = self.workspace_dir / "parsed"
        
        if not parsed_dir.exists():
            raise FileNotFoundError(
                f"Parsed directory not found: {parsed_dir}. "
                f"Please parse files first using 'parse --session-id {session_id}'"
            )
        
        # Find all JSON files (mappings, mapplets, workflows, etc.)
        import glob
        json_files = glob.glob(str(parsed_dir / "*.json"))
        
        if not json_files:
            raise ValueError(f"No JSON files found in {parsed_dir}")
        
        logger.info(f"Found {len(json_files)} file(s) for session: {session_id}")
        
        results = {
            "session_id": session_id,
            "enhanced": [],
            "failed": []
        }
        
        for json_file in json_files:
            try:
                # Load canonical model from JSON file
                with open(json_file, 'r') as f:
                    canonical_model = json.load(f)
                
                # Skip non-canonical models (workflows, sessions, worklets)
                filename = Path(json_file).name
                if filename.endswith("_workflow.json") or filename.endswith("_session.json") or filename.endswith("_worklet.json"):
                    # Copy without enhancement
                    if output_dir:
                        output_path = Path(output_dir)
                    else:
                        output_path = self.workspace_dir / "parse_ai"
                    output_path.mkdir(parents=True, exist_ok=True)
                    output_file = output_path / filename
                    with open(output_file, 'w') as f:
                        json.dump(canonical_model, f, indent=2, default=str)
                    results["enhanced"].append({
                        "file": filename,
                        "mapping_name": canonical_model.get("name", filename),
                        "output_file": str(output_file),
                        "enhanced": False
                    })
                    continue
                
                # Extract mapping/mapplet name
                mapping_name = canonical_model.get("transformation_name") or canonical_model.get("mapping_name") or canonical_model.get("name") or Path(json_file).stem.replace("_mapping", "").replace("_mapplet", "")
                
                logger.info(f"Enhancing: {mapping_name}")
                
                # Enhance using the single model method
                result = self.enhance_model(mapping_name, output_dir)
                
                results["enhanced"].append(result)
            except Exception as e:
                logger.error(f"Failed to enhance {json_file}: {e}")
                results["failed"].append({
                    "file": json_file,
                    "error": str(e)
                })
        
        return results
    
    def generate_code(self, code_type: str, mapping_name: str, output_dir: Optional[str] = None,
                      review: bool = False) -> Dict[str, Any]:
        """Generate code from canonical model.
        
        Args:
            code_type: Code type (pyspark, dlt, sql, orchestration, all)
            mapping_name: Mapping name
            output_dir: Output directory (default: workspace/generated)
            review: Whether to review code
            
        Returns:
            Generated code and metadata
        """
        # Load canonical model
        canonical_model = self.version_store.load(mapping_name)
        if not canonical_model:
            raise ValueError(f"Canonical model not found: {mapping_name}")
        
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = self.workspace_dir / "generated"
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        if code_type == "all":
            types_to_generate = ["pyspark", "dlt", "sql"]
        else:
            types_to_generate = [code_type]
        
        for gen_type in types_to_generate:
            if gen_type not in self.generators:
                continue
            
            generator = self.generators[gen_type]
            code = generator.generate(canonical_model)
            
            # Save code
            mapping_name_clean = mapping_name.lower().replace("m_", "").replace(" ", "_")
            if gen_type == "pyspark":
                code_file = output_path / f"{mapping_name_clean}.py"
            elif gen_type == "dlt":
                code_file = output_path / f"{mapping_name_clean}_dlt.py"
            elif gen_type == "sql":
                code_file = output_path / f"{mapping_name_clean}_sql.sql"
            else:
                code_file = output_path / f"{mapping_name_clean}_{gen_type}.py"
            
            with open(code_file, 'w') as f:
                f.write(code)
            
            # Quality check
            quality_result = self.quality_checker.check_code_quality(code, gen_type, canonical_model)
            
            # Review if requested
            review_result = None
            if review and self.agent_orchestrator:
                try:
                    review_result = self.agent_orchestrator.review_code(code, canonical_model)
                except Exception as e:
                    logger.warning(f"Code review failed: {e}")
            
            results[gen_type] = {
                "file": str(code_file),
                "quality_score": quality_result.get("overall_score"),
                "mapping_name": mapping_name,
                "review": review_result
            }
            
            # Save code metadata to graph
            if self.graph_store:
                try:
                    rel_path = os.path.relpath(code_file, Path.cwd())
                    self.graph_store.save_code_metadata(
                        mapping_name=mapping_name,
                        code_type=gen_type,
                        file_path=rel_path,
                        language="python" if gen_type != "sql" else "sql",
                        quality_score=quality_result.get("overall_score")
                    )
                except Exception as e:
                    logger.warning(f"Failed to save code metadata: {e}")
        
        return results
    
    def generate_code_for_session(self, session_id: str, code_type: str = "pyspark",
                                  output_dir: Optional[str] = None, review: bool = False) -> Dict[str, Any]:
        """Generate code for all mappings in a session (workflow-aware, like test_flow.py).
        
        Reads parsed JSON files from workspace/parsed/ directory and organizes by workflow structure.
        Also generates orchestration code for workflows.
        
        Args:
            session_id: Session ID
            code_type: Code type (pyspark, dlt, sql, orchestration, all)
            output_dir: Output directory (default: workspace/generated)
            review: Whether to review code
            
        Returns:
            Dictionary with generation results for all mappings and workflows
        """
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = self.workspace_dir / "generated"
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {
            "session_id": session_id,
            "generated": [],
            "failed": [],
            "workflows": [],
            "shared_code": []
        }
        
        # Try workflow-aware generation if graph store is available
        if self.graph_store and self.graph_queries:
            try:
                # Get all workflows from Neo4j
                workflows = self.graph_queries.list_pipelines()
                
                logger.info(f"Checking for workflows in Neo4j: found {len(workflows)} workflow(s)")
                if workflows:
                    for wf in workflows:
                        logger.info(f"  - {wf['name']} ({wf.get('task_count', 0)} tasks)")
                    
                    logger.info(f"Using workflow-aware generation for {len(workflows)} workflow(s)")
                    result = self._generate_code_workflow_aware(
                        workflows, code_type, output_path, results, review
                    )
                    
                    # Also generate orchestration for standalone sub-pipelines (worklets)
                    self._generate_sub_pipelines_orchestration(code_type, output_path, result)
                    
                    return result
                else:
                    logger.warning("No workflows found in Neo4j - falling back to file-based generation")
                    logger.warning("Hint: Ensure workflows are parsed and saved to Neo4j using 'parse' and 'enhance' commands")
            except Exception as e:
                logger.warning(f"Workflow-aware generation failed: {e}, falling back to file-based")
                import traceback
                logger.debug(traceback.format_exc())
        
        # Fallback: File-based generation (flat structure)
        parsed_dir = self.workspace_dir / "parsed"
        
        if not parsed_dir.exists():
            raise FileNotFoundError(
                f"Parsed directory not found: {parsed_dir}. "
                f"Please parse files first using 'parse --session-id {session_id}'"
            )
        
        # Find all mapping JSON files
        import glob
        mapping_files = glob.glob(str(parsed_dir / "*_mapping.json"))
        
        if not mapping_files:
            raise ValueError(f"No mapping files found in {parsed_dir}")
        
        logger.info(f"Found {len(mapping_files)} mapping file(s) for session: {session_id}")
        
        for mapping_file in mapping_files:
            try:
                # Load canonical model from JSON file
                with open(mapping_file, 'r') as f:
                    canonical_model = json.load(f)
                
                mapping_name = canonical_model.get("transformation_name") or canonical_model.get("name") or Path(mapping_file).stem.replace("_mapping", "")
                
                logger.info(f"Generating code for: {mapping_name}")
                
                # Generate code using the single mapping method
                code_result = self.generate_code(code_type, mapping_name, str(output_path), review)
                
                results["generated"].append({
                    "mapping_name": mapping_name,
                    "file": mapping_file,
                    "results": code_result
                })
            except Exception as e:
                logger.error(f"Failed to generate code for {mapping_file}: {e}")
                results["failed"].append({
                    "file": mapping_file,
                    "error": str(e)
                })
        
        # Generate shared code for mapplets (like test_flow.py)
        self._generate_shared_code_for_session(str(output_path), results)
        
        return results
    
    def _generate_code_workflow_aware(self, workflows: List[Dict[str, Any]], code_type: str,
                                     output_dir: Path, results: Dict[str, Any], review: bool) -> Dict[str, Any]:
        """Generate code organized by workflow structure (like test_flow.py).
        
        Args:
            workflows: List of workflows from graph
            code_type: Code type to generate
            output_dir: Base output directory
            results: Results dictionary to update
            review: Whether to review code
            
        Returns:
            Updated results dictionary
        """
        workflows_dir = output_dir / "workflows"
        shared_dir = output_dir / "shared"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        shared_dir.mkdir(parents=True, exist_ok=True)
        
        # Track all mappings for shared code generation
        all_mappings = {}
        
        for workflow in workflows:
            workflow_name = workflow["name"]
            logger.info(f"Processing workflow: {workflow_name}")
            
            # Get workflow structure
            workflow_structure = self.graph_queries.get_pipeline_structure(workflow_name)
            if not workflow_structure:
                logger.warning(f"Workflow structure not found: {workflow_name}")
                continue
            
            # Create workflow directory
            workflow_dir = workflows_dir / _clean_component_name(workflow_name)
            workflow_dir.mkdir(parents=True, exist_ok=True)
            
            # Process tasks (sessions)
            tasks = workflow_structure.get("tasks", [])
            tasks_dir = workflow_dir / "tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)
            
            for task in tasks:
                task_name = task["name"]
                task_type = task.get("type", "")
                task_source_type = task.get("source_component_type", "")
                
                logger.info(f"  Processing task: {task_name} (type: {task_type})")
                
                task_dir = tasks_dir / _clean_component_name(task_name)
                task_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate session config (like test_flow.py)
                is_session = (task_type == "Session" or "Session" in task_type or 
                             task_source_type == "session")
                if is_session:
                    self._generate_session_config(task, str(task_dir))
                
                # Check if this task is a worklet (sub-pipeline)
                is_worklet = (task_type == "Worklet" or "Worklet" in task_type or 
                             task_source_type == "worklet")
                
                if is_worklet:
                    # Generate orchestration code for worklet (sub-pipeline)
                    logger.info(f"    Generating orchestration for worklet: {task_name}")
                    worklet_structure = self.graph_queries.get_pipeline_structure(task_name)
                    if worklet_structure:
                        # Worklets are stored as SubPipeline, try to get structure
                        # If get_pipeline_structure doesn't work for worklets, try getting sub-pipeline structure
                        worklet_orchestration_dir = task_dir / "orchestration"
                        worklet_orchestration_dir.mkdir(parents=True, exist_ok=True)
                        self._generate_workflow_orchestration(worklet_structure, str(worklet_orchestration_dir))
                    else:
                        # Try to get sub-pipeline structure directly
                        worklet_structure = self._get_sub_pipeline_structure(task_name)
                        if worklet_structure:
                            worklet_orchestration_dir = task_dir / "orchestration"
                            worklet_orchestration_dir.mkdir(parents=True, exist_ok=True)
                            self._generate_workflow_orchestration(worklet_structure, str(worklet_orchestration_dir))
                
                # Process transformations (mappings)
                transformations = task.get("transformations", [])
                transformations_dir = task_dir / "transformations"
                transformations_dir.mkdir(parents=True, exist_ok=True)
                
                for transformation_info in transformations:
                    transformation_name = transformation_info.get("transformation_name") or transformation_info.get("name")
                    if not transformation_name:
                        continue
                    
                    logger.info(f"    Generating code for transformation: {transformation_name}")
                    logger.debug(f"[DEBUG] Loading canonical model for: {transformation_name}")
                    
                    # Load canonical model (VersionStore handles all fallback logic)
                    canonical_model = self.version_store.load(transformation_name)
                    
                    if not canonical_model:
                        logger.warning(f"Canonical model not found: {transformation_name}")
                        continue
                    
                    # Store for shared code generation
                    all_mappings[transformation_name] = canonical_model
                    
                    # Generate code
                    transformation_dir = transformations_dir / _clean_component_name(transformation_name)
                    transformation_dir.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        generator = self.generators.get(code_type)
                        if not generator:
                            logger.warning(f"[DEBUG] Generator not found for code type: {code_type}")
                            continue
                        
                        logger.debug(f"[DEBUG] Calling generator.generate() for {transformation_name}")
                        code = generator.generate(canonical_model)
                        logger.debug(f"[DEBUG] Generator returned code of length: {len(code)} characters")
                        logger.debug(f"[DEBUG] Code preview (first 200 chars): {code[:200]}")
                        
                        code_file = transformation_dir / f"{_clean_component_name(transformation_name)}.py"
                        logger.debug(f"[DEBUG] Writing code to: {code_file}")
                        with open(code_file, 'w') as f:
                            f.write(code)
                        logger.debug(f"[DEBUG] Code written successfully. File size: {code_file.stat().st_size} bytes")
                        
                        # Save code metadata to graph
                        if self.graph_store:
                            try:
                                rel_path = os.path.relpath(code_file, Path.cwd())
                                self.graph_store.save_code_metadata(
                                    mapping_name=transformation_name,
                                    code_type=code_type,
                                    file_path=rel_path,
                                    language="python",
                                    quality_score=None
                                )
                            except Exception as e:
                                logger.warning(f"Failed to save code metadata: {e}")
                        
                        results["generated"].append({
                            "mapping": transformation_name,
                            "type": code_type,
                            "file": str(code_file),
                            "workflow": workflow_name,
                            "task": task_name
                        })
                    except Exception as e:
                        logger.error(f"Failed to generate code for {transformation_name}: {e}")
                        results["failed"].append({
                            "mapping": transformation_name,
                            "type": code_type,
                            "error": str(e),
                            "workflow": workflow_name,
                            "task": task_name
                        })
            
            # Generate workflow orchestration files (pipelines)
            orchestration_dir = workflow_dir / "orchestration"
            orchestration_dir.mkdir(parents=True, exist_ok=True)
            self._generate_workflow_orchestration(workflow_structure, str(orchestration_dir))
            
            # Count tasks and transformations
            total_transformations = sum(
                len(task.get("transformations", []))
                for task in tasks
            )
            results["workflows"].append({
                "name": workflow_name,
                "tasks": len(tasks),
                "transformations": total_transformations
            })
        
        # Generate shared code for mapplets
        self._generate_shared_code_for_session(str(output_dir), results)
        
        # Run validation steps
        try:
            self._run_validation_steps(str(output_dir), results)
        except Exception as e:
            logger.warning(f"Validation steps failed: {e}")
        
        return results
    
    def _run_validation_steps(self, output_dir: str, results: Dict[str, Any]):
        """Run validation steps: traceability and code validation.
        
        Args:
            output_dir: Output directory
            results: Results dictionary to update
        """
        logger.info("Running validation steps...")
        
        try:
            from validation import TraceabilityValidator, CodeValidator, ValidationReportGenerator, LogicValidator, CompletenessValidator
            
            # Step 1: Traceability validation
            logger.info("Step 1: Validating traceability (source components → generated code)...")
            traceability_validator = TraceabilityValidator(
                graph_store=self.graph_store,
                graph_queries=self.graph_queries
            )
            traceability_results = traceability_validator.validate_traceability(
                workspace_dir=str(self.workspace_dir)
            )
            
            # Step 2: Code validation
            logger.info("Step 2: Validating generated code files...")
            code_validator = CodeValidator()
            code_validation_results = code_validator.validate_code_files(
                generated_dir=str(Path(output_dir))
            )
            
            # Step 3: Logic validation (generated code matches source mappings)
            logger.info("Step 3: Validating logic (generated code vs source mappings)...")
            logic_validator = LogicValidator(graph_store=self.graph_store)
            logic_validation_results = logic_validator.validate_generated_code(
                str(self.workspace_dir)
            )
            
            # Step 4: Completeness validation (all transformations implemented)
            logger.info("Step 4: Validating completeness (all transformations implemented)...")
            completeness_validator = CompletenessValidator(graph_store=self.graph_store)
            completeness_validation_results = completeness_validator.validate_completeness(
                str(self.workspace_dir)
            )
            
            # Generate reports
            validation_dir = self.workspace_dir / "validation"
            report_generator = ValidationReportGenerator()
            report_files = report_generator.generate_reports(
                traceability_results=traceability_results,
                code_validation_results=code_validation_results,
                logic_validation_results=logic_validation_results,
                completeness_validation_results=completeness_validation_results,
                output_dir=str(validation_dir)
            )
            
            results["validation"] = {
                "traceability": traceability_results,
                "code_validation": code_validation_results,
                "logic_validation": logic_validation_results,
                "completeness_validation": completeness_validation_results,
                "reports": report_files
            }
            
            logger.info(f"Validation complete. Reports: {report_files['json']}, {report_files['html']}")
            
        except ImportError as e:
            logger.warning(f"Validation modules not available: {e}")
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise
    
    def _generate_sub_pipelines_orchestration(self, code_type: str, output_dir: Path, results: Dict[str, Any]):
        """Generate orchestration code for standalone sub-pipelines (worklets) not part of workflows.
        
        Args:
            code_type: Code type to generate
            output_dir: Base output directory
            results: Results dictionary to update
        """
        if not self.graph_store:
            return
        
        try:
            with self.graph_store.driver.session() as session:
                # Get sub-pipelines that are not contained in any workflow
                sub_pipelines_result = session.run("""
                    MATCH (sp:SubPipeline)
                    WHERE NOT EXISTS((:Pipeline)-[:CONTAINS]->(sp))
                    RETURN sp.name as name
                    ORDER BY sp.name
                """)
                
                sub_pipelines = [record["name"] for record in sub_pipelines_result]
                
                if not sub_pipelines:
                    return
                
                logger.info(f"Found {len(sub_pipelines)} standalone sub-pipeline(s) (worklets)")
                
                workflows_dir = output_dir / "workflows"
                workflows_dir.mkdir(parents=True, exist_ok=True)
                
                for worklet_name in sub_pipelines:
                    logger.info(f"Processing standalone worklet: {worklet_name}")
                    
                    # Get sub-pipeline structure
                    worklet_structure = self._get_sub_pipeline_structure(worklet_name)
                    if not worklet_structure:
                        logger.warning(f"Sub-pipeline structure not found: {worklet_name}")
                        continue
                    
                    # Create worklet directory
                    worklet_dir = workflows_dir / _clean_component_name(worklet_name)
                    worklet_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Generate orchestration code for worklet
                    orchestration_dir = worklet_dir / "orchestration"
                    orchestration_dir.mkdir(parents=True, exist_ok=True)
                    self._generate_workflow_orchestration(worklet_structure, str(orchestration_dir))
                    
                    # Process tasks and transformations in worklet
                    tasks = worklet_structure.get("tasks", [])
                    tasks_dir = worklet_dir / "tasks"
                    tasks_dir.mkdir(parents=True, exist_ok=True)
                    
                    for task in tasks:
                        task_name = task["name"]
                        task_type = task.get("type", "")
                        task_source_type = task.get("source_component_type", "")
                        transformations = task.get("transformations", [])
                        
                        task_dir = tasks_dir / _clean_component_name(task_name)
                        task_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Generate session config for sessions
                        is_session = (task_type == "Session" or "Session" in task_type or 
                                     task_source_type == "session")
                        if is_session:
                            self._generate_session_config(task, str(task_dir))
                        
                        transformations_dir = task_dir / "transformations"
                        transformations_dir.mkdir(parents=True, exist_ok=True)
                        
                        for transformation_info in transformations:
                            transformation_name = transformation_info.get("transformation_name") or transformation_info.get("name")
                            if not transformation_name:
                                continue
                            
                            # Load canonical model and generate code
                            canonical_model = self.version_store.load(transformation_name)
                            if not canonical_model:
                                parsed_dir = self.workspace_dir / "parsed"
                                mapping_file = parsed_dir / f"{transformation_name}_mapping.json"
                                if mapping_file.exists():
                                    with open(mapping_file, 'r') as f:
                                        canonical_model = json.load(f)
                                else:
                                    continue
                            
                            # Generate code
                            generator = self.generators.get(code_type)
                            if generator:
                                try:
                                    code = generator.generate(canonical_model)
                                    transformation_dir = transformations_dir / _clean_component_name(transformation_name)
                                    transformation_dir.mkdir(parents=True, exist_ok=True)
                                    
                                    code_file = transformation_dir / f"{_clean_component_name(transformation_name)}.py"
                                    with open(code_file, 'w') as f:
                                        f.write(code)
                                    
                                    # Save code metadata
                                    if self.graph_store:
                                        try:
                                            rel_path = os.path.relpath(code_file, Path.cwd())
                                            self.graph_store.save_code_metadata(
                                                mapping_name=transformation_name,
                                                code_type=code_type,
                                                file_path=rel_path,
                                                language="python",
                                                quality_score=None
                                            )
                                        except Exception as e:
                                            logger.warning(f"Failed to save code metadata: {e}")
                                    
                                    results["generated"].append({
                                        "mapping": transformation_name,
                                        "type": code_type,
                                        "file": str(code_file),
                                        "workflow": worklet_name,
                                        "task": task_name
                                    })
                                except Exception as e:
                                    logger.error(f"Failed to generate code for {transformation_name}: {e}")
                    
                    results["workflows"].append({
                        "name": worklet_name,
                        "tasks": len(tasks),
                        "transformations": sum(len(t.get("transformations", [])) for t in tasks),
                        "type": "worklet"
                    })
        except Exception as e:
            logger.warning(f"Failed to generate sub-pipelines orchestration: {e}")
    
    def _get_sub_pipeline_structure(self, worklet_name: str) -> Optional[Dict[str, Any]]:
        """Get sub-pipeline (worklet) structure.
        
        Args:
            worklet_name: Worklet name
            
        Returns:
            Sub-pipeline structure dict or None
        """
        if not self.graph_store or not self.graph_queries:
            return None
        
        try:
            with self.graph_store.driver.session() as session:
                # Get sub-pipeline
                sub_pipeline_result = session.run("""
                    MATCH (sp:SubPipeline {name: $name})
                    RETURN sp.name as name, sp.type as type, sp.source_component_type as source_component_type, 
                           properties(sp) as properties
                """, name=worklet_name).single()
                
                if not sub_pipeline_result:
                    return None
                
                sub_pipeline = {
                    "name": sub_pipeline_result["name"],
                    "type": sub_pipeline_result["type"],
                    "source_component_type": sub_pipeline_result.get("source_component_type", "worklet"),
                    "properties": dict(sub_pipeline_result["properties"]) if sub_pipeline_result["properties"] else {}
                }
                
                # Get tasks in sub-pipeline
                tasks_result = session.run("""
                    MATCH (sp:SubPipeline {name: $name})-[:CONTAINS]->(t:Task)
                    RETURN DISTINCT t.name as name, 
                           t.type as type, 
                           t.source_component_type as source_component_type,
                           properties(t) as properties
                    ORDER BY t.name
                """, name=worklet_name)
                
                tasks = []
                for task_record in tasks_result:
                    task_name = task_record["name"]
                    if not task_name:
                        continue
                    
                    task_props = dict(task_record["properties"]) if task_record["properties"] else {}
                    
                    # Get transformations for this task
                    transformations_result = session.run("""
                        MATCH (t:Task {name: $task_name})
                        OPTIONAL MATCH (t)-[:EXECUTES]->(trans:Transformation)
                        WHERE trans.source_component_type = 'mapping' OR trans.source_component_type IS NULL
                        RETURN trans.name as name, 
                               trans.transformation_name as transformation_name,
                               trans.complexity as complexity
                    """, task_name=task_name)
                    
                    transformations = []
                    for trans_record in transformations_result:
                        trans_name = trans_record.get("name")
                        if trans_name:
                            transformation_name = trans_record.get("transformation_name") or trans_name
                            transformations.append({
                                "name": trans_name,
                                "transformation_name": transformation_name,
                                "complexity": trans_record.get("complexity")
                            })
                    
                    tasks.append({
                        "name": task_name,
                        "type": task_record["type"],
                        "source_component_type": task_record.get("source_component_type", "session"),
                        "properties": task_props,
                        "transformations": transformations
                    })
                
                sub_pipeline["tasks"] = tasks
                return sub_pipeline
        except Exception as e:
            logger.warning(f"Failed to get sub-pipeline structure for {worklet_name}: {e}")
            return None
    
    def _generate_session_config(self, session: Dict[str, Any], session_dir: str):
        """Generate session configuration file (like test_flow.py).
        
        Args:
            session: Session dict (task)
            session_dir: Session directory
        """
        config_path = Path(session_dir) / "session_config.json"
        transformations = session.get("transformations", [])
        with open(config_path, 'w') as f:
            json.dump({
                "name": session["name"],
                "type": session.get("type", "SESSION"),
                "source_component_type": session.get("source_component_type", "session"),
                "properties": session.get("properties", {}),
                "transformations": [
                    {
                        "name": t.get("transformation_name") or t.get("name"),
                        "complexity": t.get("complexity")
                    }
                    for t in transformations
                ]
            }, f, indent=2)
        logger.debug(f"Generated session config: {config_path}")
    
    def _generate_workflow_orchestration(self, workflow_structure: Dict[str, Any], orchestration_dir: str):
        """Generate workflow orchestration files (like test_flow.py).
        
        Args:
            workflow_structure: Workflow structure dict
            orchestration_dir: Orchestration directory
        """
        try:
            from generators.orchestration_generator import OrchestrationGenerator
            orchestration_gen = OrchestrationGenerator()
            
            # Generate Airflow DAG
            airflow_dag = orchestration_gen.generate_airflow_dag(workflow_structure)
            airflow_path = Path(orchestration_dir) / "airflow_dag.py"
            with open(airflow_path, 'w') as f:
                f.write(airflow_dag)
            logger.info(f"Generated Airflow DAG: {airflow_path}")
            
            # Save Airflow DAG to Neo4j
            if self.graph_store:
                try:
                    workflow_name = workflow_structure.get("name", "unknown")
                    rel_path = os.path.relpath(airflow_path, Path.cwd())
                    self.graph_store.save_code_metadata(
                        mapping_name=workflow_name,
                        code_type="airflow",
                        file_path=rel_path,
                        language="python",
                        component_type="workflow"
                    )
                except Exception as e:
                    logger.warning(f"Failed to save Airflow DAG metadata: {e}")
            
            # Generate Databricks Workflow
            databricks_workflow = orchestration_gen.generate_databricks_workflow(workflow_structure)
            databricks_path = Path(orchestration_dir) / "databricks_workflow.json"
            with open(databricks_path, 'w') as f:
                json.dump(databricks_workflow, f, indent=2)
            logger.info(f"Generated Databricks Workflow: {databricks_path}")
            
            # Save Databricks Workflow to Neo4j
            if self.graph_store:
                try:
                    workflow_name = workflow_structure.get("name", "unknown")
                    rel_path = os.path.relpath(databricks_path, Path.cwd())
                    self.graph_store.save_code_metadata(
                        mapping_name=workflow_name,
                        code_type="databricks",
                        file_path=rel_path,
                        language="json",
                        component_type="workflow"
                    )
                except Exception as e:
                    logger.warning(f"Failed to save Databricks Workflow metadata: {e}")
            
            # Skip Prefect Flow generation for now (can be enabled later if needed)
            # prefect_flow = orchestration_gen.generate_prefect_flow(workflow_structure)
            # prefect_path = Path(orchestration_dir) / "prefect_flow.py"
            # with open(prefect_path, 'w') as f:
            #     f.write(prefect_flow)
            # logger.info(f"Generated Prefect Flow: {prefect_path}")
            
            # Generate documentation
            docs = orchestration_gen.generate_workflow_documentation(workflow_structure)
            docs_path = Path(orchestration_dir) / "README.md"
            with open(docs_path, 'w') as f:
                f.write(docs)
            logger.info(f"Generated Workflow Documentation: {docs_path}")
            
        except ImportError as e:
            logger.warning(f"Orchestration generator not available: {e}")
        except Exception as e:
            logger.error(f"Failed to generate orchestration code: {e}")
    
    def _generate_shared_code_for_session(self, output_dir: str, results: Dict[str, Any]):
        """Generate shared code for mapplets (like test_flow.py _generate_shared_code).
        
        Args:
            output_dir: Output directory
            results: Results dictionary to update
        """
        shared_dir = Path(output_dir) / "shared"
        shared_dir.mkdir(parents=True, exist_ok=True)
        
        utils_path = shared_dir / "common_utils.py"
        mapplet_functions = []
        
        # Get PySpark generator
        if "pyspark" not in self.generators:
            return
        
        pyspark_generator = self.generators["pyspark"]
        
        # Load mapplets from graph or parsed files
        mapplet_names = []
        
        # Try loading from graph
        if self.graph_store:
            try:
                with self.graph_store.driver.session() as session:
                    result = session.run("""
                        MATCH (rt:ReusableTransformation)
                        RETURN rt.name as name
                        ORDER BY rt.name
                    """)
                    mapplet_names = [record["name"] for record in result]
            except Exception as e:
                logger.warning(f"Failed to load mapplets from graph: {e}")
        
        # Fallback: try to find mapplet files in parsed directory
        if not mapplet_names:
            parsed_dir = self.workspace_dir / "parsed"
            if parsed_dir.exists():
                import glob
                mapplet_files = glob.glob(str(parsed_dir / "*_mapplet.json"))
                mapplet_names = [Path(f).stem.replace("_mapplet", "") for f in mapplet_files]
        
        # Generate function for each mapplet
        for mapplet_name in mapplet_names:
            try:
                # Try to load from version store
                mapplet_data = self.version_store.load(mapplet_name)
                if not mapplet_data:
                    # Try loading from file
                    parsed_dir = self.workspace_dir / "parsed"
                    mapplet_file = parsed_dir / f"{mapplet_name}_mapplet.json"
                    if mapplet_file.exists():
                        with open(mapplet_file, 'r') as f:
                            mapplet_data = json.load(f)
                
                if mapplet_data:
                    # Generate function code
                    function_lines = pyspark_generator.generate_mapplet_function(mapplet_data)
                    mapplet_functions.extend(function_lines)
                    logger.info(f"Generated function for mapplet: {mapplet_name}")
            except Exception as e:
                logger.warning(f"Failed to generate function for mapplet {mapplet_name}: {e}")
        
        # Write shared utilities file
        with open(utils_path, 'w') as f:
            f.write('"""Common utilities and reusable functions (mapplets)."""\n')
            f.write('from pyspark.sql import functions as F\n')
            f.write('from pyspark.sql.types import *\n\n')
            f.write('# Mapplet functions (reusable transformations)\n')
            f.write('# This file contains reusable mapplet functions extracted from Informatica mapplets\n\n')
            
            if mapplet_functions:
                f.write('\n'.join(mapplet_functions))
            else:
                f.write('# No mapplets found or mapplet code generation not available\n')
        
        results["shared_code"] = [{"file": str(utils_path), "type": "mapplets"}]
        
        # Save code metadata for mapplets if graph_store is available
        if self.graph_store and mapplet_functions:
            try:
                project_root = Path.cwd()
                abs_path = utils_path.resolve()
                try:
                    rel_path = os.path.relpath(abs_path, project_root)
                except ValueError:
                    rel_path = str(abs_path)
                
                # Save individual mapplet metadata
                for mapplet_name in mapplet_names:
                    try:
                        self.graph_store.save_code_metadata(
                            mapping_name=mapplet_name,
                            code_type="pyspark",
                            file_path=rel_path,
                            language="python",
                            component_type="mapplet"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to save code metadata for mapplet {mapplet_name}: {e}")
            except Exception as e:
                logger.warning(f"Failed to save mapplet code metadata: {e}")
    
    def review_code(self, file_path: str, fix: bool = False) -> Dict[str, Any]:
        """Review generated code with AI.
        
        Args:
            file_path: Path to code file
            fix: Whether to auto-fix issues
            
        Returns:
            Review results
        """
        if not self.agent_orchestrator:
            raise RuntimeError("AI orchestrator not available")
        
        with open(file_path, 'r') as f:
            code = f.read()
        
        # Review
        review_result = self.agent_orchestrator.review_code(code)
        
        # Fix if requested
        fixed_code = None
        if fix and review_result.get("needs_fix"):
            fix_result = self.agent_orchestrator.fix_code(code, review_result.get("issues", []))
            fixed_code = fix_result.get("fixed_code")
            
            if fixed_code:
                # Save fixed code
                fixed_path = Path(file_path).parent / f"{Path(file_path).stem}_fixed{Path(file_path).suffix}"
                with open(fixed_path, 'w') as f:
                    f.write(fixed_code)
        
        return {
            "file": file_path,
            "review": review_result,
            "fixed": fixed_code is not None,
            "fixed_file": str(fixed_path) if fixed_code else None
        }
    
    def review_session(self, session_id: str, fix: bool = False, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Review all generated code for a session.
        
        Args:
            session_id: Session ID
            fix: Whether to auto-fix issues
            output_dir: Output directory (default: workspace/generated_ai)
            
        Returns:
            Dictionary with review results
        """
        # Use workspace/generated directory (like test_flow.py)
        generated_dir = self.workspace_dir / "generated"
        
        if not generated_dir.exists():
            raise FileNotFoundError(
                f"Generated directory not found: {generated_dir}. "
                f"Please generate code first using 'generate-code --session-id {session_id}'"
            )
        
        return self.review_directory(str(generated_dir), fix, output_dir)
    
    def review_directory(self, directory: str, fix: bool = False, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Review all code files in a directory (like test_flow.py).
        
        Preserves directory structure and saves AI review status to Neo4j.
        
        Args:
            directory: Directory path
            fix: Whether to auto-fix issues
            output_dir: Output directory (default: workspace/generated_ai)
            
        Returns:
            Dictionary with review results
        """
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = self.workspace_dir / "generated_ai"
        output_path.mkdir(parents=True, exist_ok=True)
        
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # First, copy ALL files and directories from generated to generated_ai to ensure generated_ai has everything
        # This includes .py, .sql, .json, .yaml, .yml, .md, and any other files, plus empty directories
        import shutil
        logger.info(f"Copying all files and directories from {directory_path} to {output_path}...")
        
        # First, copy all files
        for item in directory_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(directory_path)
                dest_file = output_path / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_file)
                logger.debug(f"Copied file: {rel_path}")
        
        # Then, ensure all directories exist (including empty ones)
        for item in directory_path.rglob("*"):
            if item.is_dir():
                rel_path = item.relative_to(directory_path)
                dest_dir = output_path / rel_path
                dest_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured directory: {rel_path}")
        
        # Find all Python and SQL files for review (like test_flow.py)
        code_files = list(directory_path.rglob("*.py")) + list(directory_path.rglob("*.sql"))
        
        results = {
            "reviewed": [],
            "failed": []
        }
        
        for code_file in code_files:
            rel_path = os.path.relpath(code_file, directory_path)
            try:
                # Read code
                with open(code_file, 'r') as f:
                    code = f.read()
                
                # Review code
                review_result = self.agent_orchestrator.review_code(code)
                
                # Extract AI review score
                ai_review_score = review_result.get("score")
                ai_fixed = False
                
                # Preserve directory structure in output
                rel_dir = os.path.dirname(rel_path)
                if rel_dir:
                    output_subdir = output_path / rel_dir
                    output_subdir.mkdir(parents=True, exist_ok=True)
                else:
                    output_subdir = output_path
                
                # Save review results
                review_filename = f"{code_file.stem}_review.json"
                review_file = output_subdir / review_filename
                with open(review_file, 'w') as f:
                    json.dump(review_result, f, indent=2, default=str)
                
                # Fix code if needed
                fixed_code = code
                needs_fix = review_result.get("needs_fix", False) and review_result.get("issues")
                
                if needs_fix and fix:
                    try:
                        fix_result = self.agent_orchestrator.fix_code(code, review_result.get("issues", []))
                        fixed_code = fix_result.get("fixed_code", code)
                        ai_fixed = True
                    except Exception as e:
                        logger.warning(f"Code fix failed: {e}")
                
                # Save code (fixed or original) preserving structure
                output_file = output_subdir / code_file.name
                with open(output_file, 'w') as f:
                    f.write(fixed_code)
                
                # Save AI review status to Neo4j (like test_flow.py)
                if self.graph_store:
                    try:
                        project_root = Path.cwd()
                        abs_path = os.path.abspath(code_file)
                        try:
                            rel_path_to_save = os.path.relpath(abs_path, project_root)
                        except ValueError:
                            rel_path_to_save = abs_path
                        
                        # Update AI review status
                        self.graph_store.update_ai_review_status(
                            file_path=rel_path_to_save,
                            ai_review_score=ai_review_score,
                            ai_fixed=ai_fixed
                        )
                    except Exception as e:
                        logger.warning(f"Failed to save AI review status to Neo4j: {e}")
                
                results["reviewed"].append({
                    "file": rel_path,
                    "review_file": str(review_file),
                    "output_file": str(output_file),
                    "issues_count": len(review_result.get("issues", [])),
                    "fixed": ai_fixed,
                    "ai_review_score": ai_review_score
                })
            except Exception as e:
                results["failed"].append({
                    "file": rel_path,
                    "error": str(e)
                })
        
        return results
    
    def fix_code(self, file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Fix code issues.
        
        Args:
            file_path: Path to code file
            output_path: Optional output path (default: overwrite)
            
        Returns:
            Fix results
        """
        return self.review_code(file_path, fix=True)
    
    def fix_session(self, session_id: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Fix all generated code for a session.
        
        Args:
            session_id: Session ID
            output_dir: Output directory (default: workspace/generated_ai)
            
        Returns:
            Dictionary with fix results
        """
        return self.review_session(session_id, fix=True, output_dir=output_dir)
    
    def fix_directory(self, directory: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Fix all code files in a directory.
        
        Args:
            directory: Directory path
            output_dir: Output directory (default: workspace/generated_ai)
            
        Returns:
            Dictionary with fix results
        """
        return self.review_directory(directory, fix=True, output_dir=output_dir)
    
    def generate_hierarchy(self, session_id: Optional[str] = None, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Generate component hierarchy/tree structure.
        
        Args:
            session_id: Optional session ID to filter files
            output_dir: Output directory (default: workspace)
            
        Returns:
            Dictionary with hierarchy results
        """
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = self.workspace_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        if self.mode == "http":
            # HTTP mode - use API endpoint
            file_ids_param = ""
            if session_id:
                self._load_sessions()
                if session_id in self._sessions:
                    file_ids = self._sessions[session_id].get("file_ids", [])
                    file_ids_param = ",".join(file_ids)
            
            params = {}
            if file_ids_param:
                params["file_ids"] = file_ids_param
            
            response = requests.get(f"{self.api_url}/api/v1/hierarchy", params=params, timeout=30)
            response.raise_for_status()
            hierarchy_data = response.json()
            
            if hierarchy_data.get("success"):
                hierarchy = hierarchy_data.get("hierarchy", {})
                
                # Save hierarchy
                hierarchy_file = output_path / "hierarchy.json"
                with open(hierarchy_file, 'w') as f:
                    json.dump(hierarchy, f, indent=2, default=str)
                
                # Generate text tree
                tree_file = output_path / "hierarchy_tree.txt"
                self._generate_text_tree(hierarchy, str(tree_file))
                
                return {
                    "success": True,
                    "hierarchy_file": str(hierarchy_file),
                    "tree_file": str(tree_file)
                }
            else:
                return {"success": False, "message": "API returned unsuccessful response"}
        else:
            # Direct mode - use HierarchyBuilder
            try:
                from api.hierarchy_builder import HierarchyBuilder
                
                builder = HierarchyBuilder()
                
                # Get file IDs from session if provided
                file_id_list = None
                if session_id:
                    self._load_sessions()
                    if session_id in self._sessions:
                        file_id_list = self._sessions[session_id].get("file_ids", [])
                
                hierarchy = builder.build_hierarchy_from_files(file_id_list)
                
                # Save hierarchy
                hierarchy_file = output_path / "hierarchy.json"
                with open(hierarchy_file, 'w') as f:
                    json.dump(hierarchy, f, indent=2, default=str)
                
                # Generate text tree
                tree_file = output_path / "hierarchy_tree.txt"
                self._generate_text_tree(hierarchy, str(tree_file))
                
                return {
                    "success": True,
                    "hierarchy_file": str(hierarchy_file),
                    "tree_file": str(tree_file)
                }
            except Exception as e:
                logger.error(f"Hierarchy generation failed: {e}")
                return {"success": False, "error": str(e)}
    
    def _generate_text_tree(self, hierarchy: Dict, output_file: str):
        """Generate text representation of hierarchy tree (like test_flow.py)."""
        nodes = hierarchy.get("nodes", [])
        edges = hierarchy.get("edges", [])
        
        # Build tree structure
        node_map = {node["id"]: node for node in nodes}
        children_map = {}
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source and target:
                if source not in children_map:
                    children_map[source] = []
                children_map[source].append(target)
        
        # Find roots
        has_parent = {edge.get("target") for edge in edges if edge.get("target")}
        roots = [node for node in nodes if node["id"] not in has_parent]
        
        def render_node(node_id, level=0, prefix=""):
            node = node_map.get(node_id)
            if not node:
                return ""
            
            indent = "  " * level
            icon = {"workflow": "🔄", "worklet": "📦", "session": "⚙️", "mapping": "📋"}.get(node.get("type"), "📄")
            label = node.get("data", {}).get("label") or node.get("label") or node_id
            node_type = node.get("type", "unknown")
            
            lines = [f"{prefix}{indent}{icon} {label} ({node_type})"]
            
            children = children_map.get(node_id, [])
            for i, child_id in enumerate(children):
                is_last = i == len(children) - 1
                child_prefix = prefix + ("  " if level > 0 else "") + ("└─ " if is_last else "├─ ")
                lines.extend(render_node(child_id, level + 1, child_prefix).split('\n'))
            
            return '\n'.join(lines)
        
        with open(output_file, 'w') as f:
            f.write("Informatica Hierarchy Tree\n")
            f.write("=" * 60 + "\n\n")
            for root in roots:
                f.write(render_node(root["id"]) + "\n")
    
    def generate_lineage(self, session_id: Optional[str] = None, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Generate workflow DAG/lineage diagrams.
        
        Args:
            session_id: Optional session ID to filter workflows
            output_dir: Output directory (default: workspace)
            
        Returns:
            Dictionary with lineage results
        """
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = self.workspace_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Use workspace/staging directory (like test_flow.py)
        staging_dir = self.workspace_dir / "staging"
        
        if not staging_dir.exists():
            raise FileNotFoundError(
                f"Staging directory not found: {staging_dir}. "
                f"Please upload files first using 'upload --session-id {session_id}'"
            )
        
        # Find workflow files
        import glob
        workflow_files = glob.glob(str(staging_dir / "*workflow*.xml"))
        
        if not workflow_files:
            raise ValueError(f"No workflow files found in {staging_dir}")
        
        results = {
            "generated": [],
            "failed": []
        }
        
        try:
            from parser import WorkflowParser
            from dag import DAGBuilder, DAGVisualizer
        except ImportError as e:
            raise RuntimeError(f"Required modules not available: {e}")
        
        for workflow_file in workflow_files:
            try:
                filename = Path(workflow_file).name
                logger.info(f"Generating lineage for: {filename}")
                
                # Parse workflow
                parser = WorkflowParser(workflow_file)
                workflow_data = parser.parse()
                
                # Build DAG
                dag_builder = DAGBuilder()
                dag = dag_builder.build(workflow_data)
                
                # Visualize
                visualizer = DAGVisualizer()
                
                # Generate Mermaid diagram
                mermaid_file = output_path / f"{Path(workflow_file).stem}_lineage.mermaid"
                mermaid_diagram = visualizer.visualize(dag, format="mermaid")
                with open(mermaid_file, 'w') as f:
                    f.write(mermaid_diagram)
                
                # Generate DOT diagram
                dot_file = output_path / f"{Path(workflow_file).stem}_lineage.dot"
                dot_diagram = visualizer.visualize(dag, format="dot")
                with open(dot_file, 'w') as f:
                    f.write(dot_diagram)
                
                # Generate JSON
                json_file = output_path / f"{Path(workflow_file).stem}_lineage.json"
                with open(json_file, 'w') as f:
                    json.dump(dag, f, indent=2, default=str)
                
                results["generated"].append({
                    "workflow": filename,
                    "mermaid": str(mermaid_file),
                    "dot": str(dot_file),
                    "json": str(json_file)
                })
            except Exception as e:
                logger.error(f"Failed to generate lineage for {workflow_file}: {e}")
                results["failed"].append({
                    "file": workflow_file,
                    "error": str(e)
                })
        
        return results
    
    def generate_diff_reports(self, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Generate diff reports comparing parse vs enhance and generated vs reviewed code.
        
        Args:
            output_dir: Output directory for diff reports (default: workspace/diffs)
            
        Returns:
            Dictionary with diff report file paths
        """
        if output_dir is None:
            output_dir = str(self.workspace_dir / "diffs")
        
        logger.info("Generating diff reports...")
        
        try:
            import sys
            from pathlib import Path
            
            # Import DiffGenerator from scripts/utils
            scripts_utils_path = Path(__file__).parent.parent.parent / "scripts" / "utils"
            if str(scripts_utils_path) not in sys.path:
                sys.path.insert(0, str(scripts_utils_path))
            
            from generate_diff import DiffGenerator
            
            diff_generator = DiffGenerator(workspace_dir=str(self.workspace_dir))
            diff_results = diff_generator.generate_all_diffs(output_dir)
            
            logger.info(f"Diff reports generated in: {output_dir}")
            
            return {
                "success": True,
                "output_dir": output_dir,
                "results": diff_results
            }
            
        except ImportError as e:
            logger.error(f"Failed to import DiffGenerator: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Failed to generate diff reports: {e}")
            return {
                "success": False,
                "error": str(e)
            }

