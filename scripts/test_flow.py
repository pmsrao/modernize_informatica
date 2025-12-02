#!/usr/bin/env python3
"""
Step-by-step testing script for Informatica Modernization flow.

This script provides command-line interface for testing each step of the modernization process:
- Upload files
- Parse mappings
- Enhance with AI
- Generate hierarchy
- Generate lineage
- Generate canonical model images
- Generate code
- Review & fix code
"""
import argparse
import json
import os
import sys
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

try:
    from src.api.file_manager import file_manager
    from parser import MappingParser, WorkflowParser, SessionParser, WorkletParser
    from normalizer import MappingNormalizer
    from generators import PySparkGenerator, DLTGenerator, SQLGenerator
    from dag import DAGBuilder, DAGVisualizer
    from versioning.version_store import VersionStore
    from graph.graph_store import GraphStore
    from graph.graph_queries import GraphQueries
    from src.assessment.profiler import Profiler
    from src.assessment.analyzer import Analyzer
    from src.assessment.wave_planner import WavePlanner
    from src.assessment.report_generator import ReportGenerator
    from config import settings
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root and dependencies are installed.")
    sys.exit(1)


class TestFlow:
    """Test flow orchestrator for step-by-step testing."""
    
    def __init__(self, api_url: str = "http://localhost:8000", use_api: bool = True):
        self.api_url = api_url.rstrip('/')
        self.use_api = use_api
        self.uploaded_files: Dict[str, str] = {}  # filename -> file_id
        self.parsed_mappings: Dict[str, Dict] = {}  # mapping_name -> canonical_model
        
    def upload_files(self, file_paths: List[str], staging_dir: str) -> Dict[str, Any]:
        """Upload files to staging directory and optionally to API.
        
        Args:
            file_paths: List of file paths or glob patterns
            staging_dir: Directory to copy files to
            
        Returns:
            Dictionary with upload results
        """
        print(f"\n{'='*60}")
        print("STEP A: Upload Files")
        print(f"{'='*60}")
        
        # Expand glob patterns
        all_files = []
        for pattern in file_paths:
            if '*' in pattern or '?' in pattern:
                all_files.extend(glob.glob(pattern))
            else:
                all_files.append(pattern)
        
        # Create staging directory
        os.makedirs(staging_dir, exist_ok=True)
        
        results = {
            "uploaded": [],
            "failed": [],
            "file_ids": {}
        }
        
        for file_path in all_files:
            if not os.path.exists(file_path):
                print(f"⚠️  File not found: {file_path}")
                results["failed"].append({"file": file_path, "error": "File not found"})
                continue
            
            filename = os.path.basename(file_path)
            staging_path = os.path.join(staging_dir, filename)
            
            try:
                # Copy to staging
                import shutil
                shutil.copy2(file_path, staging_path)
                print(f"✅ Copied: {filename} -> {staging_path}")
                
                # Upload to API if enabled
                if self.use_api:
                    try:
                        with open(file_path, 'rb') as f:
                            files = {'file': (filename, f, 'application/xml')}
                            response = requests.post(
                                f"{self.api_url}/api/v1/upload",
                                files=files,
                                timeout=30
                            )
                            response.raise_for_status()
                            data = response.json()
                            file_id = data.get("file_id")
                            self.uploaded_files[filename] = file_id
                            results["file_ids"][filename] = file_id
                            print(f"   📤 Uploaded to API: file_id={file_id}")
                    except requests.exceptions.RequestException as e:
                        print(f"   ⚠️  API upload failed: {e}")
                        print(f"   📝 File copied to staging but not uploaded to API")
                
                results["uploaded"].append({
                    "file": filename,
                    "staging_path": staging_path,
                    "file_id": self.uploaded_files.get(filename)
                })
                
            except Exception as e:
                print(f"❌ Failed: {filename} - {e}")
                results["failed"].append({"file": filename, "error": str(e)})
        
        # Save results
        results_file = os.path.join(staging_dir, "upload_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 Summary: {len(results['uploaded'])} uploaded, {len(results['failed'])} failed")
        print(f"📁 Results saved to: {results_file}")
        
        return results
    
    def parse_mappings(self, staging_dir: str, output_dir: str) -> Dict[str, Any]:
        """Parse all Informatica files (mappings, workflows, sessions, worklets).
        
        Note: Only mappings create canonical models (transformations in generic terminology).
        Workflows/tasks (sessions)/worklets create orchestration structures and are stored separately.
        Neo4j stores components using Informatica labels (Session, Mapping) but the canonical
        model uses generic terminology (Task, Transformation).
        
        Args:
            staging_dir: Directory with uploaded files
            output_dir: Directory to save parsed results
            
        Returns:
            Dictionary with parse results
        """
        print(f"\n{'='*60}")
        print("STEP B: Parse All Files")
        print(f"{'='*60}")
        print("ℹ️  Note: Only mappings create canonical models (transformations).")
        print("   Workflows/tasks (sessions)/worklets create orchestration structures.")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Find all Informatica XML files
        all_files = (
            glob.glob(os.path.join(staging_dir, "*mapping*.xml")) +
            glob.glob(os.path.join(staging_dir, "*workflow*.xml")) +
            glob.glob(os.path.join(staging_dir, "*session*.xml")) +
            glob.glob(os.path.join(staging_dir, "*worklet*.xml"))
        )
        
        if not all_files:
            print("⚠️  No Informatica XML files found in staging directory")
            return {"parsed": [], "failed": []}
        
        results = {
            "parsed": [],
            "failed": [],
            "by_type": {
                "mappings": [],
                "workflows": [],
                "sessions": [],
                "worklets": []
            }
        }
        
        normalizer = MappingNormalizer()
        
        # Try to import progress indicator
        try:
            from tqdm import tqdm
            use_progress = True
        except ImportError:
            use_progress = False
            tqdm = None
        
        # Initialize graph store if enabled
        graph_store = None
        try:
            from config import settings
            enable_graph = getattr(settings, 'enable_graph_store', False) or os.getenv('ENABLE_GRAPH_STORE', 'false').lower() == 'true'
            if enable_graph:
                graph_store = GraphStore()
                print("   ✅ Graph store enabled - components will be saved to Neo4j")
        except Exception as e:
            print(f"   ⚠️  Graph store not available: {e}")
            graph_store = None
        
        # Use progress indicator if available
        file_iter = tqdm(all_files, desc="Parsing files", unit="file") if use_progress and tqdm else all_files
        
        for file_path in file_iter:
            filename = os.path.basename(file_path)
            file_type = self._detect_file_type(filename)
            print(f"\n📋 Parsing {file_type.upper()}: {filename}")
            
            try:
                if file_type == "mapping":
                    # Parse mapping to canonical model
                    parser = MappingParser(file_path)
                    raw_mapping = parser.parse()
                    canonical_model = normalizer.normalize(raw_mapping)
                    mapping_name = canonical_model.get("mapping_name", filename.replace(".xml", ""))
                    
                    # Save canonical model
                    output_file = os.path.join(output_dir, f"{mapping_name}.json")
                    with open(output_file, 'w') as f:
                        json.dump(canonical_model, f, indent=2, default=str)
                    
                    self.parsed_mappings[mapping_name] = canonical_model
                    
                    # Save to Neo4j if graph store is enabled
                    if graph_store:
                        try:
                            graph_store.save_mapping(canonical_model)
                            # Save file metadata
                            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
                            graph_store.save_file_metadata(
                                component_type="Mapping",
                                component_name=mapping_name,
                                file_path=file_path,
                                filename=filename,
                                file_size=file_size,
                                parsed_at=datetime.now().isoformat()
                            )
                            print(f"   💾 Saved to Neo4j: {mapping_name}")
                        except Exception as e:
                            print(f"   ⚠️  Failed to save to Neo4j: {e}")
                    
                    print(f"   ✅ Parsed to canonical model: {mapping_name}")
                    print(f"   💾 Saved to: {output_file}")
                    
                    results["parsed"].append({
                        "file": filename,
                        "type": file_type,
                        "mapping_name": mapping_name,
                        "output_file": output_file
                    })
                    results["by_type"]["mappings"].append(mapping_name)
                    
                elif file_type == "workflow":
                    # Parse workflow to DAG structure
                    parser = WorkflowParser(file_path)
                    workflow_data = parser.parse()
                    workflow_name = workflow_data.get("name", filename.replace(".xml", ""))
                    
                    # Save workflow structure
                    output_file = os.path.join(output_dir, f"{workflow_name}_workflow.json")
                    with open(output_file, 'w') as f:
                        json.dump(workflow_data, f, indent=2, default=str)
                    
                    # Save to Neo4j if graph store is enabled
                    if graph_store:
                        try:
                            graph_store.save_workflow(workflow_data)
                            # Save file metadata
                            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
                            graph_store.save_file_metadata(
                                component_type="Workflow",
                                component_name=workflow_name,
                                file_path=file_path,
                                filename=filename,
                                file_size=file_size,
                                parsed_at=datetime.now().isoformat()
                            )
                            print(f"   💾 Saved to Neo4j: {workflow_name}")
                        except Exception as e:
                            print(f"   ⚠️  Failed to save to Neo4j: {e}")
                    
                    print(f"   ✅ Parsed workflow structure: {workflow_name}")
                    print(f"   💾 Saved to: {output_file}")
                    
                    results["parsed"].append({
                        "file": filename,
                        "type": file_type,
                        "workflow_name": workflow_name,
                        "output_file": output_file
                    })
                    results["by_type"]["workflows"].append(workflow_name)
                    
                elif file_type == "session":
                    # Parse session configuration
                    parser = SessionParser(file_path)
                    session_data = parser.parse()
                    session_name = session_data.get("name", filename.replace(".xml", ""))
                    
                    # Save session structure
                    output_file = os.path.join(output_dir, f"{session_name}_session.json")
                    with open(output_file, 'w') as f:
                        json.dump(session_data, f, indent=2, default=str)
                    
                    # Save to Neo4j if graph store is enabled
                    if graph_store:
                        try:
                            # Normalize session data (session parser returns "mapping", graph store expects "mapping_name")
                            normalized_session = {
                                "name": session_name,
                                "type": "SESSION",
                                "mapping_name": session_data.get("mapping") or session_data.get("mapping_name"),
                                "config": session_data.get("config", {})
                            }
                            # Workflow relationship will be built in second pass
                            graph_store.save_session(normalized_session, None)
                            # Save file metadata
                            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
                            graph_store.save_file_metadata(
                                component_type="Session",
                                component_name=session_name,
                                file_path=file_path,
                                filename=filename,
                                file_size=file_size,
                                parsed_at=datetime.now().isoformat()
                            )
                            print(f"   💾 Saved to Neo4j: {session_name}")
                        except Exception as e:
                            print(f"   ⚠️  Failed to save to Neo4j: {e}")
                    
                    print(f"   ✅ Parsed session configuration: {session_name}")
                    print(f"   💾 Saved to: {output_file}")
                    
                    results["parsed"].append({
                        "file": filename,
                        "type": file_type,
                        "session_name": session_name,
                        "output_file": output_file
                    })
                    results["by_type"]["sessions"].append(session_name)
                    
                elif file_type == "worklet":
                    # Parse worklet structure
                    parser = WorkletParser(file_path)
                    worklet_data = parser.parse()
                    worklet_name = worklet_data.get("name", filename.replace(".xml", ""))
                    
                    # Save worklet structure
                    output_file = os.path.join(output_dir, f"{worklet_name}_worklet.json")
                    with open(output_file, 'w') as f:
                        json.dump(worklet_data, f, indent=2, default=str)
                    
                    # Save to Neo4j if graph store is enabled
                    if graph_store:
                        try:
                            # Try to find workflow that contains this worklet
                            workflow_name = None  # Would need to be determined from workflow files
                            graph_store.save_worklet(worklet_data, workflow_name)
                            # Save file metadata
                            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
                            graph_store.save_file_metadata(
                                component_type="Worklet",
                                component_name=worklet_name,
                                file_path=file_path,
                                filename=filename,
                                file_size=file_size,
                                parsed_at=datetime.now().isoformat()
                            )
                            print(f"   💾 Saved to Neo4j: {worklet_name}")
                        except Exception as e:
                            print(f"   ⚠️  Failed to save to Neo4j: {e}")
                    
                    print(f"   ✅ Parsed worklet structure: {worklet_name}")
                    print(f"   💾 Saved to: {output_file}")
                    
                    results["parsed"].append({
                        "file": filename,
                        "type": file_type,
                        "worklet_name": worklet_name,
                        "output_file": output_file
                    })
                    results["by_type"]["worklets"].append(worklet_name)
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results["failed"].append({"file": filename, "type": file_type, "error": str(e)})
        
        # Second pass: Build relationships in Neo4j if graph store is enabled
        if graph_store:
            print(f"\n🔗 Building relationships in Neo4j...")
            try:
                # Reload workflow files to build relationships
                workflow_files = glob.glob(os.path.join(output_dir, "*_workflow.json"))
                for workflow_file in workflow_files:
                    try:
                        with open(workflow_file, 'r') as f:
                            workflow_data = json.load(f)
                        
                        workflow_name = workflow_data.get("name")
                        if not workflow_name:
                            continue
                        
                        # Process tasks to link sessions/worklets to workflow
                        tasks = workflow_data.get("tasks", [])
                        for task in tasks:
                            task_name = task.get("name", "")
                            task_type = task.get("type", "")
                            
                            if task_type == "Session" or "Session" in task_type:
                                # Ensure session exists and link to workflow
                                try:
                                    # Try to load session data to get mapping name
                                    session_file = os.path.join(output_dir, f"{task_name}_session.json")
                                    session_data = {"name": task_name, "type": task_type}
                                    if os.path.exists(session_file):
                                        with open(session_file, 'r') as f:
                                            loaded_session = json.load(f)
                                            session_data["mapping_name"] = loaded_session.get("mapping") or loaded_session.get("mapping_name")
                                            session_data["config"] = loaded_session.get("config", {})
                                    
                                    # Save/update session and link to workflow
                                    graph_store.save_session(session_data, workflow_name)
                                    print(f"      ✅ Linked task {task_name} to workflow {workflow_name}")
                                except Exception as e:
                                    print(f"      ⚠️  Could not link session {task_name} to workflow {workflow_name}: {e}")
                                    logger.debug(f"Could not link session {task_name} to workflow: {e}", exc_info=True)
                            
                            elif task_type == "Worklet" or "Worklet" in task_type:
                                worklet_name = task.get("worklet_name") or task_name
                                # Ensure worklet exists and link to workflow
                                try:
                                    # Try to load worklet data if available
                                    # Try multiple naming patterns
                                    worklet_file = None
                                    for pattern in [
                                        f"{worklet_name}_worklet.json",
                                        f"{worklet_name.lower()}_worklet.json",
                                        f"worklet_{worklet_name.lower()}_worklet.json"
                                    ]:
                                        candidate = os.path.join(output_dir, pattern)
                                        if os.path.exists(candidate):
                                            worklet_file = candidate
                                            break
                                    
                                    worklet_data = {}
                                    if worklet_file and os.path.exists(worklet_file):
                                        with open(worklet_file, 'r') as f:
                                            worklet_data = json.load(f)
                                    
                                    # If worklet file not found or empty, try to re-parse from original XML
                                    if not worklet_data or not worklet_data.get("tasks"):
                                        # Try to find and re-parse the original worklet XML file
                                        worklet_xml_patterns = [
                                            os.path.join(staging_dir, f"{worklet_name}.xml"),
                                            os.path.join(staging_dir, f"{worklet_name.lower()}.xml"),
                                            os.path.join(staging_dir, f"worklet_{worklet_name.lower()}.xml"),
                                            os.path.join(staging_dir, f"worklet_{worklet_name}.xml")
                                        ]
                                        
                                        worklet_xml = None
                                        for pattern in worklet_xml_patterns:
                                            if os.path.exists(pattern):
                                                worklet_xml = pattern
                                                break
                                        
                                        if worklet_xml:
                                            try:
                                                parser = WorkletParser(worklet_xml)
                                                worklet_data = parser.parse()
                                                print(f"      🔄 Re-parsed worklet {worklet_name} from XML: {len(worklet_data.get('tasks', []))} task(s)")
                                            except Exception as e:
                                                print(f"      ⚠️  Could not re-parse worklet XML: {e}")
                                                if not worklet_data:
                                                    worklet_data = {"name": worklet_name, "tasks": []}
                                        else:
                                            if not worklet_data:
                                                worklet_data = {"name": worklet_name, "tasks": []}
                                            print(f"      ⚠️  Worklet XML not found for {worklet_name}, using existing data")
                                    
                                    # If worklet_data still has no tasks, try to find worklet XML in staging_dir
                                    if not worklet_data.get("tasks"):
                                        worklet_xml_patterns = [
                                            os.path.join(staging_dir, f"{worklet_name}.xml"),
                                            os.path.join(staging_dir, f"{worklet_name.lower()}.xml"),
                                            os.path.join(staging_dir, f"worklet_{worklet_name.lower()}.xml"),
                                            os.path.join(staging_dir, f"worklet_{worklet_name}.xml")
                                        ]
                                        
                                        for pattern in worklet_xml_patterns:
                                            if os.path.exists(pattern):
                                                try:
                                                    parser = WorkletParser(pattern)
                                                    parsed_data = parser.parse()
                                                    if parsed_data.get("tasks"):
                                                        worklet_data["tasks"] = parsed_data["tasks"]
                                                        print(f"      🔄 Re-parsed worklet {worklet_name} from staging: {len(worklet_data['tasks'])} task(s)")
                                                        break
                                                except Exception as e:
                                                    continue
                                    
                                    # Ensure worklet has a name
                                    if not worklet_data.get("name"):
                                        worklet_data["name"] = worklet_name
                                    
                                    # Save/update worklet and link to workflow
                                    # This will also create sessions from tasks inside the worklet
                                    graph_store.save_worklet(worklet_data, workflow_name)
                                    
                                    # Save worklet first (this will create sessions from tasks if worklet_data has tasks)
                                    graph_store.save_worklet(worklet_data, workflow_name)
                                    
                                    # Now ensure sessions inside the worklet are created and linked
                                    # The save_worklet method should handle this, but let's also do it explicitly
                                    worklet_tasks = worklet_data.get("tasks", [])
                                    if worklet_tasks:
                                        print(f"      📋 Found {len(worklet_tasks)} task(s) in worklet {worklet_name}")
                                        for worklet_task in worklet_tasks:
                                            worklet_task_name = worklet_task.get("name", "")
                                            worklet_task_type = worklet_task.get("type", "")
                                            
                                            if worklet_task_type == "Session" or "Session" in worklet_task_type:
                                                # Try to find mapping name from session name pattern
                                                # Session names like S_M_INGEST_CUSTOMERS map to M_INGEST_CUSTOMERS
                                                mapping_name = None
                                                if worklet_task_name.startswith("S_M_"):
                                                    mapping_name = worklet_task_name.replace("S_M_", "M_")
                                                
                                                # Try to load session data to get mapping name
                                                session_file = None
                                                for pattern in [
                                                    f"{worklet_task_name}_session.json",
                                                    f"{worklet_task_name.lower()}_session.json",
                                                    f"session_{worklet_task_name.lower()}_session.json"
                                                ]:
                                                    candidate = os.path.join(output_dir, pattern)
                                                    if os.path.exists(candidate):
                                                        session_file = candidate
                                                        break
                                                
                                                session_data = {"name": worklet_task_name, "type": worklet_task_type}
                                                if session_file:
                                                    with open(session_file, 'r') as f:
                                                        loaded_session = json.load(f)
                                                        session_data["mapping_name"] = loaded_session.get("mapping") or loaded_session.get("mapping_name") or mapping_name
                                                        session_data["config"] = loaded_session.get("config", {})
                                                elif mapping_name:
                                                    session_data["mapping_name"] = mapping_name
                                                
                                                # Save session - save_worklet should have created it, but ensure it exists
                                                try:
                                                    # The session should already be linked to worklet by save_worklet
                                                    # But let's ensure it exists
                                                    graph_store.save_session(session_data, None)  # Don't link to workflow, worklet handles it
                                                    print(f"      ✅ Ensured task {worklet_task_name} exists and linked to worklet {worklet_name}")
                                                except Exception as e:
                                                    print(f"      ⚠️  Could not ensure session {worklet_task_name} in worklet {worklet_name}: {e}")
                                    else:
                                        print(f"      ⚠️  Worklet {worklet_name} has no tasks in worklet_data")
                                    
                                    print(f"      ✅ Linked worklet {worklet_name} to workflow {workflow_name}")
                                except Exception as e:
                                    print(f"      ⚠️  Could not link worklet {worklet_name} to workflow {workflow_name}: {e}")
                                    logger.debug(f"Could not link worklet {worklet_name} to workflow: {e}", exc_info=True)
                        
                        print(f"   ✅ Built relationships for workflow: {workflow_name}")
                    except Exception as e:
                        print(f"   ⚠️  Failed to build relationships for workflow: {e}")
                
                print(f"   ✅ Relationship building complete")
            except Exception as e:
                print(f"   ⚠️  Relationship building failed: {e}")
        
        # Save summary
        summary_file = os.path.join(output_dir, "parse_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 Summary:")
        print(f"   Mappings (canonical models): {len(results['by_type']['mappings'])}")
        print(f"   Workflows: {len(results['by_type']['workflows'])}")
        print(f"   Sessions: {len(results['by_type']['sessions'])}")
        print(f"   Worklets: {len(results['by_type']['worklets'])}")
        print(f"   Failed: {len(results['failed'])}")
        print(f"📁 Summary saved to: {summary_file}")
        
        return results
    
    def _detect_file_type(self, filename: str) -> str:
        """Detect Informatica file type from filename.
        
        Args:
            filename: XML filename
            
        Returns:
            File type: 'mapping', 'workflow', 'session', or 'worklet'
        """
        filename_lower = filename.lower()
        if "mapping" in filename_lower:
            return "mapping"
        elif "workflow" in filename_lower:
            return "workflow"
        elif "session" in filename_lower:
            return "session"
        elif "worklet" in filename_lower:
            return "worklet"
        else:
            return "unknown"
    
    def enhance_with_ai(self, parsed_dir: str, output_dir: str) -> Dict[str, Any]:
        """Enhance parsed models with AI.
        
        Args:
            parsed_dir: Directory with parsed JSON files
            output_dir: Directory to save enhanced models
            
        Returns:
            Dictionary with enhancement results
        """
        print(f"\n{'='*60}")
        print("STEP C: Enhance with AI")
        print(f"{'='*60}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Find parsed JSON files
        parsed_files = glob.glob(os.path.join(parsed_dir, "*.json"))
        parsed_files = [f for f in parsed_files if not f.endswith("_summary.json")]
        
        if not parsed_files:
            print("⚠️  No parsed files found")
            return {"enhanced": [], "failed": []}
        
        try:
            from ai_agents import AgentOrchestrator
            orchestrator = AgentOrchestrator()
        except ImportError:
            print("⚠️  AI agents not available, skipping enhancement")
            return {"enhanced": [], "failed": [], "skipped": True}
        
        results = {
            "enhanced": [],
            "failed": []
        }
        
        for json_file in parsed_files:
            filename = os.path.basename(json_file)
            print(f"\n🤖 Enhancing: {filename}")
            
            try:
                # Load canonical model
                with open(json_file, 'r') as f:
                    canonical_model = json.load(f)
                
                # Skip non-canonical models (worklets, sessions, workflows without mapping_name)
                # Only enhance mappings which have a proper canonical model structure
                if not canonical_model or not isinstance(canonical_model, dict):
                    print(f"   ⚠️  Skipping: Not a valid canonical model (empty or invalid structure)")
                    continue
                
                # Check if it's a canonical model (has mapping_name or transformations)
                if "mapping_name" not in canonical_model and "transformations" not in canonical_model:
                    # This might be a workflow/worklet/session structure, skip it
                    print(f"   ⚠️  Skipping: Not a canonical mapping model (workflow/worklet/session structure)")
                    continue
                
                # Enhance with AI
                enhanced = orchestrator.enhance_model(canonical_model, use_llm=True)
                
                # Save enhanced model
                mapping_name = enhanced.get("mapping_name", filename.replace(".json", "").replace("_workflow", "").replace("_worklet", "").replace("_session", ""))
                output_file = os.path.join(output_dir, f"{mapping_name}_enhanced.json")
                
                with open(output_file, 'w') as f:
                    json.dump(enhanced, f, indent=2, default=str)
                
                print(f"   ✅ Enhanced: {mapping_name}")
                print(f"   💾 Saved to: {output_file}")
                
                results["enhanced"].append({
                    "file": filename,
                    "mapping_name": mapping_name,
                    "output_file": output_file
                })
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results["failed"].append({"file": filename, "error": str(e)})
        
        # Save summary
        summary_file = os.path.join(output_dir, "enhance_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 Summary: {len(results['enhanced'])} enhanced, {len(results['failed'])} failed")
        
        return results
    
    def generate_hierarchy(self, output_dir: str) -> Dict[str, Any]:
        """Generate hierarchy/tree structure.
        
        Args:
            output_dir: Directory to save hierarchy
            
        Returns:
            Dictionary with hierarchy results
        """
        print(f"\n{'='*60}")
        print("STEP D: Generate Hierarchy")
        print(f"{'='*60}")
        
        try:
            if self.use_api:
                # Get hierarchy from API
                response = requests.get(f"{self.api_url}/api/v1/hierarchy", timeout=30)
                response.raise_for_status()
                hierarchy_data = response.json()
                
                if hierarchy_data.get("success"):
                    hierarchy = hierarchy_data.get("hierarchy", {})
                    
                    # Save hierarchy
                    hierarchy_file = os.path.join(output_dir, "hierarchy.json")
                    with open(hierarchy_file, 'w') as f:
                        json.dump(hierarchy, f, indent=2, default=str)
                    
                    print(f"✅ Hierarchy generated")
                    print(f"💾 Saved to: {hierarchy_file}")
                    
                    # Generate text tree
                    tree_file = os.path.join(output_dir, "hierarchy_tree.txt")
                    self._generate_text_tree(hierarchy, tree_file)
                    print(f"🌳 Text tree saved to: {tree_file}")
                    
                    return {"success": True, "hierarchy_file": hierarchy_file, "tree_file": tree_file}
                else:
                    print("⚠️  API returned unsuccessful response")
                    return {"success": False}
            else:
                # Build hierarchy from files
                print("⚠️  Direct hierarchy building not implemented, use API mode")
                return {"success": False, "message": "Use API mode for hierarchy generation"}
                
        except Exception as e:
            print(f"❌ Failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_text_tree(self, hierarchy: Dict, output_file: str):
        """Generate text representation of hierarchy tree."""
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
    
    def generate_lineage(self, output_dir: str, staging_dir: str = None) -> Dict[str, Any]:
        """Generate lineage diagrams.
        
        Args:
            output_dir: Directory to save lineage diagrams
            staging_dir: Directory with uploaded files (default: test_log/staging)
            
        Returns:
            Dictionary with lineage results
        """
        print(f"\n{'='*60}")
        print("STEP E: Generate Lineage Diagrams")
        print(f"{'='*60}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        if staging_dir is None:
            staging_dir = "test_log/staging"
        
        try:
            # Find workflow files
            workflow_files = glob.glob(os.path.join(staging_dir, "*workflow*.xml"))
            
            if not workflow_files:
                print("⚠️  No workflow files found for lineage generation")
                return {"generated": [], "failed": []}
            
            results = {"generated": [], "failed": []}
            
            for workflow_file in workflow_files:
                filename = os.path.basename(workflow_file)
                print(f"\n📊 Generating lineage for: {filename}")
                
                try:
                    # Parse workflow
                    parser = WorkflowParser(workflow_file)
                    workflow_data = parser.parse()
                    
                    # Build DAG
                    dag_builder = DAGBuilder()
                    dag = dag_builder.build(workflow_data)
                    
                    # Visualize
                    visualizer = DAGVisualizer()
                    
                    # Generate Mermaid diagram
                    mermaid_file = os.path.join(output_dir, f"{filename}_lineage.mermaid")
                    mermaid_diagram = visualizer.visualize(dag, format="mermaid")
                    with open(mermaid_file, 'w') as f:
                        f.write(mermaid_diagram)
                    
                    # Generate DOT diagram
                    dot_file = os.path.join(output_dir, f"{filename}_lineage.dot")
                    dot_diagram = visualizer.visualize(dag, format="dot")
                    with open(dot_file, 'w') as f:
                        f.write(dot_diagram)
                    
                    # Generate JSON
                    json_file = os.path.join(output_dir, f"{filename}_lineage.json")
                    with open(json_file, 'w') as f:
                        json.dump(dag, f, indent=2, default=str)
                    
                    print(f"   ✅ Generated: {mermaid_file}, {dot_file}, {json_file}")
                    
                    results["generated"].append({
                        "workflow": filename,
                        "mermaid": mermaid_file,
                        "dot": dot_file,
                        "json": json_file
                    })
                    
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
                    results["failed"].append({"file": filename, "error": str(e)})
            
            print(f"\n📊 Summary: {len(results['generated'])} generated, {len(results['failed'])} failed")
            return results
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            return {"generated": [], "failed": [], "error": str(e)}
    
    def generate_canonical_images(self, output_dir: str) -> Dict[str, Any]:
        """Generate canonical model visualizations.
        
        Args:
            output_dir: Directory to save images
            
        Returns:
            Dictionary with visualization results
        """
        print(f"\n{'='*60}")
        print("STEP F: Generate Canonical Model Images")
        print(f"{'='*60}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Find parsed or enhanced models
        # Resolve paths relative to project root
        project_root = Path(__file__).parent.parent
        
        # Handle both test_log/diagrams and test_log cases
        if "diagrams" in output_dir:
            # If output_dir is test_log/diagrams, get test_log base
            base_dir = os.path.dirname(output_dir)
            if not os.path.isabs(base_dir):
                base_dir = os.path.join(project_root, base_dir)
        else:
            base_dir = output_dir
            if not os.path.isabs(base_dir):
                base_dir = os.path.join(project_root, base_dir)
        
        parse_ai_dir = os.path.join(base_dir, "parse_ai")
        parsed_dir = os.path.join(base_dir, "parsed")
        
        model_files = []
        for dir_path in [parse_ai_dir, parsed_dir]:
            if os.path.exists(dir_path):
                found_files = glob.glob(os.path.join(dir_path, "*.json"))
                # Exclude summary files
                found_files = [f for f in found_files if not os.path.basename(f).endswith("_summary.json") and not os.path.basename(f).endswith("summary.json")]
                model_files.extend(found_files)
                if found_files:
                    print(f"   📁 Found {len(found_files)} model(s) in {os.path.basename(dir_path)}")
        
        if not model_files:
            print("⚠️  No canonical model files found")
            return {"generated": [], "failed": []}
        
        results = {"generated": [], "failed": []}
        
        for model_file in model_files:
            filename = os.path.basename(model_file)
            print(f"\n🕸️  Generating visualization for: {filename}")
            
            try:
                with open(model_file, 'r') as f:
                    canonical_model = json.load(f)
                
                # Generate Mermaid diagram
                mermaid_content = self._canonical_to_mermaid(canonical_model)
                mermaid_file = os.path.join(output_dir, f"{filename.replace('.json', '')}_canonical.mermaid")
                with open(mermaid_file, 'w') as f:
                    f.write(mermaid_content)
                
                print(f"   ✅ Generated: {mermaid_file}")
                results["generated"].append({
                    "model": filename,
                    "mermaid": mermaid_file
                })
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results["failed"].append({"file": filename, "error": str(e)})
        
        print(f"\n📊 Summary: {len(results['generated'])} generated, {len(results['failed'])} failed")
        return results
    
    def _canonical_to_mermaid(self, model: Dict) -> str:
        """Convert canonical model to Mermaid diagram."""
        lines = ["graph TD"]
        
        mapping_name = model.get("mapping_name", "Unknown")
        
        # Sources
        for source in model.get("sources", []):
            source_id = source.get("name", "").replace(" ", "_")
            source_label = source.get("name", "Source")
            lines.append(f'    {source_id}["{source_label}<br/>Source"]')
        
        # Transformations
        for trans in model.get("transformations", []):
            trans_id = trans.get("name", "").replace(" ", "_")
            trans_label = trans.get("name", "Transformation")
            trans_type = trans.get("type", "Unknown")
            lines.append(f'    {trans_id}["{trans_label}<br/>{trans_type}"]')
        
        # Targets
        for target in model.get("targets", []):
            target_id = target.get("name", "").replace(" ", "_")
            target_label = target.get("name", "Target")
            lines.append(f'    {target_id}["{target_label}<br/>Target"]')
        
        # Connectors
        for connector in model.get("connectors", []):
            from_trans = connector.get("from_transformation", "").replace(" ", "_")
            to_trans = connector.get("to_transformation", "").replace(" ", "_")
            if from_trans and to_trans:
                lines.append(f'    {from_trans} --> {to_trans}')
        
        return "\n".join(lines)
    
    def generate_code(self, output_dir: str, workflow_aware: bool = True) -> Dict[str, Any]:
        """Generate code (PySpark/DLT/SQL) with workflow-aware organization.
        
        Args:
            output_dir: Directory to save generated code
            workflow_aware: If True, organize by workflow structure; if False, use flat per-mapping structure
            
        Returns:
            Dictionary with generation results
        """
        print(f"\n{'='*60}")
        print("STEP G: Generate Code")
        print(f"{'='*60}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize graph store and queries if available
        graph_store = None
        graph_queries = None
        version_store = None
        
        try:
            # Check if graph store is enabled (using lowercase attribute name from settings)
            enable_graph = getattr(settings, 'enable_graph_store', False) or os.getenv('ENABLE_GRAPH_STORE', 'false').lower() == 'true'
            if enable_graph:
                graph_store = GraphStore()
                graph_queries = GraphQueries(graph_store)
                graph_first = getattr(settings, 'graph_first', False) or os.getenv('GRAPH_FIRST', 'false').lower() == 'true'
                version_store = VersionStore(graph_store=graph_store, graph_first=graph_first)
                print("✅ Graph store enabled - using workflow-aware generation")
        except Exception as e:
            print(f"⚠️  Graph store not available: {e}")
            print("   Falling back to file-based generation")
        
        results = {"generated": [], "failed": [], "workflows": [], "shared_code": []}
        
        # Generate only PySpark code (regular transformation code, not DLT pipeline)
        # DLT and SQL can be enabled via configuration if needed
        generators = {
            "pyspark": PySparkGenerator(),
            # "dlt": DLTGenerator(),  # Disabled - user wants regular PySpark, not DLT
            # "sql": SQLGenerator()   # Disabled - focus on PySpark transformations
        }
        
        # Try workflow-aware generation if graph store is available
        if workflow_aware and graph_store and graph_queries:
            try:
                # Get all workflows from Neo4j
                workflows = graph_queries.list_workflows()
                
                if workflows:
                    print(f"\n📋 Found {len(workflows)} workflow(s) in graph")
                    return self._generate_code_workflow_aware(
                        workflows, graph_queries, version_store, generators, output_dir, results, graph_store
                    )
                else:
                    # Fallback: Try to build workflow structure from parsed files
                    print("⚠️  No workflows found in graph, trying to build from parsed files...")
                    workflows_from_files = self._build_workflows_from_files()
                    if workflows_from_files:
                        print(f"📋 Found {len(workflows_from_files)} workflow(s) from parsed files")
                        return self._generate_code_workflow_aware_from_files(
                            workflows_from_files, version_store, generators, output_dir, results
                        )
                    else:
                        print("⚠️  No workflows found, falling back to file-based generation")
            except Exception as e:
                print(f"⚠️  Workflow-aware generation failed: {e}")
                import traceback
                traceback.print_exc()
                print("   Falling back to file-based generation")
        
        # Fallback: File-based generation (original method)
        return self._generate_code_file_based(generators, output_dir, results)
    
    def _generate_code_workflow_aware(self, workflows: List[Dict[str, Any]], 
                                      graph_queries: GraphQueries,
                                      version_store: VersionStore,
                                      generators: Dict[str, Any],
                                      output_dir: str,
                                      results: Dict[str, Any],
                                      graph_store: Optional[GraphStore] = None) -> Dict[str, Any]:
        """Generate code organized by workflow structure.
        
        Note: Uses generic canonical model terminology (tasks/transformations) but
        Neo4j stores components using Informatica labels (Session/Mapping).
        
        Args:
            workflows: List of workflows from graph
            graph_queries: GraphQueries instance
            version_store: VersionStore instance
            generators: Code generators dict
            output_dir: Base output directory
            results: Results dictionary to update
            
        Returns:
            Updated results dictionary
        """
        workflows_dir = os.path.join(output_dir, "workflows")
        shared_dir = os.path.join(output_dir, "shared")
        os.makedirs(workflows_dir, exist_ok=True)
        os.makedirs(shared_dir, exist_ok=True)
        
        # Track all mappings to detect reusable patterns
        all_mappings = {}
        all_transformations = {}
        
        for workflow in workflows:
            workflow_name = workflow["name"]
            print(f"\n🔄 Processing workflow: {workflow_name}")
            
            # Get workflow structure
            workflow_structure = graph_queries.get_workflow_structure(workflow_name)
            if not workflow_structure:
                print(f"   ⚠️  Workflow structure not found: {workflow_name}")
                continue
            
            # Create workflow directory
            workflow_dir = os.path.join(workflows_dir, workflow_name.lower().replace("wf_", "").replace(" ", "_"))
            os.makedirs(workflow_dir, exist_ok=True)
            
            # Generate workflow README
            self._generate_workflow_readme(workflow_structure, workflow_dir)
            
            # Process tasks (stored as Session nodes in Neo4j, but use generic Task terminology in canonical model)
            tasks = workflow_structure.get("tasks", [])
            tasks_dir = os.path.join(workflow_dir, "tasks")
            os.makedirs(tasks_dir, exist_ok=True)
            
            for task in tasks:
                task_name = task["name"]
                print(f"   ⚙️  Processing task: {task_name}")
                
                task_dir = os.path.join(tasks_dir, task_name.lower().replace("s_", "").replace(" ", "_"))
                os.makedirs(task_dir, exist_ok=True)
                
                # Generate task config
                self._generate_session_config(task, task_dir)
                
                # Process transformations (stored as Mapping nodes in Neo4j, but use generic Transformation terminology)
                transformations = task.get("transformations", [])
                transformations_dir = os.path.join(task_dir, "transformations")
                os.makedirs(transformations_dir, exist_ok=True)
                
                for transformation_info in transformations:
                    # Get transformation name (stored as mapping_name in Neo4j)
                    transformation_name = transformation_info.get("transformation_name") or transformation_info.get("name")
                    if not transformation_name:
                        continue
                    transformation_name_clean = transformation_name.lower().replace("m_", "").replace(" ", "_")
                    
                    print(f"      📋 Generating code for transformation: {transformation_name}")
                    
                    # Load canonical model
                    canonical_model = None
                    try:
                        # Try loading from version store (Neo4j or JSON)
                        canonical_model = version_store.load(transformation_name)
                        if not canonical_model:
                            # Try loading from JSON files as fallback
                            canonical_model = self._load_canonical_model_from_files(transformation_name)
                    except Exception as e:
                        print(f"      ⚠️  Failed to load canonical model: {e}")
                        results["failed"].append({
                            "transformation": transformation_name,
                            "workflow": workflow_name,
                            "task": task_name,
                            "error": f"Failed to load model: {str(e)}"
                        })
                        continue
                    
                    if not canonical_model:
                        print(f"      ⚠️  Canonical model not found: {transformation_name}")
                        continue
                    
                    # Store for reusable code detection
                    all_mappings[transformation_name] = canonical_model
                    for trans in canonical_model.get("transformations", []):
                        trans_type = trans.get("type", "")
                        if trans_type not in all_transformations:
                            all_transformations[trans_type] = []
                        all_transformations[trans_type].append({
                            "transformation": transformation_name,
                            "transformation_detail": trans
                        })
                    
                    # Generate code for transformation
                    transformation_dir = os.path.join(transformations_dir, transformation_name_clean)
                    os.makedirs(transformation_dir, exist_ok=True)
                    
                    # Only generate PySpark code (regular transformation code, not DLT)
                    code_type = "pyspark"
                    generator = generators["pyspark"]
                    try:
                        code = generator.generate(canonical_model)
                        
                        # Generate descriptive filename
                        code_file = os.path.join(transformation_dir, f"{transformation_name_clean}_pyspark.py")
                        
                        with open(code_file, 'w') as f:
                            f.write(code)
                        
                        print(f"         ✅ Generated {code_type.upper()}: {os.path.basename(code_file)}")
                        
                        # Save code metadata to Neo4j if graph store is available
                        if graph_store:
                            try:
                                # Determine language from code type
                                language = "python" if code_type in ["pyspark", "dlt"] else "sql"
                                # Get quality score if available
                                quality_score = None
                                try:
                                    from generators.code_quality_checker import CodeQualityChecker
                                    quality_checker = CodeQualityChecker()
                                    quality_report = quality_checker.check_code_quality(code, canonical_model)
                                    quality_score = quality_report.get("overall_score")
                                except Exception:
                                    pass  # Quality check is optional
                                
                                graph_store.save_code_metadata(
                                    mapping_name=transformation_name,
                                    code_type=code_type,
                                    file_path=os.path.abspath(code_file),
                                    language=language,
                                    quality_score=quality_score
                                )
                            except Exception as e:
                                print(f"         ⚠️  Failed to save code metadata: {e}")
                        
                        results["generated"].append({
                            "mapping": transformation_name,
                            "type": code_type,
                            "file": code_file,
                            "workflow": workflow_name,
                            "session": task_name
                        })
                        
                    except Exception as e:
                        error_msg = str(e)
                        print(f"         ⚠️  {code_type.upper()} generation failed: {error_msg}")
                        results["failed"].append({
                            "mapping": transformation_name,
                            "type": code_type,
                            "error": error_msg,
                            "workflow": workflow_name,
                            "session": task_name
                        })
                    
                    # Generate mapping spec
                    self._generate_mapping_spec(canonical_model, transformation_dir)
            
            # Generate workflow orchestration files
            orchestration_dir = os.path.join(workflow_dir, "orchestration")
            os.makedirs(orchestration_dir, exist_ok=True)
            self._generate_workflow_orchestration(workflow_structure, orchestration_dir)
            
            # Count tasks and transformations
            tasks = workflow_structure.get("tasks", [])
            total_transformations = sum(
                len(task.get("transformations", []))
                for task in tasks
            )
            results["workflows"].append({
                "name": workflow_name,
                "tasks": len(tasks),
                "transformations": total_transformations
            })
        
        # Generate shared/reusable code
        if all_mappings:
            print(f"\n📦 Generating shared/reusable code...")
            self._generate_shared_code(all_transformations, shared_dir, results)
        
        # Save summary
        summary_file = os.path.join(output_dir, "generation_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 Summary:")
        print(f"   Workflows: {len(results['workflows'])}")
        print(f"   Generated files: {len(results['generated'])}")
        print(f"   Failed: {len(results['failed'])}")
        print(f"   Shared code files: {len(results['shared_code'])}")
        
        return results
    
    def _generate_code_file_based(self, generators: Dict[str, Any], 
                                  output_dir: str, 
                                  results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code using file-based approach (fallback).
        
        Args:
            generators: Code generators dict
            output_dir: Output directory
            results: Results dictionary to update
            
        Returns:
            Updated results dictionary
        """
        # Find enhanced or parsed models
        project_root = Path(__file__).parent.parent
        parse_ai_dir = os.path.join(project_root, "test_log", "parse_ai")
        parsed_dir = os.path.join(project_root, "test_log", "parsed")
        
        model_files = []
        for dir_path in [parse_ai_dir, parsed_dir]:
            if os.path.exists(dir_path):
                found_files = glob.glob(os.path.join(dir_path, "*.json"))
                found_files = [f for f in found_files if not os.path.basename(f).endswith("_summary.json") 
                              and not os.path.basename(f).endswith("summary.json")]
                model_files.extend(found_files)
                if found_files:
                    print(f"   📁 Found {len(found_files)} model(s) in {os.path.basename(dir_path)}")
        
        if not model_files:
            print("⚠️  No canonical model files found")
            print(f"   Searched in: {parse_ai_dir}")
            print(f"   Searched in: {parsed_dir}")
            print("   💡 Tip: Run 'make parse' first to create canonical models")
            return results
        
        for model_file in model_files:
            filename = os.path.basename(model_file)
            
            # Skip non-mapping files (workflows, sessions, worklets don't have canonical models)
            if "_workflow.json" in filename or "_session.json" in filename or "_worklet.json" in filename:
                print(f"\n⏭️  Skipping {filename} (workflow/session/worklet - no canonical model for code generation)")
                continue
            
            print(f"\n💻 Generating code for: {filename}")
            
            try:
                with open(model_file, 'r') as f:
                    canonical_model = json.load(f)
                
                # Check if this is actually a canonical model (has mapping_name)
                mapping_name = canonical_model.get("mapping_name")
                if not mapping_name:
                    print(f"   ⚠️  Skipping {filename} - not a canonical mapping model (no mapping_name)")
                    continue
                
                mapping_name_clean = mapping_name.lower().replace("m_", "").replace(" ", "_")
                mapping_dir = os.path.join(output_dir, mapping_name_clean)
                os.makedirs(mapping_dir, exist_ok=True)
                
                # Only generate PySpark code (skip DLT and SQL for now, or make configurable)
                # User requested regular PySpark transformation code, not DLT
                code_types_to_generate = {"pyspark": generators["pyspark"]}
                
                for code_type, generator in code_types_to_generate.items():
                    try:
                        code = generator.generate(canonical_model)
                        
                        # Generate descriptive filename
                        if code_type == "pyspark":
                            code_file = os.path.join(mapping_dir, f"{mapping_name_clean}_pyspark.py")
                        elif code_type == "dlt":
                            code_file = os.path.join(mapping_dir, f"{mapping_name_clean}_dlt.py")
                        else:
                            code_file = os.path.join(mapping_dir, f"{mapping_name_clean}_sql.sql")
                        
                        with open(code_file, 'w') as f:
                            f.write(code)
                        
                        print(f"   ✅ Generated {code_type.upper()}: {code_file}")
                        
                        # Save code metadata to Neo4j if graph store is available
                        graph_store = None
                        try:
                            enable_graph = getattr(settings, 'enable_graph_store', False) or os.getenv('ENABLE_GRAPH_STORE', 'false').lower() == 'true'
                            if enable_graph:
                                graph_store = GraphStore()
                        except Exception:
                            pass
                        
                        if graph_store:
                            try:
                                # Determine language from code type
                                language = "python" if code_type in ["pyspark", "dlt"] else "sql"
                                # Get quality score if available
                                quality_score = None
                                try:
                                    from generators.code_quality_checker import CodeQualityChecker
                                    quality_checker = CodeQualityChecker()
                                    quality_report = quality_checker.check_code_quality(code, canonical_model)
                                    quality_score = quality_report.get("overall_score")
                                except Exception:
                                    pass  # Quality check is optional
                                
                                graph_store.save_code_metadata(
                                    mapping_name=mapping_name,
                                    code_type=code_type,
                                    file_path=os.path.abspath(code_file),
                                    language=language,
                                    quality_score=quality_score
                                )
                            except Exception as e:
                                print(f"   ⚠️  Failed to save code metadata: {e}")
                        
                        results["generated"].append({
                            "mapping": mapping_name,
                            "type": code_type,
                            "file": code_file
                        })
                        
                    except Exception as e:
                        error_msg = str(e)
                        print(f"   ⚠️  {code_type.upper()} generation failed: {error_msg}")
                        results["failed"].append({
                            "mapping": mapping_name,
                            "type": code_type,
                            "error": error_msg
                        })
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results["failed"].append({"file": filename, "error": str(e)})
        
        # Generate workflow orchestration code from parsed workflow files
        print(f"\n🔄 Generating workflow orchestration code...")
        workflow_files = []
        for dir_path in [parse_ai_dir, parsed_dir]:
            if os.path.exists(dir_path):
                found_files = glob.glob(os.path.join(dir_path, "*_workflow.json"))
                workflow_files.extend(found_files)
        
        if workflow_files:
            workflows_dir = os.path.join(output_dir, "workflows")
            os.makedirs(workflows_dir, exist_ok=True)
            
            for workflow_file in workflow_files:
                filename = os.path.basename(workflow_file)
                workflow_name = filename.replace("_workflow.json", "").replace(".json", "")
                
                try:
                    with open(workflow_file, 'r') as f:
                        workflow_data = json.load(f)
                    
                    # Create workflow directory structure
                    workflow_dir = os.path.join(workflows_dir, workflow_name.lower().replace("wf_", "").replace(" ", "_"))
                    orchestration_dir = os.path.join(workflow_dir, "orchestration")
                    os.makedirs(orchestration_dir, exist_ok=True)
                    
                    # Transform workflow data to expected format if needed
                    # Parsed workflows have 'tasks' and 'links', but orchestration generator expects 'sessions' with 'mappings'
                    if "tasks" in workflow_data and "sessions" not in workflow_data:
                        # Convert tasks to sessions format (simplified - assumes tasks are sessions)
                        # In a real scenario, we'd need to map tasks to sessions and sessions to mappings
                        transformed_workflow = {
                            "name": workflow_data.get("name", workflow_name),
                            "type": workflow_data.get("type", "WORKFLOW"),
                            "sessions": []
                        }
                        # For now, create a session for each task (this is a simplified approach)
                        # TODO: Properly map tasks to sessions and sessions to mappings from Neo4j or parsed files
                        for task in workflow_data.get("tasks", []):
                            if task.get("type") == "Session" or "Session" in task.get("type", ""):
                                transformed_workflow["sessions"].append({
                                    "name": task.get("name", ""),
                                    "type": task.get("type", "SESSION"),
                                    "mappings": []  # Would need to be populated from session files or Neo4j
                                })
                        workflow_data = transformed_workflow
                    
                    # Generate orchestration code
                    print(f"   🔄 Processing workflow: {workflow_name}")
                    self._generate_workflow_orchestration(workflow_data, orchestration_dir)
                    
                    results["workflows"].append({
                        "name": workflow_name,
                        "orchestration_dir": orchestration_dir
                    })
                    
                except Exception as e:
                    print(f"   ⚠️  Failed to generate orchestration for {workflow_name}: {e}")
                    results["failed"].append({"workflow": workflow_name, "error": str(e)})
        else:
            print("   ℹ️  No workflow files found for orchestration generation")
        
        # Save summary
        summary_file = os.path.join(output_dir, "generation_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 Summary: {len(results['generated'])} files generated, {len(results['failed'])} failed")
        if results.get("workflows"):
            print(f"   Workflows with orchestration: {len(results['workflows'])}")
        return results
    
    def _load_canonical_model_from_files(self, mapping_name: str) -> Optional[Dict[str, Any]]:
        """Load canonical model from JSON files.
        
        Args:
            mapping_name: Mapping name
            
        Returns:
            Canonical model dict or None
        """
        project_root = Path(__file__).parent.parent
        parse_ai_dir = os.path.join(project_root, "test_log", "parse_ai")
        parsed_dir = os.path.join(project_root, "test_log", "parsed")
        
        # Try enhanced first, then parsed
        for dir_path in [parse_ai_dir, parsed_dir]:
            if os.path.exists(dir_path):
                # Try exact match
                for pattern in [f"{mapping_name}.json", f"{mapping_name}_enhanced.json"]:
                    file_path = os.path.join(dir_path, pattern)
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, 'r') as f:
                                return json.load(f)
                        except Exception:
                            continue
                
                # Try partial match
                for file_path in glob.glob(os.path.join(dir_path, "*.json")):
                    if mapping_name.lower() in os.path.basename(file_path).lower():
                        try:
                            with open(file_path, 'r') as f:
                                model = json.load(f)
                                if model.get("mapping_name") == mapping_name:
                                    return model
                        except Exception:
                            continue
        
        return None
    
    def _generate_workflow_readme(self, workflow_structure: Dict[str, Any], workflow_dir: str):
        """Generate workflow README.
        
        Args:
            workflow_structure: Workflow structure dict
            workflow_dir: Workflow directory
        """
        readme_path = os.path.join(workflow_dir, "README.md")
        with open(readme_path, 'w') as f:
            f.write(f"# {workflow_structure['name']}\n\n")
            f.write(f"## Workflow Overview\n\n")
            f.write(f"**Type**: {workflow_structure.get('type', 'WORKFLOW')}\n\n")
            f.write(f"**Sessions**: {len(workflow_structure.get('sessions', []))}\n\n")
            total_mappings = sum(len(s.get('mappings', [])) for s in workflow_structure.get('sessions', []))
            f.write(f"**Mappings**: {total_mappings}\n\n")
            f.write(f"## Sessions\n\n")
            for session in workflow_structure.get('sessions', []):
                f.write(f"- **{session['name']}**: {len(session.get('mappings', []))} mapping(s)\n")
    
    def _generate_session_config(self, session: Dict[str, Any], session_dir: str):
        """Generate session configuration file.
        
        Args:
            session: Session dict
            session_dir: Session directory
        """
        config_path = os.path.join(session_dir, "session_config.json")
        with open(config_path, 'w') as f:
            json.dump({
                "name": session["name"],
                "type": session.get("type", "SESSION"),
                "properties": session.get("properties", {}),
                "mappings": [m["name"] for m in session.get("mappings", [])]
            }, f, indent=2)
    
    def _generate_mapping_spec(self, canonical_model: Dict[str, Any], mapping_dir: str):
        """Generate mapping specification.
        
        Args:
            canonical_model: Canonical model dict
            mapping_dir: Mapping directory
        """
        try:
            from generators import SpecGenerator
            spec_generator = SpecGenerator()
            spec = spec_generator.generate(canonical_model)
            spec_path = os.path.join(mapping_dir, "mapping_spec.md")
            with open(spec_path, 'w') as f:
                f.write(spec)
        except Exception as e:
            # Spec generation is optional
            pass
    
    def _generate_workflow_orchestration(self, workflow_structure: Dict[str, Any], orchestration_dir: str):
        """Generate workflow orchestration files.
        
        Args:
            workflow_structure: Workflow structure dict
            orchestration_dir: Orchestration directory
        """
        try:
            from generators.orchestration_generator import OrchestrationGenerator
            orchestration_gen = OrchestrationGenerator()
            
            # Generate Airflow DAG
            airflow_dag = orchestration_gen.generate_airflow_dag(workflow_structure)
            airflow_path = os.path.join(orchestration_dir, "airflow_dag.py")
            with open(airflow_path, 'w') as f:
                f.write(airflow_dag)
            print(f"         ✅ Generated Airflow DAG: {os.path.basename(airflow_path)}")
            
            # Generate Databricks Workflow
            databricks_workflow = orchestration_gen.generate_databricks_workflow(workflow_structure)
            databricks_path = os.path.join(orchestration_dir, "databricks_workflow.json")
            with open(databricks_path, 'w') as f:
                json.dump(databricks_workflow, f, indent=2)
            print(f"         ✅ Generated Databricks Workflow: {os.path.basename(databricks_path)}")
            
            # Generate Prefect Flow (optional)
            prefect_flow = orchestration_gen.generate_prefect_flow(workflow_structure)
            prefect_path = os.path.join(orchestration_dir, "prefect_flow.py")
            with open(prefect_path, 'w') as f:
                f.write(prefect_flow)
            print(f"         ✅ Generated Prefect Flow: {os.path.basename(prefect_path)}")
            
            # Generate documentation
            docs = orchestration_gen.generate_workflow_documentation(workflow_structure)
            docs_path = os.path.join(orchestration_dir, "README.md")
            with open(docs_path, 'w') as f:
                f.write(docs)
            print(f"         ✅ Generated Workflow Documentation: {os.path.basename(docs_path)}")
            
        except ImportError:
            # Fallback to basic DAG JSON if orchestration generator not available
            print("         ⚠️  Orchestration generator not available, generating basic DAG JSON")
            dag_data = {
                "workflow": workflow_structure["name"],
                "sessions": [
                    {
                        "name": s["name"],
                        "mappings": [m["name"] for m in s.get("mappings", [])]
                    }
                    for s in workflow_structure.get("sessions", [])
                ]
            }
            
            dag_path = os.path.join(orchestration_dir, "workflow_dag.json")
            with open(dag_path, 'w') as f:
                json.dump(dag_data, f, indent=2)
        except Exception as e:
            print(f"         ⚠️  Failed to generate orchestration code: {e}")
            # Still generate basic DAG JSON as fallback
            dag_data = {
                "workflow": workflow_structure["name"],
                "sessions": [
                    {
                        "name": s["name"],
                        "mappings": [m["name"] for m in s.get("mappings", [])]
                    }
                    for s in workflow_structure.get("sessions", [])
                ]
            }
            
            dag_path = os.path.join(orchestration_dir, "workflow_dag.json")
            with open(dag_path, 'w') as f:
                json.dump(dag_data, f, indent=2)
    
    def _generate_shared_code(self, all_transformations: Dict[str, List], shared_dir: str, results: Dict[str, Any]):
        """Generate shared/reusable code from common patterns.
        
        Args:
            all_transformations: Dict of transformation type to list of transformations
            shared_dir: Shared code directory
            results: Results dictionary to update
        """
        # Create shared utilities
        utils_path = os.path.join(shared_dir, "common_utils.py")
        with open(utils_path, 'w') as f:
            f.write('"""Common utilities and reusable functions."""\n')
            f.write('from pyspark.sql import functions as F\n')
            f.write('from pyspark.sql.types import *\n\n')
            f.write('# Common transformation patterns\n')
            f.write('# This file contains reusable functions extracted from common patterns\n\n')
        
        results["shared_code"].append({"file": utils_path, "type": "utilities"})
        
        # Create config directory
        config_dir = os.path.join(shared_dir, "config")
        os.makedirs(config_dir, exist_ok=True)
        
        # Generate database config template
        db_config_path = os.path.join(config_dir, "database_config.py")
        with open(db_config_path, 'w') as f:
            f.write('"""Database configuration."""\n\n')
            f.write('# Update with your database connection details\n')
            f.write('DATABASE_CONFIG = {\n')
            f.write('    "source_db": {\n')
            f.write('        "host": "your_source_host",\n')
            f.write('        "database": "your_source_database"\n')
            f.write('    },\n')
            f.write('    "target_db": {\n')
            f.write('        "host": "your_target_host",\n')
            f.write('        "database": "your_target_database"\n')
            f.write('    }\n')
            f.write('}\n')
        
        results["shared_code"].append({"file": db_config_path, "type": "config"})
        
        # Generate Spark config
        spark_config_path = os.path.join(config_dir, "spark_config.py")
        with open(spark_config_path, 'w') as f:
            f.write('"""Spark configuration."""\n\n')
            f.write('from pyspark.sql import SparkSession\n\n')
            f.write('def get_spark_session(app_name: str = "InformaticaMigration"):\n')
            f.write('    """Get or create Spark session."""\n')
            f.write('    return SparkSession.builder.appName(app_name).getOrCreate()\n')
        
        results["shared_code"].append({"file": spark_config_path, "type": "config"})
        
        print(f"   ✅ Generated shared code in: {shared_dir}")
    
    def _build_workflows_from_files(self) -> List[Dict[str, Any]]:
        """Build workflow structure from parsed JSON files.
        
        Returns:
            List of workflow structures
        """
        project_root = Path(__file__).parent.parent
        parsed_dir = os.path.join(project_root, "test_log", "parsed")
        
        workflows = []
        
        # Find workflow JSON files
        workflow_files = glob.glob(os.path.join(parsed_dir, "*_workflow.json"))
        
        for workflow_file in workflow_files:
            try:
                with open(workflow_file, 'r') as f:
                    workflow_data = json.load(f)
                
                workflow_name = workflow_data.get("name", "")
                if not workflow_name:
                    continue
                
                # Build workflow structure
                workflow_structure = {
                    "name": workflow_name,
                    "type": "WORKFLOW",
                    "sessions": []
                }
                
                # Find session files that reference this workflow
                session_files = glob.glob(os.path.join(parsed_dir, "*_session.json"))
                for session_file in session_files:
                    try:
                        with open(session_file, 'r') as f:
                            session_data = json.load(f)
                        
                        # Check if session is part of this workflow (via tasks/links)
                        # For now, we'll include all sessions and let the user organize
                        session_name = session_data.get("name", "")
                        if session_name:
                            # Find mappings executed by this session
                            mappings = []
                            # Try to find mappings from parsed files
                            mapping_files = glob.glob(os.path.join(parsed_dir, "M_*.json"))
                            for mapping_file in mapping_files:
                                # Skip workflow/session/worklet files
                                if "_workflow.json" in mapping_file or "_session.json" in mapping_file or "_worklet.json" in mapping_file:
                                    continue
                                
                                try:
                                    with open(mapping_file, 'r') as f:
                                        mapping_data = json.load(f)
                                    mapping_name = mapping_data.get("mapping_name", "")
                                    if mapping_name:
                                        mappings.append({
                                            "name": mapping_name,
                                            "mapping_name": mapping_name,
                                            "complexity": mapping_data.get("_performance_metadata", {}).get("estimated_complexity", "UNKNOWN")
                                        })
                                except Exception:
                                    continue
                            
                            workflow_structure["sessions"].append({
                                "name": session_name,
                                "type": "SESSION",
                                "properties": {},
                                "mappings": mappings
                            })
                    except Exception:
                        continue
                
                if workflow_structure["sessions"]:
                    workflows.append(workflow_structure)
                    
            except Exception as e:
                print(f"   ⚠️  Failed to load workflow from {workflow_file}: {e}")
                continue
        
        return workflows
    
    def _generate_code_workflow_aware_from_files(self, workflows: List[Dict[str, Any]],
                                                 version_store: VersionStore,
                                                 generators: Dict[str, Any],
                                                 output_dir: str,
                                                 results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code organized by workflow structure (from parsed files).
        
        Args:
            workflows: List of workflows from parsed files
            version_store: VersionStore instance
            generators: Code generators dict
            output_dir: Base output directory
            results: Results dictionary to update
            
        Returns:
            Updated results dictionary
        """
        workflows_dir = os.path.join(output_dir, "workflows")
        shared_dir = os.path.join(output_dir, "shared")
        os.makedirs(workflows_dir, exist_ok=True)
        os.makedirs(shared_dir, exist_ok=True)
        
        for workflow in workflows:
            workflow_name = workflow["name"]
            print(f"\n🔄 Processing workflow: {workflow_name}")
            
            # Create workflow directory
            workflow_dir = os.path.join(workflows_dir, workflow_name.lower().replace("wf_", "").replace(" ", "_"))
            os.makedirs(workflow_dir, exist_ok=True)
            
            # Generate workflow README
            self._generate_workflow_readme(workflow, workflow_dir)
            
            # Process sessions
            sessions_dir = os.path.join(workflow_dir, "sessions")
            os.makedirs(sessions_dir, exist_ok=True)
            
            for session in workflow.get("sessions", []):
                session_name = session["name"]
                print(f"   ⚙️  Processing session: {session_name}")
                
                session_dir = os.path.join(sessions_dir, session_name.lower().replace("s_", "").replace(" ", "_"))
                os.makedirs(session_dir, exist_ok=True)
                
                # Generate session config
                self._generate_session_config(session, session_dir)
                
                # Process mappings in session
                mappings_dir = os.path.join(session_dir, "mappings")
                os.makedirs(mappings_dir, exist_ok=True)
                
                for mapping_info in session.get("mappings", []):
                    mapping_name = mapping_info["name"]
                    mapping_name_clean = mapping_name.lower().replace("m_", "").replace(" ", "_")
                    
                    print(f"      📋 Generating code for mapping: {mapping_name}")
                    
                    # Load canonical model
                    canonical_model = None
                    try:
                        canonical_model = version_store.load(mapping_name)
                        if not canonical_model:
                            canonical_model = self._load_canonical_model_from_files(mapping_name)
                    except Exception as e:
                        print(f"      ⚠️  Failed to load canonical model: {e}")
                        results["failed"].append({
                            "mapping": mapping_name,
                            "workflow": workflow_name,
                            "session": session_name,
                            "error": f"Failed to load model: {str(e)}"
                        })
                        continue
                    
                    if not canonical_model:
                        print(f"      ⚠️  Canonical model not found: {mapping_name}")
                        continue
                    
                    # Generate code for mapping
                    mapping_dir = os.path.join(mappings_dir, mapping_name_clean)
                    os.makedirs(mapping_dir, exist_ok=True)
                    
                    # Only generate PySpark code (regular transformation code, not DLT)
                    code_type = "pyspark"
                    generator = generators["pyspark"]
                    try:
                        code = generator.generate(canonical_model)
                        
                        # Generate descriptive filename
                        code_file = os.path.join(mapping_dir, f"{mapping_name_clean}_pyspark.py")
                        
                        with open(code_file, 'w') as f:
                            f.write(code)
                        
                        print(f"         ✅ Generated {code_type.upper()}: {os.path.basename(code_file)}")
                        
                        results["generated"].append({
                            "mapping": mapping_name,
                            "type": code_type,
                            "file": code_file,
                            "workflow": workflow_name,
                            "session": session_name
                        })
                        
                    except Exception as e:
                        error_msg = str(e)
                        print(f"         ⚠️  {code_type.upper()} generation failed: {error_msg}")
                        results["failed"].append({
                            "mapping": mapping_name,
                            "type": code_type,
                            "error": error_msg,
                            "workflow": workflow_name,
                            "session": session_name
                        })
                    
                    # Generate mapping spec
                    self._generate_mapping_spec(canonical_model, mapping_dir)
            
            # Generate workflow orchestration files
            orchestration_dir = os.path.join(workflow_dir, "orchestration")
            os.makedirs(orchestration_dir, exist_ok=True)
            self._generate_workflow_orchestration(workflow, orchestration_dir)
            
            results["workflows"].append({
                "name": workflow_name,
                "sessions": len(workflow.get("sessions", [])),
                "mappings": sum(len(s.get("mappings", [])) for s in workflow.get("sessions", []))
            })
        
        # Generate shared code
        print(f"\n📦 Generating shared/reusable code...")
        self._generate_shared_code({}, shared_dir, results)
        
        # Save summary
        summary_file = os.path.join(output_dir, "generation_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 Summary:")
        print(f"   Workflows: {len(results['workflows'])}")
        print(f"   Generated files: {len(results['generated'])}")
        print(f"   Failed: {len(results['failed'])}")
        print(f"   Shared code files: {len(results['shared_code'])}")
        
        return results
    
    def review_code(self, generated_dir: str, output_dir: str) -> Dict[str, Any]:
        """Review and fix code with AI, preserving directory structure.
        
        Args:
            generated_dir: Directory with generated code
            output_dir: Directory to save reviewed/fixed code
            
        Returns:
            Dictionary with review results
        """
        print(f"\n{'='*60}")
        print("STEP H: Review & Fix Code with AI")
        print(f"{'='*60}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            from ai_agents import AgentOrchestrator
            orchestrator = AgentOrchestrator()
        except ImportError:
            print("⚠️  AI agents not available, skipping code review")
            return {"reviewed": [], "failed": [], "skipped": True}
        
        # Find generated code files (preserve directory structure)
        code_files = []
        for ext in ["*.py", "*.sql"]:
            code_files.extend(glob.glob(os.path.join(generated_dir, "**", ext), recursive=True))
        
        if not code_files:
            print("⚠️  No generated code files found")
            return {"reviewed": [], "failed": []}
        
        results = {"reviewed": [], "failed": []}
        
        for code_file in code_files:
            filename = os.path.basename(code_file)
            rel_path = os.path.relpath(code_file, generated_dir)
            print(f"\n🔍 Reviewing: {rel_path}")
            
            try:
                # Read code
                with open(code_file, 'r') as f:
                    code = f.read()
                
                # Detect actual code type from content
                actual_code_type = self._detect_code_type(code, filename)
                original_ext = os.path.splitext(filename)[1]
                
                # Review code
                review = orchestrator.review_code(code)
                
                # Preserve directory structure in output
                rel_dir = os.path.dirname(rel_path)
                if rel_dir:
                    output_subdir = os.path.join(output_dir, rel_dir)
                    os.makedirs(output_subdir, exist_ok=True)
                else:
                    output_subdir = output_dir
                
                # Save review results (preserve structure)
                review_filename = f"{os.path.splitext(filename)[0]}_review.json"
                review_file = os.path.join(output_subdir, review_filename)
                with open(review_file, 'w') as f:
                    json.dump(review, f, indent=2, default=str)
                
                # Fix code if needed
                fixed_code = code
                if review.get("needs_fix") and review.get("issues"):
                    try:
                        fix_result = orchestrator.fix_code(code, review.get("issues", []))
                        fixed_code = fix_result.get("fixed_code", code)
                        
                        # Re-detect code type after fix (may have changed)
                        actual_code_type_after_fix = self._detect_code_type(fixed_code, filename)
                        
                        # Determine correct filename based on actual code type
                        base_name = os.path.splitext(filename)[0]
                        # Remove existing type suffix if present
                        for suffix in ["_pyspark", "_dlt", "_sql"]:
                            if base_name.endswith(suffix):
                                base_name = base_name[:-len(suffix)]
                                break
                        
                        # Set correct extension based on actual code type
                        if actual_code_type_after_fix == "python":
                            fixed_filename = f"{base_name}_pyspark.py"
                        elif actual_code_type_after_fix == "dlt":
                            fixed_filename = f"{base_name}_dlt.py"
                        else:
                            # Keep original extension if still SQL
                            fixed_filename = f"{base_name}_sql.sql"
                        
                        # Save fixed code with correct filename
                        fixed_file = os.path.join(output_subdir, fixed_filename)
                        with open(fixed_file, 'w') as f:
                            f.write(fixed_code)
                        
                        # If filename changed, note it
                        if fixed_filename != filename:
                            print(f"   ⚠️  Code type changed: {original_ext} -> .py (renamed to {fixed_filename})")
                        
                        print(f"   ✅ Fixed code saved to: {fixed_file}")
                    except Exception as e:
                        print(f"   ⚠️  Code fix failed: {e}")
                        # Save original code even if fix failed
                        fixed_file = os.path.join(output_subdir, filename)
                        with open(fixed_file, 'w') as f:
                            f.write(code)
                
                print(f"   ✅ Review saved to: {review_file}")
                print(f"   📊 Issues found: {len(review.get('issues', []))}")
                
                results["reviewed"].append({
                    "file": rel_path,
                    "review_file": review_file,
                    "issues_count": len(review.get("issues", [])),
                    "fixed": review.get("needs_fix", False),
                    "code_type": actual_code_type
                })
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results["failed"].append({"file": rel_path, "error": str(e)})
        
        # Save summary
        summary_file = os.path.join(output_dir, "review_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 Summary: {len(results['reviewed'])} reviewed, {len(results['failed'])} failed")
        return results
    
    def run_assessment(self, output_dir: str) -> Dict[str, Any]:
        """Run pre-migration assessment.
        
        Args:
            output_dir: Directory to save assessment reports
            
        Returns:
            Dictionary with assessment results
        """
        print(f"\n{'='*60}")
        print("STEP I: Pre-Migration Assessment")
        print(f"{'='*60}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize graph store
        try:
            from config import settings
            enable_graph = getattr(settings, 'enable_graph_store', False) or os.getenv('ENABLE_GRAPH_STORE', 'false').lower() == 'true'
            if not enable_graph:
                print("⚠️  Graph store not enabled. Assessment requires Neo4j.")
                return {"skipped": True, "reason": "Graph store not enabled"}
            
            graph_store = GraphStore(
                uri=getattr(settings, 'neo4j_uri', os.getenv('NEO4J_URI', 'bolt://localhost:7687')),
                user=getattr(settings, 'neo4j_user', os.getenv('NEO4J_USER', 'neo4j')),
                password=getattr(settings, 'neo4j_password', os.getenv('NEO4J_PASSWORD', 'password'))
            )
        except Exception as e:
            print(f"❌ Failed to initialize graph store: {e}")
            return {"failed": True, "error": str(e)}
        
        try:
            # Initialize assessment components
            profiler = Profiler(graph_store)
            analyzer = Analyzer(graph_store, profiler)
            wave_planner = WavePlanner(graph_store, profiler, analyzer)
            report_generator = ReportGenerator(graph_store, profiler, analyzer, wave_planner)
            
            # Run assessment with progress indicators
            print("\n📊 Profiling repository...")
            try:
                from tqdm import tqdm
                use_progress = True
            except ImportError:
                use_progress = False
            
            profile = profiler.profile_repository()
            print(f"   ✅ Found {profile['total_workflows']} workflows, {profile['total_mappings']} mappings")
            
            print("\n🔍 Analyzing components...")
            patterns = analyzer.identify_patterns()
            blockers = analyzer.identify_blockers()
            effort = analyzer.estimate_migration_effort()
            dependencies = analyzer.find_dependencies()
            
            print(f"   ✅ Identified {len(blockers)} blockers, {len(dependencies['dependency_graph'])} dependencies")
            print(f"   📈 Estimated effort: {effort['total_effort_days']:.1f} days")
            
            print("\n🌊 Planning migration waves...")
            waves = wave_planner.plan_migration_waves(max_wave_size=10)
            print(f"   ✅ Generated {len(waves)} migration waves")
            
            # Generate reports
            print("\n📄 Generating reports...")
            summary_report = report_generator.generate_summary_report()
            detailed_report = report_generator.generate_detailed_report()
            wave_plan = report_generator.generate_wave_plan(max_wave_size=10)
            
            # Save reports
            assessment_dir = os.path.join(output_dir, "assessment")
            os.makedirs(assessment_dir, exist_ok=True)
            
            summary_file = os.path.join(assessment_dir, "assessment_summary.json")
            detailed_file = os.path.join(assessment_dir, "assessment_detailed.json")
            wave_file = os.path.join(assessment_dir, "migration_waves.json")
            html_file = os.path.join(assessment_dir, "assessment_report.html")
            
            with open(summary_file, 'w') as f:
                json.dump(summary_report, f, indent=2, default=str)
            with open(detailed_file, 'w') as f:
                json.dump(detailed_report, f, indent=2, default=str)
            with open(wave_file, 'w') as f:
                json.dump(wave_plan, f, indent=2, default=str)
            
            report_generator.export_to_html(detailed_report, html_file)
            
            print(f"\n📊 Assessment Summary:")
            print(f"   Overall Complexity: {summary_report['overall_complexity']}")
            print(f"   Total Effort: {summary_report['total_effort_days']:.1f} days")
            print(f"   Blockers: {summary_report['blocker_count']}")
            print(f"   Migration Waves: {summary_report['wave_count']}")
            print(f"\n📁 Reports saved to: {assessment_dir}")
            print(f"   - Summary: {summary_file}")
            print(f"   - Detailed: {detailed_file}")
            print(f"   - Waves: {wave_file}")
            print(f"   - HTML: {html_file}")
            
            return {
                "success": True,
                "summary": summary_report,
                "reports": {
                    "summary": summary_file,
                    "detailed": detailed_file,
                    "waves": wave_file,
                    "html": html_file
                }
            }
            
        except Exception as e:
            print(f"❌ Assessment failed: {e}")
            import traceback
            traceback.print_exc()
            return {"failed": True, "error": str(e)}
    
    def _detect_code_type(self, code: str, filename: str) -> str:
        """Detect actual code type from content.
        
        Args:
            code: Code content
            filename: Original filename
            
        Returns:
            Code type: 'python', 'dlt', or 'sql'
        """
        code_lower = code.lower()
        
        # Check for Python/DataFrame operations
        python_indicators = [
            "from pyspark",
            "import pyspark",
            "spark.createDataFrame",
            "spark.table(",
            "df.write",
            "df.select",
            "df.filter",
            "df.join",
            "col(",
            "F.",
            "functions as F"
        ]
        
        # Check for DLT
        dlt_indicators = [
            "@dlt.table",
            "import dlt",
            "dlt.read(",
            "dlt.table("
        ]
        
        # Check for SQL
        sql_indicators = [
            "select ",
            "from ",
            "where ",
            "group by",
            "order by",
            "insert into",
            "create table"
        ]
        
        # Count indicators
        python_count = sum(1 for indicator in python_indicators if indicator in code_lower)
        dlt_count = sum(1 for indicator in dlt_indicators if indicator in code_lower)
        sql_count = sum(1 for indicator in sql_indicators if indicator in code_lower and 
                       not any(py_ind in code_lower for py_ind in python_indicators))
        
        # Determine type
        if dlt_count > 0:
            return "dlt"
        elif python_count > 0:
            return "python"
        elif sql_count > 2 and python_count == 0:
            return "sql"
        else:
            # Default based on filename
            if filename.endswith(".py"):
                return "python"
            elif filename.endswith(".sql"):
                return "sql"
            else:
                return "python"  # Default to Python


def main():
    parser = argparse.ArgumentParser(description="Step-by-step testing for Informatica Modernization")
    parser.add_argument("command", choices=["upload", "parse", "enhance", "hierarchy", "lineage", "canonical", "code", "review", "assess"],
                       help="Command to execute")
    parser.add_argument("--files", help="File paths or glob patterns (for upload)")
    parser.add_argument("--staging-dir", default="test_log/staging", help="Staging directory")
    parser.add_argument("--parsed-dir", default="test_log/parsed", help="Parsed models directory")
    parser.add_argument("--output-dir", default="test_log", help="Output directory")
    parser.add_argument("--generated-dir", default="test_log/generated", help="Generated code directory")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    parser.add_argument("--no-api", action="store_true", help="Don't use API, use direct Python calls")
    
    args = parser.parse_args()
    
    flow = TestFlow(api_url=args.api_url, use_api=not args.no_api)
    
    if args.command == "upload":
        if not args.files:
            print("Error: --files is required for upload command")
            sys.exit(1)
        file_list = args.files.split()
        flow.upload_files(file_list, args.staging_dir)
    
    elif args.command == "parse":
        flow.parse_mappings(args.staging_dir, args.parsed_dir)
    
    elif args.command == "enhance":
        # Use output_dir directly (Makefile already sets it to test_log/parse_ai)
        flow.enhance_with_ai(args.parsed_dir, args.output_dir)
    
    elif args.command == "hierarchy":
        flow.generate_hierarchy(args.output_dir)
    
    elif args.command == "lineage":
        flow.generate_lineage(args.output_dir, args.staging_dir)
    
    elif args.command == "canonical":
        flow.generate_canonical_images(args.output_dir)
    
    elif args.command == "code":
        # output_dir should already be test_log/generated from Makefile
        flow.generate_code(args.output_dir)
    
    elif args.command == "review":
        # Use output_dir directly (Makefile already sets it to test_log/generated_ai)
        flow.review_code(args.generated_dir, args.output_dir)
    
    elif args.command == "assess":
        # Run assessment after parsing
        flow.run_assessment(args.output_dir)


if __name__ == "__main__":
    main()

