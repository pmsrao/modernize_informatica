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

from graph.graph_store import GraphStore
from utils.logger import get_logger

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
    
    def find_dependent_transformations(self, transformation_name: str) -> List[Dict[str, Any]]:
        """Find all transformations that depend on this transformation.
        
        Args:
            transformation_name: Transformation name
            
        Returns:
            List of dependent transformations with depth
        """
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH path = (t:Transformation {name: $name, source_component_type: 'mapping'})<-[:DEPENDS_ON*]-(dependent:Transformation)
                WHERE dependent.source_component_type = 'mapping' OR dependent.source_component_type IS NULL
                RETURN dependent.name as name, 
                       dependent.transformation_name as transformation_name,
                       length(path) as depth
                ORDER BY depth
            """, name=transformation_name)
            
            return [dict(record) for record in result]
    
    def find_transformations_using_table(self, table_name: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find all transformations using a specific table.
        
        Args:
            table_name: Table name
            database: Optional database name
            
        Returns:
            List of transformations using the table
        """
        with self.graph_store.driver.session() as session:
            if database:
                result = session.run("""
                    MATCH (tab:Table {name: $table, database: $database})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(t:Transformation)
                    WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                    RETURN DISTINCT t.name as name, t.transformation_name as transformation_name, t.complexity as complexity
                """, table=table_name, database=database)
            else:
                result = session.run("""
                    MATCH (tab:Table {name: $table})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(t:Transformation)
                    WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                    RETURN DISTINCT t.name as name, t.transformation_name as transformation_name, t.complexity as complexity
                """, table=table_name)
            
            return [dict(record) for record in result]
    
    def trace_lineage(self, source_table: str, target_table: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """Trace data lineage from source to target across transformations.
        
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
                              <-[:HAS_SOURCE]-(t1:Transformation)
                              WHERE t1.source_component_type = 'mapping' OR t1.source_component_type IS NULL
                              -[:HAS_TARGET]->(tgt1:Target)
                              -[:WRITES_TABLE]->(intermediate:Table)
                              <-[:READS_TABLE]-(s2:Source)
                              <-[:HAS_SOURCE]-(t2:Transformation)
                              WHERE t2.source_component_type = 'mapping' OR t2.source_component_type IS NULL
                              -[:HAS_TARGET]->(tgt2:Target)
                              -[:WRITES_TABLE]->(tgt:Table {name: $target, database: $database})
                    RETURN path, 
                           [n in nodes(path) WHERE n:Transformation AND (n.source_component_type = 'mapping' OR n.source_component_type IS NULL) | n.name] as transformations
                    LIMIT 10
                """, source=source_table, target=target_table, database=database)
            else:
                result = session.run("""
                    MATCH path = (src:Table {name: $source})
                              <-[:READS_TABLE]-(s:Source)
                              <-[:HAS_SOURCE]-(t1:Transformation)
                              WHERE t1.source_component_type = 'mapping' OR t1.source_component_type IS NULL
                              -[:HAS_TARGET]->(tgt1:Target)
                              -[:WRITES_TABLE]->(intermediate:Table)
                              <-[:READS_TABLE]-(s2:Source)
                              <-[:HAS_SOURCE]-(t2:Transformation)
                              WHERE t2.source_component_type = 'mapping' OR t2.source_component_type IS NULL
                              -[:HAS_TARGET]->(tgt2:Target)
                              -[:WRITES_TABLE]->(tgt:Table {name: $target})
                    RETURN path, 
                           [n in nodes(path) WHERE n:Transformation AND (n.source_component_type = 'mapping' OR n.source_component_type IS NULL) | n.name] as transformations
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
                    RETURN t.name as name, t.transformation as transformation, t.type as type
                    LIMIT 50
                """, type=transformation_type, pattern=pattern)
            else:
                result = session.run("""
                    MATCH (t:Transformation {type: $type})
                    RETURN t.name as name, t.transformation as transformation, t.type as type
                    LIMIT 50
                """, type=transformation_type)
            
            return [dict(record) for record in result]
    
    def get_migration_order(self) -> List[Dict[str, Any]]:
        """Get recommended migration order based on dependencies.
        
        Returns:
            List of transformations in recommended migration order
        """
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH (t:Transformation)
                WHERE (t.source_component_type = 'mapping' OR t.source_component_type IS NULL)
                AND NOT (t)-[:DEPENDS_ON]->()
                RETURN t.name as name, t.transformation_name as transformation_name, t.complexity as complexity
                ORDER BY t.complexity
            """)
            
            return [dict(record) for record in result]
    
    def get_transformation_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about transformations in graph.
        
        Returns:
            Statistics dictionary
        """
        with self.graph_store.driver.session() as session:
            stats = {}
            
            # Total transformations (mappings)
            result = session.run("""
                MATCH (t:Transformation)
                WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                RETURN count(t) as count
            """).single()
            stats["total_transformations"] = result["count"] if result else 0
            
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
                MATCH (t:Transformation)
                WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                RETURN t.complexity as complexity, count(t) as count
                ORDER BY complexity
            """)
            stats["complexity_distribution"] = {record["complexity"]: record["count"] for record in result}
            
            return stats
    
    def find_pattern_across_transformations(self, pattern_type: str, pattern_value: str) -> List[Dict[str, Any]]:
        """Find transformations using a specific pattern.
        
        Args:
            pattern_type: Type of pattern (e.g., "expression", "transformation", "table")
            pattern_value: Pattern value to search for
            
        Returns:
            List of transformations using the pattern
        """
        with self.graph_store.driver.session() as session:
            if pattern_type == "expression":
                result = session.run("""
                    MATCH (t:Transformation)-[:HAS_TRANSFORMATION]->(main:Transformation)
                    WHERE (main.source_component_type = 'mapping' OR main.source_component_type IS NULL)
                    AND toString(t.properties) CONTAINS $pattern
                    RETURN DISTINCT main.name as name, main.transformation_name as transformation_name, 
                           t.name as transformation, t.type as type
                    LIMIT 50
                """, pattern=pattern_value)
            elif pattern_type == "table":
                result = session.run("""
                    MATCH (tab:Table {name: $pattern})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(t:Transformation)
                    WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                    RETURN DISTINCT t.name as name, t.transformation_name as transformation_name
                    UNION
                    MATCH (tab:Table {name: $pattern})<-[:WRITES_TABLE]-(tgt:Target)<-[:HAS_TARGET]-(t:Transformation)
                    WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                    RETURN DISTINCT t.name as name, t.transformation_name as transformation_name
                    LIMIT 50
                """, pattern=pattern_value)
            else:
                result = session.run("""
                    MATCH (t:Transformation)
                    WHERE (t.source_component_type = 'mapping' OR t.source_component_type IS NULL)
                    AND toString(t) CONTAINS $pattern
                    RETURN DISTINCT t.name as name, t.transformation_name as transformation_name
                    LIMIT 50
                """, pattern=pattern_value)
            
            return [dict(record) for record in result]
    
    def get_impact_analysis(self, transformation_name: str) -> Dict[str, Any]:
        """Get comprehensive impact analysis for a transformation.
        
        Args:
            transformation_name: Transformation name to analyze
            
        Returns:
            Impact analysis results
        """
        with self.graph_store.driver.session() as session:
            # Find all tables used by this transformation
            # Use UNION to handle both Source and Target separately (Neo4j doesn't allow mixing label expressions)
            tables_result = session.run("""
                MATCH (t:Transformation {name: $name, source_component_type: 'mapping'})-[:HAS_SOURCE]->(s:Source)-[:READS_TABLE]->(tab:Table)
                RETURN DISTINCT tab.name as table, tab.database as database, 'READS_TABLE' as relationship_type
                UNION
                MATCH (t:Transformation {name: $name, source_component_type: 'mapping'})-[:HAS_TARGET]->(tgt:Target)-[:WRITES_TABLE]->(tab:Table)
                RETURN DISTINCT tab.name as table, tab.database as database, 'WRITES_TABLE' as relationship_type
            """, name=transformation_name)
            
            # Group by table to collect relationship types
            tables_dict = {}
            for record in tables_result:
                table_name = record["table"]
                if table_name not in tables_dict:
                    tables_dict[table_name] = {
                        "table": table_name,
                        "database": record["database"],
                        "relationship_types": []
                    }
                if record["relationship_type"] not in tables_dict[table_name]["relationship_types"]:
                    tables_dict[table_name]["relationship_types"].append(record["relationship_type"])
            
            tables = list(tables_dict.values())
            
            # Find dependent transformations
            deps_result = session.run("""
                MATCH path = (t:Transformation {name: $name, source_component_type: 'mapping'})<-[:DEPENDS_ON*]-(dependent:Transformation)
                WHERE dependent.source_component_type = 'mapping' OR dependent.source_component_type IS NULL
                RETURN DISTINCT dependent.name as name, dependent.transformation_name as transformation_name,
                       length(path) as depth
                ORDER BY depth
            """, name=transformation_name)
            
            dependents = [dict(record) for record in deps_result]
            
            # Find transformations using same tables
            shared_tables = []
            for table_info in tables:
                table_name = table_info.get("table")
                if table_name:
                    shared = session.run("""
                        MATCH (tab:Table {name: $table})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(t:Transformation)
                        WHERE t.name <> $transformation AND (t.source_component_type = 'mapping' OR t.source_component_type IS NULL)
                        RETURN DISTINCT t.name as name, t.transformation_name as transformation_name
                        UNION
                        MATCH (tab:Table {name: $table})<-[:WRITES_TABLE]-(tgt:Target)<-[:HAS_TARGET]-(t:Transformation)
                        WHERE t.name <> $transformation AND (t.source_component_type = 'mapping' OR t.source_component_type IS NULL)
                        RETURN DISTINCT t.name as name, t.transformation_name as transformation_name
                        LIMIT 10
                    """, table=table_name, transformation=transformation_name)
                    shared_tables.extend([dict(record) for record in shared])
            
            return {
                "transformation": transformation_name,
                "tables_used": tables,
                "dependent_transformations": dependents,
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
        """Get migration readiness assessment for all transformations.
        
        Returns:
            List of transformations with readiness scores
        """
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH (t:Transformation)
                WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                OPTIONAL MATCH (t)-[:HAS_TRANSFORMATION]->(nested:Transformation)
                WITH t, count(nested) as trans_count,
                     collect(DISTINCT nested.type) as trans_types
                RETURN t.name as name, t.transformation_name as transformation_name,
                       t.complexity as complexity,
                       trans_count,
                       trans_types,
                       CASE 
                         WHEN t.complexity = 'LOW' AND trans_count < 5 THEN 'READY'
                         WHEN t.complexity = 'MEDIUM' AND trans_count < 10 THEN 'READY'
                         WHEN t.complexity = 'HIGH' THEN 'REVIEW_NEEDED'
                         ELSE 'REVIEW_NEEDED'
                       END as readiness
                ORDER BY readiness, trans_count
            """)
            
            return [dict(record) for record in result]
    
    def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all pipelines (workflows) in the graph.
        
        Returns:
            List of pipelines with metadata
        """
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH (p:Pipeline)
                OPTIONAL MATCH (p)-[:CONTAINS]->(t:Task)
                RETURN p.name as name,
                       p.type as type,
                       p.source_component_type as source_component_type,
                       count(DISTINCT t) as task_count
                ORDER BY p.name
            """)
            
            pipelines = []
            for record in result:
                pipelines.append({
                    "name": record["name"],
                    "type": record["type"],
                    "source_component_type": record.get("source_component_type", "workflow"),
                    "task_count": record["task_count"]
                })
            return pipelines
    
    def get_pipeline_structure(self, pipeline_name: str) -> Optional[Dict[str, Any]]:
        """Get complete pipeline structure with tasks and transformations.
        
        Returns a generic canonical model representation:
        - Pipeline contains Tasks (generic term for Informatica Sessions)
        - Tasks contain Transformations (generic term for Informatica Mappings)
        
        Args:
            pipeline_name: Pipeline name
            
        Returns:
            Pipeline structure with tasks and transformations, or None if not found
            Structure: {
                "name": "...",
                "type": "...",
                "source_component_type": "workflow",
                "properties": {...},
                "tasks": [
                    {
                        "name": "...",
                        "type": "...",
                        "properties": {...},
                        "transformations": [...]
                    }
                ]
            }
        """
        with self.graph_store.driver.session() as session:
            # Get pipeline (workflow)
            pipeline_result = session.run("""
                MATCH (p:Pipeline {name: $name})
                RETURN p.name as name, p.type as type, p.source_component_type as source_component_type, properties(p) as properties
            """, name=pipeline_name).single()
            
            if not pipeline_result:
                return None
            
            pipeline = {
                "name": pipeline_result["name"],
                "type": pipeline_result["type"],
                "source_component_type": pipeline_result.get("source_component_type", "workflow"),
                "properties": dict(pipeline_result["properties"]) if pipeline_result["properties"] else {}
            }
            
            # Get tasks in pipeline (directly or via sub pipelines) with their transformations
            tasks_result = session.run("""
                MATCH (p:Pipeline {name: $name})
                OPTIONAL MATCH (p)-[:CONTAINS]->(t:Task)
                OPTIONAL MATCH (p)-[:CONTAINS]->(sp:SubPipeline)-[:CONTAINS]->(t2:Task)
                WITH collect(DISTINCT t) + collect(DISTINCT t2) as all_tasks
                UNWIND [task IN all_tasks WHERE task IS NOT NULL] as task_node
                RETURN DISTINCT task_node.name as name, 
                       task_node.type as type, 
                       task_node.source_component_type as source_component_type,
                       properties(task_node) as properties
                ORDER BY task_node.name
            """, name=pipeline_name)
            
            # Then, for each task, get its transformations
            tasks = []
            for task_record in tasks_result:
                task_name = task_record["name"]
                if not task_name:
                    continue
                    
                task_props = dict(task_record["properties"]) if task_record["properties"] else {}
                
                # Get transformations for this task via EXECUTES relationship
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
            
            pipeline["tasks"] = tasks
            return pipeline
    
    
    def get_tasks_in_pipeline(self, pipeline_name: str) -> List[Dict[str, Any]]:
        """Get all tasks in a workflow.
        
        Args:
            workflow_name: Workflow/Pipeline name
            
        Returns:
            List of tasks in the workflow
        """
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH (p:Pipeline {name: $name})-[:CONTAINS]->(t:Task)
                RETURN t.name as name, t.type as type, t.source_component_type as source_component_type, properties(t) as properties
                ORDER BY t.name
            """, name=pipeline_name)
            
            return [dict(record) for record in result]
    
    def get_field_lineage(self, field_name: str, transformation_name: str) -> List[Dict[str, Any]]:
        """Get column-level lineage for a specific field.
        
        Args:
            field_name: Field name
            transformation_name: Transformation name containing the field
            
        Returns:
            List of source fields that feed into this field
        """
        with self.graph_store.driver.session() as session:
            # First try direct DERIVED_FROM relationships (same transformation)
            result = session.run("""
                MATCH (target_field:Field {name: $field_name, transformation: $transformation})
                MATCH (source_field:Field)-[:DERIVED_FROM]->(target_field)
                WHERE source_field.transformation = $transformation
                RETURN DISTINCT source_field.name as source_field,
                       source_field.transformation as source_transformation,
                       source_field.parent_transformation as source_parent_transformation,
                       1 as depth
                ORDER BY source_field.name
            """, field_name=field_name, transformation=transformation_name)
            
            direct_lineage = [dict(record) for record in result]
            
            # Also try path-based queries for cross-transformation lineage
            result2 = session.run("""
                MATCH path = (source_field:Field)-[:FEEDS|DERIVED_FROM*]->(target_field:Field {name: $field_name, transformation: $transformation})
                WHERE source_field <> target_field
                RETURN DISTINCT source_field.name as source_field,
                       source_field.transformation as source_transformation,
                       source_field.parent_transformation as source_parent_transformation,
                       length(path) as depth
                ORDER BY depth
            """, field_name=field_name, transformation=transformation_name)
            
            path_lineage = [dict(record) for record in result2]
            
            # Combine and deduplicate
            seen = set()
            combined = []
            for item in direct_lineage + path_lineage:
                key = (item.get("source_field"), item.get("source_transformation"))
                if key not in seen:
                    seen.add(key)
                    combined.append(item)
            
            return combined
    
    def get_field_impact(self, field_name: str, transformation_name: str) -> List[Dict[str, Any]]:
        """Get impact analysis for a field - find all fields that depend on this field.
        
        Args:
            field_name: Field name
            transformation_name: Transformation name containing the field
            
        Returns:
            List of dependent fields
        """
        with self.graph_store.driver.session() as session:
            # First try direct DERIVED_FROM relationships (same transformation)
            result = session.run("""
                MATCH (source_field:Field {name: $field_name, transformation: $transformation})
                MATCH (target_field:Field)-[:DERIVED_FROM]->(source_field)
                WHERE target_field.transformation = $transformation
                RETURN DISTINCT target_field.name as target_field,
                       target_field.transformation as target_transformation,
                       target_field.parent_transformation as target_parent_transformation,
                       1 as depth
                ORDER BY target_field.name
            """, field_name=field_name, transformation=transformation_name)
            
            direct_impact = [dict(record) for record in result]
            
            # Also try path-based queries for cross-transformation impact
            result2 = session.run("""
                MATCH path = (source_field:Field {name: $field_name, transformation: $transformation})-[:FEEDS|DERIVED_FROM*]->(target_field:Field)
                WHERE source_field <> target_field
                RETURN DISTINCT target_field.name as target_field,
                       target_field.transformation as target_transformation,
                       target_field.parent_transformation as target_parent_transformation,
                       length(path) as depth
                ORDER BY depth
            """, field_name=field_name, transformation=transformation_name)
            
            path_impact = [dict(record) for record in result2]
            
            # Combine and deduplicate
            seen = set()
            combined = []
            for item in direct_impact + path_impact:
                key = (item.get("target_field"), item.get("target_transformation"))
                if key not in seen:
                    seen.add(key)
                    combined.append(item)
            
            return combined
    
    def get_cross_pipeline_field_dependencies(self, field_name: str) -> List[Dict[str, Any]]:
        """Find field dependencies across different pipelines/transformations.
        
        Args:
            field_name: Field name to search for
            
        Returns:
            List of transformations and fields that use this field
        """
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH (source_field:Field {name: $field_name})
                MATCH path = (source_field)-[:FEEDS|DERIVED_FROM*]->(target_field:Field)
                WHERE source_field.transformation <> target_field.transformation
                RETURN DISTINCT target_field.transformation as target_transformation,
                       target_field.name as target_field,
                       target_field.parent_transformation as target_parent_transformation,
                       length(path) as depth
                ORDER BY target_transformation, depth
            """, field_name=field_name)
            
            return [dict(record) for record in result]
    
    def get_transformation_code_files(self, transformation_name: str) -> List[Dict[str, Any]]:
        """Get code files for a transformation.
        
        Args:
            transformation_name: Name of the transformation (mapping)
            
        Returns:
            List of code file metadata dictionaries
        """
        return self.graph_store.get_code_metadata(transformation_name)
    
    def get_mapping_code_files(self, mapping_name: str) -> List[Dict[str, Any]]:
        """Backward compatibility alias for get_transformation_code_files."""
        return self.get_transformation_code_files(mapping_name)
    
    def get_component_file_metadata(self, component_name: str, component_type: str) -> Optional[Dict[str, Any]]:
        """Get file metadata for a component.
        
        Args:
            component_name: Name of the component
            component_type: Type of component (Workflow, Session, Worklet, Mapping, Mapplet)
            
        Returns:
            File metadata dictionary or None
        """
        return self.graph_store.get_file_metadata(component_name, component_type)
    
    def list_all_source_files(self) -> List[Dict[str, Any]]:
        """List all source files with metadata.
        
        Returns:
            List of source file metadata dictionaries
        """
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH (f:SourceFile)
                RETURN f
                ORDER BY f.filename
            """)
            
            return [dict(record["f"]) for record in result]
    
    def get_components_by_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Find components loaded from a specific file.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            List of components with their types
        """
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH (f:SourceFile {file_path: $file_path})<-[:LOADED_FROM]-(component)
                RETURN labels(component)[0] as component_type, 
                       component.name as component_name,
                       properties(component) as properties
            """, file_path=file_path)
            
            return [dict(record) for record in result]
    
    def list_all_code_files(self) -> List[Dict[str, Any]]:
        """List all generated code files with metadata.
        
        Returns:
            List of code metadata dictionaries
        """
        return self.graph_store.list_all_code_files()
    
    def get_code_repository_structure(self) -> Dict[str, Any]:
        """Get tree structure of generated code repository.
        
        Returns:
            Dictionary with repository tree structure - simple filesystem view
            Shows the actual folder structure as it exists on disk
        """
        import os
        from pathlib import Path
        
        # Simple filesystem-based tree structure
        # Show generated_ai (AI-reviewed code) instead of generated
        project_root = Path(__file__).parent.parent.parent
        generated_dir = project_root / "workspace" / "generated_ai"
        # Fallback to generated if generated_ai doesn't exist
        if not generated_dir.exists():
            generated_dir = project_root / "workspace" / "generated"
        
        def build_tree(path: Path, rel_path: str = "") -> Dict[str, Any]:
            """Recursively build tree structure from filesystem."""
            tree = {}
            
            if not path.exists():
                return tree
            
            try:
                items = sorted(path.iterdir())
                for item in items:
                    item_rel_path = os.path.join(rel_path, item.name) if rel_path else item.name
                    
                    if item.is_file() and item.suffix in ['.py', '.sql', '.json', '.yaml', '.yml']:
                        # It's a file - store with relative path for loading
                        rel_path = str(item.relative_to(generated_dir))
                        tree[item.name] = {
                            "type": "file",
                            "path": rel_path,
                            "file_path": rel_path  # Use relative path - API will resolve it
                        }
                    elif item.is_dir():
                        # It's a directory - recurse
                        subtree = build_tree(item, item_rel_path)
                        if subtree:
                            tree[item.name] = subtree
            except PermissionError:
                pass
            
            return tree
        
        tree = build_tree(generated_dir)
        return tree

    def get_source_repository_structure(self) -> Dict[str, Any]:
        """Get tree structure of source repository (staging directory).
        
        Returns:
            Dictionary with repository tree structure - simple filesystem view
            Shows the actual folder structure as it exists on disk
        """
        import os
        from pathlib import Path
        
        # Simple filesystem-based tree structure for source files
        project_root = Path(__file__).parent.parent.parent
        staging_dir = project_root / "workspace" / "staging"
        
        def build_tree(path: Path, rel_path: str = "") -> Dict[str, Any]:
            """Recursively build tree structure from filesystem."""
            tree = {}
            
            if not path.exists():
                return tree
            
            try:
                items = sorted(path.iterdir())
                for item in items:
                    item_rel_path = os.path.join(rel_path, item.name) if rel_path else item.name
                    
                    if item.is_file():
                        # It's a file - store with relative path for loading
                        rel_path = str(item.relative_to(staging_dir))
                        tree[item.name] = {
                            "type": "file",
                            "path": rel_path,
                            "file_path": rel_path  # Use relative path - API will resolve it
                        }
                    elif item.is_dir():
                        # It's a directory - recurse
                        subtree = build_tree(item, item_rel_path)
                        if subtree:
                            tree[item.name] = subtree
            except PermissionError:
                pass
            
            return tree
        
        tree = build_tree(staging_dir)
        return tree
    
    def get_repository_statistics(self) -> Dict[str, Any]:
        """Get repository statistics for assessment.
        
        Returns:
            Dictionary with component counts and distributions
        """
        with self.graph_store.driver.session() as session:
            stats = {}
            
            # Count all component types
            component_types = ["Workflow", "Session", "Worklet", "Mapping", "Transformation", 
                            "Source", "Target", "Table"]
            
            for comp_type in component_types:
                result = session.run(f"MATCH (n:{comp_type}) RETURN count(n) as count").single()
                stats[f"total_{comp_type.lower()}s"] = result["count"] if result else 0
            
            # Transformation type distribution
            result = session.run("""
                MATCH (t:Transformation)
                RETURN t.type as type, count(t) as count
                ORDER BY count DESC
            """)
            stats["transformation_type_distribution"] = {
                record["type"]: record["count"] for record in result
            }
            
            return stats
    
    def get_complexity_metrics(self) -> Dict[str, Any]:
        """Get complexity metrics for assessment.
        
        Returns:
            Dictionary with complexity analysis
        """
        with self.graph_store.driver.session() as session:
            metrics = {}
            
            # Mapping complexity distribution
            result = session.run("""
                MATCH (m:Mapping)
                WHERE m.complexity IS NOT NULL
                RETURN m.complexity as complexity, count(m) as count
            """)
            metrics["mapping_complexity_distribution"] = {
                record["complexity"]: record["count"] for record in result
            }
            
            # Average transformations per mapping
            result = session.run("""
                MATCH (m:Mapping)
                OPTIONAL MATCH (m)-[:HAS_TRANSFORMATION]->(t:Transformation)
                WITH m, count(t) as trans_count
                RETURN avg(trans_count) as avg_trans, 
                       max(trans_count) as max_trans,
                       min(trans_count) as min_trans
            """).single()
            
            if result:
                metrics["transformation_statistics"] = {
                    "average": float(result["avg_trans"]) if result["avg_trans"] else 0.0,
                    "max": result["max_trans"] if result["max_trans"] else 0,
                    "min": result["min_trans"] if result["min_trans"] else 0
                }
            
            return metrics
    
    def get_pattern_usage(self) -> Dict[str, Any]:
        """Get pattern usage statistics for assessment.
        
        Returns:
            Dictionary with pattern analysis
        """
        with self.graph_store.driver.session() as session:
            patterns = {}
            
            # Transformation type patterns
            result = session.run("""
                MATCH (m:Mapping)-[:HAS_TRANSFORMATION]->(t:Transformation)
                WITH t.type as trans_type, count(*) as usage_count
                WHERE usage_count > 1
                RETURN trans_type, usage_count
                ORDER BY usage_count DESC
                LIMIT 20
            """)
            patterns["transformation_patterns"] = [
                {"type": record["trans_type"], "usage_count": record["usage_count"]}
                for record in result
            ]
            
            # SCD type distribution
            result = session.run("""
                MATCH (m:Mapping)
                WHERE m.scd_type IS NOT NULL
                RETURN m.scd_type as scd_type, count(m) as count
            """)
            patterns["scd_type_distribution"] = {
                record["scd_type"]: record["count"] for record in result
            }
            
            # External system usage
            result = session.run("""
                MATCH (m:Mapping)-[:HAS_SOURCE]->(s:Source)
                WHERE s.database_type IS NOT NULL AND s.database_type <> 'Informatica'
                RETURN DISTINCT s.database_type as system_type, count(DISTINCT m) as mapping_count
            """)
            patterns["external_system_usage"] = [
                {"system_type": record["system_type"], "mapping_count": record["mapping_count"]}
                for record in result
            ]
            
            return patterns
    
    def get_dependency_graph(self) -> Dict[str, Any]:
        """Get complete dependency graph for assessment.
        
        Returns:
            Dictionary with dependency information
        """
        with self.graph_store.driver.session() as session:
            # Get all mapping dependencies
            result = session.run("""
                MATCH (m1:Mapping)-[:DEPENDS_ON]->(m2:Mapping)
                RETURN m1.name as source, m2.name as target
            """)
            
            dependency_edges = [
                {"source": record["source"], "target": record["target"]}
                for record in result
            ]
            
            # Get independent mappings
            result = session.run("""
                MATCH (m:Mapping)
                WHERE NOT (m)-[:DEPENDS_ON]->()
                RETURN m.name as name
            """)
            independent_mappings = [record["name"] for record in result]
            
            # Get highly dependent mappings
            result = session.run("""
                MATCH (m:Mapping)-[:DEPENDS_ON]->(dep:Mapping)
                WITH m, count(dep) as dep_count
                WHERE dep_count > 3
                RETURN m.name as name, dep_count
                ORDER BY dep_count DESC
            """)
            highly_dependent = [
                {"name": record["name"], "dependency_count": record["dep_count"]}
                for record in result
            ]
            
            return {
                "dependency_edges": dependency_edges,
                "independent_mappings": independent_mappings,
                "highly_dependent_mappings": highly_dependent,
                "total_dependencies": len(dependency_edges)
            }

