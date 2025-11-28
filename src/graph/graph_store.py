"""Graph Store — Neo4j implementation for canonical models."""
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
            "CREATE INDEX target_name IF NOT EXISTS FOR (t:Target) ON (t.name)"
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
                tx.run("""
                    MERGE (t:Table {name: $table, database: $database})
                    SET t.platform = COALESCE(t.platform, 'Unknown')
                    WITH t
                    MATCH (s:Source {name: $source, mapping: $mapping})
                    MERGE (s)-[:READS_TABLE]->(t)
                """, table=table_name, database=database,
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
                tx.run("""
                    MERGE (tab:Table {name: $table, database: $database})
                    SET tab.platform = COALESCE(tab.platform, 'Unknown')
                    WITH tab
                    MATCH (t:Target {name: $target, mapping: $mapping})
                    MERGE (t)-[:WRITES_TABLE]->(tab)
                """, table=table_name, database=database,
                      target=target_name, mapping=mapping_name)
        
        # 4. Create Transformation nodes
        for trans in model.get("transformations", []):
            trans_name = trans.get("name", "")
            trans_type = trans.get("type", "")
            
            # Prepare properties (exclude internal fields except _optimization_hint)
            trans_props = {
                "name": trans_name,
                "type": trans_type,
                "mapping": mapping_name,
                "optimization_hint": trans.get("_optimization_hint")
            }
            
            # Add other non-internal properties
            for key, value in trans.items():
                if not key.startswith("_") or key == "_optimization_hint":
                    if key not in ["name", "type"]:  # Already set above
                        trans_props[key] = value
            
            tx.run("""
                MERGE (t:Transformation {name: $name, mapping: $mapping})
                SET t += $props
                WITH t
                MATCH (m:Mapping {name: $mapping})
                MERGE (m)-[:HAS_TRANSFORMATION]->(t)
            """, name=trans_name, mapping=mapping_name, props=trans_props)
        
        # 5. Create Connector relationships
        for conn in model.get("connectors", []):
            from_trans = conn.get("from_transformation", "")
            to_trans = conn.get("to_transformation", "")
            
            if from_trans and to_trans:
                tx.run("""
                    MATCH (t1:Transformation {name: $from_trans, mapping: $mapping})
                    MATCH (t2:Transformation {name: $to_trans, mapping: $mapping})
                    MERGE (t1)-[r:CONNECTS_TO {from_port: $from_port, to_port: $to_port}]->(t2)
                """, from_trans=from_trans, to_trans=to_trans, mapping=mapping_name,
                      from_port=conn.get("from_port", ""),
                      to_port=conn.get("to_port", ""))
    
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
            # Merge properties
            for key, value in trans.items():
                if key not in ["name", "type"]:
                    trans_dict[key] = value
            model["transformations"].append(trans_dict)
        
        # Load connectors
        connectors_result = tx.run("""
            MATCH (t1:Transformation {mapping: $name})-[r:CONNECTS_TO]->(t2:Transformation {mapping: $name})
            RETURN t1.name as from, t2.name as to, r.from_port as from_port, r.to_port as to_port
        """, name=mapping_name)
        
        for record in connectors_result:
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
    
    def close(self):
        """Close Neo4j connection."""
        self.driver.close()
        logger.info("GraphStore connection closed")

