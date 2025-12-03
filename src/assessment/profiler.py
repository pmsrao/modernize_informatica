"""Profiler — Collects component statistics from Neo4j."""
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
from src.graph.graph_queries import GraphQueries
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Profiler:
    """Profiles Informatica repository to collect component statistics."""
    
    def __init__(self, graph_store: GraphStore):
        """Initialize profiler.
        
        Args:
            graph_store: GraphStore instance
        """
        self.graph_store = graph_store
        self.graph_queries = GraphQueries(graph_store)
        logger.info("Profiler initialized")
    
    def profile_repository(self) -> Dict[str, Any]:
        """Get overall repository statistics.
        
        Returns:
            Dictionary with repository statistics:
            - total_workflows: int
            - total_sessions: int (tasks)
            - total_worklets: int
            - total_mappings: int
            - total_transformations: int
            - total_sources: int
            - total_targets: int
            - total_tables: int
            - component_type_distribution: Dict[str, int]
            - average_tasks_per_workflow: float
            - average_transformations_per_mapping: float
        """
        logger.info("Profiling repository...")
        
        with self.graph_store.driver.session() as session:
            stats = {}
            
            # Count pipelines (workflows)
            result = session.run("MATCH (p:Pipeline) RETURN count(p) as count").single()
            stats["total_workflows"] = result["count"] if result else 0
            
            # Count tasks (sessions)
            result = session.run("MATCH (t:Task) RETURN count(t) as count").single()
            stats["total_sessions"] = result["count"] if result else 0
            
            # Count sub pipelines (worklets)
            result = session.run("MATCH (sp:SubPipeline) RETURN count(sp) as count").single()
            stats["total_worklets"] = result["count"] if result else 0
            
            # Count transformations (mappings) - filter by source_component_type
            result = session.run("""
                MATCH (t:Transformation)
                WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                RETURN count(t) as count
            """).single()
            stats["total_mappings"] = result["count"] if result else 0
            
            # Count transformations
            result = session.run("MATCH (t:Transformation) RETURN count(t) as count").single()
            stats["total_transformations"] = result["count"] if result else 0
            
            # Count sources
            result = session.run("MATCH (s:Source) RETURN count(s) as count").single()
            stats["total_sources"] = result["count"] if result else 0
            
            # Count targets
            result = session.run("MATCH (t:Target) RETURN count(t) as count").single()
            stats["total_targets"] = result["count"] if result else 0
            
            # Count tables
            result = session.run("MATCH (t:Table) RETURN count(t) as count").single()
            stats["total_tables"] = result["count"] if result else 0
            
            # Component type distribution
            stats["component_type_distribution"] = {
                "workflows": stats["total_workflows"],
                "sessions": stats["total_sessions"],
                "worklets": stats["total_worklets"],
                "mappings": stats["total_mappings"],
                "transformations": stats["total_transformations"],
                "sources": stats["total_sources"],
                "targets": stats["total_targets"],
                "tables": stats["total_tables"]
            }
            
            # Average tasks per pipeline
            if stats["total_workflows"] > 0:
                result = session.run("""
                    MATCH (p:Pipeline)
                    OPTIONAL MATCH (p)-[:CONTAINS]->(t:Task)
                    WITH p, count(t) as task_count
                    RETURN avg(task_count) as avg_tasks
                """).single()
                stats["average_tasks_per_workflow"] = float(result["avg_tasks"]) if result and result["avg_tasks"] is not None else 0.0
            else:
                stats["average_tasks_per_workflow"] = 0.0
            
            # Average nested transformations per transformation
            if stats["total_mappings"] > 0:
                result = session.run("""
                    MATCH (t:Transformation)
                    WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                    OPTIONAL MATCH (t)-[:HAS_TRANSFORMATION]->(nt:Transformation)
                    WITH t, count(nt) as trans_count
                    RETURN avg(trans_count) as avg_trans
                """).single()
                stats["average_transformations_per_mapping"] = float(result["avg_trans"]) if result and result["avg_trans"] is not None else 0.0
            else:
                stats["average_transformations_per_mapping"] = 0.0
            
            logger.info(f"Repository profiling complete: {stats['total_workflows']} workflows, "
                       f"{stats['total_mappings']} mappings, {stats['total_transformations']} transformations")
            
            return stats
    
    def profile_workflows(self) -> List[Dict[str, Any]]:
        """Analyze workflow complexity.
        
        Returns:
            List of workflow profiles with:
            - name: str
            - task_count: int
            - worklet_count: int
            - mapping_count: int
            - complexity_score: str (LOW/MEDIUM/HIGH)
            - has_dependencies: bool
        """
        logger.info("Profiling workflows...")
        
        pipelines = self.graph_queries.list_pipelines()
        workflow_profiles = []
        
        with self.graph_store.driver.session() as session:
            for pipeline in pipelines:
                pipeline_name = pipeline["name"]
                
                # Get detailed pipeline structure
                pipeline_structure = self.graph_queries.get_pipeline_structure(pipeline_name)
                if not pipeline_structure:
                    continue
                
                # Count sub pipelines (worklets)
                result = session.run("""
                    MATCH (p:Pipeline {name: $name})-[:CONTAINS]->(sp:SubPipeline)
                    RETURN count(sp) as count
                """, name=pipeline_name).single()
                worklet_count = result["count"] if result else 0
                
                # Count transformations via tasks
                transformation_count = 0
                for task in pipeline_structure.get("tasks", []):
                    transformation_count += len(task.get("transformations", []))
                
                # Calculate complexity score
                task_count = pipeline.get("task_count", 0)
                complexity_score = self._calculate_workflow_complexity(task_count, worklet_count, transformation_count)
                
                # Check for dependencies
                result = session.run("""
                    MATCH (p:Pipeline {name: $name})
                    OPTIONAL MATCH (p)-[:CONTAINS]->(t:Task)-[:EXECUTES]->(trans:Transformation)
                    OPTIONAL MATCH (trans)-[:DEPENDS_ON]->(dep:Transformation)
                    RETURN count(DISTINCT dep) > 0 as has_dependencies
                """, name=pipeline_name).single()
                has_dependencies = result["has_dependencies"] if result else False
                
                workflow_profiles.append({
                    "name": pipeline_name,
                    "task_count": task_count,
                    "worklet_count": worklet_count,
                    "mapping_count": transformation_count,
                    "complexity_score": complexity_score,
                    "has_dependencies": has_dependencies
                })
        
        logger.info(f"Profiled {len(workflow_profiles)} workflows")
        return workflow_profiles
    
    def profile_mappings(self) -> List[Dict[str, Any]]:
        """Analyze mapping complexity.
        
        Returns:
            List of mapping profiles with:
            - name: str
            - transformation_count: int
            - expression_complexity: str (SIMPLE/MEDIUM/COMPLEX)
            - lookup_count: int
            - custom_function_count: int
            - aggregator_count: int
            - router_count: int
            - complexity_score: str (LOW/MEDIUM/HIGH)
        """
        logger.info("Profiling mappings...")
        
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH (t:Transformation)
                WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                OPTIONAL MATCH (t)-[:HAS_TRANSFORMATION]->(nt:Transformation)
                WITH t, collect(nt) as transformations
                RETURN t.name as name,
                       t.transformation_name as transformation_name,
                       t.complexity as stored_complexity,
                       size(transformations) as transformation_count,
                       transformations
            """)
            
            mapping_profiles = []
            
            for record in result:
                mapping_name = record["name"]
                transformations = record["transformations"]
                transformation_count = record["transformation_count"]
                
                # Count transformation types
                lookup_count = sum(1 for t in transformations if t.get("type") == "Lookup")
                aggregator_count = sum(1 for t in transformations if t.get("type") == "Aggregator")
                router_count = sum(1 for t in transformations if t.get("type") == "Router")
                
                # Analyze expressions for complexity
                expression_complexity = self._analyze_expression_complexity(transformations)
                
                # Count custom functions (would need to parse expressions)
                custom_function_count = 0  # Placeholder - would need expression parsing
                
                # Calculate complexity score
                complexity_score = self._calculate_mapping_complexity(
                    transformation_count, expression_complexity, lookup_count,
                    aggregator_count, router_count
                )
                
                mapping_profiles.append({
                    "name": mapping_name,
                    "transformation_name": record.get("transformation_name"),
                    "transformation_count": transformation_count,
                    "expression_complexity": expression_complexity,
                    "lookup_count": lookup_count,
                    "custom_function_count": custom_function_count,
                    "aggregator_count": aggregator_count,
                    "router_count": router_count,
                    "complexity_score": complexity_score,
                    "stored_complexity": record.get("stored_complexity")
                })
            
            logger.info(f"Profiled {len(mapping_profiles)} mappings")
            return mapping_profiles
    
    def profile_transformations(self) -> Dict[str, Any]:
        """Analyze transformation type distribution and patterns.
        
        Returns:
            Dictionary with transformation statistics:
            - type_distribution: Dict[str, int]
            - average_per_mapping: Dict[str, float]
            - lookup_cache_usage: Dict[str, int]
            - partitioning_strategies: Dict[str, int]
        """
        logger.info("Profiling transformations...")
        
        with self.graph_store.driver.session() as session:
            # Transformation type distribution
            result = session.run("""
                MATCH (t:Transformation)
                RETURN t.type as type, count(t) as count
                ORDER BY count DESC
            """)
            type_distribution = {record["type"]: record["count"] for record in result}
            
            # Average nested transformations per transformation by type
            result = session.run("""
                MATCH (t:Transformation)
                WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                OPTIONAL MATCH (t)-[:HAS_TRANSFORMATION]->(nt:Transformation)
                WITH t, nt.type as trans_type, count(nt) as count
                WHERE trans_type IS NOT NULL
                WITH trans_type, collect(count) as counts
                RETURN trans_type, avg(counts) as avg_count
            """)
            average_per_mapping = {record["trans_type"]: float(record["avg_count"]) for record in result}
            
            # Lookup cache usage (placeholder - would need to parse transformation properties)
            lookup_cache_usage = {
                "cached": 0,
                "uncached": 0,
                "persistent": 0
            }
            
            # Partitioning strategies (placeholder - would need to parse session properties)
            partitioning_strategies = {
                "hash": 0,
                "round_robin": 0,
                "key_range": 0,
                "pass_through": 0
            }
            
            return {
                "type_distribution": type_distribution,
                "average_per_mapping": average_per_mapping,
                "lookup_cache_usage": lookup_cache_usage,
                "partitioning_strategies": partitioning_strategies
            }
    
    def calculate_complexity_metrics(self) -> Dict[str, Any]:
        """Compute overall complexity metrics.
        
        Returns:
            Dictionary with complexity metrics:
            - overall_complexity: str (LOW/MEDIUM/HIGH)
            - workflow_complexity_distribution: Dict[str, int]
            - mapping_complexity_distribution: Dict[str, int]
            - high_complexity_workflows: List[str]
            - high_complexity_mappings: List[str]
        """
        logger.info("Calculating complexity metrics...")
        
        workflow_profiles = self.profile_workflows()
        mapping_profiles = self.profile_mappings()
        
        # Workflow complexity distribution
        workflow_complexity_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        high_complexity_workflows = []
        
        for workflow in workflow_profiles:
            complexity = workflow["complexity_score"]
            workflow_complexity_distribution[complexity] = workflow_complexity_distribution.get(complexity, 0) + 1
            if complexity == "HIGH":
                high_complexity_workflows.append(workflow["name"])
        
        # Mapping complexity distribution
        mapping_complexity_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        high_complexity_mappings = []
        
        for mapping in mapping_profiles:
            complexity = mapping["complexity_score"]
            mapping_complexity_distribution[complexity] = mapping_complexity_distribution.get(complexity, 0) + 1
            if complexity == "HIGH":
                high_complexity_mappings.append(mapping["name"])
        
        # Overall complexity
        total_workflows = len(workflow_profiles)
        total_mappings = len(mapping_profiles)
        high_workflow_ratio = len(high_complexity_workflows) / total_workflows if total_workflows > 0 else 0
        high_mapping_ratio = len(high_complexity_mappings) / total_mappings if total_mappings > 0 else 0
        
        if high_workflow_ratio > 0.3 or high_mapping_ratio > 0.3:
            overall_complexity = "HIGH"
        elif high_workflow_ratio > 0.1 or high_mapping_ratio > 0.1:
            overall_complexity = "MEDIUM"
        else:
            overall_complexity = "LOW"
        
        return {
            "overall_complexity": overall_complexity,
            "workflow_complexity_distribution": workflow_complexity_distribution,
            "mapping_complexity_distribution": mapping_complexity_distribution,
            "high_complexity_workflows": high_complexity_workflows,
            "high_complexity_mappings": high_complexity_mappings
        }
    
    def _calculate_workflow_complexity(self, task_count: int, worklet_count: int, mapping_count: int) -> str:
        """Calculate workflow complexity score.
        
        Args:
            task_count: Number of tasks (sessions)
            worklet_count: Number of worklets
            mapping_count: Number of mappings
            
        Returns:
            Complexity score: LOW, MEDIUM, or HIGH
        """
        score = task_count * 1 + worklet_count * 2 + mapping_count * 0.5
        
        if score > 15:
            return "HIGH"
        elif score > 5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_mapping_complexity(self, transformation_count: int, expression_complexity: str,
                                     lookup_count: int, aggregator_count: int, router_count: int) -> str:
        """Calculate mapping complexity score.
        
        Args:
            transformation_count: Total transformation count
            expression_complexity: Expression complexity (SIMPLE/MEDIUM/COMPLEX)
            lookup_count: Number of lookup transformations
            aggregator_count: Number of aggregator transformations
            router_count: Number of router transformations
            
        Returns:
            Complexity score: LOW, MEDIUM, or HIGH
        """
        score = transformation_count * 1
        
        if expression_complexity == "COMPLEX":
            score += 5
        elif expression_complexity == "MEDIUM":
            score += 2
        
        score += lookup_count * 2
        score += aggregator_count * 3
        score += router_count * 2
        
        if score > 20:
            return "HIGH"
        elif score > 10:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _analyze_expression_complexity(self, transformations: List[Any]) -> str:
        """Analyze expression complexity from transformations.
        
        Args:
            transformations: List of transformation nodes
            
        Returns:
            Complexity level: SIMPLE, MEDIUM, or COMPLEX
        """
        # Placeholder implementation
        # Would need to parse expressions from transformation properties
        # For now, use transformation count as proxy
        if len(transformations) > 10:
            return "COMPLEX"
        elif len(transformations) > 5:
            return "MEDIUM"
        else:
            return "SIMPLE"

