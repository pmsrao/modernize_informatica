"""Analyzer — Identifies patterns and migration blockers."""
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
from src.assessment.profiler import Profiler
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Analyzer:
    """Analyzes Informatica components to identify patterns and blockers."""
    
    def __init__(self, graph_store: GraphStore, profiler: Optional[Profiler] = None):
        """Initialize analyzer.
        
        Args:
            graph_store: GraphStore instance
            profiler: Optional Profiler instance (will create if not provided)
        """
        self.graph_store = graph_store
        self.graph_queries = GraphQueries(graph_store)
        self.profiler = profiler or Profiler(graph_store)
        logger.info("Analyzer initialized")
    
    def identify_patterns(self) -> Dict[str, Any]:
        """Find common patterns in the repository.
        
        Returns:
            Dictionary with pattern analysis:
            - lookup_cache_patterns: Dict[str, int]
            - partitioning_strategies: Dict[str, int]
            - custom_function_usage: List[Dict[str, Any]]
            - external_dependencies: List[Dict[str, Any]]
            - scd_type_distribution: Dict[str, int]
            - common_transformation_patterns: List[Dict[str, Any]]
        """
        logger.info("Identifying patterns...")
        
        patterns = {}
        
        # Lookup cache patterns (placeholder - would need to parse transformation properties)
        patterns["lookup_cache_patterns"] = {
            "cached": 0,
            "uncached": 0,
            "persistent": 0
        }
        
        # Partitioning strategies (placeholder - would need to parse session properties)
        patterns["partitioning_strategies"] = {
            "hash": 0,
            "round_robin": 0,
            "key_range": 0,
            "pass_through": 0
        }
        
        # Custom function usage
        with self.graph_store.driver.session() as session:
            # This would require parsing expressions - placeholder for now
            patterns["custom_function_usage"] = []
            
            # External dependencies (transformations that reference external systems)
            # Note: database_type property doesn't exist in current schema, removing this query
            patterns["external_dependencies"] = []
        
        # SCD type distribution
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH (t:Transformation)
                WHERE (t.source_component_type = 'mapping' OR t.source_component_type IS NULL)
                AND t.scd_type IS NOT NULL
                RETURN t.scd_type as scd_type, count(t) as count
            """)
            patterns["scd_type_distribution"] = {
                record["scd_type"]: record["count"]
                for record in result
            }
        
        # Common transformation patterns
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH (t:Transformation)-[:HAS_TRANSFORMATION]->(nt:Transformation)
                WHERE (t.source_component_type = 'mapping' OR t.source_component_type IS NULL)
                WITH t.type as trans_type, count(*) as usage_count
                WHERE usage_count > 1
                RETURN trans_type, usage_count
                ORDER BY usage_count DESC
                LIMIT 20
            """)
            patterns["common_transformation_patterns"] = [
                {
                    "transformation_type": record["trans_type"],
                    "usage_count": record["usage_count"]
                }
                for record in result
            ]
        
        logger.info(f"Identified {len(patterns['common_transformation_patterns'])} common patterns")
        return patterns
    
    def identify_blockers(self) -> List[Dict[str, Any]]:
        """Identify migration blockers.
        
        Returns:
            List of blockers with:
            - component_name: str
            - component_type: str (WORKFLOW/MAPPING/TRANSFORMATION)
            - blocker_type: str (UNSUPPORTED_TRANSFORMATION/COMPLEX_EXPRESSION/EXTERNAL_DEPENDENCY/CUSTOM_JAVA/COMPLEX_DEPENDENCY)
            - severity: str (LOW/MEDIUM/HIGH)
            - description: str
            - recommendation: str
        """
        logger.info("Identifying migration blockers...")
        
        blockers = []
        
        # Check for unsupported transformation types
        with self.graph_store.driver.session() as session:
            # List of potentially problematic transformation types
            unsupported_types = ["Java Transformation", "Custom Transformation", "Advanced External Procedure"]
            
            result = session.run("""
                MATCH (t:Transformation)
                WHERE (t.source_component_type = 'mapping' OR t.source_component_type IS NULL)
                AND t.type IN $unsupported_types
                RETURN t.name as transformation_name,
                       t.transformation_name as transformation_name_full,
                       t.type as transformation_type
            """, unsupported_types=unsupported_types)
            
            for record in result:
                transformation_name = record.get("transformation_name_full") or record["transformation_name"]
                blockers.append({
                    "component_name": transformation_name,
                    "component_type": "TRANSFORMATION",
                    "blocker_type": "UNSUPPORTED_TRANSFORMATION",
                    "severity": "HIGH",
                    "description": f"Transformation uses unsupported type: {record['transformation_type']}",
                    "recommendation": f"Review transformation '{record['transformation_name']}' and consider rewriting logic"
                })
        
        # Check for complex expressions (mappings with many transformations)
        mapping_profiles = self.profiler.profile_mappings()
        for mapping in mapping_profiles:
            if mapping["complexity_score"] == "HIGH" and mapping["transformation_count"] > 15:
                blockers.append({
                    "component_name": mapping["name"],
                    "component_type": "MAPPING",
                    "blocker_type": "COMPLEX_EXPRESSION",
                    "severity": "MEDIUM",
                    "description": f"Mapping has {mapping['transformation_count']} transformations and high complexity",
                    "recommendation": "Break down into smaller mappings or review transformation logic"
                })
        
        # Check for external dependencies
        patterns = self.identify_patterns()
        for dep in patterns.get("external_dependencies", []):
            blockers.append({
                "component_name": dep["mapping_name"],
                "component_type": "MAPPING",
                "blocker_type": "EXTERNAL_DEPENDENCY",
                "severity": "MEDIUM",
                "description": f"Mapping depends on external systems: {', '.join(dep['external_systems'])}",
                "recommendation": "Ensure external system connectivity and credentials are available in target platform"
            })
        
        # Check for complex workflow dependencies
        workflow_profiles = self.profiler.profile_workflows()
        for workflow in workflow_profiles:
            if workflow["has_dependencies"] and workflow["complexity_score"] == "HIGH":
                blockers.append({
                    "component_name": workflow["name"],
                    "component_type": "WORKFLOW",
                    "blocker_type": "COMPLEX_DEPENDENCY",
                    "severity": "MEDIUM",
                    "description": f"Workflow has complex dependencies and high complexity",
                    "recommendation": "Review workflow dependencies and consider breaking into smaller workflows"
                })
        
        logger.info(f"Identified {len(blockers)} migration blockers")
        return blockers
    
    def estimate_migration_effort(self) -> Dict[str, Any]:
        """Calculate effort estimates per mapping/workflow.
        
        Returns:
            Dictionary with effort estimates:
            - mapping_effort: List[Dict[str, Any]]
            - workflow_effort: List[Dict[str, Any]]
            - total_effort_days: float
            - effort_by_complexity: Dict[str, float]
        """
        logger.info("Estimating migration effort...")
        
        mapping_profiles = self.profiler.profile_mappings()
        workflow_profiles = self.profiler.profile_workflows()
        
        # Estimate effort per mapping
        mapping_effort = []
        for mapping in mapping_profiles:
            complexity = mapping["complexity_score"]
            if complexity == "LOW":
                effort_days = 1.5  # Simple mappings: 1-2 days
            elif complexity == "MEDIUM":
                effort_days = 4.0  # Medium complexity: 3-5 days
            elif complexity == "HIGH":
                effort_days = 10.0  # High complexity: 1-2 weeks
            else:
                effort_days = 2.0
            
            mapping_effort.append({
                "mapping_name": mapping["name"],
                "complexity": complexity,
                "effort_days": effort_days,
                "transformation_count": mapping["transformation_count"]
            })
        
        # Estimate effort per workflow
        workflow_effort = []
        for workflow in workflow_profiles:
            complexity = workflow["complexity_score"]
            base_effort = 0.5  # Base workflow setup effort
            
            # Add effort based on task count
            task_effort = workflow["task_count"] * 0.2
            
            # Add effort based on complexity
            if complexity == "HIGH":
                complexity_effort = 2.0
            elif complexity == "MEDIUM":
                complexity_effort = 1.0
            else:
                complexity_effort = 0.5
            
            total_effort = base_effort + task_effort + complexity_effort
            
            workflow_effort.append({
                "workflow_name": workflow["name"],
                "complexity": complexity,
                "effort_days": total_effort,
                "task_count": workflow["task_count"]
            })
        
        # Calculate totals
        total_mapping_effort = sum(m["effort_days"] for m in mapping_effort)
        total_workflow_effort = sum(w["effort_days"] for w in workflow_effort)
        total_effort_days = total_mapping_effort + total_workflow_effort
        
        # Effort by complexity
        effort_by_complexity = {
            "LOW": sum(m["effort_days"] for m in mapping_effort if m["complexity"] == "LOW") +
                   sum(w["effort_days"] for w in workflow_effort if w["complexity"] == "LOW"),
            "MEDIUM": sum(m["effort_days"] for m in mapping_effort if m["complexity"] == "MEDIUM") +
                      sum(w["effort_days"] for w in workflow_effort if w["complexity"] == "MEDIUM"),
            "HIGH": sum(m["effort_days"] for m in mapping_effort if m["complexity"] == "HIGH") +
                    sum(w["effort_days"] for w in workflow_effort if w["complexity"] == "HIGH")
        }
        
        logger.info(f"Estimated total migration effort: {total_effort_days:.1f} days")
        
        return {
            "mapping_effort": mapping_effort,
            "workflow_effort": workflow_effort,
            "total_effort_days": total_effort_days,
            "effort_by_complexity": effort_by_complexity
        }
    
    def categorize_by_complexity(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group components by complexity.
        
        Returns:
            Dictionary with components grouped by complexity:
            - LOW: List of component dicts
            - MEDIUM: List of component dicts
            - HIGH: List of component dicts
        """
        logger.info("Categorizing components by complexity...")
        
        mapping_profiles = self.profiler.profile_mappings()
        workflow_profiles = self.profiler.profile_workflows()
        
        categorized = {
            "LOW": [],
            "MEDIUM": [],
            "HIGH": []
        }
        
        # Categorize mappings
        for mapping in mapping_profiles:
            complexity = mapping["complexity_score"]
            categorized[complexity].append({
                "name": mapping["name"],
                "type": "MAPPING",
                "complexity": complexity,
                "transformation_count": mapping["transformation_count"]
            })
        
        # Categorize workflows
        for workflow in workflow_profiles:
            complexity = workflow["complexity_score"]
            categorized[complexity].append({
                "name": workflow["name"],
                "type": "WORKFLOW",
                "complexity": complexity,
                "task_count": workflow["task_count"]
            })
        
        logger.info(f"Categorized components: {len(categorized['LOW'])} LOW, "
                   f"{len(categorized['MEDIUM'])} MEDIUM, {len(categorized['HIGH'])} HIGH")
        
        return categorized
    
    def find_dependencies(self) -> Dict[str, Any]:
        """Analyze cross-mapping dependencies.
        
        Returns:
            Dictionary with dependency analysis:
            - dependency_graph: List[Dict[str, Any]]
            - independent_mappings: List[str]
            - highly_dependent_mappings: List[str]
            - circular_dependencies: List[List[str]]
        """
        logger.info("Analyzing dependencies...")
        
        with self.graph_store.driver.session() as session:
            # Get all transformation dependencies
            result = session.run("""
                MATCH (t1:Transformation)-[:DEPENDS_ON]->(t2:Transformation)
                WHERE (t1.source_component_type = 'mapping' OR t1.source_component_type IS NULL)
                AND (t2.source_component_type = 'mapping' OR t2.source_component_type IS NULL)
                RETURN t1.name as source, t2.name as target
            """)
            
            dependency_graph = [
                {"source": record["source"], "target": record["target"]}
                for record in result
            ]
            
            # Find independent transformations (no dependencies)
            result = session.run("""
                MATCH (t:Transformation)
                WHERE (t.source_component_type = 'mapping' OR t.source_component_type IS NULL)
                AND NOT (t)-[:DEPENDS_ON]->()
                RETURN t.name as name
            """)
            independent_mappings = [record["name"] for record in result]
            
            # Find highly dependent transformations (many dependencies)
            result = session.run("""
                MATCH (t:Transformation)-[:DEPENDS_ON]->(dep:Transformation)
                WHERE (t.source_component_type = 'mapping' OR t.source_component_type IS NULL)
                WITH t, count(dep) as dep_count
                WHERE dep_count > 3
                RETURN t.name as name, dep_count
                ORDER BY dep_count DESC
            """)
            highly_dependent_mappings = [
                {"name": record["name"], "dependency_count": record["dep_count"]}
                for record in result
            ]
            
            # Detect circular dependencies (simplified - would need more sophisticated algorithm)
            circular_dependencies = []
            # Placeholder - full circular dependency detection would require graph traversal
            
            logger.info(f"Found {len(dependency_graph)} dependencies, "
                       f"{len(independent_mappings)} independent mappings")
            
            return {
                "dependency_graph": dependency_graph,
                "independent_mappings": independent_mappings,
                "highly_dependent_mappings": highly_dependent_mappings,
                "circular_dependencies": circular_dependencies
            }

