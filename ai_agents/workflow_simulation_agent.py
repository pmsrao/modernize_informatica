"""Simulates execution workflow"""
import json
from typing import Dict, Any, Optional
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.llm.llm_manager import LLMManager
from src.llm.prompt_templates import get_workflow_simulation_prompt
from src.utils.logger import get_logger
from src.utils.exceptions import ModernizationError

logger = get_logger(__name__)


class WorkflowSimulationAgent:
    """Simulates ETL workflow execution to identify bottlenecks and issues."""
    
    def __init__(self, llm: Optional[LLMManager] = None):
        """Initialize Workflow Simulation Agent.
        
        Args:
            llm: Optional LLM manager instance (creates new one if not provided)
        """
        self.llm = llm or LLMManager()
        logger.info("Workflow Simulation Agent initialized")

    def simulate(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate workflow execution.
        
        Args:
            workflow: DAG model with nodes, edges, execution_levels
            
        Returns:
            Simulation results with:
            - execution_sequence: Step-by-step execution
            - critical_path: Longest execution path
            - bottlenecks: Performance bottlenecks
            - single_points_of_failure: Critical tasks
            - resource_requirements: Resource needs
            - optimization_suggestions: Improvement suggestions
        """
        try:
            workflow_name = workflow.get("workflow_name", "unknown")
            logger.info(f"Simulating workflow: {workflow_name}")
            
            # First, do pattern-based simulation (fast, deterministic)
            pattern_simulation = self._pattern_based_simulation(workflow)
            
            # Then, get LLM-based simulation (comprehensive)
            llm_simulation = {}
            try:
                prompt = get_workflow_simulation_prompt(workflow)
                llm_response = self.llm.ask(prompt)
                
                # Parse JSON response from LLM
                try:
                    llm_simulation = json.loads(llm_response)
                    if not isinstance(llm_simulation, dict):
                        llm_simulation = {}
                except json.JSONDecodeError:
                    logger.warning("Failed to parse LLM simulation as JSON, using pattern-based only")
                    llm_simulation = {}
                    
            except Exception as e:
                logger.warning(f"LLM simulation failed: {str(e)}, using pattern-based only")
            
            # Merge results
            result = {
                "execution_sequence": llm_simulation.get("execution_sequence", pattern_simulation.get("execution_sequence", [])),
                "critical_path": llm_simulation.get("critical_path", pattern_simulation.get("critical_path", [])),
                "bottlenecks": llm_simulation.get("bottlenecks", pattern_simulation.get("bottlenecks", [])),
                "single_points_of_failure": llm_simulation.get("single_points_of_failure", pattern_simulation.get("single_points_of_failure", [])),
                "resource_requirements": llm_simulation.get("resource_requirements", pattern_simulation.get("resource_requirements", {})),
                "optimization_suggestions": llm_simulation.get("optimization_suggestions", pattern_simulation.get("optimization_suggestions", []))
            }
            
            logger.info(f"Workflow simulation completed for {workflow_name}")
            return result
            
        except Exception as e:
            logger.error(f"Workflow simulation failed: {str(e)}")
            raise ModernizationError(f"Workflow simulation failed: {str(e)}") from e

    def _pattern_based_simulation(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate workflow using pattern matching (deterministic).
        
        Args:
            workflow: DAG model
            
        Returns:
            Pattern-based simulation results
        """
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])
        execution_levels = workflow.get("execution_levels", [])
        
        # Build execution sequence from levels
        execution_sequence = []
        for level_idx, level in enumerate(execution_levels, 1):
            execution_sequence.append({
                "level": level_idx,
                "tasks": level,
                "execution_type": "parallel" if len(level) > 1 else "sequential",
                "estimated_duration": "unknown",
                "dependencies": []
            })
        
        # Identify critical path (longest path)
        critical_path = []
        if execution_levels:
            # Simple heuristic: tasks in sequential levels
            for level in execution_levels:
                if len(level) == 1:
                    critical_path.append(level[0])
        
        # Identify bottlenecks (tasks with many dependencies)
        bottlenecks = []
        task_dependencies = {}
        for edge in edges:
            to_task = edge.get("to")
            if to_task not in task_dependencies:
                task_dependencies[to_task] = 0
            task_dependencies[to_task] += 1
        
        for task, dep_count in task_dependencies.items():
            if dep_count > 2:
                bottlenecks.append({
                    "task": task,
                    "reason": f"Has {dep_count} incoming dependencies",
                    "impact": "May cause delays if upstream tasks are slow"
                })
        
        # Identify single points of failure (tasks with no parallel alternatives)
        single_points = []
        for level in execution_levels:
            if len(level) == 1:
                single_points.append(level[0])
        
        # Resource requirements (simple heuristic)
        resource_requirements = {}
        for level_idx, level in enumerate(execution_levels, 1):
            resource_requirements[f"level_{level_idx}"] = f"{len(level)} task(s)"
        
        return {
            "execution_sequence": execution_sequence,
            "critical_path": critical_path,
            "bottlenecks": bottlenecks,
            "single_points_of_failure": single_points,
            "resource_requirements": resource_requirements,
            "optimization_suggestions": [
                {
                    "suggestion": "Consider parallelizing sequential tasks where possible",
                    "benefit": "Reduced overall execution time",
                    "priority": "Medium"
                } if any(len(level) == 1 for level in execution_levels) else None
            ]
        }
