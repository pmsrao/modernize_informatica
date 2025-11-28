"""Agent Orchestrator
Coordinates multiple AI agents with error handling and parallel execution.
"""
from typing import Dict, Any, Optional, List
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
from ai_agents.model_enhancement_agent import ModelEnhancementAgent
from ai_agents.model_validation_agent import ModelValidationAgent
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
        
        # Initialize enhancement agents (Phase 1)
        self.enhancement_agent = ModelEnhancementAgent(self.llm, use_llm=False)
        self.validation_agent = ModelValidationAgent()
        
        # Initialize code review agent (Priority 2)
        from ai_agents.code_review_agent import CodeReviewAgent
        self.review_agent = CodeReviewAgent(self.llm, use_llm=True)
        
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
    
    def enhance_model(self, canonical_model: Dict[str, Any], 
                     use_llm: bool = False) -> Dict[str, Any]:
        """Enhance canonical model using Model Enhancement Agent.
        
        Args:
            canonical_model: Canonical mapping model to enhance
            use_llm: Whether to use LLM-based enhancements (default: False)
            
        Returns:
            Enhanced canonical model with provenance tracking
        """
        try:
            # Update enhancement agent LLM setting if needed
            if use_llm != self.enhancement_agent.use_llm:
                self.enhancement_agent.use_llm = use_llm
            
            return self.enhancement_agent.enhance(canonical_model)
        except Exception as e:
            logger.error(f"Model enhancement failed: {str(e)}")
            raise ModernizationError(f"Model enhancement failed: {str(e)}") from e
    
    def validate_model(self, enhanced_model: Dict[str, Any],
                      original_model: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate enhanced canonical model using Model Validation Agent.
        
        Args:
            enhanced_model: Enhanced canonical model to validate
            original_model: Optional original model for comparison
            
        Returns:
            Validation result dictionary
        """
        try:
            return self.validation_agent.validate(enhanced_model, original_model)
        except Exception as e:
            logger.error(f"Model validation failed: {str(e)}")
            raise ModernizationError(f"Model validation failed: {str(e)}") from e
    
    def process_with_enhancement(self, canonical_model: Dict[str, Any],
                                 enable_enhancement: bool = True,
                                 use_llm: bool = False) -> Dict[str, Any]:
        """Process mapping with AI enhancement (Phase 1 implementation).
        
        Args:
            canonical_model: Canonical mapping model
            enable_enhancement: Whether to enhance the model
            use_llm: Whether to use LLM-based enhancements
            
        Returns:
            Dictionary with:
            - canonical_model: Enhanced or original model
            - enhancement_applied: Whether enhancement was applied
            - validation: Validation results if enhanced
        """
        try:
            import json
            original_model = json.loads(json.dumps(canonical_model))  # Deep copy
            
            if enable_enhancement:
                # Enhance model
                enhanced = self.enhance_model(canonical_model, use_llm=use_llm)
                
                # Validate enhanced model
                validation = self.validate_model(enhanced, original_model)
                
                if validation["is_valid"]:
                    return {
                        "canonical_model": enhanced,
                        "enhancement_applied": True,
                        "validation": validation
                    }
                else:
                    logger.warning("Enhancement validation failed, using original model")
                    return {
                        "canonical_model": original_model,
                        "enhancement_applied": False,
                        "validation": validation
                    }
            else:
                return {
                    "canonical_model": original_model,
                    "enhancement_applied": False,
                    "validation": None
                }
                
        except Exception as e:
            logger.error(f"Process with enhancement failed: {str(e)}")
            raise ModernizationError(f"Process with enhancement failed: {str(e)}") from e
    
    def review_code(self, code: str, canonical_model: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Review generated code for issues and improvements.
        
        Args:
            code: Generated code to review
            canonical_model: Optional canonical model for context
            
        Returns:
            Review results
        """
        try:
            logger.info("Reviewing generated code")
            review = self.review_agent.review(code, canonical_model)
            logger.info(f"Code review completed: {review.get('severity')} severity, score: {review.get('score')}/100")
            return review
        except Exception as e:
            logger.error(f"Code review failed: {str(e)}")
            raise ModernizationError(f"Code review failed: {str(e)}") from e
    
    def fix_code(self, code: str, issues: List[Dict[str, Any]], canonical_model: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fix code based on review issues.
        
        Args:
            code: Code to fix
            issues: List of issues from review
            canonical_model: Optional canonical model for context
            
        Returns:
            Fixed code result
        """
        try:
            logger.info(f"Fixing code based on {len(issues)} issues")
            
            # Extract error messages from issues
            error_messages = [f"{i.get('category')}: {i.get('issue')}" for i in issues if i.get('severity') in ['HIGH', 'MEDIUM']]
            error_message = "; ".join(error_messages) if error_messages else None
            
            # Use code fix agent
            fix_result = self.code_fix_agent.fix(code, error_message=error_message)
            
            logger.info("Code fix completed")
            return fix_result
            
        except Exception as e:
            logger.error(f"Code fix failed: {str(e)}")
            raise ModernizationError(f"Code fix failed: {str(e)}") from e
