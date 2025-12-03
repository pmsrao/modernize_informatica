"""SCD Detector — Production Grade
Detects Type-1 / Type-2 / Type-3 SCD logic based on fields, expressions, update strategy.
"""
from typing import Dict, Any, List, Optional


class SCDDetector:
    """Detects Slowly Changing Dimension patterns in mappings."""
    
    def detect(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Detect SCD type and related information.
        
        Returns:
        {
            "type": "SCD1" | "SCD2" | "SCD3" | "NONE",
            "strategy": "HISTORICAL" | "CURRENT_FLAG" | "OVERWRITE",
            "keys": {
                "business_keys": [...],
                "surrogate_key": "...",
                "primary_key": "..."
            },
            "effective_dates": {
                "from_field": "...",
                "to_field": "...",
                "from_default": "...",
                "to_default": "..."
            },
            "current_flag": {
                "field": "...",
                "true_value": "...",
                "false_value": "..."
            },
            "versioning": {
                "version_field": "...",
                "version_strategy": "AUTO_INCREMENT|TIMESTAMP"
            }
        }
        """
        scd_info = {
            "type": "NONE",
            "strategy": None,
            "keys": {
                "business_keys": [],
                "surrogate_key": None,
                "primary_key": None
            },
            "effective_dates": {
                "from_field": None,
                "to_field": None,
                "from_default": None,
                "to_default": None
            },
            "current_flag": {
                "field": None,
                "true_value": None,
                "false_value": None
            },
            "versioning": {
                "version_field": None,
                "version_strategy": None
            }
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
            effective_from = self._find_effective_from(target_fields)
            effective_to = self._find_effective_to(target_fields)
            
            scd_info["effective_dates"]["from_field"] = effective_from
            scd_info["effective_dates"]["to_field"] = effective_to
            scd_info["effective_dates"]["from_default"] = "SYSDATE"  # Common default
            scd_info["effective_dates"]["to_default"] = "NULL"  # Common default for active records
            
            # Determine strategy
            if any("CURRENT_FLAG" in f or "IS_CURRENT" in f for f in target_fields):
                scd_info["strategy"] = "CURRENT_FLAG"
                current_flag_field = self._find_current_flag_field(target_fields)
                if current_flag_field:
                    scd_info["current_flag"]["field"] = current_flag_field
                    scd_info["current_flag"]["true_value"] = "Y"  # Common values
                    scd_info["current_flag"]["false_value"] = "N"
            else:
                scd_info["strategy"] = "HISTORICAL"
            
            # Find keys
            keys = self._find_scd_keys(mapping, scd_info["type"])
            scd_info["keys"]["business_keys"] = keys
            scd_info["keys"]["primary_key"] = self._find_primary_key(target_fields, mapping)
            scd_info["keys"]["surrogate_key"] = self._find_surrogate_key(target_fields)
            
            # Find versioning
            version_field = self._find_version_field(target_fields)
            if version_field:
                scd_info["versioning"]["version_field"] = version_field
                scd_info["versioning"]["version_strategy"] = "AUTO_INCREMENT"  # Default assumption
        
        # Detect SCD1 (simple overwrite)
        elif self._has_scd1_indicators(target_fields, mapping):
            scd_info["type"] = "SCD1"
            scd_info["strategy"] = "OVERWRITE"
            keys = self._find_scd_keys(mapping, scd_info["type"])
            scd_info["keys"]["business_keys"] = keys
            scd_info["keys"]["primary_key"] = self._find_primary_key(target_fields, mapping)
        
        # Detect SCD3 (current and previous value)
        elif self._has_scd3_indicators(target_fields, mapping):
            scd_info["type"] = "SCD3"
            scd_info["strategy"] = "CURRENT_PREVIOUS"
            keys = self._find_scd_keys(mapping, scd_info["type"])
            scd_info["keys"]["business_keys"] = keys
            scd_info["keys"]["primary_key"] = self._find_primary_key(target_fields, mapping)
        
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
    
    def _find_current_flag_field(self, target_fields: List[str]) -> Optional[str]:
        """Find current flag field name."""
        for field in target_fields:
            if "CURRENT_FLAG" in field or "IS_CURRENT" in field:
                return field
        return None
    
    def _find_primary_key(self, target_fields: List[str], mapping: Dict[str, Any]) -> Optional[str]:
        """Find primary key field."""
        # Look for PRIMARY_KEY or fields ending in _PK or _ID
        for field in target_fields:
            if "PRIMARY_KEY" in field or field.endswith("_PK") or field.endswith("_ID"):
                return field
        
        # Check target fields
        for target in mapping.get("targets", []):
            for field in target.get("fields", []):
                field_name = field.get("name", "").upper()
                if "PRIMARY" in field_name and "KEY" in field_name:
                    return field.get("name", "")
        
        return None
    
    def _find_surrogate_key(self, target_fields: List[str]) -> Optional[str]:
        """Find surrogate key field."""
        for field in target_fields:
            if "SURROGATE" in field or field.endswith("_SK"):
                return field
        return None
    
    def _find_version_field(self, target_fields: List[str]) -> Optional[str]:
        """Find version field."""
        for field in target_fields:
            if "VERSION" in field or "VER" in field:
                return field
        return None
