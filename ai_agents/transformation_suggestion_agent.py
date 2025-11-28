"""Transformation Suggestion Agent
Suggests optimizations or modernized transformations.
"""
import json
from typing import Dict, Any, List, Optional
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.llm.llm_manager import LLMManager
from src.llm.prompt_templates import get_transformation_suggestion_prompt
from src.utils.logger import get_logger
from src.utils.exceptions import ModernizationError

logger = get_logger(__name__)


class TransformationSuggestionAgent:
    """Suggests optimizations and improvements for Informatica transformations."""
    
    def __init__(self, llm: Optional[LLMManager] = None, target_platform: str = "PySpark"):
        """Initialize Transformation Suggestion Agent.
        
        Args:
            llm: Optional LLM manager instance (creates new one if not provided)
            target_platform: Target platform for suggestions (PySpark, SQL, etc.)
        """
        self.llm = llm or LLMManager()
        self.target_platform = target_platform
        logger.info(f"Transformation Suggestion Agent initialized for {target_platform}")

    def suggest(self, mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze transformations and suggest optimizations.
        
        Args:
            mapping: Canonical mapping model
            
        Returns:
            List of suggestion objects, each with:
            - transformation: Transformation name
            - field: Field name (optional)
            - current_pattern: Current implementation
            - suggestion: Suggested improvement
            - benefits: List of benefits
            - improved_code: Example improved code
            - priority: High, Medium, or Low
        """
        try:
            if not mapping or not isinstance(mapping, dict):
                raise ModernizationError("Invalid mapping: mapping must be a non-empty dictionary")
            
            mapping_name = mapping.get("mapping_name", "unknown")
            logger.info(f"Generating suggestions for mapping: {mapping_name}")
            
            # First, do pattern-based suggestions (fast, deterministic)
            pattern_suggestions = self._generate_pattern_suggestions(mapping)
            
            # Then, get LLM-based suggestions (comprehensive)
            llm_suggestions = []
            try:
                prompt = get_transformation_suggestion_prompt(mapping, self.target_platform)
                llm_response = self.llm.ask(prompt)
                
                # Parse JSON response from LLM
                try:
                    llm_suggestions = json.loads(llm_response)
                    if not isinstance(llm_suggestions, list):
                        llm_suggestions = []
                except json.JSONDecodeError:
                    logger.warning("Failed to parse LLM suggestions as JSON, using pattern-based only")
                    llm_suggestions = []
                    
            except Exception as e:
                logger.warning(f"LLM suggestion generation failed: {str(e)}, using pattern-based only")
            
            # Combine and deduplicate suggestions
            all_suggestions = pattern_suggestions + llm_suggestions
            unique_suggestions = self._deduplicate_suggestions(all_suggestions)
            
            # Sort by priority
            priority_order = {"High": 0, "Medium": 1, "Low": 2}
            unique_suggestions.sort(key=lambda x: priority_order.get(x.get("priority", "Low"), 2))
            
            logger.info(f"Generated {len(unique_suggestions)} suggestions for {mapping_name}")
            return unique_suggestions
            
        except Exception as e:
            logger.error(f"Suggestion generation failed: {str(e)}")
            raise ModernizationError(f"Suggestion generation failed: {str(e)}") from e

    def _generate_pattern_suggestions(self, mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate suggestions using pattern matching (deterministic).
        
        Args:
            mapping: Canonical mapping model
            
        Returns:
            List of suggestions
        """
        suggestions = []
        transformations = mapping.get("transformations", [])
        
        for transformation in transformations:
            trans_name = transformation.get("name", "unknown")
            trans_type = transformation.get("type", "")
            
            # Check expression transformations
            if trans_type == "EXPRESSION":
                output_ports = transformation.get("output_ports", [])
                for port in output_ports:
                    field = port.get("name", "")
                    expression = port.get("expression", "")
                    expr_upper = expression.upper()
                    
                    # Suggest concat_ws for string concatenation
                    if "||" in expression and self.target_platform == "PySpark":
                        suggestions.append({
                            "transformation": trans_name,
                            "field": field,
                            "current_pattern": f"String concatenation using || operator: {expression}",
                            "suggestion": "Use PySpark concat_ws function for better null handling",
                            "benefits": [
                                "Handles nulls gracefully (skips null values)",
                                "More readable and idiomatic PySpark",
                                "Better performance"
                            ],
                            "improved_code": f"F.concat_ws(' ', F.col('FIRST_NAME'), F.col('LAST_NAME'))",
                            "priority": "Medium"
                        })
                    
                    # Suggest when/otherwise for nested IIF
                    if expr_upper.count("IIF") > 2 and self.target_platform == "PySpark":
                        suggestions.append({
                            "transformation": trans_name,
                            "field": field,
                            "current_pattern": f"Deeply nested IIF statements: {expression[:50]}...",
                            "suggestion": "Use PySpark when/otherwise chain for better readability",
                            "benefits": [
                                "More readable than nested IIF",
                                "Easier to maintain and debug",
                                "Better performance"
                            ],
                            "improved_code": "F.when(condition1, value1).when(condition2, value2).otherwise(default_value)",
                            "priority": "High"
                        })
                    
                    # Suggest coalesce for NVL
                    if "NVL" in expr_upper and self.target_platform == "PySpark":
                        suggestions.append({
                            "transformation": trans_name,
                            "field": field,
                            "current_pattern": f"Using NVL function: {expression}",
                            "suggestion": "Use PySpark coalesce function (equivalent to NVL)",
                            "benefits": [
                                "Standard PySpark function",
                                "More readable",
                                "Supports multiple arguments"
                            ],
                            "improved_code": "F.coalesce(F.col('field'), F.lit('default_value'))",
                            "priority": "Low"
                        })
            
            # Suggest splitting complex transformations
            if trans_type == "EXPRESSION":
                output_ports = transformation.get("output_ports", [])
                if len(output_ports) > 10:
                    suggestions.append({
                        "transformation": trans_name,
                        "field": None,
                        "current_pattern": f"Single transformation with {len(output_ports)} output fields",
                        "suggestion": "Consider splitting into multiple transformations for better maintainability",
                        "benefits": [
                            "Easier to understand and maintain",
                            "Better testability",
                            "More modular design"
                        ],
                        "improved_code": "Split into EXP_CALCULATIONS, EXP_ENRICHMENTS, etc.",
                        "priority": "Medium"
                    })
        
        return suggestions

    def _deduplicate_suggestions(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate suggestions.
        
        Args:
            suggestions: List of suggestion objects
            
        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []
        
        for suggestion in suggestions:
            # Create a key from transformation, field, and suggestion
            key = (
                suggestion.get("transformation", ""),
                suggestion.get("field", ""),
                suggestion.get("suggestion", "")[:100]
            )
            if key not in seen:
                seen.add(key)
                unique.append(suggestion)
        
        return unique
