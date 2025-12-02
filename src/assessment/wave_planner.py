"""Wave Planner — Generates migration wave recommendations."""
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
from src.assessment.analyzer import Analyzer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WavePlanner:
    """Plans migration waves based on dependencies and complexity."""
    
    def __init__(self, graph_store: GraphStore, 
                 profiler: Optional[Profiler] = None,
                 analyzer: Optional[Analyzer] = None):
        """Initialize wave planner.
        
        Args:
            graph_store: GraphStore instance
            profiler: Optional Profiler instance
            analyzer: Optional Analyzer instance
        """
        self.graph_store = graph_store
        self.graph_queries = GraphQueries(graph_store)
        self.profiler = profiler or Profiler(graph_store)
        self.analyzer = analyzer or Analyzer(graph_store, self.profiler)
        logger.info("WavePlanner initialized")
    
    def plan_migration_waves(self, max_wave_size: int = 10, 
                            complexity_mix: bool = True) -> List[Dict[str, Any]]:
        """Group components into migration waves based on dependencies and complexity.
        
        Args:
            max_wave_size: Maximum number of mappings per wave
            complexity_mix: Whether to mix complexity levels in each wave
        
        Returns:
            List of migration waves, each containing:
            - wave_number: int
            - components: List[Dict[str, Any]]
            - total_effort_days: float
            - complexity_distribution: Dict[str, int]
            - dependencies_satisfied: bool
        """
        logger.info(f"Planning migration waves (max size: {max_wave_size})...")
        
        # Get dependencies
        dependencies = self.analyzer.find_dependencies()
        dependency_map = {
            dep["source"]: dep["target"]
            for dep in dependencies["dependency_graph"]
        }
        
        # Get component priorities
        prioritized = self.prioritize_components()
        
        # Group into waves
        waves = []
        current_wave = {
            "wave_number": 1,
            "components": [],
            "total_effort_days": 0.0,
            "complexity_distribution": {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
            "migrated_components": set()
        }
        
        for component in prioritized:
            component_name = component["name"]
            component_type = component["type"]
            
            # Check if dependencies are satisfied
            if component_type == "MAPPING":
                # Check if this mapping depends on any unmigrated mappings
                depends_on = [
                    dep["target"]
                    for dep in dependencies["dependency_graph"]
                    if dep["source"] == component_name
                ]
                
                dependencies_satisfied = all(
                    dep in current_wave["migrated_components"]
                    for dep in depends_on
                )
                
                if not dependencies_satisfied and len(current_wave["components"]) > 0:
                    # Start new wave if dependencies not satisfied
                    waves.append(current_wave)
                    current_wave = {
                        "wave_number": len(waves) + 1,
                        "components": [],
                        "total_effort_days": 0.0,
                        "complexity_distribution": {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
                        "migrated_components": set(current_wave["migrated_components"])
                    }
            
            # Check wave size limit
            if len(current_wave["components"]) >= max_wave_size:
                waves.append(current_wave)
                current_wave = {
                    "wave_number": len(waves) + 1,
                    "components": [],
                    "total_effort_days": 0.0,
                    "complexity_distribution": {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
                    "migrated_components": set(current_wave["migrated_components"])
                }
            
            # Add component to current wave
            current_wave["components"].append(component)
            current_wave["total_effort_days"] += component.get("effort_days", 0)
            complexity = component.get("complexity", "MEDIUM")
            current_wave["complexity_distribution"][complexity] = \
                current_wave["complexity_distribution"].get(complexity, 0) + 1
            current_wave["migrated_components"].add(component_name)
        
        # Add final wave
        if current_wave["components"]:
            waves.append(current_wave)
        
        # Validate waves
        for wave in waves:
            wave["dependencies_satisfied"] = self.validate_wave_dependencies(
                wave, dependencies["dependency_graph"]
            )
        
        logger.info(f"Planned {len(waves)} migration waves")
        return waves
    
    def prioritize_components(self) -> List[Dict[str, Any]]:
        """Rank components by business value and complexity.
        
        Returns:
            List of components sorted by priority (highest first)
        """
        logger.info("Prioritizing components...")
        
        # Get effort estimates
        effort_estimates = self.analyzer.estimate_migration_effort()
        
        # Create priority list
        prioritized = []
        
        # Add mappings (prioritize low complexity, independent ones first)
        dependencies = self.analyzer.find_dependencies()
        independent_mappings = set(dependencies["independent_mappings"])
        
        for mapping_effort in effort_estimates["mapping_effort"]:
            mapping_name = mapping_effort["mapping_name"]
            complexity = mapping_effort["complexity"]
            
            # Priority score: lower complexity and independent = higher priority
            priority_score = 100
            
            # Independent mappings get higher priority
            if mapping_name in independent_mappings:
                priority_score += 50
            
            # Lower complexity gets higher priority
            if complexity == "LOW":
                priority_score += 30
            elif complexity == "MEDIUM":
                priority_score += 15
            
            # Lower effort gets slightly higher priority
            priority_score -= mapping_effort["effort_days"] * 2
            
            prioritized.append({
                "name": mapping_name,
                "type": "MAPPING",
                "complexity": complexity,
                "effort_days": mapping_effort["effort_days"],
                "priority_score": priority_score,
                "transformation_count": mapping_effort["transformation_count"]
            })
        
        # Add workflows (prioritize simpler ones)
        for workflow_effort in effort_estimates["workflow_effort"]:
            workflow_name = workflow_effort["workflow_name"]
            complexity = workflow_effort["complexity"]
            
            priority_score = 50  # Workflows generally lower priority than mappings
            
            if complexity == "LOW":
                priority_score += 20
            elif complexity == "MEDIUM":
                priority_score += 10
            
            priority_score -= workflow_effort["effort_days"] * 2
            
            prioritized.append({
                "name": workflow_name,
                "type": "WORKFLOW",
                "complexity": complexity,
                "effort_days": workflow_effort["effort_days"],
                "priority_score": priority_score,
                "task_count": workflow_effort["task_count"]
            })
        
        # Sort by priority score (descending)
        prioritized.sort(key=lambda x: x["priority_score"], reverse=True)
        
        logger.info(f"Prioritized {len(prioritized)} components")
        return prioritized
    
    def validate_wave_dependencies(self, wave: Dict[str, Any], 
                                  dependency_graph: List[Dict[str, str]]) -> bool:
        """Ensure wave respects dependencies.
        
        Args:
            wave: Wave dictionary
            dependency_graph: List of dependency relationships
        
        Returns:
            True if all dependencies are satisfied, False otherwise
        """
        component_names = {c["name"] for c in wave["components"]}
        migrated = wave.get("migrated_components", set())
        
        # Check all dependencies for components in this wave
        for component in wave["components"]:
            if component["type"] == "MAPPING":
                component_name = component["name"]
                
                # Find dependencies
                dependencies = [
                    dep["target"]
                    for dep in dependency_graph
                    if dep["source"] == component_name
                ]
                
                # Check if dependencies are satisfied (either in this wave or previously migrated)
                for dep in dependencies:
                    if dep not in component_names and dep not in migrated:
                        return False
        
        return True

