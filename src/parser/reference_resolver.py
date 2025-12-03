"""Reference Resolver - Resolves references between Informatica objects.
Resolves mapping references in sessions, worklet references in workflows, etc.
"""
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from utils.exceptions import ValidationError, ParsingError
from utils.logger import get_logger
from parser import MappingParser, WorkflowParser, SessionParser, WorkletParser, MappletParser
from versioning.version_store import VersionStore

logger = get_logger(__name__)


class ReferenceResolver:
    """Resolves references between Informatica objects."""
    
    def __init__(self, version_store: Optional[VersionStore] = None):
        """Initialize reference resolver.
        
        Args:
            version_store: Optional version store for loading parsed objects
        """
        self.version_store = version_store or VersionStore()
        self.parsed_objects: Dict[str, Dict[str, Any]] = {}
        self.file_paths: Dict[str, str] = {}
    
    def register_mapping(self, mapping_name: str, mapping_data: Dict[str, Any], file_path: Optional[str] = None):
        """Register a parsed mapping.
        
        Args:
            mapping_name: Name of the mapping
            mapping_data: Parsed mapping data
            file_path: Optional file path
        """
        self.parsed_objects[f"mapping:{mapping_name}"] = mapping_data
        if file_path:
            self.file_paths[f"mapping:{mapping_name}"] = file_path
        logger.debug(f"Registered mapping: {mapping_name}")
    
    def register_session(self, session_name: str, session_data: Dict[str, Any], file_path: Optional[str] = None):
        """Register a parsed session.
        
        Args:
            session_name: Name of the session
            session_data: Parsed session data
            file_path: Optional file path
        """
        self.parsed_objects[f"session:{session_name}"] = session_data
        if file_path:
            self.file_paths[f"session:{session_name}"] = file_path
        logger.debug(f"Registered session: {session_name}")
    
    def register_workflow(self, workflow_name: str, workflow_data: Dict[str, Any], file_path: Optional[str] = None):
        """Register a parsed workflow.
        
        Args:
            workflow_name: Name of the workflow
            workflow_data: Parsed workflow data
            file_path: Optional file path
        """
        self.parsed_objects[f"workflow:{workflow_name}"] = workflow_data
        if file_path:
            self.file_paths[f"workflow:{workflow_name}"] = file_path
        logger.debug(f"Registered workflow: {workflow_name}")
    
    def register_worklet(self, worklet_name: str, worklet_data: Dict[str, Any], file_path: Optional[str] = None):
        """Register a parsed worklet.
        
        Args:
            worklet_name: Name of the worklet
            worklet_data: Parsed worklet data
            file_path: Optional file path
        """
        self.parsed_objects[f"worklet:{worklet_name}"] = worklet_data
        if file_path:
            self.file_paths[f"worklet:{worklet_name}"] = file_path
        logger.debug(f"Registered worklet: {worklet_name}")
    
    def register_mapplet(self, mapplet_name: str, mapplet_data: Dict[str, Any], file_path: Optional[str] = None):
        """Register a parsed mapplet.
        
        Args:
            mapplet_name: Name of the mapplet
            mapplet_data: Parsed mapplet data
            file_path: Optional file path
        """
        self.parsed_objects[f"mapplet:{mapplet_name}"] = mapplet_data
        if file_path:
            self.file_paths[f"mapplet:{mapplet_name}"] = file_path
        logger.debug(f"Registered mapplet: {mapplet_name}")
    
    def register_reusable_transformation(self, reusable_name: str, transformation_data: Dict[str, Any]):
        """Register a reusable transformation.
        
        Args:
            reusable_name: Name of the reusable transformation
            transformation_data: Parsed transformation data
        """
        self.parsed_objects[f"reusable:{reusable_name}"] = transformation_data
        logger.debug(f"Registered reusable transformation: {reusable_name}")
    
    def resolve_reusable_transformations(self, mapping_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Resolve reusable transformation references in mapping.
        
        Args:
            mapping_data: Mapping data with reusable transformation references
            
        Returns:
            Dictionary of resolved reusable transformations keyed by reusable name
        """
        resolved_reusables = {}
        transformations = mapping_data.get("transformations", [])
        
        for trans in transformations:
            if trans.get("is_reusable", False):
                reusable_name = trans.get("reusable_name", trans.get("name", ""))
                if reusable_name and reusable_name not in resolved_reusables:
                    # Check if already registered
                    key = f"reusable:{reusable_name}"
                    if key in self.parsed_objects:
                        resolved_reusables[reusable_name] = self.parsed_objects[key]
                        logger.debug(f"Resolved reusable transformation {reusable_name} from parsed objects")
                    else:
                        # Store the transformation itself as the reusable definition
                        resolved_reusables[reusable_name] = trans
                        self.register_reusable_transformation(reusable_name, trans)
        
        return resolved_reusables
    
    def resolve_session_mapping(self, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Resolve mapping reference in session.
        
        Args:
            session_data: Session data with mapping reference
            
        Returns:
            Resolved mapping data or None if not found
        """
        mapping_name = session_data.get("mapping")
        if not mapping_name:
            return None
        
        # Try to get from parsed objects
        key = f"mapping:{mapping_name}"
        if key in self.parsed_objects:
            logger.debug(f"Resolved mapping {mapping_name} from parsed objects")
            return self.parsed_objects[key]
        
        # Try to get from version store
        try:
            mapping_data = self.version_store.load(mapping_name)
            if mapping_data:
                logger.debug(f"Resolved mapping {mapping_name} from version store")
                return mapping_data
        except Exception as e:
            logger.warning(f"Could not load mapping {mapping_name} from version store: {e}")
        
        # Try to load from file path if available
        if key in self.file_paths:
            try:
                parser = MappingParser(self.file_paths[key])
                mapping_data = parser.parse()
                self.register_mapping(mapping_name, mapping_data, self.file_paths[key])
                return mapping_data
            except Exception as e:
                logger.warning(f"Could not load mapping {mapping_name} from file: {e}")
        
        logger.warning(f"Mapping {mapping_name} not found")
        return None
    
    def resolve_workflow_worklets(self, workflow_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Resolve worklet references in workflow.
        
        Args:
            workflow_data: Workflow data with worklet references
            
        Returns:
            Dictionary of resolved worklets keyed by worklet name
        """
        resolved_worklets = {}
        tasks = workflow_data.get("tasks", [])
        
        for task in tasks:
            if task.get("type") == "Worklet":
                worklet_name = task.get("name")
                if worklet_name:
                    # Try to get from parsed objects
                    key = f"worklet:{worklet_name}"
                    if key in self.parsed_objects:
                        resolved_worklets[worklet_name] = self.parsed_objects[key]
                        logger.debug(f"Resolved worklet {worklet_name} from parsed objects")
                        continue
                    
                    # Try to get from version store
                    try:
                        worklet_data = self.version_store.load(worklet_name)
                        if worklet_data:
                            resolved_worklets[worklet_name] = worklet_data
                            logger.debug(f"Resolved worklet {worklet_name} from version store")
                            continue
                    except Exception as e:
                        logger.warning(f"Could not load worklet {worklet_name} from version store: {e}")
                    
                    # Try to load from file path if available
                    if key in self.file_paths:
                        try:
                            parser = WorkletParser(self.file_paths[key])
                            worklet_data = parser.parse()
                            self.register_worklet(worklet_name, worklet_data, self.file_paths[key])
                            resolved_worklets[worklet_name] = worklet_data
                            continue
                        except Exception as e:
                            logger.warning(f"Could not load worklet {worklet_name} from file: {e}")
                    
                    logger.warning(f"Worklet {worklet_name} not found")
        
        return resolved_worklets
    
    def resolve_mapping_mapplets(self, mapping_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Resolve mapplet references in mapping.
        
        Args:
            mapping_data: Mapping data with mapplet instance references
            
        Returns:
            Dictionary of resolved mapplets keyed by mapplet name
        """
        resolved_mapplets = {}
        transformations = mapping_data.get("transformations", [])
        
        for trans in transformations:
            if trans.get("type") == "MAPPLET_INSTANCE":
                mapplet_ref = trans.get("mapplet_ref")
                if mapplet_ref and mapplet_ref not in resolved_mapplets:
                    # Try to get from parsed objects
                    key = f"mapplet:{mapplet_ref}"
                    if key in self.parsed_objects:
                        resolved_mapplets[mapplet_ref] = self.parsed_objects[key]
                        logger.debug(f"Resolved mapplet {mapplet_ref} from parsed objects")
                        continue
                    
                    # Try to get from version store
                    try:
                        mapplet_data = self.version_store.load(mapplet_ref)
                        if mapplet_data:
                            resolved_mapplets[mapplet_ref] = mapplet_data
                            logger.debug(f"Resolved mapplet {mapplet_ref} from version store")
                            continue
                    except Exception as e:
                        logger.warning(f"Could not load mapplet {mapplet_ref} from version store: {e}")
                    
                    # Try to load from file path if available
                    if key in self.file_paths:
                        try:
                            parser = MappletParser(self.file_paths[key])
                            mapplet_data = parser.parse()
                            self.register_mapplet(mapplet_ref, mapplet_data, self.file_paths[key])
                            resolved_mapplets[mapplet_ref] = mapplet_data
                            continue
                        except Exception as e:
                            logger.warning(f"Could not load mapplet {mapplet_ref} from file: {e}")
                    
                    logger.warning(f"Mapplet {mapplet_ref} not found")
        
        return resolved_mapplets
    
    def resolve_transformation_references(self, mapping_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve transformation references within a mapping.
        
        Args:
            mapping_data: Mapping data with transformation references
            
        Returns:
            Mapping data with resolved references
        """
        transformations = mapping_data.get("transformations", [])
        connectors = mapping_data.get("connectors", [])
        
        # Build transformation lookup
        trans_lookup = {t.get("name"): t for t in transformations}
        
        # Resolve connector references
        for connector in connectors:
            from_trans = connector.get("from_transformation")
            to_trans = connector.get("to_transformation")
            
            if from_trans and from_trans not in trans_lookup:
                logger.warning(f"Source transformation {from_trans} not found in mapping")
            
            if to_trans and to_trans not in trans_lookup:
                logger.warning(f"Target transformation {to_trans} not found in mapping")
        
        # Resolve port references in expressions
        for trans in transformations:
            if trans.get("type") == "EXPRESSION":
                ports = trans.get("ports", [])
                for port in ports:
                    expression = port.get("expression", "")
                    if expression:
                        # Check for port references like :LKP.port_name
                        # This is handled by the translator, but we can validate here
                        pass
        
        return mapping_data
    
    def validate_references(self, session_data: Dict[str, Any]) -> List[str]:
        """Validate all references in a session.
        
        Args:
            session_data: Session data to validate
            
        Returns:
            List of validation errors (empty if all valid)
        """
        errors = []
        
        # Validate mapping reference
        mapping_name = session_data.get("mapping")
        if mapping_name:
            mapping = self.resolve_session_mapping(session_data)
            if not mapping:
                errors.append(f"Mapping '{mapping_name}' referenced in session '{session_data.get('name')}' not found")
        
        return errors
    
    def validate_workflow_references(self, workflow_data: Dict[str, Any]) -> List[str]:
        """Validate all references in a workflow.
        
        Args:
            workflow_data: Workflow data to validate
            
        Returns:
            List of validation errors (empty if all valid)
        """
        errors = []
        tasks = workflow_data.get("tasks", [])
        
        for task in tasks:
            task_name = task.get("name")
            task_type = task.get("type")
            
            if task_type == "Session":
                # Validate session mapping reference
                # This would require loading the session first
                pass
            elif task_type == "Worklet":
                worklet_name = task_name
                worklets = self.resolve_workflow_worklets(workflow_data)
                if worklet_name not in worklets:
                    errors.append(f"Worklet '{worklet_name}' referenced in workflow '{workflow_data.get('name')}' not found")
        
        return errors
    
    def validate_mapplet_references(self, mapping_data: Dict[str, Any]) -> List[str]:
        """Validate all mapplet references in a mapping.
        
        Args:
            mapping_data: Mapping data to validate
            
        Returns:
            List of validation errors (empty if all valid)
        """
        errors = []
        transformations = mapping_data.get("transformations", [])
        
        for trans in transformations:
            if trans.get("type") == "MAPPLET_INSTANCE":
                mapplet_ref = trans.get("mapplet_ref")
                mapplets = self.resolve_mapping_mapplets(mapping_data)
                if mapplet_ref not in mapplets:
                    errors.append(f"Mapplet '{mapplet_ref}' referenced in mapping '{mapping_data.get('name')}' not found")
        
        return errors
    
    def resolve_all(self, workflow_data: Dict[str, Any], session_data_list: List[Dict[str, Any]], 
                   mapping_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve all references in a complete workflow hierarchy.
        
        Args:
            workflow_data: Workflow data
            session_data_list: List of session data
            mapping_data_list: List of mapping data
            
        Returns:
            Complete resolved hierarchy
        """
        # Register all objects
        for mapping in mapping_data_list:
            self.register_mapping(mapping.get("name", ""), mapping)
        
        for session in session_data_list:
            self.register_session(session.get("name", ""), session)
        
        self.register_workflow(workflow_data.get("name", ""), workflow_data)
        
        # Resolve references
        resolved_workflow = workflow_data.copy()
        resolved_workflow["resolved_worklets"] = self.resolve_workflow_worklets(workflow_data)
        
        resolved_sessions = []
        for session in session_data_list:
            resolved_session = session.copy()
            mapping = self.resolve_session_mapping(session)
            if mapping:
                resolved_session["resolved_mapping"] = mapping
            resolved_sessions.append(resolved_session)
        
        return {
            "workflow": resolved_workflow,
            "sessions": resolved_sessions,
            "mappings": mapping_data_list
        }

