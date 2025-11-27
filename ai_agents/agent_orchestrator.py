"""Agent Orchestrator
Coordinates multiple AI agents with error handling and parallel execution.
"""
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from ai_agents.rule_explainer_agent import RuleExplainerAgent
from ai_agents.mapping_summary_agent import MappingSummaryAgent
from ai_agents.risk_detection_agent import RiskDetectionAgent
from ai_agents.transformation_suggestion_agent import TransformationSuggestionAgent
from ai_agents.code_fix_agent import CodeFixAgent
from ai_agents.impact_analysis_agent import ImpactAnalysisAgent
from ai_agents.mapping_reconstruction_agent import MappingReconstructionAgent
from ai_agents.workflow_simulation_agent import WorkflowSimulationAgent
from src.llm.llm_manager import LLMManager
from src.utils.logger import get_logger
from src.utils.exceptions import ModernizationError

logger = get_logger(__name__)


class AgentOrchestrator:
    """Orchestrates multiple AI agents with error handling and caching."""
    
    def __init__(self, llm: Optional[LLMManager] = None, enable_parallel: bool = True):
        """Initialize Agent Orchestrator.
        
        Args:
            llm: Optional shared LLM manager instance
            enable_parallel: Whether to run independent agents in parallel
        """
        self.llm = llm or LLMManager()
        self.enable_parallel = enable_parallel
        
        # Initialize core agents
        self.rule_agent = RuleExplainerAgent(self.llm)
        self.summary_agent = MappingSummaryAgent(self.llm)
        self.risk_agent = RiskDetectionAgent(self.llm)
        self.suggestion_agent = TransformationSuggestionAgent(self.llm)
        
        # Initialize advanced agents
        self.code_fix_agent = CodeFixAgent(self.llm)
        self.impact_agent = ImpactAnalysisAgent(self.llm)
        self.reconstruction_agent = MappingReconstructionAgent(self.llm)
        self.simulation_agent = WorkflowSimulationAgent(self.llm)
        
        logger.info("Agent Orchestrator initialized")

    def run_all(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Run all core agents on a mapping.
        
        Args:
            mapping: Canonical mapping model
            
        Returns:
            Dictionary with results from all agents:
            - summary: Mapping summary
            - explanations: Rule explanations
            - risks: Risk analysis
            - suggestions: Optimization suggestions
            - errors: Any errors encountered
        """
        try:
            mapping_name = mapping.get("mapping_name", "unknown")
            logger.info(f"Running all agents for mapping: {mapping_name}")
            
            results = {
                "summary": None,
                "explanations": [],
                "risks": [],
                "suggestions": [],
                "errors": []
            }
            
            if self.enable_parallel:
                # Run independent agents in parallel
                with ThreadPoolExecutor(max_workers=4) as executor:
                    futures = {
                        executor.submit(self._safe_summarize, mapping): "summary",
                        executor.submit(self._safe_explain, mapping): "explanations",
                        executor.submit(self._safe_detect_risks, mapping): "risks",
                        executor.submit(self._safe_suggest, mapping): "suggestions"
                    }
                    
                    for future in as_completed(futures):
                        key = futures[future]
                        try:
                            result = future.result()
                            results[key] = result
                        except Exception as e:
                            logger.error(f"Agent {key} failed: {str(e)}")
                            results["errors"].append(f"{key}: {str(e)}")
            else:
                # Run sequentially
                results["summary"] = self._safe_summarize(mapping)
                results["explanations"] = self._safe_explain(mapping)
                results["risks"] = self._safe_detect_risks(mapping)
                results["suggestions"] = self._safe_suggest(mapping)
            
            logger.info(f"Completed all agents for {mapping_name}")
            return results
            
        except Exception as e:
            logger.error(f"Agent orchestration failed: {str(e)}")
            raise ModernizationError(f"Agent orchestration failed: {str(e)}") from e

    def _safe_summarize(self, mapping: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Safely run summary agent with error handling."""
        try:
            return self.summary_agent.summarize(mapping)
        except Exception as e:
            logger.warning(f"Summary agent failed: {str(e)}")
            return None

    def _safe_explain(self, mapping: Dict[str, Any]) -> list:
        """Safely run rule explainer agent with error handling."""
        try:
            return self.rule_agent.explain(mapping)
        except Exception as e:
            logger.warning(f"Rule explainer agent failed: {str(e)}")
            return []

    def _safe_detect_risks(self, mapping: Dict[str, Any]) -> list:
        """Safely run risk detection agent with error handling."""
        try:
            return self.risk_agent.detect_risks(mapping)
        except Exception as e:
            logger.warning(f"Risk detection agent failed: {str(e)}")
            return []

    def _safe_suggest(self, mapping: Dict[str, Any]) -> list:
        """Safely run suggestion agent with error handling."""
        try:
            return self.suggestion_agent.suggest(mapping)
        except Exception as e:
            logger.warning(f"Suggestion agent failed: {str(e)}")
            return []

    def fix_code(self, pyspark_code: str, error_message: Optional[str] = None) -> Dict[str, Any]:
        """Fix PySpark code using Code Fix Agent.
        
        Args:
            pyspark_code: Code to fix
            error_message: Optional error message
            
        Returns:
            Fixed code and explanation
        """
        try:
            return self.code_fix_agent.fix(pyspark_code, error_message)
        except Exception as e:
            logger.error(f"Code fix failed: {str(e)}")
            raise ModernizationError(f"Code fix failed: {str(e)}") from e

    def analyze_impact(self, mapping: Dict[str, Any], change_target: str, change_description: str) -> Dict[str, Any]:
        """Analyze impact of changes using Impact Analysis Agent.
        
        Args:
            mapping: Canonical mapping model
            change_target: What is being changed
            change_description: Description of change
            
        Returns:
            Impact analysis results
        """
        try:
            return self.impact_agent.analyze(mapping, change_target, change_description)
        except Exception as e:
            logger.error(f"Impact analysis failed: {str(e)}")
            raise ModernizationError(f"Impact analysis failed: {str(e)}") from e

    def reconstruct_mapping(self, clues: Dict[str, Any]) -> Dict[str, Any]:
        """Reconstruct mapping using Reconstruction Agent.
        
        Args:
            clues: Partial information about the mapping
            
        Returns:
            Reconstructed mapping model
        """
        try:
            return self.reconstruction_agent.reconstruct(clues)
        except Exception as e:
            logger.error(f"Mapping reconstruction failed: {str(e)}")
            raise ModernizationError(f"Mapping reconstruction failed: {str(e)}") from e

    def simulate_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate workflow using Workflow Simulation Agent.
        
        Args:
            workflow: DAG model
            
        Returns:
            Simulation results
        """
        try:
            return self.simulation_agent.simulate(workflow)
        except Exception as e:
            logger.error(f"Workflow simulation failed: {str(e)}")
            raise ModernizationError(f"Workflow simulation failed: {str(e)}") from e
