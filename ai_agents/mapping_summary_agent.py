"""Mapping Summary Agent
Generates human-readable summary of mapping logic.
"""
import json
from typing import Dict, Any, Optional
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from llm.llm_manager import LLMManager
from llm.prompt_templates import get_mapping_summary_prompt
from utils.logger import get_logger
from utils.exceptions import ModernizationError

logger = get_logger(__name__)


class MappingSummaryAgent:
    """Generates comprehensive summaries of Informatica mappings."""
    
    def __init__(self, llm: Optional[LLMManager] = None):
        """Initialize Mapping Summary Agent.
        
        Args:
            llm: Optional LLM manager instance (creates new one if not provided)
        """
        self.llm = llm or LLMManager()
        logger.info("Mapping Summary Agent initialized")

    def summarize(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive summary of mapping logic.
        
        Args:
            mapping: Canonical mapping model
            
        Returns:
            Dictionary with:
            - mapping: Mapping name
            - summary: Narrative summary
            - sources: List of source names
            - targets: List of target names
            - transformations: List of transformation types
            - key_business_rules: List of key business rules identified
        """
        try:
            if not mapping or not isinstance(mapping, dict):
                raise ModernizationError("Invalid mapping: mapping must be a non-empty dictionary")
            
            mapping_name = mapping.get("mapping_name", "unknown")
            logger.info(f"Generating summary for mapping: {mapping_name}")
            
            # Extract basic information
            sources = [s.get("name", "unknown") for s in mapping.get("sources", [])]
            targets = [t.get("name", "unknown") for t in mapping.get("targets", [])]
            transformations = [t.get("type", "unknown") for t in mapping.get("transformations", [])]
            
            # Get LLM-generated summary
            try:
                prompt = get_mapping_summary_prompt(mapping)
                summary_text = self.llm.ask(prompt)
                
                # Extract key business rules from transformations
                key_rules = self._extract_business_rules(mapping)
                
                result = {
                    "mapping": mapping_name,
                    "summary": summary_text.strip(),
                    "sources": sources,
                    "targets": targets,
                    "transformation_types": list(set(transformations)),
                    "transformation_count": len(transformations),
                    "key_business_rules": key_rules,
                    "scd_type": mapping.get("scd_type", "NONE"),
                    "has_incremental_load": len(mapping.get("incremental_keys", [])) > 0
                }
                
                logger.info(f"Summary generated successfully for {mapping_name}")
                return result
                
            except Exception as e:
                logger.warning(f"LLM summary generation failed: {str(e)}, using fallback")
                # Fallback summary
                return {
                    "mapping": mapping_name,
                    "summary": self._generate_fallback_summary(mapping),
                    "sources": sources,
                    "targets": targets,
                    "transformation_types": list(set(transformations)),
                    "transformation_count": len(transformations),
                    "key_business_rules": [],
                    "scd_type": mapping.get("scd_type", "NONE"),
                    "has_incremental_load": len(mapping.get("incremental_keys", [])) > 0,
                    "error": str(e)
                }
            
        except Exception as e:
            logger.error(f"Mapping summary failed: {str(e)}")
            raise ModernizationError(f"Mapping summary failed: {str(e)}") from e

    def _extract_business_rules(self, mapping: Dict[str, Any]) -> list:
        """Extract key business rules from mapping.
        
        Args:
            mapping: Canonical mapping model
            
        Returns:
            List of business rule descriptions
        """
        rules = []
        transformations = mapping.get("transformations", [])
        
        for transformation in transformations:
            trans_type = transformation.get("type", "")
            trans_name = transformation.get("name", "")
            
            # Extract rules from expressions
            if trans_type == "EXPRESSION":
                output_ports = transformation.get("output_ports", [])
                for port in output_ports:
                    expr = port.get("expression", "")
                    field = port.get("name", "")
                    if expr and "IIF" in expr.upper():
                        rules.append(f"{field}: Conditional logic in {trans_name}")
            
            # Extract rules from filters
            elif trans_type == "FILTER":
                filter_cond = transformation.get("filter_condition", "")
                if filter_cond:
                    rules.append(f"Filter condition in {trans_name}: {filter_cond}")
            
            # Extract rules from routers
            elif trans_type == "ROUTER":
                groups = transformation.get("groups", [])
                for group in groups:
                    cond = group.get("condition", "")
                    if cond:
                        rules.append(f"Routing condition in {trans_name}: {cond}")
        
        return rules

    def _generate_fallback_summary(self, mapping: Dict[str, Any]) -> str:
        """Generate a basic fallback summary without LLM.
        
        Args:
            mapping: Canonical mapping model
            
        Returns:
            Basic summary text
        """
        mapping_name = mapping.get("mapping_name", "unknown")
        sources = [s.get("name") for s in mapping.get("sources", [])]
        targets = [t.get("name") for t in mapping.get("targets", [])]
        transformations = mapping.get("transformations", [])
        
        summary = f"This mapping ({mapping_name}) processes data from {len(sources)} source(s) "
        if sources:
            summary += f"({', '.join(sources[:3])}"
            if len(sources) > 3:
                summary += f" and {len(sources) - 3} more"
            summary += ") "
        
        summary += f"and writes to {len(targets)} target(s) "
        if targets:
            summary += f"({', '.join(targets[:3])}"
            if len(targets) > 3:
                summary += f" and {len(targets) - 3} more"
            summary += "). "
        
        summary += f"It applies {len(transformations)} transformation(s) including "
        trans_types = [t.get("type") for t in transformations]
        unique_types = list(set(trans_types))
        summary += ", ".join(unique_types[:3])
        if len(unique_types) > 3:
            summary += f", and {len(unique_types) - 3} more types"
        summary += "."
        
        return summary
