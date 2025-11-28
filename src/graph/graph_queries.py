"""Graph Queries — High-level query interface."""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.graph.graph_store import GraphStore
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GraphQueries:
    """High-level query interface for graph database."""
    
    def __init__(self, graph_store: GraphStore):
        """Initialize graph queries.
        
        Args:
            graph_store: GraphStore instance
        """
        self.graph_store = graph_store
        logger.info("GraphQueries initialized")
    
    def find_dependent_mappings(self, mapping_name: str) -> List[Dict[str, Any]]:
        """Find all mappings that depend on this mapping.
        
        Args:
            mapping_name: Mapping name
            
        Returns:
            List of dependent mappings with depth
        """
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH path = (m:Mapping {name: $name})<-[:DEPENDS_ON*]-(dependent:Mapping)
                RETURN dependent.name as name, 
                       dependent.mapping_name as mapping_name,
                       length(path) as depth
                ORDER BY depth
            """, name=mapping_name)
            
            return [dict(record) for record in result]
    
    def find_mappings_using_table(self, table_name: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find all mappings using a specific table.
        
        Args:
            table_name: Table name
            database: Optional database name
            
        Returns:
            List of mappings using the table
        """
        with self.graph_store.driver.session() as session:
            if database:
                result = session.run("""
                    MATCH (t:Table {name: $table, database: $database})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(m:Mapping)
                    RETURN DISTINCT m.name as name, m.mapping_name as mapping_name, m.complexity as complexity
                """, table=table_name, database=database)
            else:
                result = session.run("""
                    MATCH (t:Table {name: $table})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(m:Mapping)
                    RETURN DISTINCT m.name as name, m.mapping_name as mapping_name, m.complexity as complexity
                """, table=table_name)
            
            return [dict(record) for record in result]
    
    def trace_lineage(self, source_table: str, target_table: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """Trace data lineage from source to target across mappings.
        
        Args:
            source_table: Source table name
            target_table: Target table name
            database: Optional database name
            
        Returns:
            Lineage path
        """
        with self.graph_store.driver.session() as session:
            if database:
                result = session.run("""
                    MATCH path = (src:Table {name: $source, database: $database})
                              <-[:READS_TABLE]-(s:Source)
                              <-[:HAS_SOURCE]-(m1:Mapping)
                              -[:HAS_TARGET]->(t1:Target)
                              -[:WRITES_TABLE]->(intermediate:Table)
                              <-[:READS_TABLE]-(s2:Source)
                              <-[:HAS_SOURCE]-(m2:Mapping)
                              -[:HAS_TARGET]->(t2:Target)
                              -[:WRITES_TABLE]->(tgt:Table {name: $target, database: $database})
                    RETURN path, 
                           [n in nodes(path) WHERE n:Mapping | n.name] as mappings
                    LIMIT 10
                """, source=source_table, target=target_table, database=database)
            else:
                result = session.run("""
                    MATCH path = (src:Table {name: $source})
                              <-[:READS_TABLE]-(s:Source)
                              <-[:HAS_SOURCE]-(m1:Mapping)
                              -[:HAS_TARGET]->(t1:Target)
                              -[:WRITES_TABLE]->(intermediate:Table)
                              <-[:READS_TABLE]-(s2:Source)
                              <-[:HAS_SOURCE]-(m2:Mapping)
                              -[:HAS_TARGET]->(t2:Target)
                              -[:WRITES_TABLE]->(tgt:Table {name: $target})
                    RETURN path, 
                           [n in nodes(path) WHERE n:Mapping | n.name] as mappings
                    LIMIT 10
                """, source=source_table, target=target_table)
            
            return [dict(record) for record in result]
    
    def find_similar_transformations(self, transformation_type: str, 
                                     pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find similar transformations across mappings.
        
        Args:
            transformation_type: Transformation type
            pattern: Optional pattern to match
            
        Returns:
            List of similar transformations
        """
        with self.graph_store.driver.session() as session:
            if pattern:
                result = session.run("""
                    MATCH (t:Transformation {type: $type})
                    WHERE toString(t.properties) CONTAINS $pattern
                    RETURN t.name as name, t.mapping as mapping, t.type as type
                    LIMIT 50
                """, type=transformation_type, pattern=pattern)
            else:
                result = session.run("""
                    MATCH (t:Transformation {type: $type})
                    RETURN t.name as name, t.mapping as mapping, t.type as type
                    LIMIT 50
                """, type=transformation_type)
            
            return [dict(record) for record in result]
    
    def get_migration_order(self) -> List[Dict[str, Any]]:
        """Get recommended migration order based on dependencies.
        
        Returns:
            List of mappings in recommended migration order
        """
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH (m:Mapping)
                WHERE NOT (m)-[:DEPENDS_ON]->()
                RETURN m.name as name, m.mapping_name as mapping_name, m.complexity as complexity
                ORDER BY m.complexity
            """)
            
            return [dict(record) for record in result]
    
    def get_mapping_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about mappings in graph.
        
        Returns:
            Statistics dictionary
        """
        with self.graph_store.driver.session() as session:
            stats = {}
            
            # Total mappings
            result = session.run("MATCH (m:Mapping) RETURN count(m) as count").single()
            stats["total_mappings"] = result["count"] if result else 0
            
            # Total transformations
            result = session.run("MATCH (t:Transformation) RETURN count(t) as count").single()
            stats["total_transformations"] = result["count"] if result else 0
            
            # Total tables
            result = session.run("MATCH (t:Table) RETURN count(t) as count").single()
            stats["total_tables"] = result["count"] if result else 0
            
            # Transformations by type
            result = session.run("""
                MATCH (t:Transformation)
                RETURN t.type as type, count(t) as count
                ORDER BY count DESC
            """)
            stats["transformations_by_type"] = {record["type"]: record["count"] for record in result}
            
            # Complexity distribution
            result = session.run("""
                MATCH (m:Mapping)
                RETURN m.complexity as complexity, count(m) as count
                ORDER BY complexity
            """)
            stats["complexity_distribution"] = {record["complexity"]: record["count"] for record in result}
            
            return stats

