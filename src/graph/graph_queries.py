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
    
    def find_pattern_across_mappings(self, pattern_type: str, pattern_value: str) -> List[Dict[str, Any]]:
        """Find mappings using a specific pattern.
        
        Args:
            pattern_type: Type of pattern (e.g., "expression", "transformation", "table")
            pattern_value: Pattern value to search for
            
        Returns:
            List of mappings using the pattern
        """
        with self.graph_store.driver.session() as session:
            if pattern_type == "expression":
                result = session.run("""
                    MATCH (t:Transformation)-[:HAS_TRANSFORMATION]->(m:Mapping)
                    WHERE toString(t.properties) CONTAINS $pattern
                    RETURN DISTINCT m.name as name, m.mapping_name as mapping_name, 
                           t.name as transformation, t.type as type
                    LIMIT 50
                """, pattern=pattern_value)
            elif pattern_type == "table":
                result = session.run("""
                    MATCH (tab:Table {name: $pattern})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(m:Mapping)
                    RETURN DISTINCT m.name as name, m.mapping_name as mapping_name
                    UNION
                    MATCH (tab:Table {name: $pattern})<-[:WRITES_TABLE]-(t:Target)<-[:HAS_TARGET]-(m:Mapping)
                    RETURN DISTINCT m.name as name, m.mapping_name as mapping_name
                    LIMIT 50
                """, pattern=pattern_value)
            else:
                result = session.run("""
                    MATCH (m:Mapping)
                    WHERE toString(m) CONTAINS $pattern
                    RETURN DISTINCT m.name as name, m.mapping_name as mapping_name
                    LIMIT 50
                """, pattern=pattern_value)
            
            return [dict(record) for record in result]
    
    def get_impact_analysis(self, mapping_name: str) -> Dict[str, Any]:
        """Get comprehensive impact analysis for a mapping.
        
        Args:
            mapping_name: Mapping name to analyze
            
        Returns:
            Impact analysis results
        """
        with self.graph_store.driver.session() as session:
            # Find all tables used by this mapping
            # Use UNION to handle both Source and Target separately (Neo4j doesn't allow mixing label expressions)
            tables_result = session.run("""
                MATCH (m:Mapping {name: $name})-[:HAS_SOURCE]->(s:Source)-[:READS_TABLE]->(tab:Table)
                RETURN DISTINCT tab.name as table, tab.database as database, 'READS_TABLE' as relationship_type
                UNION
                MATCH (m:Mapping {name: $name})-[:HAS_TARGET]->(t:Target)-[:WRITES_TABLE]->(tab:Table)
                RETURN DISTINCT tab.name as table, tab.database as database, 'WRITES_TABLE' as relationship_type
            """, name=mapping_name)
            
            tables = [dict(record) for record in tables_result]
            
            # Find dependent mappings
            deps_result = session.run("""
                MATCH (m:Mapping {name: $name})<-[:DEPENDS_ON*]-(dependent:Mapping)
                RETURN DISTINCT dependent.name as name, dependent.mapping_name as mapping_name,
                       length(path) as depth
                ORDER BY depth
            """, name=mapping_name)
            
            dependents = [dict(record) for record in deps_result]
            
            # Find mappings using same tables
            shared_tables = []
            for table_info in tables:
                table_name = table_info.get("table")
                if table_name:
                    shared = session.run("""
                        MATCH (tab:Table {name: $table})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(m:Mapping)
                        WHERE m.name <> $mapping
                        RETURN DISTINCT m.name as name, m.mapping_name as mapping_name
                        UNION
                        MATCH (tab:Table {name: $table})<-[:WRITES_TABLE]-(t:Target)<-[:HAS_TARGET]-(m:Mapping)
                        WHERE m.name <> $mapping
                        RETURN DISTINCT m.name as name, m.mapping_name as mapping_name
                        LIMIT 10
                    """, table=table_name, mapping=mapping_name)
                    shared_tables.extend([dict(record) for record in shared])
            
            return {
                "mapping": mapping_name,
                "tables_used": tables,
                "dependent_mappings": dependents,
                "shared_tables": list(set([s["name"] for s in shared_tables])),
                "impact_score": self._calculate_impact_score(len(dependents), len(tables), len(shared_tables))
            }
    
    def _calculate_impact_score(self, num_dependents: int, num_tables: int, num_shared: int) -> str:
        """Calculate impact score.
        
        Args:
            num_dependents: Number of dependent mappings
            num_tables: Number of tables used
            num_shared: Number of shared tables
            
        Returns:
            Impact score (LOW, MEDIUM, HIGH)
        """
        score = num_dependents * 3 + num_tables * 1 + num_shared * 2
        
        if score > 20:
            return "HIGH"
        elif score > 10:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_migration_readiness(self) -> List[Dict[str, Any]]:
        """Get migration readiness assessment for all mappings.
        
        Returns:
            List of mappings with readiness scores
        """
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH (m:Mapping)
                OPTIONAL MATCH (m)-[:HAS_TRANSFORMATION]->(t:Transformation)
                WITH m, count(t) as trans_count,
                     collect(DISTINCT t.type) as trans_types
                RETURN m.name as name, m.mapping_name as mapping_name,
                       m.complexity as complexity,
                       trans_count,
                       trans_types,
                       CASE 
                         WHEN m.complexity = 'LOW' AND trans_count < 5 THEN 'READY'
                         WHEN m.complexity = 'MEDIUM' AND trans_count < 10 THEN 'READY'
                         WHEN m.complexity = 'HIGH' THEN 'REVIEW_NEEDED'
                         ELSE 'REVIEW_NEEDED'
                       END as readiness
                ORDER BY readiness, trans_count
            """)
            
            return [dict(record) for record in result]

