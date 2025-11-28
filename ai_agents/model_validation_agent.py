"""Model Validation Agent
Validates enhanced canonical model for consistency and correctness.
"""
import json
import hashlib
from typing import Dict, Any, List, Optional
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.utils.logger import get_logger
from src.utils.exceptions import ModernizationError

logger = get_logger(__name__)


class ModelValidationAgent:
    """Validates enhanced canonical model for consistency and correctness."""
    
    def __init__(self):
        """Initialize Model Validation Agent."""
        logger.info("Model Validation Agent initialized")
    
    def validate(self, enhanced_model: Dict[str, Any], 
                 original_model: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate enhanced canonical model.
        
        Args:
            enhanced_model: Enhanced canonical model to validate
            original_model: Optional original model for comparison
            
        Returns:
            Validation result dictionary:
            {
                "is_valid": bool,
                "errors": List[str],
                "warnings": List[str],
                "rollback_recommended": bool,
                "validation_details": Dict
            }
        """
        try:
            if not enhanced_model or not isinstance(enhanced_model, dict):
                return {
                    "is_valid": False,
                    "errors": ["Enhanced model is not a valid dictionary"],
                    "warnings": [],
                    "rollback_recommended": True,
                    "validation_details": {}
                }
            
            errors = []
            warnings = []
            validation_details = {}
            
            # 1. Schema validation
            schema_validation = self._validate_schema(enhanced_model)
            if not schema_validation["is_valid"]:
                errors.extend(schema_validation["errors"])
            validation_details["schema_validation"] = schema_validation
            
            # 2. Consistency checks
            consistency_check = self._check_consistency(enhanced_model)
            if not consistency_check["is_valid"]:
                errors.extend(consistency_check["errors"])
                warnings.extend(consistency_check["warnings"])
            validation_details["consistency_check"] = consistency_check
            
            # 3. Compare with original (if provided)
            if original_model:
                diff_analysis = self._compare_models(original_model, enhanced_model)
                validation_details["diff_analysis"] = diff_analysis
                
                if diff_analysis.get("breaking_changes"):
                    warnings.append("Enhancement introduces breaking changes")
                    if len(diff_analysis["breaking_changes"]) > 3:
                        warnings.append("Multiple breaking changes detected - review recommended")
            
            # 4. Enhancement quality check
            enhancement_quality = self._check_enhancement_quality(enhanced_model)
            validation_details["enhancement_quality"] = enhancement_quality
            
            if not enhancement_quality["is_valid"]:
                warnings.extend(enhancement_quality["warnings"])
            
            # Determine if rollback is recommended
            rollback_recommended = (
                len(errors) > 0 or
                len([w for w in warnings if "breaking" in w.lower()]) > 2 or
                enhancement_quality.get("confidence_score", 1.0) < 0.5
            )
            
            is_valid = len(errors) == 0
            
            result = {
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "rollback_recommended": rollback_recommended,
                "validation_details": validation_details
            }
            
            logger.info(f"Model validation completed: valid={is_valid}, errors={len(errors)}, warnings={len(warnings)}")
            return result
            
        except Exception as e:
            logger.error(f"Model validation failed: {str(e)}")
            return {
                "is_valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": [],
                "rollback_recommended": True,
                "validation_details": {}
            }
    
    def _validate_schema(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that model conforms to canonical model schema.
        
        Args:
            model: Canonical model to validate
            
        Returns:
            Validation result
        """
        errors = []
        
        # Required top-level fields
        required_fields = ["mapping_name"]
        for field in required_fields:
            if field not in model:
                errors.append(f"Missing required field: {field}")
        
        # Validate sources structure
        if "sources" in model:
            if not isinstance(model["sources"], list):
                errors.append("Sources must be a list")
            else:
                for i, source in enumerate(model["sources"]):
                    if not isinstance(source, dict):
                        errors.append(f"Source {i} must be a dictionary")
                    elif "name" not in source:
                        errors.append(f"Source {i} missing required field: name")
        
        # Validate targets structure
        if "targets" in model:
            if not isinstance(model["targets"], list):
                errors.append("Targets must be a list")
            else:
                for i, target in enumerate(model["targets"]):
                    if not isinstance(target, dict):
                        errors.append(f"Target {i} must be a dictionary")
                    elif "name" not in target:
                        errors.append(f"Target {i} missing required field: name")
        
        # Validate transformations structure
        if "transformations" in model:
            if not isinstance(model["transformations"], list):
                errors.append("Transformations must be a list")
            else:
                for i, trans in enumerate(model["transformations"]):
                    if not isinstance(trans, dict):
                        errors.append(f"Transformation {i} must be a dictionary")
                    elif "name" not in trans:
                        errors.append(f"Transformation {i} missing required field: name")
                    elif "type" not in trans:
                        errors.append(f"Transformation {i} missing required field: type")
        
        # Validate enhancement metadata if present
        if "_provenance" in model:
            provenance = model["_provenance"]
            if not isinstance(provenance, dict):
                errors.append("Provenance must be a dictionary")
            else:
                required_provenance_fields = ["enhanced_at", "enhancement_agent"]
                for field in required_provenance_fields:
                    if field not in provenance:
                        errors.append(f"Provenance missing required field: {field}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    def _check_consistency(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Check model for internal consistency.
        
        Args:
            model: Canonical model to check
            
        Returns:
            Consistency check result
        """
        errors = []
        warnings = []
        
        # Check transformation references in connectors
        transformation_names = {trans.get("name") for trans in model.get("transformations", [])}
        source_names = {src.get("name") for src in model.get("sources", [])}
        target_names = {tgt.get("name") for tgt in model.get("targets", [])}
        
        all_valid_names = transformation_names | source_names | target_names
        
        for connector in model.get("connectors", []):
            from_instance = connector.get("from_instance")
            to_instance = connector.get("to_instance")
            
            if from_instance and from_instance not in all_valid_names:
                warnings.append(f"Connector references unknown source/transformation: {from_instance}")
            
            if to_instance and to_instance not in all_valid_names:
                warnings.append(f"Connector references unknown target/transformation: {to_instance}")
        
        # Check for duplicate transformation names
        trans_names = [trans.get("name") for trans in model.get("transformations", [])]
        if len(trans_names) != len(set(trans_names)):
            errors.append("Duplicate transformation names found")
        
        # Check optimization hints are valid
        valid_hints = ["broadcast_join", "partition_by_group_by", "filter_pushdown", "consider_splitting"]
        for trans in model.get("transformations", []):
            if "_optimization_hint" in trans:
                hint = trans["_optimization_hint"]
                if hint not in valid_hints:
                    warnings.append(f"Unknown optimization hint: {hint} in {trans.get('name')}")
        
        # Check data quality rules structure
        if "_data_quality_rules" in model:
            rules = model["_data_quality_rules"]
            if not isinstance(rules, list):
                errors.append("Data quality rules must be a list")
            else:
                for i, rule in enumerate(rules):
                    if not isinstance(rule, dict):
                        errors.append(f"Data quality rule {i} must be a dictionary")
                    elif "type" not in rule:
                        warnings.append(f"Data quality rule {i} missing type")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _compare_models(self, original: Dict[str, Any], 
                       enhanced: Dict[str, Any]) -> Dict[str, Any]:
        """Compare original and enhanced models.
        
        Args:
            original: Original canonical model
            enhanced: Enhanced canonical model
            
        Returns:
            Comparison result with differences
        """
        breaking_changes = []
        non_breaking_changes = []
        
        # Check for removed required fields
        original_fields = set(original.keys())
        enhanced_fields = set(enhanced.keys())
        
        removed_fields = original_fields - enhanced_fields
        for field in removed_fields:
            if field in ["mapping_name", "sources", "targets", "transformations"]:
                breaking_changes.append(f"Required field removed: {field}")
            else:
                non_breaking_changes.append(f"Field removed: {field}")
        
        # Check for added enhancement fields (non-breaking)
        added_fields = enhanced_fields - original_fields
        enhancement_fields = {f for f in added_fields if f.startswith("_")}
        for field in enhancement_fields:
            non_breaking_changes.append(f"Enhancement field added: {field}")
        
        # Check transformation count
        original_trans_count = len(original.get("transformations", []))
        enhanced_trans_count = len(enhanced.get("transformations", []))
        if original_trans_count != enhanced_trans_count:
            breaking_changes.append(f"Transformation count changed: {original_trans_count} -> {enhanced_trans_count}")
        
        return {
            "breaking_changes": breaking_changes,
            "non_breaking_changes": non_breaking_changes,
            "total_changes": len(breaking_changes) + len(non_breaking_changes)
        }
    
    def _check_enhancement_quality(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Check quality of enhancements applied.
        
        Args:
            model: Enhanced canonical model
            
        Returns:
            Quality check result
        """
        warnings = []
        confidence_score = 1.0
        
        # Check if provenance exists
        if "_provenance" not in model:
            warnings.append("No provenance tracking found")
            confidence_score -= 0.2
        
        # Check if enhancements were actually applied
        enhancements_applied = model.get("_enhancements_applied", [])
        if not enhancements_applied:
            warnings.append("No enhancements were applied")
            confidence_score -= 0.3
        
        # Check optimization hints are reasonable
        trans_with_hints = [t for t in model.get("transformations", []) if "_optimization_hint" in t]
        total_trans = len(model.get("transformations", []))
        if total_trans > 0:
            hint_ratio = len(trans_with_hints) / total_trans
            if hint_ratio < 0.1 and total_trans > 5:
                warnings.append("Low ratio of transformations with optimization hints")
                confidence_score -= 0.1
        
        return {
            "is_valid": confidence_score >= 0.5,
            "warnings": warnings,
            "confidence_score": max(0.0, confidence_score),
            "enhancements_count": len(enhancements_applied)
        }

