"""Hybrid API Client for CLI - Supports both direct and HTTP modes."""
import os
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


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
                graph_first=graph_first
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
        """Upload a single file.
        
        Args:
            file_path: Path to file to upload
            session_id: Optional session ID to group uploads
            
        Returns:
            Dictionary with file_id and session metadata
        """
        if self.mode == "http":
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f, 'application/xml')}
                response = requests.post(f"{self.api_url}/api/v1/upload", files=files)
                response.raise_for_status()
                result = response.json()
                
                file_id = result.get("file_id")
                if session_id:
                    if session_id not in self._sessions:
                        self._sessions[session_id] = {"file_ids": [], "created_at": datetime.now().isoformat()}
                    self._sessions[session_id]["file_ids"].append(file_id)
                
                return {
                    "file_id": file_id,
                    "session_id": session_id,
                    "filename": result.get("filename"),
                    "file_size": result.get("file_size")
                }
        else:
            # Direct mode
            with open(file_path, 'rb') as f:
                content = f.read()
            
            metadata = self.file_manager.save_uploaded_file(content, Path(file_path).name)
            file_id = metadata["file_id"]
            
            if session_id:
                if session_id not in self._sessions:
                    self._sessions[session_id] = {"file_ids": [], "created_at": datetime.now().isoformat()}
                self._sessions[session_id]["file_ids"].append(file_id)
            
            return {
                "file_id": file_id,
                "session_id": session_id,
                "filename": metadata["filename"],
                "file_size": metadata["file_size"]
            }
    
    def upload_directory(self, directory: str, recursive: bool = False, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Upload all files from a directory.
        
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
        
        file_ids = []
        uploaded_files = []
        
        # Find all XML files
        pattern = "**/*.xml" if recursive else "*.xml"
        xml_files = list(directory_path.glob(pattern))
        
        for xml_file in xml_files:
            try:
                result = self.upload_file(str(xml_file), session_id)
                file_ids.append(result["file_id"])
                uploaded_files.append(result["filename"])
            except Exception as e:
                logger.warning(f"Failed to upload {xml_file}: {e}")
        
        self._sessions[session_id] = {
            "file_ids": file_ids,
            "created_at": datetime.now().isoformat(),
            "files": uploaded_files
        }
        
        return {
            "session_id": session_id,
            "file_ids": file_ids,
            "count": len(file_ids),
            "files": uploaded_files
        }
    
    def get_session_files(self, session_id: str) -> List[str]:
        """Get file IDs for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of file IDs
        """
        if session_id in self._sessions:
            return self._sessions[session_id]["file_ids"]
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
            
            # Save to graph if enabled
            if self.graph_store and file_type == "mapping":
                try:
                    self.graph_store.save_transformation(canonical_model)
                except Exception as e:
                    logger.warning(f"Failed to save to graph: {e}")
            
            return {
                "canonical_model": canonical_model,
                "mapping_name": mapping_name,
                "file_type": file_type
            }
    
    def parse_session(self, session_id: str, file_type: Optional[str] = None, enhance: bool = False) -> Dict[str, Any]:
        """Parse all files from a session.
        
        Args:
            session_id: Session ID
            file_type: Optional file type filter (or None for all)
            enhance: Whether to enhance with AI
            
        Returns:
            Dictionary with parse results
        """
        file_ids = self.get_session_files(session_id)
        if not file_ids:
            raise ValueError(f"No files found for session: {session_id}")
        
        results = {
            "session_id": session_id,
            "parsed": [],
            "failed": []
        }
        
        for file_id in file_ids:
            try:
                result = self.parse_file(file_type, file_id=file_id, enhance=enhance)
                results["parsed"].append(result)
            except Exception as e:
                results["failed"].append({
                    "file_id": file_id,
                    "error": str(e)
                })
        
        return results
    
    def parse_directory(self, directory: str, file_type: Optional[str] = None, 
                       recursive: bool = False, enhance: bool = False) -> Dict[str, Any]:
        """Parse all files from a directory.
        
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
        
        return results
    
    def enhance_model(self, mapping_name: str) -> Dict[str, Any]:
        """Enhance canonical model with AI.
        
        Args:
            mapping_name: Mapping name or ID
            
        Returns:
            Enhanced canonical model
        """
        if not self.agent_orchestrator:
            raise RuntimeError("AI orchestrator not available")
        
        # Load canonical model
        canonical_model = self.version_store.load(mapping_name)
        if not canonical_model:
            raise ValueError(f"Canonical model not found: {mapping_name}")
        
        # Enhance
        enhanced = self.agent_orchestrator.enhance_canonical_model(canonical_model)
        if enhanced:
            self.version_store.save(mapping_name, enhanced)
            return {"mapping_name": mapping_name, "enhanced": True, "model": enhanced}
        else:
            return {"mapping_name": mapping_name, "enhanced": False, "model": canonical_model}
    
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
    
    def fix_code(self, file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Fix code issues.
        
        Args:
            file_path: Path to code file
            output_path: Optional output path (default: overwrite)
            
        Returns:
            Fix results
        """
        return self.review_code(file_path, fix=True)

