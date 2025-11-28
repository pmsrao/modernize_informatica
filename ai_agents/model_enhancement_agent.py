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
        
        Args:
            model: Canonical model
            
        Returns:
            Enhanced model with LLM-based improvements
        """
        try:
            mapping_name = model.get("mapping_name", "unknown")
            logger.info(f"Applying LLM-based enhancements to: {mapping_name}")
            
            # Import prompt template
            from src.llm.prompt_templates import get_model_enhancement_prompt
            
            # Build prompt
            prompt = get_model_enhancement_prompt(model)
            
            # Call LLM
            response = self.llm.generate(prompt, max_tokens=2000)
            
            # Parse LLM response
            enhancements = self._parse_llm_enhancements(response)
            
            # Apply enhancements to model
            enhanced = self._apply_llm_enhancements(model, enhancements)
            
            logger.info(f"LLM enhancements applied to: {mapping_name}")
            return enhanced
            
        except Exception as e:
            logger.warning(f"LLM enhancement failed: {str(e)}, using pattern-based only")
            # Return model as-is if LLM fails
            return model
    
    def _parse_llm_enhancements(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response into structured enhancements.
        
        Args:
            llm_response: Raw LLM response text
            
        Returns:
            Structured enhancements dictionary
        """
        try:
            # Try to extract JSON from response
            import re
            
            # Look for JSON block in response
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                enhancements = json.loads(json_str)
                return enhancements
            else:
                # If no JSON found, return empty enhancements
                logger.warning("No JSON found in LLM response, using empty enhancements")
                return {}
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {str(e)}")
            return {}
        except Exception as e:
            logger.warning(f"Error parsing LLM enhancements: {str(e)}")
            return {}
    
    def _apply_llm_enhancements(self, model: Dict[str, Any], enhancements: Dict[str, Any]) -> Dict[str, Any]:
        """Apply LLM-suggested enhancements to model.
        
        Args:
            model: Original canonical model
            enhancements: LLM-suggested enhancements
            
        Returns:
            Enhanced model
        """
        enhanced = json.loads(json.dumps(model))  # Deep copy
        llm_enhancements_applied = []
        
        # Apply metadata enhancements
        for meta_enh in enhancements.get("metadata_enhancements", []):
            field_path = meta_enh.get("field", "")
            suggestion = meta_enh.get("suggestion", "")
            confidence = meta_enh.get("confidence", "Medium")
            
            if confidence in ["High", "Medium"]:
                # Parse field path (e.g., "SQ_CUSTOMER/CUSTOMER_ID")
                parts = field_path.split("/")
                if len(parts) == 2:
                    source_or_trans = parts[0]
                    field_name = parts[1]
                    
                    # Find and update field
                    for source in enhanced.get("sources", []):
                        if source.get("name") == source_or_trans:
                            for field in source.get("fields", []):
                                if field.get("name") == field_name:
                                    # Apply suggestion (e.g., "Add data type: STRING")
                                    if "data_type" in suggestion:
                                        data_type = suggestion.split(":")[-1].strip()
                                        field["data_type"] = data_type
                                        llm_enhancements_applied.append(f"Added data type {data_type} to {field_path}")
                    
                    # Check transformations
                    for trans in enhanced.get("transformations", []):
                        if trans.get("name") == source_or_trans:
                            for port in trans.get("ports", []):
                                if port.get("name") == field_name:
                                    if "data_type" in suggestion:
                                        data_type = suggestion.split(":")[-1].strip()
                                        port["data_type"] = data_type
                                        llm_enhancements_applied.append(f"Added data type {data_type} to {field_path}")
        
        # Apply optimization hints (merge with existing)
        for opt_hint in enhancements.get("optimization_hints", []):
            trans_name = opt_hint.get("transformation", "")
            hint = opt_hint.get("hint", "")
            priority = opt_hint.get("priority", "Medium")
            
            if priority in ["High", "Medium"]:
                for trans in enhanced.get("transformations", []):
                    if trans.get("name") == trans_name:
                        # Merge with existing hints
                        if "_optimization_hint" not in trans or priority == "High":
                            trans["_optimization_hint"] = hint
                            trans["_optimization_reason"] = opt_hint.get("reason", "")
                            llm_enhancements_applied.append(f"Added {hint} hint to {trans_name}")
        
        # Apply data quality rules
        if "_data_quality_rules" not in enhanced:
            enhanced["_data_quality_rules"] = []
        
        for dq_rule in enhancements.get("data_quality_rules", []):
            rule_type = dq_rule.get("type", "")
            field = dq_rule.get("field", "")
            severity = dq_rule.get("severity", "WARNING")
            
            if severity in ["ERROR", "WARNING"]:
                enhanced["_data_quality_rules"].append({
                    "type": rule_type,
                    "field": field,
                    "severity": severity,
                    "description": dq_rule.get("rule", "")
                })
                llm_enhancements_applied.append(f"Added {rule_type} rule for {field}")
        
        # Update performance metadata
        perf_meta = enhancements.get("performance_metadata", {})
        if perf_meta:
            if "_performance_metadata" not in enhanced:
                enhanced["_performance_metadata"] = {}
            
            # Merge performance metadata
            enhanced["_performance_metadata"].update(perf_meta)
            llm_enhancements_applied.append("Updated performance metadata from LLM")
        
        # Track LLM enhancements
        if "_llm_enhancements_applied" not in enhanced:
            enhanced["_llm_enhancements_applied"] = []
        enhanced["_llm_enhancements_applied"].extend(llm_enhancements_applied)
        
        return enhanced
    
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

