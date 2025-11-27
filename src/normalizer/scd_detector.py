"""SCD Detector — Production Grade
Detects Type-1 / Type-2 / Type-3 SCD logic based on fields, expressions, update strategy.
"""
from typing import Dict, Any, List


class SCDDetector:
    """Detects Slowly Changing Dimension patterns in mappings."""
    
    def detect(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Detect SCD type and related information.
        
        Returns:
        {
            "type": "SCD1" | "SCD2" | "SCD3" | "NONE",
            "keys": [...],
            "effective_from": "...",
            "effective_to": "..."
        }
        """
        scd_info = {
            "type": "NONE",
            "keys": [],
            "effective_from": None,
            "effective_to": None
        }
        
        # Check for Update Strategy transformation
        has_update_strategy = False
        for trans in mapping.get("transformations", []):
            if trans.get("type") == "UPDATE_STRATEGY":
                has_update_strategy = True
                break
        
        # Check target fields for SCD indicators
        target_fields = []
        for target in mapping.get("targets", []):
            target_fields.extend([f.get("name", "").upper() for f in target.get("fields", [])])
        
        # Detect SCD2 (most common)
        if self._has_scd2_indicators(target_fields, mapping):
            scd_info["type"] = "SCD2"
            scd_info["effective_from"] = self._find_effective_from(target_fields)
            scd_info["effective_to"] = self._find_effective_to(target_fields)
            scd_info["keys"] = self._find_scd_keys(mapping, scd_info["type"])
        
        # Detect SCD1 (simple overwrite)
        elif self._has_scd1_indicators(target_fields, mapping):
            scd_info["type"] = "SCD1"
            scd_info["keys"] = self._find_scd_keys(mapping, scd_info["type"])
        
        # Detect SCD3 (current and previous value)
        elif self._has_scd3_indicators(target_fields, mapping):
            scd_info["type"] = "SCD3"
            scd_info["keys"] = self._find_scd_keys(mapping, scd_info["type"])
        
        return scd_info
    
    def _has_scd2_indicators(self, target_fields: List[str], mapping: Dict[str, Any]) -> bool:
        """Check for SCD2 indicators."""
        # SCD2 typically has EFFECTIVE_FROM and EFFECTIVE_TO columns
        has_effective_from = any("EFFECTIVE_FROM" in f or "EFF_FROM" in f or "START_DATE" in f 
                                 for f in target_fields)
        has_effective_to = any("EFFECTIVE_TO" in f or "EFF_TO" in f or "END_DATE" in f 
                               for f in target_fields)
        
        # Also check for CURRENT_FLAG or IS_CURRENT
        has_current_flag = any("CURRENT_FLAG" in f or "IS_CURRENT" in f for f in target_fields)
        
        # Check for UPDATE_TIMESTAMP in expressions
        has_timestamp = False
        for trans in mapping.get("transformations", []):
            for port in trans.get("ports", []):
                expr = port.get("expression", "").upper()
                if "UPDATE_TIMESTAMP" in expr or "MODIFIED_DATE" in expr:
                    has_timestamp = True
                    break
        
        return (has_effective_from and has_effective_to) or (has_current_flag and has_timestamp)
    
    def _has_scd1_indicators(self, target_fields: List[str], mapping: Dict[str, Any]) -> bool:
        """Check for SCD1 indicators (simple overwrite)."""
        # SCD1 typically uses hash comparison or direct updates
        for trans in mapping.get("transformations", []):
            for port in trans.get("ports", []):
                expr = port.get("expression", "").upper()
                if "HASH" in expr or "CHECKSUM" in expr:
                    return True
        
        # Check for Update Strategy with DD_UPDATE
        for trans in mapping.get("transformations", []):
            if trans.get("type") == "UPDATE_STRATEGY":
                expr = trans.get("update_strategy_expression", "").upper()
                if "DD_UPDATE" in expr:
                    return True
        
        return False
    
    def _has_scd3_indicators(self, target_fields: List[str], mapping: Dict[str, Any]) -> bool:
        """Check for SCD3 indicators (current and previous value)."""
        # SCD3 has fields like CURRENT_VALUE and PREVIOUS_VALUE
        has_current = any("CURRENT_" in f or "CURR_" in f for f in target_fields)
        has_previous = any("PREVIOUS_" in f or "PREV_" in f or "OLD_" in f for f in target_fields)
        
        return has_current and has_previous
    
    def _find_effective_from(self, target_fields: List[str]) -> str:
        """Find effective from date field name."""
        for field in target_fields:
            if "EFFECTIVE_FROM" in field or "EFF_FROM" in field or "START_DATE" in field:
                return field
        return ""
    
    def _find_effective_to(self, target_fields: List[str]) -> str:
        """Find effective to date field name."""
        for field in target_fields:
            if "EFFECTIVE_TO" in field or "EFF_TO" in field or "END_DATE" in field:
                return field
        return ""
    
    def _find_scd_keys(self, mapping: Dict[str, Any], scd_type: str) -> List[str]:
        """Find primary/business keys used for SCD."""
        keys = []
        
        # Look for key indicators in target fields
        for target in mapping.get("targets", []):
            for field in target.get("fields", []):
                field_name = field.get("name", "").upper()
                # Common key patterns
                if any(keyword in field_name for keyword in ["_KEY", "_ID", "PRIMARY_KEY", "BUSINESS_KEY"]):
                    keys.append(field.get("name", ""))
        
        # Look for keys in join conditions
        for trans in mapping.get("transformations", []):
            if trans.get("type") == "JOINER":
                for cond in trans.get("conditions", []):
                    left_port = cond.get("left_port", "")
                    right_port = cond.get("right_port", "")
                    if left_port:
                        keys.append(left_port)
                    if right_port:
                        keys.append(right_port)
        
        return list(set(keys))  # Remove duplicates
