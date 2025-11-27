"""Rule Explainer Agent
LLM-powered agent to explain complex mapping rules in business terms.
"""
import json
from typing import Dict, Any, List, Optional
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.llm.llm_manager import LLMManager
from src.llm.prompt_templates import get_rule_explanation_prompt
from src.utils.logger import get_logger
from src.utils.exceptions import ModernizationError

logger = get_logger(__name__)


class RuleExplainerAgent:
    """Explains Informatica expressions in human-readable business terms."""
    
    def __init__(self, llm: Optional[LLMManager] = None):
        """Initialize Rule Explainer Agent.
        
        Args:
            llm: Optional LLM manager instance (creates new one if not provided)
        """
        self.llm = llm or LLMManager()
        logger.info("Rule Explainer Agent initialized")

    def explain(self, mapping: Dict[str, Any], field_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Explain expressions in a mapping.
        
        Args:
            mapping: Canonical mapping model
            field_name: Optional specific field to explain (if None, explains all)
            
        Returns:
            List of explanations, each with:
            - field: Field name
            - expression: Original expression
            - explanation: Human-readable explanation
        """
        try:
            logger.info(f"Explaining expressions for mapping: {mapping.get('mapping_name', 'unknown')}")
            
            explanations = []
            transformations = mapping.get("transformations", [])
            
            # Find expression transformations
            for transformation in transformations:
                if transformation.get("type") != "EXPRESSION":
                    continue
                
                trans_name = transformation.get("name", "unknown")
                output_ports = transformation.get("output_ports", [])
                
                # Extract expressions from output ports
                for port in output_ports:
                    field = port.get("name", "")
                    expression = port.get("expression", "")
                    
                    # Skip if field_name specified and doesn't match
                    if field_name and field != field_name:
                        continue
                    
                    if not expression:
                        continue
                    
                    # Build context
                    context = {
                        "transformation": trans_name,
                        "mapping": mapping.get("mapping_name", "unknown"),
                        "field_type": port.get("data_type", "unknown")
                    }
                    
                    # Get explanation from LLM
                    try:
                        prompt = get_rule_explanation_prompt(field, expression, context)
                        explanation_text = self.llm.ask(prompt)
                        
                        explanations.append({
                            "field": field,
                            "transformation": trans_name,
                            "expression": expression,
                            "explanation": explanation_text.strip(),
                            "field_type": port.get("data_type", "unknown")
                        })
                        
                        logger.debug(f"Explained field: {field}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to explain field {field}: {str(e)}")
                        # Provide fallback explanation
                        explanations.append({
                            "field": field,
                            "transformation": trans_name,
                            "expression": expression,
                            "explanation": f"Expression calculates {field} using: {expression}",
                            "field_type": port.get("data_type", "unknown"),
                            "error": str(e)
                        })
            
            logger.info(f"Generated {len(explanations)} explanations")
            return explanations
            
        except Exception as e:
            logger.error(f"Rule explanation failed: {str(e)}")
            raise ModernizationError(f"Rule explanation failed: {str(e)}") from e

    def explain_expression(self, expression: str, field_name: str = "field", context: Optional[Dict[str, Any]] = None) -> str:
        """Explain a single expression.
        
        Args:
            expression: Informatica expression to explain
            field_name: Name of the field
            context: Optional context dictionary
            
        Returns:
            Human-readable explanation
        """
        try:
            prompt = get_rule_explanation_prompt(field_name, expression, context)
            explanation = self.llm.ask(prompt)
            return explanation.strip()
        except Exception as e:
            logger.error(f"Expression explanation failed: {str(e)}")
            raise ModernizationError(f"Expression explanation failed: {str(e)}") from e
