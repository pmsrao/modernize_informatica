"""Model Enhancement Agent
Enhances canonical model with AI insights, metadata, and optimizations.
"""
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.llm.llm_manager import LLMManager
from src.utils.logger import get_logger
from src.utils.exceptions import ModernizationError

logger = get_logger(__name__)


class ModelEnhancementAgent:
    """Enhances canonical model with AI insights, metadata, and optimizations."""
    
    def __init__(self, llm: Optional[LLMManager] = None, use_llm: bool = False):
        """Initialize Model Enhancement Agent.
        
        Args:
            llm: Optional LLM manager instance (creates new one if not provided)
            use_llm: Whether to use LLM-based enhancements (default: False for Phase 1)
        """
        self.llm = llm or LLMManager()
        self.use_llm = use_llm
        logger.info(f"Model Enhancement Agent initialized (LLM: {use_llm})")
    
    def enhance(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance canonical model with AI insights.
        
        Args:
            model: Canonical mapping model
            
        Returns:
            Enhanced canonical model with:
            - metadata_enhancements: Added metadata
            - optimization_hints: Performance suggestions
            - data_quality_rules: Quality constraints
            - _provenance: Track of all changes
        """
        try:
            if not model or not isinstance(model, dict):
                raise ModernizationError("Invalid model: model must be a non-empty dictionary")
            
            mapping_name = model.get("mapping_name", "unknown")
            logger.info(f"Enhancing canonical model: {mapping_name}")
            
            # Deep copy to avoid modifying original
            enhanced = json.loads(json.dumps(model))  # Deep copy
            
            # Phase 1: Pattern-based enhancements (fast, deterministic)
            enhanced = self._pattern_enhancements(enhanced)
            
            # Phase 2: LLM-based enhancements (optional, comprehensive)
            if self.use_llm:
                try:
                    enhanced = self._llm_enhancements(enhanced)
                except Exception as e:
                    logger.warning(f"LLM enhancement failed: {str(e)}, using pattern-based only")
            
            # Track provenance
            enhanced["_provenance"] = self._create_provenance(model, enhanced)
            
            logger.info(f"Successfully enhanced model: {mapping_name}")
            return enhanced
            
        except Exception as e:
            logger.error(f"Model enhancement failed: {str(e)}")
            raise ModernizationError(f"Model enhancement failed: {str(e)}") from e
    
    def _pattern_enhancements(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Fast, deterministic enhancements based on patterns.
        
        Args:
            model: Canonical model
            
        Returns:
            Enhanced model with pattern-based improvements
        """
        enhanced = model.copy()
        enhancements_applied = []
        
        # 1. Add missing data types to source fields
        for source in enhanced.get("sources", []):
            if "fields" in source:
                for field in source["fields"]:
                    if "data_type" not in field or not field.get("data_type"):
                        inferred_type = self._infer_data_type(field.get("name", ""))
                        if inferred_type:
                            field["data_type"] = inferred_type
                            enhancements_applied.append(f"Inferred data type for {field.get('name')}")
        
        # 2. Add optimization hints to transformations
        for trans in enhanced.get("transformations", []):
            trans_type = trans.get("type", "")
            trans_name = trans.get("name", "")
            
            # Lookup transformations: suggest broadcast join
            if trans_type == "LOOKUP":
                if "_optimization_hint" not in trans:
                    trans["_optimization_hint"] = "broadcast_join"
                    trans["_optimization_reason"] = "Lookup tables are typically small and benefit from broadcast"
                    enhancements_applied.append(f"Added broadcast_join hint to {trans_name}")
            
            # Aggregator transformations: suggest partitioning
            elif trans_type == "AGGREGATOR":
                group_by_ports = trans.get("group_by_ports", [])
                if group_by_ports and "_optimization_hint" not in trans:
                    trans["_optimization_hint"] = "partition_by_group_by"
                    trans["_optimization_reason"] = "Partitioning by group-by columns improves aggregation performance"
                    enhancements_applied.append(f"Added partition hint to {trans_name}")
            
            # Expression transformations with many output ports: suggest splitting
            elif trans_type == "EXPRESSION":
                ports = trans.get("ports", [])
                output_ports = [p for p in ports if p.get("port_type") == "OUTPUT" or p.get("expression")]
                if len(output_ports) > 10 and "_optimization_hint" not in trans:
                    trans["_optimization_hint"] = "consider_splitting"
                    trans["_optimization_reason"] = "Large number of output ports suggests splitting for maintainability"
                    enhancements_applied.append(f"Added splitting suggestion to {trans_name}")
            
            # Filter transformations: suggest filter pushdown
            elif trans_type == "FILTER":
                if "_optimization_hint" not in trans:
                    trans["_optimization_hint"] = "filter_pushdown"
                    trans["_optimization_reason"] = "Apply filter early in pipeline to reduce data volume"
                    enhancements_applied.append(f"Added filter pushdown hint to {trans_name}")
        
        # 3. Add data quality rules based on patterns
        if "_data_quality_rules" not in enhanced:
            enhanced["_data_quality_rules"] = []
        
        # Add not-null constraints for key fields
        for target in enhanced.get("targets", []):
            if "fields" in target:
                for field in target["fields"]:
                    field_name = field.get("name", "").upper()
                    # Common key field patterns
                    if any(keyword in field_name for keyword in ["_ID", "_KEY", "PRIMARY_KEY"]):
                        if "NOT_NULL" not in [r.get("type") for r in enhanced["_data_quality_rules"]]:
                            enhanced["_data_quality_rules"].append({
                                "type": "NOT_NULL",
                                "field": field_name,
                                "severity": "ERROR",
                                "description": f"{field_name} should not be null"
                            })
                            enhancements_applied.append(f"Added NOT_NULL rule for {field_name}")
        
        # 4. Add performance metadata
        if "_performance_metadata" not in enhanced:
            enhanced["_performance_metadata"] = {}
        
        # Estimate data volume based on transformations
        total_transformations = len(enhanced.get("transformations", []))
        if total_transformations > 5:
            enhanced["_performance_metadata"]["complexity"] = "HIGH"
            enhanced["_performance_metadata"]["estimated_runtime"] = "LONG"
        elif total_transformations > 2:
            enhanced["_performance_metadata"]["complexity"] = "MEDIUM"
            enhanced["_performance_metadata"]["estimated_runtime"] = "MEDIUM"
        else:
            enhanced["_performance_metadata"]["complexity"] = "LOW"
            enhanced["_performance_metadata"]["estimated_runtime"] = "SHORT"
        
        enhancements_applied.append(f"Added performance metadata (complexity: {enhanced['_performance_metadata']['complexity']})")
        
        # Store list of applied enhancements
        enhanced["_enhancements_applied"] = enhancements_applied
        
        return enhanced
    
    def _infer_data_type(self, field_name: str) -> Optional[str]:
        """Infer data type from field name (pattern-based).
        
        Args:
            field_name: Field name to infer type for
            
        Returns:
            Inferred data type or None
        """
        field_upper = field_name.upper()
        
        # Date/time patterns
        if any(keyword in field_upper for keyword in ["_DATE", "_DT", "_TIME", "_TS", "DATE_", "TIMESTAMP"]):
            return "TIMESTAMP"
        
        # ID patterns (usually integers or strings)
        if any(keyword in field_upper for keyword in ["_ID", "_KEY", "ID_", "KEY_"]):
            return "STRING"  # Default to string for IDs
        
        # Amount/money patterns
        if any(keyword in field_upper for keyword in ["_AMT", "_AMOUNT", "_PRICE", "_COST", "_VALUE"]):
            return "DECIMAL"
        
        # Count patterns
        if any(keyword in field_upper for keyword in ["_COUNT", "_CNT", "_QTY", "_QUANTITY"]):
            return "INTEGER"
        
        # Flag/boolean patterns
        if any(keyword in field_upper for keyword in ["_FLAG", "_IS_", "_HAS_", "_ACTIVE"]):
            return "BOOLEAN"
        
        # Default to string if no pattern matches
        return None
    
    def _llm_enhancements(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """LLM-based comprehensive enhancements.
        
        Note: This will be implemented in Phase 3. For Phase 1, this is a placeholder.
        
        Args:
            model: Canonical model
            
        Returns:
            Enhanced model with LLM-based improvements
        """
        # Phase 1: Return model as-is (LLM enhancements in Phase 3)
        logger.debug("LLM enhancements not yet implemented (Phase 3)")
        return model
    
    def _create_provenance(self, original_model: Dict[str, Any], 
                          enhanced_model: Dict[str, Any]) -> Dict[str, Any]:
        """Create provenance tracking for enhancements.
        
        Args:
            original_model: Original canonical model
            enhanced_model: Enhanced canonical model
            
        Returns:
            Provenance dictionary
        """
        # Create hash of original model for comparison
        original_str = json.dumps(original_model, sort_keys=True)
        original_hash = hashlib.md5(original_str.encode()).hexdigest()
        
        enhanced_str = json.dumps(enhanced_model, sort_keys=True)
        enhanced_hash = hashlib.md5(enhanced_str.encode()).hexdigest()
        
        return {
            "original_model_hash": original_hash,
            "enhanced_model_hash": enhanced_hash,
            "enhancements_applied": enhanced_model.get("_enhancements_applied", []),
            "enhanced_at": datetime.now().isoformat(),
            "enhancement_agent": "ModelEnhancementAgent",
            "llm_used": self.use_llm,
            "model_changed": original_hash != enhanced_hash
        }
    
    def _get_enhancement_list(self) -> List[str]:
        """Get list of enhancement types applied.
        
        Returns:
            List of enhancement type names
        """
        return [
            "data_type_inference",
            "optimization_hints",
            "data_quality_rules",
            "performance_metadata"
        ]

