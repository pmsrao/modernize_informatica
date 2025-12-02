"""Graph Store — Neo4j implementation for canonical models."""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None

from src.utils.logger import get_logger
from src.utils.exceptions import ModernizationError

logger = get_logger(__name__)


class GraphStore:
    """Neo4j-based storage for canonical models."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", 
                 password: str = "password"):
        """Initialize Neo4j connection.
        
        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
        """
        if GraphDatabase is None:
            raise ModernizationError(
                "Neo4j driver not installed. Install with: pip install neo4j"
            )
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._verify_connectivity()
        self._create_indexes()
        logger.info(f"GraphStore initialized: {uri}")
    
    def _verify_connectivity(self):
        """Verify Neo4j connection."""
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Neo4j connection verified")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise ModernizationError(f"Neo4j connection failed: {str(e)}")
    
    def _create_indexes(self):
        """Create indexes for performance."""
        indexes = [
            "CREATE INDEX mapping_name IF NOT EXISTS FOR (m:Mapping) ON (m.name)",
            "CREATE INDEX transformation_name IF NOT EXISTS FOR (t:Transformation) ON (t.name)",
            "CREATE INDEX table_name IF NOT EXISTS FOR (t:Table) ON (t.name)",
            "CREATE INDEX source_name IF NOT EXISTS FOR (s:Source) ON (s.name)",
            "CREATE INDEX target_name IF NOT EXISTS FOR (t:Target) ON (t.name)",
            "CREATE INDEX workflow_name IF NOT EXISTS FOR (w:Workflow) ON (w.name)",
            "CREATE INDEX session_name IF NOT EXISTS FOR (s:Session) ON (s.name)",
            "CREATE INDEX worklet_name IF NOT EXISTS FOR (w:Worklet) ON (w.name)",
            "CREATE INDEX source_file_path IF NOT EXISTS FOR (f:SourceFile) ON (f.file_path)",
            "CREATE INDEX generated_code_path IF NOT EXISTS FOR (c:GeneratedCode) ON (c.file_path)"
        ]
        
        with self.driver.session() as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                except Exception as e:
                    # Index might already exist, which is fine
                    logger.debug(f"Index creation: {str(e)}")
    
    def save_mapping(self, canonical_model: Dict[str, Any]) -> str:
        """Save canonical model to Neo4j.
        
        Args:
            canonical_model: Canonical model dictionary
            
        Returns:
            Mapping name
        """
        mapping_name = canonical_model.get("mapping_name", "unknown")
        logger.info(f"Saving mapping to graph: {mapping_name}")
        
        with self.driver.session() as session:
            # Use transaction for atomicity
            session.execute_write(self._create_mapping_tx, canonical_model)
        
        logger.info(f"Successfully saved mapping to graph: {mapping_name}")
        return mapping_name
    
    @staticmethod
    def _create_mapping_tx(tx, model: Dict[str, Any]):
        """Transaction function to create mapping in graph."""
        mapping_name = model.get("mapping_name", "unknown")
        
        # 1. Create Mapping node
        mapping_props = {
            "name": mapping_name,
            "mapping_name": mapping_name,
            "scd_type": model.get("scd_type", "NONE"),
            "incremental_keys": model.get("incremental_keys", []),
            "complexity": model.get("_performance_metadata", {}).get("estimated_complexity", "UNKNOWN"),
            "created_at": model.get("_provenance", {}).get("enhanced_at", ""),
            "version": 1
        }
        
        tx.run("""
            MERGE (m:Mapping {name: $name})
            SET m += $props
        """, name=mapping_name, props=mapping_props)
        
        # 2. Create Source nodes
        for source in model.get("sources", []):
            source_name = source.get("name", "")
            table_name = source.get("table", "")
            database = source.get("database", "")
            
            # Create Source node
            tx.run("""
                MERGE (s:Source {name: $name, mapping: $mapping})
                SET s.table = $table, s.database = $database
                WITH s
                MATCH (m:Mapping {name: $mapping})
                MERGE (m)-[:HAS_SOURCE]->(s)
            """, name=source_name, mapping=mapping_name, 
                  table=table_name, database=database)
            
            # Create Table node and link
            if table_name:
                # Use 'Unknown' or empty string if database is None/empty
                db_value = database if database else 'Unknown'
                tx.run("""
                    MERGE (t:Table {name: $table, database: $database})
                    SET t.platform = COALESCE(t.platform, 'Unknown')
                    WITH t
                    MATCH (s:Source {name: $source, mapping: $mapping})
                    MERGE (s)-[:READS_TABLE]->(t)
                """, table=table_name, database=db_value,
                      source=source_name, mapping=mapping_name)
            
            # Create Field nodes
            for field in source.get("fields", []):
                field_name = field.get("name", "")
                tx.run("""
                    MERGE (f:Field {name: $field, parent: $parent})
                    SET f.data_type = $data_type, f.nullable = $nullable
                    WITH f
                    MATCH (s:Source {name: $parent, mapping: $mapping})
                    MERGE (s)-[:HAS_FIELD]->(f)
                """, field=field_name, parent=source_name, mapping=mapping_name,
                      data_type=field.get("data_type"), 
                      nullable=field.get("nullable", True))
        
        # 3. Create Target nodes
        for target in model.get("targets", []):
            target_name = target.get("name", "")
            table_name = target.get("table", "")
            database = target.get("database", "")
            
            tx.run("""
                MERGE (t:Target {name: $name, mapping: $mapping})
                SET t.table = $table, t.database = $database
                WITH t
                MATCH (m:Mapping {name: $mapping})
                MERGE (m)-[:HAS_TARGET]->(t)
            """, name=target_name, mapping=mapping_name,
                  table=table_name, database=database)
            
            if table_name:
                # Use 'Unknown' or empty string if database is None/empty
                db_value = database if database else 'Unknown'
                tx.run("""
                    MERGE (tab:Table {name: $table, database: $database})
                    SET tab.platform = COALESCE(tab.platform, 'Unknown')
                    WITH tab
                    MATCH (t:Target {name: $target, mapping: $mapping})
                    MERGE (t)-[:WRITES_TABLE]->(tab)
                """, table=table_name, database=db_value,
                      target=target_name, mapping=mapping_name)
        
        # 4. Create Transformation nodes
        for trans in model.get("transformations", []):
            trans_name = trans.get("name", "")
            trans_type = trans.get("type", "")
            
            # Prepare properties (exclude internal fields except _optimization_hint)
            # Neo4j only supports primitive types, so exclude complex objects like ports, connectors
            trans_props = {
                "name": trans_name,
                "type": trans_type,
                "mapping": mapping_name,
                "optimization_hint": trans.get("_optimization_hint")
            }
            
            # Add other non-internal properties (only primitive types)
            for key, value in trans.items():
                if not key.startswith("_") or key == "_optimization_hint":
                    if key not in ["name", "type", "ports", "connectors"]:  # Exclude complex objects
                        # Only add primitive types (str, int, float, bool, None) or lists of primitives
                        if isinstance(value, (str, int, float, bool, type(None))):
                            trans_props[key] = value
                        elif isinstance(value, list) and all(isinstance(item, (str, int, float, bool, type(None))) for item in value):
                            trans_props[key] = value
                        # For complex objects, serialize to JSON string
                        elif isinstance(value, (dict, list)):
                            trans_props[f"{key}_json"] = json.dumps(value)
            
            tx.run("""
                MERGE (t:Transformation {name: $name, mapping: $mapping})
                SET t += $props
                WITH t
                MATCH (m:Mapping {name: $mapping})
                MERGE (m)-[:HAS_TRANSFORMATION]->(t)
            """, name=trans_name, mapping=mapping_name, props=trans_props)
        
        # 5. Create Connector relationships
        logger.debug(f"Creating {len(model.get('connectors', []))} connector relationships")
        for conn in model.get("connectors", []):
            from_trans = conn.get("from_transformation", "")
            to_trans = conn.get("to_transformation", "")
            from_port = conn.get("from_port", "")
            to_port = conn.get("to_port", "")
            
            if not from_trans or not to_trans:
                continue
            
            # Check if from_trans is a Source
            source_result = tx.run("""
                MATCH (s:Source {name: $from_trans, mapping: $mapping})
                RETURN s
                LIMIT 1
            """, from_trans=from_trans, mapping=mapping_name)
            
            if source_result.single():
                # Source -> Transformation
                tx.run("""
                    MATCH (s:Source {name: $from_trans, mapping: $mapping})
                    MATCH (t:Transformation {name: $to_trans, mapping: $mapping})
                    MERGE (s)-[r:CONNECTS_TO]->(t)
                    SET r.from_port = $from_port, r.to_port = $to_port
                """, from_trans=from_trans, to_trans=to_trans, mapping=mapping_name,
                      from_port=from_port, to_port=to_port)
                logger.debug(f"Created Source->Transformation connector: {from_trans} -> {to_trans}")
                continue
            
            # Check if to_trans is a Target
            target_result = tx.run("""
                MATCH (t:Target {name: $to_trans, mapping: $mapping})
                RETURN t
                LIMIT 1
            """, to_trans=to_trans, mapping=mapping_name)
            
            if target_result.single():
                # Transformation -> Target
                tx.run("""
                    MATCH (trans:Transformation {name: $from_trans, mapping: $mapping})
                    MATCH (t:Target {name: $to_trans, mapping: $mapping})
                    MERGE (trans)-[r:CONNECTS_TO]->(t)
                    SET r.from_port = $from_port, r.to_port = $to_port
                """, from_trans=from_trans, to_trans=to_trans, mapping=mapping_name,
                      from_port=from_port, to_port=to_port)
                logger.debug(f"Created Transformation->Target connector: {from_trans} -> {to_trans}")
                continue
            
            # Transformation -> Transformation
            tx.run("""
                MATCH (t1:Transformation {name: $from_trans, mapping: $mapping})
                MATCH (t2:Transformation {name: $to_trans, mapping: $mapping})
                MERGE (t1)-[r:CONNECTS_TO]->(t2)
                SET r.from_port = $from_port, r.to_port = $to_port
            """, from_trans=from_trans, to_trans=to_trans, mapping=mapping_name,
                  from_port=from_port, to_port=to_port)
            logger.debug(f"Created Transformation->Transformation connector: {from_trans} -> {to_trans}")
    
    def load_mapping(self, mapping_name: str) -> Optional[Dict[str, Any]]:
        """Load canonical model from Neo4j.
        
        Args:
            mapping_name: Name of mapping to load
            
        Returns:
            Canonical model dictionary or None
        """
        logger.info(f"Loading mapping from graph: {mapping_name}")
        
        with self.driver.session() as session:
            result = session.execute_read(self._load_mapping_tx, mapping_name)
        
        if result:
            logger.info(f"Successfully loaded mapping from graph: {mapping_name}")
        else:
            logger.warning(f"Mapping not found in graph: {mapping_name}")
        
        return result
    
    @staticmethod
    def _load_mapping_tx(tx, mapping_name: str) -> Optional[Dict[str, Any]]:
        """Transaction function to load mapping from graph."""
        # Load mapping node
        mapping_result = tx.run("""
            MATCH (m:Mapping {name: $name})
            RETURN m
        """, name=mapping_name).single()
        
        if not mapping_result:
            return None
        
        mapping_node = dict(mapping_result["m"])
        model = {
            "mapping_name": mapping_node.get("mapping_name", mapping_name),
            "scd_type": mapping_node.get("scd_type", "NONE"),
            "incremental_keys": mapping_node.get("incremental_keys", []),
            "sources": [],
            "targets": [],
            "transformations": [],
            "connectors": []
        }
        
        # Load sources
        sources_result = tx.run("""
            MATCH (m:Mapping {name: $name})-[:HAS_SOURCE]->(s:Source)
            RETURN s
        """, name=mapping_name)
        
        for record in sources_result:
            source = dict(record["s"])
            model["sources"].append({
                "name": source.get("name"),
                "table": source.get("table"),
                "database": source.get("database"),
                "fields": []  # Load fields separately if needed
            })
        
        # Load targets
        targets_result = tx.run("""
            MATCH (m:Mapping {name: $name})-[:HAS_TARGET]->(t:Target)
            RETURN t
        """, name=mapping_name)
        
        for record in targets_result:
            target = dict(record["t"])
            model["targets"].append({
                "name": target.get("name"),
                "table": target.get("table"),
                "database": target.get("database"),
                "fields": []
            })
        
        # Load transformations
        trans_result = tx.run("""
            MATCH (m:Mapping {name: $name})-[:HAS_TRANSFORMATION]->(t:Transformation)
            RETURN t
        """, name=mapping_name)
        
        for record in trans_result:
            trans = dict(record["t"])
            trans_dict = {
                "name": trans.get("name"),
                "type": trans.get("type"),
                "ports": []
            }
            # Merge properties (deserialize JSON strings back to objects)
            for key, value in trans.items():
                if key not in ["name", "type"]:
                    # Deserialize JSON strings back to objects
                    if key.endswith("_json") and isinstance(value, str):
                        try:
                            original_key = key[:-5]  # Remove "_json" suffix
                            trans_dict[original_key] = json.loads(value)
                        except json.JSONDecodeError:
                            trans_dict[key] = value
                    else:
                        trans_dict[key] = value
            model["transformations"].append(trans_dict)
        
        # Load connectors from all relationship types
        # Source -> Transformation
        source_conns = tx.run("""
            MATCH (s:Source {mapping: $name})-[r:CONNECTS_TO]->(t:Transformation {mapping: $name})
            RETURN s.name as from, t.name as to, r.from_port as from_port, r.to_port as to_port
        """, name=mapping_name)
        
        for record in source_conns:
            model["connectors"].append({
                "from_transformation": record["from"],
                "to_transformation": record["to"],
                "from_port": record.get("from_port", ""),
                "to_port": record.get("to_port", "")
            })
        
        # Transformation -> Target
        target_conns = tx.run("""
            MATCH (t:Transformation {mapping: $name})-[r:CONNECTS_TO]->(target:Target {mapping: $name})
            RETURN t.name as from, target.name as to, r.from_port as from_port, r.to_port as to_port
        """, name=mapping_name)
        
        for record in target_conns:
            model["connectors"].append({
                "from_transformation": record["from"],
                "to_transformation": record["to"],
                "from_port": record.get("from_port", ""),
                "to_port": record.get("to_port", "")
            })
        
        # Transformation -> Transformation
        trans_conns = tx.run("""
            MATCH (t1:Transformation {mapping: $name})-[r:CONNECTS_TO]->(t2:Transformation {mapping: $name})
            RETURN t1.name as from, t2.name as to, r.from_port as from_port, r.to_port as to_port
        """, name=mapping_name)
        
        for record in trans_conns:
            model["connectors"].append({
                "from_transformation": record["from"],
                "to_transformation": record["to"],
                "from_port": record.get("from_port", ""),
                "to_port": record.get("to_port", "")
            })
        
        return model
    
    def query_dependencies(self, mapping_name: str) -> List[str]:
        """Find all mappings that depend on this mapping.
        
        Args:
            mapping_name: Mapping name
            
        Returns:
            List of dependent mapping names
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:Mapping {name: $name})<-[:DEPENDS_ON*]-(dependent:Mapping)
                RETURN DISTINCT dependent.name as name
            """, name=mapping_name)
            
            return [record["name"] for record in result]
    
    def query_mappings_using_table(self, table_name: str, database: str = None) -> List[str]:
        """Find all mappings using a specific table.
        
        Args:
            table_name: Table name
            database: Optional database name
            
        Returns:
            List of mapping names
        """
        with self.driver.session() as session:
            if database:
                result = session.run("""
                    MATCH (t:Table {name: $table, database: $database})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(m:Mapping)
                    RETURN DISTINCT m.name as name
                """, table=table_name, database=database)
            else:
                result = session.run("""
                    MATCH (t:Table {name: $table})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(m:Mapping)
                    RETURN DISTINCT m.name as name
                """, table=table_name)
            
            return [record["name"] for record in result]
    
    def delete_mapping(self, mapping_name: str) -> bool:
        """Delete mapping and all related nodes from graph.
        
        Args:
            mapping_name: Mapping name to delete
            
        Returns:
            True if deleted, False if not found
        """
        logger.info(f"Deleting mapping from graph: {mapping_name}")
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:Mapping {name: $name})
                DETACH DELETE m
                RETURN count(m) as deleted
            """, name=mapping_name).single()
            
            deleted = result["deleted"] > 0 if result else False
            
            if deleted:
                logger.info(f"Successfully deleted mapping from graph: {mapping_name}")
            else:
                logger.warning(f"Mapping not found in graph: {mapping_name}")
            
            return deleted
    
    def list_all_mappings(self) -> List[str]:
        """List all mapping names in graph.
        
        Returns:
            List of mapping names
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:Mapping)
                RETURN m.name as name
                ORDER BY m.name
            """)
            
            return [record["name"] for record in result]
    
    def save_workflow(self, workflow_data: Dict[str, Any]) -> str:
        """Save workflow to Neo4j.
        
        Args:
            workflow_data: Workflow data dictionary with name, tasks, links
            
        Returns:
            Workflow name
        """
        workflow_name = workflow_data.get("name", "unknown")
        logger.info(f"Saving workflow to graph: {workflow_name}")
        
        with self.driver.session() as session:
            session.execute_write(self._create_workflow_tx, workflow_data)
        
        logger.info(f"Successfully saved workflow to graph: {workflow_name}")
        return workflow_name
    
    @staticmethod
    def _create_workflow_tx(tx, workflow_data: Dict[str, Any]):
        """Transaction function to create workflow in graph."""
        workflow_name = workflow_data.get("name", "unknown")
        
        # Create Workflow node
        workflow_props = {
            "name": workflow_name,
            "type": workflow_data.get("type", "WORKFLOW")
        }
        
        tx.run("""
            MERGE (w:Workflow {name: $name})
            SET w += $props
        """, name=workflow_name, props=workflow_props)
        
        # Process tasks (sessions, worklets, etc.)
        tasks = workflow_data.get("tasks", [])
        for task in tasks:
            task_name = task.get("name", "")
            task_type = task.get("type", "")
            
            if task_type == "Session" or "Session" in task_type:
                # Create Session node and link to workflow
                tx.run("""
                    MERGE (s:Session {name: $name})
                    SET s.type = $type
                    WITH s
                    MATCH (w:Workflow {name: $workflow})
                    MERGE (w)-[:CONTAINS]->(s)
                """, name=task_name, type=task_type, workflow=workflow_name)
                
                # Link session to mapping if mapping name is available
                mapping_name = task.get("mapping_name")
                if mapping_name:
                    tx.run("""
                        MATCH (s:Session {name: $session})
                        MATCH (m:Mapping {name: $mapping})
                        MERGE (s)-[:EXECUTES]->(m)
                    """, session=task_name, mapping=mapping_name)
            
            elif task_type == "Worklet" or "Worklet" in task_type:
                # Create Worklet node and link to workflow
                worklet_name = task.get("worklet_name") or task_name
                tx.run("""
                    MERGE (wl:Worklet {name: $name})
                    SET wl.type = $type
                    WITH wl
                    MATCH (w:Workflow {name: $workflow})
                    MERGE (w)-[:CONTAINS]->(wl)
                """, name=worklet_name, type=task_type, workflow=workflow_name)
        
        # Process links (dependencies)
        links = workflow_data.get("links", [])
        for link in links:
            from_task = link.get("from", "")
            to_task = link.get("to", "")
            link_type = link.get("from_link", "Success")  # Success, Failed, etc.
            
            if from_task and to_task:
                # Create dependency relationship
                # Try to find nodes (could be Session or Worklet)
                tx.run("""
                    MATCH (from_node)
                    WHERE (from_node:Session OR from_node:Worklet) AND from_node.name = $from_task
                    MATCH (to_node)
                    WHERE (to_node:Session OR to_node:Worklet) AND to_node.name = $to_task
                    MERGE (from_node)-[r:DEPENDS_ON]->(to_node)
                    SET r.link_type = $link_type
                """, from_task=from_task, to_task=to_task, link_type=link_type)
    
    def save_session(self, session_data: Dict[str, Any], workflow_name: Optional[str] = None) -> str:
        """Save session to Neo4j.
        
        Args:
            session_data: Session data dictionary with name, mapping, config
            workflow_name: Optional workflow name to link session to
            
        Returns:
            Session name
        """
        session_name = session_data.get("name", "unknown")
        logger.info(f"Saving session to graph: {session_name}")
        
        with self.driver.session() as session:
            session.execute_write(self._create_session_tx, session_data, workflow_name)
        
        logger.info(f"Successfully saved session to graph: {session_name}")
        return session_name
    
    @staticmethod
    def _create_session_tx(tx, session_data: Dict[str, Any], workflow_name: Optional[str] = None):
        """Transaction function to create session in graph."""
        session_name = session_data.get("name", "unknown")
        # Handle both "mapping" and "mapping_name" field names
        mapping_name = session_data.get("mapping_name") or session_data.get("mapping")
        
        # Create Session node
        session_props = {
            "name": session_name,
            "type": session_data.get("type", "SESSION")
        }
        
        tx.run("""
            MERGE (s:Session {name: $name})
            SET s += $props
        """, name=session_name, props=session_props)
        
        # Link to workflow if provided
        if workflow_name:
            # First ensure workflow exists
            tx.run("""
                MERGE (w:Workflow {name: $workflow})
            """, workflow=workflow_name)
            
            # Then create the relationship
            result = tx.run("""
                MATCH (s:Session {name: $session})
                MATCH (w:Workflow {name: $workflow})
                MERGE (w)-[r:CONTAINS]->(s)
                RETURN r
            """, session=session_name, workflow=workflow_name)
            
            # Log if relationship was created
            if not result.single():
                logger.warning(f"Failed to create CONTAINS relationship: Workflow {workflow_name} -> Session {session_name}")
        
        # Link to mapping if available
        if mapping_name:
            tx.run("""
                MATCH (s:Session {name: $session})
                MATCH (m:Mapping {name: $mapping})
                MERGE (s)-[:EXECUTES]->(m)
            """, session=session_name, mapping=mapping_name)
    
    def save_worklet(self, worklet_data: Dict[str, Any], workflow_name: Optional[str] = None) -> str:
        """Save worklet to Neo4j.
        
        Args:
            worklet_data: Worklet data dictionary with name, tasks
            workflow_name: Optional workflow name to link worklet to
            
        Returns:
            Worklet name
        """
        worklet_name = worklet_data.get("name", "unknown")
        logger.info(f"Saving worklet to graph: {worklet_name}")
        
        with self.driver.session() as session:
            session.execute_write(self._create_worklet_tx, worklet_data, workflow_name)
        
        logger.info(f"Successfully saved worklet to graph: {worklet_name}")
        return worklet_name
    
    @staticmethod
    def _create_worklet_tx(tx, worklet_data: Dict[str, Any], workflow_name: Optional[str] = None):
        """Transaction function to create worklet in graph."""
        worklet_name = worklet_data.get("name", "unknown")
        
        # Create Worklet node
        worklet_props = {
            "name": worklet_name,
            "type": "WORKLET"
        }
        
        tx.run("""
            MERGE (wl:Worklet {name: $name})
            SET wl += $props
        """, name=worklet_name, props=worklet_props)
        
        # Link to workflow if provided
        if workflow_name:
            tx.run("""
                MATCH (wl:Worklet {name: $worklet})
                MATCH (w:Workflow {name: $workflow})
                MERGE (w)-[:CONTAINS]->(wl)
            """, worklet=worklet_name, workflow=workflow_name)
        
        # Process tasks in worklet (sessions, etc.)
        tasks = worklet_data.get("tasks", [])
        for task in tasks:
            task_name = task.get("name", "")
            task_type = task.get("type", "")
            
            if task_type == "Session" or "Session" in task_type:
                # Link worklet to session
                tx.run("""
                    MATCH (wl:Worklet {name: $worklet})
                    MERGE (s:Session {name: $session})
                    SET s.type = $type
                    MERGE (wl)-[:CONTAINS]->(s)
                """, worklet=worklet_name, session=task_name, type=task_type)
                
                # Link session to mapping if available
                mapping_name = task.get("mapping_name")
                if mapping_name:
                    tx.run("""
                        MATCH (s:Session {name: $session})
                        MATCH (m:Mapping {name: $mapping})
                        MERGE (s)-[:EXECUTES]->(m)
                    """, session=task_name, mapping=mapping_name)
    
    def save_file_metadata(self, component_type: str, component_name: str, 
                          file_path: str, filename: str, file_size: int = None,
                          uploaded_at: str = None, parsed_at: str = None) -> str:
        """Save file metadata to Neo4j and link to component.
        
        Args:
            component_type: Type of component (Workflow, Session, Worklet, Mapping)
            component_name: Name of the component
            file_path: Full path to the source file
            filename: Original filename
            file_size: File size in bytes (optional)
            uploaded_at: Upload timestamp (optional)
            parsed_at: Parse timestamp (optional)
            
        Returns:
            File path (used as identifier)
        """
        logger.info(f"Saving file metadata for {component_type}: {component_name} from {filename}")
        
        with self.driver.session() as session:
            session.execute_write(self._create_file_metadata_tx, 
                                 component_type, component_name, file_path, 
                                 filename, file_size, uploaded_at, parsed_at)
        
        logger.info(f"Successfully saved file metadata: {file_path}")
        return file_path
    
    @staticmethod
    def _create_file_metadata_tx(tx, component_type: str, component_name: str,
                                 file_path: str, filename: str, file_size: int = None,
                                 uploaded_at: str = None, parsed_at: str = None):
        """Transaction function to create file metadata and link to component."""
        # Create SourceFile node
        file_props = {
            "filename": filename,
            "file_path": file_path,
            "file_type": component_type.lower(),
            "file_size": file_size,
            "uploaded_at": uploaded_at or "",
            "parsed_at": parsed_at or ""
        }
        
        tx.run("""
            MERGE (f:SourceFile {file_path: $file_path})
            SET f += $props
        """, file_path=file_path, props=file_props)
        
        # Link to component based on type
        if component_type == "Workflow":
            tx.run("""
                MATCH (f:SourceFile {file_path: $file_path})
                MATCH (w:Workflow {name: $component_name})
                MERGE (w)-[:LOADED_FROM]->(f)
            """, file_path=file_path, component_name=component_name)
        elif component_type == "Session":
            tx.run("""
                MATCH (f:SourceFile {file_path: $file_path})
                MATCH (s:Session {name: $component_name})
                MERGE (s)-[:LOADED_FROM]->(f)
            """, file_path=file_path, component_name=component_name)
        elif component_type == "Worklet":
            tx.run("""
                MATCH (f:SourceFile {file_path: $file_path})
                MATCH (wl:Worklet {name: $component_name})
                MERGE (wl)-[:LOADED_FROM]->(f)
            """, file_path=file_path, component_name=component_name)
        elif component_type == "Mapping":
            tx.run("""
                MATCH (f:SourceFile {file_path: $file_path})
                MATCH (m:Mapping {name: $component_name})
                MERGE (m)-[:LOADED_FROM]->(f)
            """, file_path=file_path, component_name=component_name)
    
    def get_file_metadata(self, component_name: str, component_type: str) -> Optional[Dict[str, Any]]:
        """Get file metadata for a component.
        
        Args:
            component_name: Name of the component
            component_type: Type of component (Workflow, Session, Worklet, Mapping)
            
        Returns:
            File metadata dictionary or None
        """
        with self.driver.session() as session:
            if component_type == "Workflow":
                result = session.run("""
                    MATCH (w:Workflow {name: $name})-[:LOADED_FROM]->(f:SourceFile)
                    RETURN f
                """, name=component_name).single()
            elif component_type == "Session":
                result = session.run("""
                    MATCH (s:Session {name: $name})-[:LOADED_FROM]->(f:SourceFile)
                    RETURN f
                """, name=component_name).single()
            elif component_type == "Worklet":
                result = session.run("""
                    MATCH (wl:Worklet {name: $name})-[:LOADED_FROM]->(f:SourceFile)
                    RETURN f
                """, name=component_name).single()
            elif component_type == "Mapping":
                result = session.run("""
                    MATCH (m:Mapping {name: $name})-[:LOADED_FROM]->(f:SourceFile)
                    RETURN f
                """, name=component_name).single()
            else:
                return None
            
            if result:
                return dict(result["f"])
            return None
    
    def save_code_metadata(self, mapping_name: str, code_type: str, file_path: str,
                          language: str, quality_score: float = None) -> str:
        """Save generated code metadata to Neo4j.
        
        Args:
            mapping_name: Name of the mapping
            code_type: Type of code (pyspark, dlt, sql)
            file_path: Path to the generated code file
            language: Programming language (python, sql)
            quality_score: Code quality score (optional)
            
        Returns:
            File path
        """
        logger.info(f"Saving code metadata for mapping {mapping_name}: {code_type}")
        
        with self.driver.session() as session:
            session.execute_write(self._create_code_metadata_tx,
                                 mapping_name, code_type, file_path, language, quality_score)
        
        logger.info(f"Successfully saved code metadata: {file_path}")
        return file_path
    
    @staticmethod
    def _create_code_metadata_tx(tx, mapping_name: str, code_type: str, file_path: str,
                                 language: str, quality_score: float = None):
        """Transaction function to create code metadata and link to mapping."""
        from datetime import datetime
        
        code_props = {
            "mapping_name": mapping_name,
            "code_type": code_type,
            "file_path": file_path,
            "language": language,
            "quality_score": quality_score,
            "generated_at": datetime.now().isoformat()
        }
        
        tx.run("""
            MERGE (c:GeneratedCode {file_path: $file_path})
            SET c += $props
            WITH c
            MATCH (m:Mapping {name: $mapping_name})
            MERGE (m)-[:HAS_CODE]->(c)
        """, file_path=file_path, mapping_name=mapping_name, props=code_props)
    
    def get_code_metadata(self, mapping_name: str) -> List[Dict[str, Any]]:
        """Get all code metadata for a mapping.
        
        Args:
            mapping_name: Name of the mapping
            
        Returns:
            List of code metadata dictionaries
        """
        with self.driver.session() as session:
            # Use OPTIONAL MATCH to handle cases where HAS_CODE relationship doesn't exist yet
            # Check if GeneratedCode nodes exist first to avoid warnings
            # Only query if there are any GeneratedCode nodes in the database
            check_result = session.run("MATCH (c:GeneratedCode) RETURN count(c) as count").single()
            if not check_result or check_result["count"] == 0:
                # No code files exist yet, return empty list
                return []
            
            result = session.run("""
                MATCH (m:Mapping {name: $name})
                OPTIONAL MATCH (m)-[r:HAS_CODE]->(c:GeneratedCode)
                WHERE c IS NOT NULL AND r IS NOT NULL
                RETURN c
                ORDER BY CASE WHEN c.code_type IS NOT NULL THEN c.code_type ELSE '' END
            """, name=mapping_name)
            
            return [dict(record["c"]) for record in result if record.get("c")]
    
    def list_all_code_files(self) -> List[Dict[str, Any]]:
        """List all generated code files with metadata.
        
        Returns:
            List of code metadata dictionaries
        """
        with self.driver.session() as session:
            # Check if GeneratedCode nodes exist first
            result = session.run("""
                MATCH (c:GeneratedCode)
                WHERE c.file_path IS NOT NULL
                RETURN c
                ORDER BY c.mapping_name, c.code_type
            """)
            
            return [dict(record["c"]) for record in result]
    
    def close(self):
        """Close Neo4j connection."""
        self.driver.close()
        logger.info("GraphStore connection closed")

