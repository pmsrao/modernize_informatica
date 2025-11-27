"""Reconstruct mapping from logs, lineage, or partial XML"""
import json
from typing import Dict, Any, Optional
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.llm.llm_manager import LLMManager
from src.llm.prompt_templates import get_mapping_reconstruction_prompt
from src.utils.logger import get_logger
from src.utils.exceptions import ModernizationError

logger = get_logger(__name__)


class MappingReconstructionAgent:
    """Reconstructs Informatica mappings from partial information."""
    
    def __init__(self, llm: Optional[LLMManager] = None):
        """Initialize Mapping Reconstruction Agent.
        
        Args:
            llm: Optional LLM manager instance (creates new one if not provided)
        """
        self.llm = llm or LLMManager()
        logger.info("Mapping Reconstruction Agent initialized")

    def reconstruct(self, clues: Dict[str, Any]) -> Dict[str, Any]:
        """Reconstruct mapping from partial clues.
        
        Args:
            clues: Dictionary containing:
                - partial_xml: Partial Informatica XML (optional)
                - log_fragments: Log file fragments (optional)
                - lineage: Lineage information (optional)
                - target_definitions: Target table structures (optional)
                - source_definitions: Source table structures (optional)
                
        Returns:
            Reconstructed canonical mapping model with:
            - mapping_name: Inferred name
            - sources: Inferred sources
            - targets: Inferred targets
            - transformations: Inferred transformations
            - connectors: Inferred data flow
            - confidence: High, Medium, or Low
            - assumptions: List of assumptions made
        """
        try:
            logger.info("Reconstructing mapping from clues")
            
            # Validate clues
            if not any(key in clues for key in ["partial_xml", "log_fragments", "lineage", "target_definitions"]):
                raise ModernizationError("Insufficient clues provided for reconstruction")
            
            # Get LLM-based reconstruction
            try:
                prompt = get_mapping_reconstruction_prompt(clues)
                llm_response = self.llm.ask(prompt)
                
                # Parse JSON response from LLM
                try:
                    reconstructed = json.loads(llm_response)
                    if not isinstance(reconstructed, dict):
                        raise json.JSONDecodeError("Not a dictionary", llm_response, 0)
                    
                    # Validate structure
                    if "mapping_name" not in reconstructed:
                        reconstructed["mapping_name"] = "RECONSTRUCTED_MAPPING"
                    
                    logger.info("Mapping reconstruction completed successfully")
                    return reconstructed
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LLM reconstruction as JSON: {str(e)}")
                    # Fallback to pattern-based reconstruction
                    return self._pattern_based_reconstruction(clues)
                    
            except Exception as e:
                logger.warning(f"LLM reconstruction failed: {str(e)}, using pattern-based")
                return self._pattern_based_reconstruction(clues)
                
        except Exception as e:
            logger.error(f"Mapping reconstruction failed: {str(e)}")
            raise ModernizationError(f"Mapping reconstruction failed: {str(e)}") from e

    def _pattern_based_reconstruction(self, clues: Dict[str, Any]) -> Dict[str, Any]:
        """Reconstruct mapping using pattern matching (fallback).
        
        Args:
            clues: Clues dictionary
            
        Returns:
            Basic reconstructed mapping
        """
        sources = []
        targets = []
        transformations = []
        
        # Extract from target definitions
        if "target_definitions" in clues:
            for target_def in clues["target_definitions"]:
                targets.append({
                    "name": target_def.get("name", "TGT_UNKNOWN"),
                    "type": "table",
                    "fields": target_def.get("fields", [])
                })
        
        # Extract from source definitions
        if "source_definitions" in clues:
            for source_def in clues["source_definitions"]:
                sources.append({
                    "name": source_def.get("name", "SRC_UNKNOWN"),
                    "type": "table",
                    "fields": source_def.get("fields", [])
                })
        
        # Infer transformations from target fields
        if targets and sources:
            # Assume at least one expression transformation
            transformations.append({
                "name": "EXP_CALCULATIONS",
                "type": "EXPRESSION",
                "input_ports": [],
                "output_ports": []
            })
        
        return {
            "mapping_name": "RECONSTRUCTED_MAPPING",
            "sources": sources,
            "targets": targets,
            "transformations": transformations,
            "connectors": [],
            "confidence": "Low",
            "assumptions": [
                "Basic structure inferred from available clues",
                "Transformations are simplified assumptions",
                "Connectors need manual verification"
            ]
        }
