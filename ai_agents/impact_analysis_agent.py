"""Impact analysis agent - Analyzes downstream dependencies of changes"""
import json
from typing import Dict, Any, List, Optional
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from llm.llm_manager import LLMManager
from llm.prompt_templates import get_impact_analysis_prompt
from utils.logger import get_logger
from utils.exceptions import ModernizationError

logger = get_logger(__name__)


class ImpactAnalysisAgent:
    """Analyzes impact of changes to mappings, fields, or transformations."""
    
    def __init__(self, llm: Optional[LLMManager] = None):
        """Initialize Impact Analysis Agent.
        
        Args:
            llm: Optional LLM manager instance (creates new one if not provided)
        """
        self.llm = llm or LLMManager()
        logger.info("Impact Analysis Agent initialized")

    def analyze(self, mapping_model: Dict[str, Any], change_target: str, change_description: str) -> Dict[str, Any]:
        """Analyze impact of a proposed change.
        
        Args:
            mapping_model: Canonical mapping model
            change_target: What is being changed (e.g., "EXP_CALC/AGE_BUCKET", "SQ_CUSTOMERS")
            change_description: Description of the proposed change
            
        Returns:
            Dictionary with impact analysis:
            - change_target: What is being changed
            - direct_dependencies: Directly affected elements
            - indirect_dependencies: Transitively affected elements
            - affected_targets: Which target tables are affected
            - data_quality_concerns: Data quality impacts
            - testing_priority: What needs to be tested
            - overall_risk: Overall risk level
        """
        try:
            mapping_name = mapping_model.get("mapping_name", "unknown")
            logger.info(f"Analyzing impact for change to {change_target} in {mapping_name}")
            
            # First, do pattern-based impact analysis (fast, deterministic)
            pattern_impact = self._analyze_pattern_impact(mapping_model, change_target)
            
            # Then, get LLM-based analysis (comprehensive)
            llm_impact = {}
            try:
                prompt = get_impact_analysis_prompt(mapping_model, change_target, change_description)
                llm_response = self.llm.ask(prompt)
                
                # Parse JSON response from LLM
                try:
                    llm_impact = json.loads(llm_response)
                    if not isinstance(llm_impact, dict):
                        llm_impact = {}
                except json.JSONDecodeError:
                    logger.warning("Failed to parse LLM impact analysis as JSON, using pattern-based only")
                    llm_impact = {}
                    
            except Exception as e:
                logger.warning(f"LLM impact analysis failed: {str(e)}, using pattern-based only")
            
            # Merge pattern-based and LLM-based results
            result = {
                "change_target": change_target,
                "change_description": change_description,
                "direct_dependencies": llm_impact.get("direct_dependencies", pattern_impact.get("direct_dependencies", [])),
                "indirect_dependencies": llm_impact.get("indirect_dependencies", pattern_impact.get("indirect_dependencies", [])),
                "affected_targets": llm_impact.get("affected_targets", pattern_impact.get("affected_targets", [])),
                "data_quality_concerns": llm_impact.get("data_quality_concerns", pattern_impact.get("data_quality_concerns", [])),
                "testing_priority": llm_impact.get("testing_priority", pattern_impact.get("testing_priority", [])),
                "overall_risk": llm_impact.get("overall_risk", pattern_impact.get("overall_risk", "Medium"))
            }
            
            logger.info(f"Impact analysis completed for {change_target}")
            return result
            
        except Exception as e:
            logger.error(f"Impact analysis failed: {str(e)}")
            raise ModernizationError(f"Impact analysis failed: {str(e)}") from e

    def _analyze_pattern_impact(self, mapping: Dict[str, Any], change_target: str) -> Dict[str, Any]:
        """Analyze impact using pattern matching (deterministic).
        
        Args:
            mapping: Canonical mapping model
            change_target: What is being changed
            
        Returns:
            Pattern-based impact analysis
        """
        # Parse change target (format: "transformation/field" or just "transformation")
        parts = change_target.split("/")
        trans_name = parts[0]
        field_name = parts[1] if len(parts) > 1 else None
        
        direct_deps = []
        indirect_deps = []
        affected_targets = []
        
        # Find the transformation being changed
        transformations = mapping.get("transformations", [])
        connectors = mapping.get("connectors", [])
        
        changed_trans = None
        for trans in transformations:
            if trans.get("name") == trans_name:
                changed_trans = trans
                break
        
        if not changed_trans:
            return {
                "direct_dependencies": [],
                "indirect_dependencies": [],
                "affected_targets": [],
                "data_quality_concerns": ["Change target not found in mapping"],
                "testing_priority": ["Verify change target exists"],
                "overall_risk": "Low"
            }
        
        # Find direct dependencies (transformations that use this one)
        for connector in connectors:
            if connector.get("from_instance") == trans_name:
                to_instance = connector.get("to_instance")
                direct_deps.append({
                    "element": to_instance,
                    "impact": f"Directly receives data from changed transformation {trans_name}",
                    "severity": "High"
                })
                
                # Check if this leads to targets
                for target in mapping.get("targets", []):
                    target_connectors = [c for c in connectors if c.get("to_instance") == target.get("name")]
                    if any(c.get("from_instance") == to_instance for c in target_connectors):
                        affected_targets.append(target.get("name"))
        
        # Find indirect dependencies (transitive)
        visited = {trans_name}
        for dep in direct_deps:
            dep_name = dep["element"]
            if dep_name not in visited:
                visited.add(dep_name)
                # Find what uses this dependency
                for connector in connectors:
                    if connector.get("from_instance") == dep_name:
                        indirect_deps.append({
                            "element": connector.get("to_instance"),
                            "impact": f"Indirectly affected through {dep_name}",
                            "severity": "Medium"
                        })
        
        # Determine overall risk
        overall_risk = "Low"
        if len(affected_targets) > 0:
            overall_risk = "High"
        elif len(direct_deps) > 0:
            overall_risk = "Medium"
        
        return {
            "direct_dependencies": direct_deps,
            "indirect_dependencies": indirect_deps,
            "affected_targets": list(set(affected_targets)),
            "data_quality_concerns": [
                "Verify data types remain compatible",
                "Check for null handling impacts",
                "Validate calculation results"
            ],
            "testing_priority": [
                f"Test {trans_name} transformation",
                "Test downstream transformations",
                "Validate target table data"
            ],
            "overall_risk": overall_risk
        }
