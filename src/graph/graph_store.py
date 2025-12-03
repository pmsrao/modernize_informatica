"""Graph Store — Neo4j implementation for canonical models."""
import json
import re
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
        """Create indexes for performance.
        
        Note: For a clean schema setup, use scripts/schema/create_neo4j_schema.py instead.
        This method is kept for backward compatibility but indexes should be created via schema script.
        """
        indexes = [
            "CREATE INDEX transformation_name IF NOT EXISTS FOR (t:Transformation) ON (t.name)",
            "CREATE INDEX reusable_transformation_name IF NOT EXISTS FOR (r:ReusableTransformation) ON (r.name)",
            "CREATE INDEX pipeline_name IF NOT EXISTS FOR (p:Pipeline) ON (p.name)",
            "CREATE INDEX task_name IF NOT EXISTS FOR (t:Task) ON (t.name)",
            "CREATE INDEX sub_pipeline_name IF NOT EXISTS FOR (s:SubPipeline) ON (s.name)",
            "CREATE INDEX source_component_type_transformation IF NOT EXISTS FOR (t:Transformation) ON (t.source_component_type)",
            "CREATE INDEX source_component_type_reusable_transformation IF NOT EXISTS FOR (r:ReusableTransformation) ON (r.source_component_type)",
            "CREATE INDEX source_component_type_pipeline IF NOT EXISTS FOR (p:Pipeline) ON (p.source_component_type)",
            "CREATE INDEX source_component_type_task IF NOT EXISTS FOR (t:Task) ON (t.source_component_type)",
            "CREATE INDEX source_component_type_sub_pipeline IF NOT EXISTS FOR (s:SubPipeline) ON (s.source_component_type)",
            "CREATE INDEX table_name IF NOT EXISTS FOR (t:Table) ON (t.name)",
            "CREATE INDEX source_name IF NOT EXISTS FOR (s:Source) ON (s.name)",
            "CREATE INDEX target_name IF NOT EXISTS FOR (t:Target) ON (t.name)",
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
    
    def save_transformation(self, canonical_model: Dict[str, Any]) -> str:
        """Save canonical model (transformation) to Neo4j.
        
        Args:
            canonical_model: Canonical model dictionary with transformation_name and source_component_type
            
        Returns:
            Transformation name
        """
        transformation_name = canonical_model.get("transformation_name", canonical_model.get("mapping_name", "unknown"))
        logger.info(f"Saving transformation to graph: {transformation_name}")
        
        with self.driver.session() as session:
            # Use transaction for atomicity
            session.execute_write(self._create_transformation_tx, canonical_model)
        
        logger.info(f"Successfully saved transformation to graph: {transformation_name}")
        return transformation_name
    
    @staticmethod
    def _create_transformation_tx(tx, model: Dict[str, Any]):
        """Transaction function to create transformation in graph."""
        transformation_name = model.get("transformation_name", model.get("mapping_name", "unknown"))
        source_component_type = model.get("source_component_type", "mapping")
        
        # 1. Create Transformation node
        complexity_metrics = model.get("complexity_metrics", {})
        semantic_tags = model.get("semantic_tags", [])
        
        transformation_props = {
            "name": transformation_name,
            "transformation_name": transformation_name,
            "source_component_type": source_component_type,
            "scd_type": model.get("scd_type", "NONE"),
            "incremental_keys": model.get("incremental_keys", []),
            "complexity": model.get("_performance_metadata", {}).get("estimated_complexity", "UNKNOWN"),
            "created_at": model.get("_provenance", {}).get("enhanced_at", ""),
            "version": 1
        }
        
        # Add semantic tags if available
        if semantic_tags:
            transformation_props["semantic_tags"] = semantic_tags
        
        # Add complexity metrics if available
        if complexity_metrics:
            transformation_props["complexity_score"] = complexity_metrics.get("complexity_score")
            transformation_props["cyclomatic_complexity"] = complexity_metrics.get("cyclomatic_complexity")
            transformation_props["transformation_count"] = complexity_metrics.get("transformation_count")
            transformation_props["connector_count"] = complexity_metrics.get("connector_count")
            transformation_props["lookup_count"] = complexity_metrics.get("lookup_count")
            transformation_props["join_count"] = complexity_metrics.get("join_count")
            transformation_props["aggregation_count"] = complexity_metrics.get("aggregation_count")
        
        tx.run("""
            MERGE (t:Transformation {name: $name})
            SET t += $props
        """, name=transformation_name, props=transformation_props)
        
        # 2. Create Source nodes
        for source in model.get("sources", []):
            source_name = source.get("name", "")
            table_name = source.get("table", "")
            database = source.get("database", "")
            
            # Create Source node
            tx.run("""
                MERGE (s:Source {name: $name, transformation: $transformation})
                SET s.table = $table, s.database = $database
                WITH s
                MATCH (t:Transformation {name: $transformation})
                MERGE (t)-[:HAS_SOURCE]->(s)
            """, name=source_name, transformation=transformation_name, 
                  table=table_name, database=database)
            
            # Create Table node and link
            if table_name:
                # Use 'Unknown' or empty string if database is None/empty
                db_value = database if database else 'Unknown'
                tx.run("""
                    MERGE (tab:Table {name: $table, database: $database})
                    SET tab.platform = COALESCE(tab.platform, 'Unknown')
                    WITH tab
                    MATCH (s:Source {name: $source, transformation: $transformation})
                    MERGE (s)-[:READS_TABLE]->(tab)
                """, table=table_name, database=db_value,
                      source=source_name, transformation=transformation_name)
            
            # Create Field nodes
            for field in source.get("fields", []):
                field_name = field.get("name", "")
                tx.run("""
                    MERGE (f:Field {name: $field, parent: $parent})
                    SET f.data_type = $data_type, f.nullable = $nullable
                    WITH f
                    MATCH (s:Source {name: $parent, transformation: $transformation})
                    MERGE (s)-[:HAS_FIELD]->(f)
                """, field=field_name, parent=source_name, transformation=transformation_name,
                      data_type=field.get("data_type"), 
                      nullable=field.get("nullable", True))
        
        # 3. Create Target nodes
        for target in model.get("targets", []):
            target_name = target.get("name", "")
            table_name = target.get("table", "")
            database = target.get("database", "")
            
            tx.run("""
                MERGE (tgt:Target {name: $name, transformation: $transformation})
                SET tgt.table = $table, tgt.database = $database
                WITH tgt
                MATCH (t:Transformation {name: $transformation})
                MERGE (t)-[:HAS_TARGET]->(tgt)
            """, name=target_name, transformation=transformation_name,
                  table=table_name, database=database)
            
            # Create Field nodes for Target fields
            for field in target.get("fields", []):
                field_name = field.get("name", "")
                tx.run("""
                    MERGE (f:Field {name: $field, parent: $parent, transformation: $transformation})
                    SET f.data_type = $data_type, f.nullable = $nullable
                    WITH f
                    MATCH (tgt:Target {name: $parent, transformation: $transformation})
                    MERGE (tgt)-[:HAS_FIELD]->(f)
                """, field=field_name, parent=target_name, transformation=transformation_name,
                      data_type=field.get("data_type"), 
                      nullable=field.get("nullable", True))
            
            if table_name:
                # Use 'Unknown' or empty string if database is None/empty
                db_value = database if database else 'Unknown'
                tx.run("""
                    MERGE (tab:Table {name: $table, database: $database})
                    SET tab.platform = COALESCE(tab.platform, 'Unknown')
                    WITH tab
                    MATCH (tgt:Target {name: $target, transformation: $transformation})
                    MERGE (tgt)-[:WRITES_TABLE]->(tab)
                """, table=table_name, database=db_value,
                      target=target_name, transformation=transformation_name)
        
        # 4. Create Transformation nodes (nested transformations within the main transformation)
        for trans in model.get("transformations", []):
            trans_name = trans.get("name", "")
            trans_type = trans.get("type", "")
            
            # Handle reusable transformation instances - create relationship to reusable transformation
            if trans_type == "MAPPLET_INSTANCE":
                reusable_transformation_ref = trans.get("reusable_transformation_ref", trans.get("mapplet_ref", ""))
                if reusable_transformation_ref:
                    tx.run("""
                        MATCH (rt:ReusableTransformation {name: $reusable_transformation_ref})
                        MATCH (t:Transformation {name: $transformation})
                        MERGE (t)-[:USES_REUSABLE_TRANSFORMATION]->(rt)
                    """, reusable_transformation_ref=reusable_transformation_ref, transformation=transformation_name)
            
            # Prepare properties (exclude internal fields except _optimization_hint)
            # Neo4j only supports primitive types, so exclude complex objects like ports, connectors
            trans_props = {
                "name": trans_name,
                "type": trans_type,
                "transformation": transformation_name,
                "optimization_hint": trans.get("_optimization_hint")
            }
            
            # Add reusable_transformation_ref for reusable transformation instances
            if trans_type == "MAPPLET_INSTANCE":
                trans_props["reusable_transformation_ref"] = trans.get("reusable_transformation_ref", trans.get("mapplet_ref", ""))
            
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
                MERGE (t:Transformation {name: $name, transformation: $transformation})
                SET t += $props
                WITH t
                MATCH (main:Transformation {name: $transformation})
                MERGE (main)-[:HAS_TRANSFORMATION]->(t)
            """, name=trans_name, transformation=transformation_name, props=trans_props)
            
            # Create Port and Field nodes for transformation ports
            ports = trans.get("ports", [])
            for port in ports:
                port_name = port.get("name", "")
                port_type = port.get("port_type", "INPUT/OUTPUT")
                port_datatype = port.get("datatype", "")
                port_precision = port.get("precision")
                port_scale = port.get("scale")
                port_expression = port.get("expression", "")
                
                # Create Port node
                tx.run("""
                    MATCH (t:Transformation {name: $trans_name, transformation: $transformation})
                    MERGE (p:Port {name: $port_name, transformation: $transformation, parent_transformation: $trans_name})
                    SET p.port_type = $port_type,
                        p.datatype = $port_datatype,
                        p.precision = $precision,
                        p.scale = $scale,
                        p.expression = $expression
                    MERGE (t)-[:HAS_PORT]->(p)
                """, trans_name=trans_name, transformation=transformation_name,
                      port_name=port_name, port_type=port_type,
                      port_datatype=port_datatype, precision=port_precision,
                      scale=port_scale, expression=port_expression)
                
                # Create Field node for this port (port represents a field)
                # Use port name as field name, or extract from expression if it's an output port
                field_name = port_name
                
                tx.run("""
                    MATCH (p:Port {name: $port_name, transformation: $transformation, parent_transformation: $trans_name})
                    MERGE (f:Field {name: $field_name, transformation: $transformation, parent_port: $port_name, parent_transformation: $trans_name})
                    SET f.data_type = $data_type,
                        f.precision = $precision,
                        f.scale = $scale,
                        f.port_type = $port_type
                    MERGE (p)-[:HAS_FIELD]->(f)
                """, port_name=port_name, transformation=transformation_name,
                      trans_name=trans_name, field_name=field_name,
                      data_type=port_datatype, precision=port_precision,
                      scale=port_scale, port_type=port_type)
                
                # For output ports with expressions, create DERIVED_FROM relationships
                # This enables column-level lineage
                if port_type in ["OUTPUT", "INPUT/OUTPUT"] and port_expression:
                    # Extract field references from expression (simplified - could be enhanced with AST)
                    # Look for patterns like field_name or :transformation.field_name
                    # Simple pattern: word characters that might be field names
                    # This is a simplified approach - full implementation would use AST
                    field_refs = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', port_expression)
                    
                    # Try to match these references to input fields in the same transformation
                    # or fields from connected transformations
                    for ref in field_refs:
                        # Skip Informatica functions and keywords
                        if ref.upper() in ['IIF', 'DECODE', 'SUBSTR', 'TRIM', 'UPPER', 'LOWER', 'TO_DATE', 'TO_CHAR', 'NULL', 'TRUE', 'FALSE']:
                            continue
                        
                        # Try to find matching input field in the same transformation
                        tx.run("""
                            MATCH (input_port:Port {name: $ref, transformation: $transformation, parent_transformation: $trans_name, port_type: 'INPUT'})
                            MATCH (input_field:Field {name: $ref, transformation: $transformation, parent_transformation: $trans_name})
                            MATCH (output_field:Field {name: $field_name, transformation: $transformation, parent_transformation: $trans_name})
                            MERGE (output_field)-[:DERIVED_FROM]->(input_field)
                        """, ref=ref, transformation=transformation_name, trans_name=trans_name, field_name=field_name)
        
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
                MATCH (s:Source {name: $from_trans, transformation: $transformation})
                RETURN s
                LIMIT 1
            """, from_trans=from_trans, transformation=transformation_name)
            
            if source_result.single():
                # Source -> Transformation
                tx.run("""
                    MATCH (s:Source {name: $from_trans, transformation: $transformation})
                    MATCH (t:Transformation {name: $to_trans, transformation: $transformation})
                    MERGE (s)-[r:CONNECTS_TO]->(t)
                    SET r.from_port = $from_port, r.to_port = $to_port
                """, from_trans=from_trans, to_trans=to_trans, transformation=transformation_name,
                      from_port=from_port, to_port=to_port)
                logger.debug(f"Created Source->Transformation connector: {from_trans} -> {to_trans}")
                
                # Create field-level FEEDS relationship
                # If from_port is "*", connect all source fields to the target port
                if from_port == "*":
                    tx.run("""
                        MATCH (s:Source {name: $from_trans, transformation: $transformation})
                        MATCH (s)-[:HAS_FIELD]->(source_field:Field)
                        MATCH (t:Transformation {name: $to_trans, transformation: $transformation})
                        MATCH (t)-[:HAS_PORT]->(target_port:Port {name: $to_port})
                        MATCH (target_port)-[:HAS_FIELD]->(target_field:Field)
                        MERGE (source_field)-[:FEEDS]->(target_field)
                    """, from_trans=from_trans, to_trans=to_trans, transformation=transformation_name, to_port=to_port)
                else:
                    # Connect specific field
                    tx.run("""
                        MATCH (s:Source {name: $from_trans, transformation: $transformation})
                        MATCH (s)-[:HAS_FIELD]->(source_field:Field {name: $from_port})
                        MATCH (t:Transformation {name: $to_trans, transformation: $transformation})
                        MATCH (t)-[:HAS_PORT]->(target_port:Port {name: $to_port})
                        MATCH (target_port)-[:HAS_FIELD]->(target_field:Field)
                        MERGE (source_field)-[:FEEDS]->(target_field)
                    """, from_trans=from_trans, to_trans=to_trans, transformation=transformation_name,
                          from_port=from_port, to_port=to_port)
                continue
            
            # Check if to_trans is a Target
            target_result = tx.run("""
                MATCH (tgt:Target {name: $to_trans, transformation: $transformation})
                RETURN tgt
                LIMIT 1
            """, to_trans=to_trans, transformation=transformation_name)
            
            if target_result.single():
                # Transformation -> Target
                tx.run("""
                    MATCH (trans:Transformation {name: $from_trans, transformation: $transformation})
                    MATCH (tgt:Target {name: $to_trans, transformation: $transformation})
                    MERGE (trans)-[r:CONNECTS_TO]->(tgt)
                    SET r.from_port = $from_port, r.to_port = $to_port
                """, from_trans=from_trans, to_trans=to_trans, transformation=transformation_name,
                      from_port=from_port, to_port=to_port)
                logger.debug(f"Created Transformation->Target connector: {from_trans} -> {to_trans}")
                
                # Create field-level FEEDS relationship
                if from_port == "*":
                    tx.run("""
                        MATCH (trans:Transformation {name: $from_trans, transformation: $transformation})
                        MATCH (trans)-[:HAS_PORT]->(source_port:Port {port_type: 'OUTPUT'})
                        MATCH (source_port)-[:HAS_FIELD]->(source_field:Field)
                        MATCH (tgt:Target {name: $to_trans, transformation: $transformation})
                        MATCH (tgt)-[:HAS_FIELD]->(target_field:Field {name: $to_port})
                        MERGE (source_field)-[:FEEDS]->(target_field)
                    """, from_trans=from_trans, to_trans=to_trans, transformation=transformation_name, to_port=to_port)
                else:
                    tx.run("""
                        MATCH (trans:Transformation {name: $from_trans, transformation: $transformation})
                        MATCH (trans)-[:HAS_PORT]->(source_port:Port {name: $from_port})
                        MATCH (source_port)-[:HAS_FIELD]->(source_field:Field)
                        MATCH (tgt:Target {name: $to_trans, transformation: $transformation})
                        MATCH (tgt)-[:HAS_FIELD]->(target_field:Field {name: $to_port})
                        MERGE (source_field)-[:FEEDS]->(target_field)
                    """, from_trans=from_trans, to_trans=to_trans, transformation=transformation_name,
                          from_port=from_port, to_port=to_port)
                continue
            
            # Transformation -> Transformation
            tx.run("""
                MATCH (t1:Transformation {name: $from_trans, transformation: $transformation})
                MATCH (t2:Transformation {name: $to_trans, transformation: $transformation})
                MERGE (t1)-[r:CONNECTS_TO]->(t2)
                SET r.from_port = $from_port, r.to_port = $to_port
            """, from_trans=from_trans, to_trans=to_trans, transformation=transformation_name,
                  from_port=from_port, to_port=to_port)
            logger.debug(f"Created Transformation->Transformation connector: {from_trans} -> {to_trans}")
            
            # Create field-level FEEDS relationship
            if from_port == "*":
                # Connect all output fields from source transformation to input port of target transformation
                tx.run("""
                    MATCH (t1:Transformation {name: $from_trans, transformation: $transformation})
                    MATCH (t1)-[:HAS_PORT]->(source_port:Port {port_type: 'OUTPUT'})
                    MATCH (source_port)-[:HAS_FIELD]->(source_field:Field)
                    MATCH (t2:Transformation {name: $to_trans, transformation: $transformation})
                    MATCH (t2)-[:HAS_PORT]->(target_port:Port {name: $to_port})
                    MATCH (target_port)-[:HAS_FIELD]->(target_field:Field)
                    MERGE (source_field)-[:FEEDS]->(target_field)
                """, from_trans=from_trans, to_trans=to_trans, transformation=transformation_name, to_port=to_port)
            else:
                # Connect specific field
                tx.run("""
                    MATCH (t1:Transformation {name: $from_trans, transformation: $transformation})
                    MATCH (t1)-[:HAS_PORT]->(source_port:Port {name: $from_port})
                    MATCH (source_port)-[:HAS_FIELD]->(source_field:Field)
                    MATCH (t2:Transformation {name: $to_trans, transformation: $transformation})
                    MATCH (t2)-[:HAS_PORT]->(target_port:Port {name: $to_port})
                    MATCH (target_port)-[:HAS_FIELD]->(target_field:Field)
                    MERGE (source_field)-[:FEEDS]->(target_field)
                """, from_trans=from_trans, to_trans=to_trans, transformation=transformation_name,
                      from_port=from_port, to_port=to_port)
    
    def load_transformation(self, transformation_name: str) -> Optional[Dict[str, Any]]:
        """Load canonical model (transformation) from Neo4j.
        
        Args:
            transformation_name: Name of transformation to load
            
        Returns:
            Canonical model dictionary or None
        """
        logger.info(f"Loading transformation from graph: {transformation_name}")
        
        with self.driver.session() as session:
            result = session.execute_read(self._load_transformation_tx, transformation_name)
        
        if result:
            logger.info(f"Successfully loaded transformation from graph: {transformation_name}")
        else:
            logger.warning(f"Transformation not found in graph: {transformation_name}")
        
        return result
    
    @staticmethod
    def _load_transformation_tx(tx, transformation_name: str) -> Optional[Dict[str, Any]]:
        """Transaction function to load transformation from graph."""
        # Load transformation node
        transformation_result = tx.run("""
            MATCH (t:Transformation {name: $name})
            WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
            RETURN t
        """, name=transformation_name).single()
        
        if not transformation_result:
            return None
        
        transformation_node = dict(transformation_result["t"])
        model = {
            "transformation_name": transformation_node.get("transformation_name", transformation_name),
            "source_component_type": transformation_node.get("source_component_type", "mapping"),
            "scd_type": transformation_node.get("scd_type", "NONE"),
            "incremental_keys": transformation_node.get("incremental_keys", []),
            "sources": [],
            "targets": [],
            "transformations": [],
            "connectors": []
        }
        
        # Load sources
        sources_result = tx.run("""
            MATCH (t:Transformation {name: $name})-[:HAS_SOURCE]->(s:Source)
            RETURN s
        """, name=transformation_name)
        
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
            MATCH (t:Transformation {name: $name})-[:HAS_TARGET]->(tgt:Target)
            RETURN tgt
        """, name=transformation_name)
        
        for record in targets_result:
            target = dict(record["tgt"])
            model["targets"].append({
                "name": target.get("name"),
                "table": target.get("table"),
                "database": target.get("database"),
                "fields": []
            })
        
        # Load transformations (nested transformations)
        trans_result = tx.run("""
            MATCH (main:Transformation {name: $name})-[:HAS_TRANSFORMATION]->(t:Transformation)
            RETURN t
        """, name=transformation_name)
        
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
            MATCH (s:Source {transformation: $name})-[r:CONNECTS_TO]->(t:Transformation {transformation: $name})
            RETURN s.name as from, t.name as to, r.from_port as from_port, r.to_port as to_port
        """, name=transformation_name)
        
        for record in source_conns:
            model["connectors"].append({
                "from_transformation": record["from"],
                "to_transformation": record["to"],
                "from_port": record.get("from_port", ""),
                "to_port": record.get("to_port", "")
            })
        
        # Transformation -> Target
        target_conns = tx.run("""
            MATCH (t:Transformation {transformation: $name})-[r:CONNECTS_TO]->(tgt:Target {transformation: $name})
            RETURN t.name as from, tgt.name as to, r.from_port as from_port, r.to_port as to_port
        """, name=transformation_name)
        
        for record in target_conns:
            model["connectors"].append({
                "from_transformation": record["from"],
                "to_transformation": record["to"],
                "from_port": record.get("from_port", ""),
                "to_port": record.get("to_port", "")
            })
        
        # Transformation -> Transformation
        trans_conns = tx.run("""
            MATCH (t1:Transformation {transformation: $name})-[r:CONNECTS_TO]->(t2:Transformation {transformation: $name})
            RETURN t1.name as from, t2.name as to, r.from_port as from_port, r.to_port as to_port
        """, name=transformation_name)
        
        for record in trans_conns:
            model["connectors"].append({
                "from_transformation": record["from"],
                "to_transformation": record["to"],
                "from_port": record.get("from_port", ""),
                "to_port": record.get("to_port", "")
            })
        
        return model
    
    def save_reusable_transformation(self, reusable_transformation_data: Dict[str, Any]) -> str:
        """Save reusable transformation (mapplet) to Neo4j.
        
        Args:
            reusable_transformation_data: Parsed reusable transformation data dictionary
            
        Returns:
            Reusable transformation name
        """
        reusable_transformation_name = reusable_transformation_data.get("name", "unknown")
        logger.info(f"Saving reusable transformation to graph: {reusable_transformation_name}")
        
        with self.driver.session() as session:
            # Use transaction for atomicity
            session.execute_write(self._create_reusable_transformation_tx, reusable_transformation_data)
        
        logger.info(f"Successfully saved reusable transformation to graph: {reusable_transformation_name}")
        return reusable_transformation_name
    
    @staticmethod
    def _create_reusable_transformation_tx(tx, reusable_transformation_data: Dict[str, Any]):
        """Transaction function to create reusable transformation in graph.
        
        Reusable transformations are similar to transformations but are reusable components.
        They have input/output ports and transformations.
        """
        reusable_transformation_name = reusable_transformation_data.get("name", "unknown")
        source_component_type = reusable_transformation_data.get("source_component_type", "mapplet")
        
        # 1. Create ReusableTransformation node
        reusable_transformation_props = {
            "name": reusable_transformation_name,
            "source_component_type": source_component_type,
            "type": "REUSABLE_TRANSFORMATION",
            "version": 1
        }
        
        tx.run("""
            MERGE (rt:ReusableTransformation {name: $name})
            SET rt += $props
        """, name=reusable_transformation_name, props=reusable_transformation_props)
        
        # 2. Create Input Port nodes
        for input_port in reusable_transformation_data.get("input_ports", []):
            port_name = input_port.get("name", "")
            tx.run("""
                MERGE (p:Port {name: $port_name, reusable_transformation: $reusable_transformation, port_type: 'INPUT'})
                SET p.data_type = $data_type, p.precision = $precision, p.scale = $scale
                WITH p
                MATCH (rt:ReusableTransformation {name: $reusable_transformation})
                MERGE (rt)-[:HAS_INPUT_PORT]->(p)
            """, port_name=port_name, reusable_transformation=reusable_transformation_name,
                  data_type=input_port.get("datatype"),
                  precision=input_port.get("precision"),
                  scale=input_port.get("scale"))
        
        # 3. Create Output Port nodes
        for output_port in reusable_transformation_data.get("output_ports", []):
            port_name = output_port.get("name", "")
            tx.run("""
                MERGE (p:Port {name: $port_name, reusable_transformation: $reusable_transformation, port_type: 'OUTPUT'})
                SET p.data_type = $data_type, p.precision = $precision, p.scale = $scale
                WITH p
                MATCH (rt:ReusableTransformation {name: $reusable_transformation})
                MERGE (rt)-[:HAS_OUTPUT_PORT]->(p)
            """, port_name=port_name, reusable_transformation=reusable_transformation_name,
                  data_type=output_port.get("datatype"),
                  precision=output_port.get("precision"),
                  scale=output_port.get("scale"))
        
        # 4. Create Transformation nodes (nested transformations within reusable transformation)
        for trans in reusable_transformation_data.get("transformations", []):
            trans_name = trans.get("name", "")
            trans_type = trans.get("type", "")
            
            # Prepare properties
            trans_props = {
                "name": trans_name,
                "type": trans_type,
                "reusable_transformation": reusable_transformation_name
            }
            
            # Add other non-internal properties
            for key, value in trans.items():
                if not key.startswith("_") or key == "_optimization_hint":
                    if key not in ["name", "type", "ports", "connectors"]:
                        if isinstance(value, (str, int, float, bool, type(None))):
                            trans_props[key] = value
                        elif isinstance(value, list) and all(isinstance(item, (str, int, float, bool, type(None))) for item in value):
                            trans_props[key] = value
                        elif isinstance(value, (dict, list)):
                            trans_props[f"{key}_json"] = json.dumps(value)
            
            tx.run("""
                MERGE (t:Transformation {name: $name, reusable_transformation: $reusable_transformation})
                SET t += $props
                WITH t
                MATCH (rt:ReusableTransformation {name: $reusable_transformation})
                MERGE (rt)-[:HAS_TRANSFORMATION]->(t)
            """, name=trans_name, reusable_transformation=reusable_transformation_name, props=trans_props)
        
        # 5. Create Connector relationships within reusable transformation
        for conn in reusable_transformation_data.get("connectors", []):
            from_trans = conn.get("from_transformation", "")
            to_trans = conn.get("to_transformation", "")
            from_port = conn.get("from_port", "")
            to_port = conn.get("to_port", "")
            
            if not from_trans or not to_trans:
                continue
            
            # Transformation -> Transformation within reusable transformation
            tx.run("""
                MATCH (t1:Transformation {name: $from_trans, reusable_transformation: $reusable_transformation})
                MATCH (t2:Transformation {name: $to_trans, reusable_transformation: $reusable_transformation})
                MERGE (t1)-[r:CONNECTS_TO]->(t2)
                SET r.from_port = $from_port, r.to_port = $to_port
            """, from_trans=from_trans, to_trans=to_trans, reusable_transformation=reusable_transformation_name,
                  from_port=from_port, to_port=to_port)
    
    def load_mapplet(self, mapplet_name: str) -> Optional[Dict[str, Any]]:
        """Load mapplet from Neo4j.
        
        Args:
            mapplet_name: Name of mapplet to load
            
        Returns:
            Mapplet data dictionary or None
        """
        logger.info(f"Loading mapplet from graph: {mapplet_name}")
        
        with self.driver.session() as session:
            result = session.execute_read(self._load_mapplet_tx, mapplet_name)
        
        if result:
            logger.info(f"Successfully loaded mapplet from graph: {mapplet_name}")
        else:
            logger.warning(f"Mapplet not found in graph: {mapplet_name}")
        
        return result
    
    @staticmethod
    def _load_mapplet_tx(tx, mapplet_name: str) -> Optional[Dict[str, Any]]:
        """Transaction function to load mapplet from graph."""
        # Load mapplet node
        mapplet_result = tx.run("""
            MATCH (m:Mapplet {name: $name})
            RETURN m
        """, name=mapplet_name).single()
        
        if not mapplet_result:
            return None
        
        mapplet_node = dict(mapplet_result["m"])
        mapplet_data = {
            "name": mapplet_node.get("name", mapplet_name),
            "type": "MAPPLET",
            "input_ports": [],
            "output_ports": [],
            "transformations": [],
            "connectors": []
        }
        
        # Load input ports
        input_ports_result = tx.run("""
            MATCH (m:Mapplet {name: $name})-[:HAS_INPUT_PORT]->(p:Port)
            RETURN p
        """, name=mapplet_name)
        
        for record in input_ports_result:
            port = dict(record["p"])
            mapplet_data["input_ports"].append({
                "name": port.get("name"),
                "datatype": port.get("data_type"),
                "precision": port.get("precision"),
                "scale": port.get("scale")
            })
        
        # Load output ports
        output_ports_result = tx.run("""
            MATCH (m:Mapplet {name: $name})-[:HAS_OUTPUT_PORT]->(p:Port)
            RETURN p
        """, name=mapplet_name)
        
        for record in output_ports_result:
            port = dict(record["p"])
            mapplet_data["output_ports"].append({
                "name": port.get("name"),
                "datatype": port.get("data_type"),
                "precision": port.get("precision"),
                "scale": port.get("scale")
            })
        
        # Load transformations
        trans_result = tx.run("""
            MATCH (m:Mapplet {name: $name})-[:HAS_TRANSFORMATION]->(t:Transformation)
            RETURN t
        """, name=mapplet_name)
        
        for record in trans_result:
            trans = dict(record["t"])
            trans_dict = {
                "name": trans.get("name"),
                "type": trans.get("type"),
                "ports": []
            }
            # Merge properties (deserialize JSON strings back to objects)
            for key, value in trans.items():
                if key not in ["name", "type", "mapplet"]:
                    if key.endswith("_json") and isinstance(value, str):
                        try:
                            original_key = key[:-5]
                            trans_dict[original_key] = json.loads(value)
                        except json.JSONDecodeError:
                            trans_dict[key] = value
                    else:
                        trans_dict[key] = value
            mapplet_data["transformations"].append(trans_dict)
        
        # Load connectors
        trans_conns = tx.run("""
            MATCH (t1:Transformation {mapplet: $name})-[r:CONNECTS_TO]->(t2:Transformation {mapplet: $name})
            RETURN t1.name as from, t2.name as to, r.from_port as from_port, r.to_port as to_port
        """, name=mapplet_name)
        
        for record in trans_conns:
            mapplet_data["connectors"].append({
                "from_transformation": record["from"],
                "to_transformation": record["to"],
                "from_port": record.get("from_port", ""),
                "to_port": record.get("to_port", "")
            })
        
        return mapplet_data
    
    def query_mappings_using_mapplet(self, mapplet_name: str) -> List[str]:
        """Find all mappings that use a specific mapplet.
        
        Args:
            mapplet_name: Mapplet name
            
        Returns:
            List of mapping names that use this mapplet
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:Mapping)-[:HAS_TRANSFORMATION]->(t:Transformation {type: 'MAPPLET_INSTANCE', mapplet_ref: $mapplet})
                RETURN DISTINCT m.name as name
            """, mapplet=mapplet_name)
            
            return [record["name"] for record in result]
    
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
        """List all transformation names in graph (legacy method name for compatibility).
        
        Returns:
            List of transformation names
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Transformation)
                WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                RETURN t.name as name
                ORDER BY t.name
            """)
            
            return [record["name"] for record in result]
    
    def save_pipeline(self, pipeline_data: Dict[str, Any]) -> str:
        """Save pipeline (workflow) to Neo4j.
        
        Args:
            pipeline_data: Pipeline data dictionary with name, tasks, links
            
        Returns:
            Pipeline name
        """
        pipeline_name = pipeline_data.get("name", "unknown")
        logger.info(f"Saving pipeline to graph: {pipeline_name}")
        
        with self.driver.session() as session:
            session.execute_write(self._create_pipeline_tx, pipeline_data)
        
        logger.info(f"Successfully saved pipeline to graph: {pipeline_name}")
        return pipeline_name
    
    @staticmethod
    def _create_pipeline_tx(tx, pipeline_data: Dict[str, Any]):
        """Transaction function to create pipeline in graph."""
        pipeline_name = pipeline_data.get("name", "unknown")
        source_component_type = pipeline_data.get("source_component_type", "workflow")
        
        # Create Pipeline node
        pipeline_props = {
            "name": pipeline_name,
            "source_component_type": source_component_type,
            "type": pipeline_data.get("type", "PIPELINE")
        }
        
        # Store structured workflow runtime configuration if available
        workflow_runtime_config = pipeline_data.get("workflow_runtime_config")
        if workflow_runtime_config:
            # Store config as JSON string for complex nested structures
            pipeline_props["workflow_runtime_config_json"] = json.dumps(workflow_runtime_config)
            # Store simple config values as properties
            if isinstance(workflow_runtime_config, dict):
                if workflow_runtime_config.get("log_level"):
                    pipeline_props["log_level"] = workflow_runtime_config.get("log_level")
                if workflow_runtime_config.get("parameter_file"):
                    pipeline_props["parameter_file"] = workflow_runtime_config.get("parameter_file")
        
        tx.run("""
            MERGE (p:Pipeline {name: $name})
            SET p += $props
        """, name=pipeline_name, props=pipeline_props)
        
        # Process tasks (sessions, worklets, and all other task types)
        tasks = pipeline_data.get("tasks", [])
        for task in tasks:
            task_name = task.get("name", "")
            task_type = task.get("type", "")
            
            if task_type == "Session" or "Session" in task_type:
                # Create Task node and link to pipeline
                task_props = {
                    "name": task_name,
                    "source_component_type": "session",
                    "type": task_type
                }
                
                # Store structured runtime configuration if available
                task_runtime_config = task.get("task_runtime_config")
                if task_runtime_config:
                    # Store config as JSON string for complex nested structures
                    task_props["task_runtime_config_json"] = json.dumps(task_runtime_config)
                    # Store simple config values as properties
                    if isinstance(task_runtime_config, dict):
                        if task_runtime_config.get("buffer_size"):
                            task_props["buffer_size"] = task_runtime_config.get("buffer_size")
                        if task_runtime_config.get("commit_interval"):
                            task_props["commit_interval"] = task_runtime_config.get("commit_interval")
                
                # Add any additional task properties
                for key, value in task.items():
                    if key not in ["name", "type", "mapping_name", "transformation_name", "task_runtime_config", "config"] and isinstance(value, (str, int, float, bool, type(None))):
                        task_props[key] = value
                    elif isinstance(value, list) and all(isinstance(item, (str, int, float, bool, type(None))) for item in value):
                        task_props[key] = value
                
                tx.run("""
                    MERGE (t:Task {name: $name})
                    SET t += $props
                    WITH t
                    MATCH (p:Pipeline {name: $pipeline})
                    MERGE (p)-[:CONTAINS]->(t)
                """, name=task_name, props=task_props, pipeline=pipeline_name)
                
                # Link task to transformation if transformation name is available
                transformation_name = task.get("transformation_name") or task.get("mapping_name")
                if transformation_name:
                    tx.run("""
                        MATCH (t:Task {name: $task})
                        MATCH (trans:Transformation {name: $transformation})
                        MERGE (t)-[:EXECUTES]->(trans)
                    """, task=task_name, transformation=transformation_name)
            
            elif task_type == "Worklet" or "Worklet" in task_type:
                # Create SubPipeline node and link to pipeline
                sub_pipeline_name = task.get("worklet_name") or task_name
                sub_pipeline_props = {
                    "name": sub_pipeline_name,
                    "source_component_type": "worklet",
                    "type": task_type
                }
                # Add any additional sub pipeline properties
                for key, value in task.items():
                    if key not in ["name", "type", "worklet_name"] and isinstance(value, (str, int, float, bool, type(None))):
                        sub_pipeline_props[key] = value
                    elif isinstance(value, list) and all(isinstance(item, (str, int, float, bool, type(None))) for item in value):
                        sub_pipeline_props[key] = value
                
                tx.run("""
                    MERGE (sp:SubPipeline {name: $name})
                    SET sp += $props
                    WITH sp
                    MATCH (p:Pipeline {name: $pipeline})
                    MERGE (p)-[:CONTAINS]->(sp)
                """, name=sub_pipeline_name, props=sub_pipeline_props, pipeline=pipeline_name)
            
            else:
                # Handle control tasks (Decision, Assignment, Command, Event-Wait/Raise) as separate node types
                # Other tasks (Email, Timer, Control) remain as generic Task nodes
                
                if task_type == "Decision":
                    # Create DecisionTask node
                    decision_props = {
                        "name": task_name,
                        "source_component_type": "decision",
                        "condition": task.get("condition", ""),
                        "default_branch": task.get("default_branch", "")
                    }
                    branches = task.get("branches", [])
                    if branches:
                        decision_props["branches_json"] = json.dumps(branches)
                    
                    tx.run("""
                        MERGE (dt:DecisionTask {name: $name})
                        SET dt += $props
                        WITH dt
                        MATCH (p:Pipeline {name: $pipeline})
                        MERGE (p)-[:CONTAINS]->(dt)
                    """, name=task_name, props=decision_props, pipeline=pipeline_name)
                    continue
                
                elif task_type == "Assignment":
                    # Create AssignmentTask node
                    assignment_props = {
                        "name": task_name,
                        "source_component_type": "assignment"
                    }
                    assignments = task.get("assignments", [])
                    if assignments:
                        assignment_props["assignments_json"] = json.dumps(assignments)
                    
                    tx.run("""
                        MERGE (at:AssignmentTask {name: $name})
                        SET at += $props
                        WITH at
                        MATCH (p:Pipeline {name: $pipeline})
                        MERGE (p)-[:CONTAINS]->(at)
                    """, name=task_name, props=assignment_props, pipeline=pipeline_name)
                    continue
                
                elif task_type == "Command":
                    # Create CommandTask node
                    command_props = {
                        "name": task_name,
                        "source_component_type": "command",
                        "command": task.get("command", ""),
                        "working_directory": task.get("working_directory", ""),
                        "success_codes": task.get("success_codes", "0"),
                        "failure_codes": task.get("failure_codes", ""),
                        "timeout": task.get("timeout")
                    }
                    
                    tx.run("""
                        MERGE (ct:CommandTask {name: $name})
                        SET ct += $props
                        WITH ct
                        MATCH (p:Pipeline {name: $pipeline})
                        MERGE (p)-[:CONTAINS]->(ct)
                    """, name=task_name, props=command_props, pipeline=pipeline_name)
                    continue
                
                elif task_type in ["Event-Wait", "Event-Raise"]:
                    # Create EventTask node
                    event_props = {
                        "name": task_name,
                        "source_component_type": "event",
                        "event_type": task_type,
                        "event_name": task.get("event_name", ""),
                        "wait_type": task.get("wait_type", ""),
                        "wait_value": task.get("wait_value", "")
                    }
                    
                    tx.run("""
                        MERGE (et:EventTask {name: $name})
                        SET et += $props
                        WITH et
                        MATCH (p:Pipeline {name: $pipeline})
                        MERGE (p)-[:CONTAINS]->(et)
                    """, name=task_name, props=event_props, pipeline=pipeline_name)
                    continue
                
                elif task_type == "Email":
                    # Initialize task_props for Email task
                    task_props = {
                        "name": task_name,
                        "source_component_type": "email",
                        "type": task_type
                    }
                    task_props["recipients"] = task.get("recipients", [])
                    task_props["subject"] = task.get("subject", "")
                    task_props["body"] = task.get("body", "")
                    task_props["attachments"] = task.get("attachments", [])
                    task_props["mail_server"] = task.get("mail_server", "")
                elif task_type == "Timer":
                    # Initialize task_props for Timer task
                    task_props = {
                        "name": task_name,
                        "source_component_type": "timer",
                        "type": task_type
                    }
                    task_props["wait_type"] = task.get("wait_type", "Duration")
                    task_props["wait_value"] = task.get("wait_value", "")
                    task_props["file_path"] = task.get("file_path")
                    task_props["event_name"] = task.get("event_name")
                elif task_type == "Control":
                    # Initialize task_props for Control task
                    task_props = {
                        "name": task_name,
                        "source_component_type": "control",
                        "type": task_type
                    }
                    task_props["control_type"] = task.get("control_type", "CONTROL")
                    task_props["error_message"] = task.get("error_message", "")
                else:
                    # Initialize task_props for other task types
                    task_props = {
                        "name": task_name,
                        "source_component_type": "task",
                        "type": task_type
                    }
                
                # Add any other properties that might be in the task
                for key, value in task.items():
                    if key not in ["name", "type"] and key not in task_props:
                        if isinstance(value, (str, int, float, bool, type(None))):
                            task_props[key] = value
                        elif isinstance(value, list) and all(isinstance(item, (str, int, float, bool, type(None))) for item in value):
                            task_props[key] = value
                        elif isinstance(value, (dict, list)):
                            task_props[f"{key}_json"] = json.dumps(value)
                
                # Store as Task node (all pipeline tasks are stored as Task nodes)
                tx.run("""
                    MERGE (t:Task {name: $name})
                    SET t += $props
                    WITH t
                    MATCH (p:Pipeline {name: $pipeline})
                    MERGE (p)-[:CONTAINS]->(t)
                """, name=task_name, props=task_props, pipeline=pipeline_name)
        
        # Process links (dependencies)
        links = pipeline_data.get("links", [])
        for link in links:
            from_task = link.get("from", "")
            to_task = link.get("to", "")
            link_type = link.get("from_link", "Success")  # Success, Failed, etc.
            
            if from_task and to_task:
                # Create dependency relationship
                # All pipeline tasks are stored as Task nodes (including Command, Email, etc.)
                # SubPipelines are stored as SubPipeline nodes
                tx.run("""
                    MATCH (from_node)
                    WHERE (from_node:Task OR from_node:SubPipeline) AND from_node.name = $from_task
                    MATCH (to_node)
                    WHERE (to_node:Task OR to_node:SubPipeline) AND to_node.name = $to_task
                    MERGE (from_node)-[r:DEPENDS_ON]->(to_node)
                    SET r.link_type = $link_type
                """, from_task=from_task, to_task=to_task, link_type=link_type)
    
    def save_task(self, task_data: Dict[str, Any], pipeline_name: Optional[str] = None) -> str:
        """Save task (session) to Neo4j.
        
        Args:
            task_data: Task data dictionary with name, transformation, config
            pipeline_name: Optional pipeline name to link task to
            
        Returns:
            Task name
        """
        task_name = task_data.get("name", "unknown")
        logger.info(f"Saving task to graph: {task_name}")
        
        with self.driver.session() as session:
            session.execute_write(self._create_task_tx, task_data, pipeline_name)
        
        logger.info(f"Successfully saved task to graph: {task_name}")
        return task_name
    
    @staticmethod
    def _create_task_tx(tx, task_data: Dict[str, Any], pipeline_name: Optional[str] = None):
        """Transaction function to create task in graph."""
        task_name = task_data.get("name", "unknown")
        # Handle both "transformation_name" and "mapping_name" field names
        transformation_name = task_data.get("transformation_name") or task_data.get("mapping_name") or task_data.get("mapping")
        source_component_type = task_data.get("source_component_type", "session")
        
        # Create Task node
        task_props = {
            "name": task_name,
            "source_component_type": source_component_type,
            "type": task_data.get("type", "TASK")
        }
        
        tx.run("""
            MERGE (t:Task {name: $name})
            SET t += $props
        """, name=task_name, props=task_props)
        
        # Link to pipeline if provided
        if pipeline_name:
            # First ensure pipeline exists
            tx.run("""
                MERGE (p:Pipeline {name: $pipeline})
            """, pipeline=pipeline_name)
            
            # Then create the relationship
            result = tx.run("""
                MATCH (t:Task {name: $task})
                MATCH (p:Pipeline {name: $pipeline})
                MERGE (p)-[r:CONTAINS]->(t)
                RETURN r
            """, task=task_name, pipeline=pipeline_name)
            
            # Log if relationship was created
            if not result.single():
                logger.warning(f"Failed to create CONTAINS relationship: Pipeline {pipeline_name} -> Task {task_name}")
        
        # Link to transformation if available
        if transformation_name:
            # Try matching by transformation_name property
            result = tx.run("""
                MATCH (t:Task {name: $task})
                MATCH (trans:Transformation)
                WHERE trans.name = $transformation OR trans.transformation_name = $transformation
                MERGE (t)-[r:EXECUTES]->(trans)
                RETURN r, trans.name as transformation_name
            """, task=task_name, transformation=transformation_name)
            
            # Log if relationship was created
            record = result.single()
            if record:
                logger.debug(f"Created EXECUTES relationship: {task_name} -> {record['transformation_name']}")
            else:
                logger.warning(f"Could not create EXECUTES relationship: Task {task_name} -> Transformation {transformation_name} (transformation not found in graph)")
    
    def save_sub_pipeline(self, sub_pipeline_data: Dict[str, Any], pipeline_name: Optional[str] = None) -> str:
        """Save sub pipeline (worklet) to Neo4j.
        
        Args:
            sub_pipeline_data: Sub pipeline data dictionary with name, tasks
            pipeline_name: Optional pipeline name to link sub pipeline to
            
        Returns:
            Sub pipeline name
        """
        sub_pipeline_name = sub_pipeline_data.get("name", "unknown")
        logger.info(f"Saving sub pipeline to graph: {sub_pipeline_name}")
        
        with self.driver.session() as session:
            session.execute_write(self._create_sub_pipeline_tx, sub_pipeline_data, pipeline_name)
        
        logger.info(f"Successfully saved sub pipeline to graph: {sub_pipeline_name}")
        return sub_pipeline_name
    
    @staticmethod
    def _create_sub_pipeline_tx(tx, sub_pipeline_data: Dict[str, Any], pipeline_name: Optional[str] = None):
        """Transaction function to create sub pipeline in graph."""
        sub_pipeline_name = sub_pipeline_data.get("name", "unknown")
        source_component_type = sub_pipeline_data.get("source_component_type", "worklet")
        
        # Create SubPipeline node
        sub_pipeline_props = {
            "name": sub_pipeline_name,
            "source_component_type": source_component_type,
            "type": "SUB_PIPELINE"
        }
        
        tx.run("""
            MERGE (sp:SubPipeline {name: $name})
            SET sp += $props
        """, name=sub_pipeline_name, props=sub_pipeline_props)
        
        # Link to pipeline if provided
        if pipeline_name:
            tx.run("""
                MATCH (sp:SubPipeline {name: $sub_pipeline})
                MATCH (p:Pipeline {name: $pipeline})
                MERGE (p)-[:CONTAINS]->(sp)
            """, sub_pipeline=sub_pipeline_name, pipeline=pipeline_name)
        
        # Process tasks in sub pipeline (sessions, etc.)
        tasks = sub_pipeline_data.get("tasks", [])
        for task in tasks:
            task_name = task.get("name", "")
            task_type = task.get("type", "")
            
            if task_type == "Session" or "Session" in task_type:
                # Link sub pipeline to task
                tx.run("""
                    MATCH (sp:SubPipeline {name: $sub_pipeline})
                    MERGE (t:Task {name: $task})
                    SET t.type = $type, t.source_component_type = 'session'
                    MERGE (sp)-[:CONTAINS]->(t)
                """, sub_pipeline=sub_pipeline_name, task=task_name, type=task_type)
                
                # Link task to transformation if available
                transformation_name = task.get("transformation_name") or task.get("mapping_name")
                if transformation_name:
                    tx.run("""
                        MATCH (t:Task {name: $task})
                        MATCH (trans:Transformation {name: $transformation})
                        MERGE (t)-[:EXECUTES]->(trans)
                    """, task=task_name, transformation=transformation_name)
    
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
        
        # Link to component based on type (using generic labels)
        if component_type == "Workflow":
            tx.run("""
                MATCH (f:SourceFile {file_path: $file_path})
                MATCH (p:Pipeline {name: $component_name})
                MERGE (p)-[:LOADED_FROM]->(f)
            """, file_path=file_path, component_name=component_name)
        elif component_type == "Session":
            tx.run("""
                MATCH (f:SourceFile {file_path: $file_path})
                MATCH (t:Task {name: $component_name})
                MERGE (t)-[:LOADED_FROM]->(f)
            """, file_path=file_path, component_name=component_name)
        elif component_type == "Worklet":
            tx.run("""
                MATCH (f:SourceFile {file_path: $file_path})
                MATCH (sp:SubPipeline {name: $component_name})
                MERGE (sp)-[:LOADED_FROM]->(f)
            """, file_path=file_path, component_name=component_name)
        elif component_type == "Mapping":
            tx.run("""
                MATCH (f:SourceFile {file_path: $file_path})
                MATCH (t:Transformation {name: $component_name})
                WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                MERGE (t)-[:LOADED_FROM]->(f)
            """, file_path=file_path, component_name=component_name)
        elif component_type == "Mapplet":
            tx.run("""
                MATCH (f:SourceFile {file_path: $file_path})
                MATCH (rt:ReusableTransformation {name: $component_name})
                MERGE (rt)-[:LOADED_FROM]->(f)
            """, file_path=file_path, component_name=component_name)
            
            # Set file_type on SourceFile for mapplets
            tx.run("""
                MATCH (f:SourceFile {file_path: $file_path})
                SET f.file_type = 'mapplet'
            """, file_path=file_path)
    
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
            elif component_type == "Mapplet":
                result = session.run("""
                    MATCH (m:Mapplet {name: $name})-[:LOADED_FROM]->(f:SourceFile)
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
            MATCH (t:Transformation {name: $mapping_name, source_component_type: 'mapping'})
            MERGE (t)-[:HAS_CODE]->(c)
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
                MATCH (t:Transformation {name: $name, source_component_type: 'mapping'})
                OPTIONAL MATCH (t)-[r:HAS_CODE]->(c:GeneratedCode)
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

