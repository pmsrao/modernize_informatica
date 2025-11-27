"""Mapping Normalizer — Production Grade
Converts parsed mapping metadata into canonical JSON form per design spec.
"""
from typing import Dict, Any, List
from normalizer.lineage_engine import LineageEngine
from normalizer.scd_detector import SCDDetector
from utils.logger import get_logger

logger = get_logger(__name__)


class MappingNormalizer:
    """Normalizes parsed mapping data into canonical model structure."""
    
    def __init__(self):
        """Initialize normalizer with lineage and SCD detectors."""
        self.lineage_engine = LineageEngine()
        self.scd_detector = SCDDetector()
    
    def normalize(self, mapping_raw: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw parsed mapping into canonical model format.
        
        Returns canonical model with structure:
        {
            "mapping_name": str,
            "sources": [...],
            "targets": [...],
            "transformations": [...],
            "connectors": [...],
            "lineage": {...},
            "scd_type": str,
            "incremental_keys": [...]
        }
        """
        mapping_name = mapping_raw.get("name", "unknown")
        logger.info(f"Normalizing mapping: {mapping_name}")
        
        try:
            # Normalize sources
            sources = self._normalize_sources(mapping_raw.get("sources", []))
            logger.debug(f"Normalized {len(sources)} sources")
            
            # Normalize targets
            targets = self._normalize_targets(mapping_raw.get("targets", []))
            logger.debug(f"Normalized {len(targets)} targets")
            
            # Normalize transformations
            transformations = self._normalize_transformations(mapping_raw.get("transformations", []))
            logger.debug(f"Normalized {len(transformations)} transformations")
            
            # Normalize connectors
            connectors = self._normalize_connectors(mapping_raw.get("connectors", []))
            logger.debug(f"Normalized {len(connectors)} connectors")
            
            # Build lineage
            lineage = self.lineage_engine.build(mapping_raw)
            logger.debug("Built lineage information")
            
            # Detect SCD type
            scd_info = self.scd_detector.detect(mapping_raw)
            logger.debug(f"Detected SCD type: {scd_info.get('type', 'NONE')}")
            
            # Detect incremental keys
            incremental_keys = self._detect_incremental_keys(mapping_raw)
            logger.debug(f"Detected {len(incremental_keys)} incremental keys")
            
            canonical_model = {
                "mapping_name": mapping_name,
                "sources": sources,
                "targets": targets,
                "transformations": transformations,
                "connectors": connectors,
                "lineage": lineage,
                "scd_type": scd_info.get("type", "NONE"),
                "incremental_keys": incremental_keys
            }
            
            logger.info(f"Successfully normalized mapping: {mapping_name}")
            return canonical_model
            
        except Exception as e:
            logger.error(f"Error normalizing mapping: {mapping_name}", error=e)
            raise
    
    def _normalize_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize source definitions."""
        normalized = []
        for src in sources:
            normalized.append({
                "name": src.get("name", ""),
                "table": src.get("table", ""),
                "database": src.get("database", ""),
                "fields": src.get("fields", [])
            })
        return normalized
    
    def _normalize_targets(self, targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize target definitions."""
        normalized = []
        for tgt in targets:
            normalized.append({
                "name": tgt.get("name", ""),
                "table": tgt.get("table", ""),
                "database": tgt.get("database", ""),
                "fields": tgt.get("fields", [])
            })
        return normalized
    
    def _normalize_transformations(self, transformations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize transformation definitions."""
        normalized = []
        for trans in transformations:
            trans_type = trans.get("type", "").upper()
            
            # Base transformation structure
            normalized_trans = {
                "type": trans_type,
                "name": trans.get("name", ""),
                "ports": trans.get("ports", [])
            }
            
            # Add type-specific attributes
            if trans_type == "LOOKUP":
                normalized_trans.update({
                    "lookup_type": trans.get("lookup_type", "connected"),
                    "cache_type": trans.get("cache_type", "none"),
                    "condition": trans.get("condition"),
                    "table_name": trans.get("table_name", ""),
                    "connection": trans.get("connection", "")
                })
            elif trans_type == "AGGREGATOR":
                normalized_trans.update({
                    "group_by_ports": trans.get("group_by_ports", []),
                    "aggregate_functions": trans.get("aggregate_functions", [])
                })
            elif trans_type == "JOINER":
                normalized_trans.update({
                    "join_type": trans.get("join_type", "INNER"),
                    "conditions": trans.get("conditions", [])
                })
            elif trans_type == "ROUTER":
                normalized_trans.update({
                    "groups": trans.get("groups", [])
                })
            elif trans_type == "FILTER":
                normalized_trans.update({
                    "filter_condition": trans.get("filter_condition", "")
                })
            elif trans_type == "SORTER":
                normalized_trans.update({
                    "sort_keys": trans.get("sort_keys", [])
                })
            elif trans_type == "RANK":
                normalized_trans.update({
                    "top_bottom": trans.get("top_bottom", "TOP"),
                    "rank_count": trans.get("rank_count", "1"),
                    "rank_keys": trans.get("rank_keys", [])
                })
            elif trans_type == "SOURCE_QUALIFIER":
                normalized_trans.update({
                    "sql_query": trans.get("sql_query", ""),
                    "filter": trans.get("filter", "")
                })
            elif trans_type == "UPDATE_STRATEGY":
                normalized_trans.update({
                    "update_strategy_expression": trans.get("update_strategy_expression", "")
                })
            
            normalized.append(normalized_trans)
        
        return normalized
    
    def _normalize_connectors(self, connectors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize connector definitions."""
        normalized = []
        for conn in connectors:
            normalized.append({
                "from_transformation": conn.get("from_transformation", ""),
                "to_transformation": conn.get("to_transformation", ""),
                "from_port": conn.get("from_port", ""),
                "to_port": conn.get("to_port", "")
            })
        return normalized
    
    def _detect_incremental_keys(self, mapping_raw: Dict[str, Any]) -> List[str]:
        """Detect incremental load keys from mapping."""
        incremental_keys = []
        
        # Check for common incremental key patterns
        for trans in mapping_raw.get("transformations", []):
            if trans.get("type") == "FILTER":
                filter_cond = trans.get("filter_condition", "")
                # Look for date-based filters
                if any(keyword in filter_cond.upper() for keyword in ["LAST_UPDATED", "MODIFIED_DATE", "CHANGE_DATE"]):
                    # Extract potential key names
                    # This is a heuristic - could be enhanced with AI
                    pass
            
            # Check source qualifier for incremental patterns
            if trans.get("type") == "SOURCE_QUALIFIER":
                sql_query = trans.get("sql_query", "")
                filter_cond = trans.get("filter", "")
                if "WHERE" in (sql_query + filter_cond).upper():
                    # Could extract column names from WHERE clause
                    pass
        
        # Check target fields for common incremental key names
        for target in mapping_raw.get("targets", []):
            for field in target.get("fields", []):
                field_name = field.get("name", "").upper()
                if any(keyword in field_name for keyword in ["LAST_UPDATED", "MODIFIED_DATE", "CHANGE_DATE", "EFFECTIVE_DATE"]):
                    incremental_keys.append(field.get("name", ""))
        
        return list(set(incremental_keys))  # Remove duplicates
