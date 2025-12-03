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
            "transformation_name": str,
            "source_component_type": "mapping",
            "sources": [...],
            "targets": [...],
            "transformations": [...],
            "connectors": [...],
            "lineage": {...},
            "scd_type": str,
            "incremental_keys": [...]
        }
        """
        transformation_name = mapping_raw.get("name", "unknown")
        logger.info(f"Normalizing transformation: {transformation_name}")
        
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
            
            # Calculate complexity metrics
            try:
                from src.normalizer.complexity_calculator import ComplexityCalculator
                complexity_calc = ComplexityCalculator()
                complexity_metrics = complexity_calc.calculate({
                    "transformations": transformations,
                    "connectors": connectors,
                    "sources": sources,
                    "targets": targets
                })
            except Exception as e:
                logger.warning(f"Failed to calculate complexity metrics: {e}")
                complexity_metrics = {}
            
            # Detect semantic tags
            try:
                from src.normalizer.semantic_tag_detector import SemanticTagDetector
                tag_detector = SemanticTagDetector()
                semantic_tags = tag_detector.detect_tags({
                    "transformations": transformations,
                    "connectors": connectors,
                    "sources": sources,
                    "targets": targets,
                    "scd_type": scd_info.get("type", "NONE"),
                    "incremental_keys": incremental_keys
                })
            except Exception as e:
                logger.warning(f"Failed to detect semantic tags: {e}")
                semantic_tags = []
            
            canonical_model = {
                "transformation_name": transformation_name,
                "source_component_type": "mapping",
                "sources": sources,
                "targets": targets,
                "transformations": transformations,
                "connectors": connectors,
                "lineage": lineage,
                "scd_type": scd_info.get("type", "NONE"),
                "incremental_keys": incremental_keys,
                "complexity_metrics": complexity_metrics,
                "semantic_tags": semantic_tags
            }
            
            logger.info(f"Successfully normalized transformation: {transformation_name}")
            return canonical_model
            
        except Exception as e:
            logger.error(f"Error normalizing transformation: {transformation_name}", error=e)
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
            
            # Handle mapplet instances
            if trans_type == "MAPPLET_INSTANCE":
                normalized.append(self._normalize_mapplet_instance(trans))
                continue
            
            # Handle custom transformations (manual intervention required)
            if trans_type == "CUSTOM_TRANSFORMATION":
                normalized.append(self._normalize_custom_transformation(trans))
                continue
            
            # Handle stored procedures (manual intervention may be required)
            if trans_type == "STORED_PROCEDURE":
                normalized.append(self._normalize_stored_procedure(trans))
                continue
            
            # Base transformation structure
            normalized_trans = {
                "type": trans_type,
                "name": trans.get("name", ""),
                "ports": trans.get("ports", [])
            }
            
            # Add reusable transformation metadata
            if trans.get("is_reusable", False):
                normalized_trans["is_reusable"] = True
                normalized_trans["reusable_name"] = trans.get("reusable_name", trans.get("name", ""))
            
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
    
    def _normalize_mapplet_instance(self, trans: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize mapplet instance transformation.
        
        Mapplet instances reference reusable transformations and need to be resolved
        during code generation by inlining the reusable transformation transformations.
        """
        return {
            "type": "MAPPLET_INSTANCE",
            "name": trans.get("name", ""),
            "reusable_transformation_ref": trans.get("mapplet_ref", trans.get("reusable_transformation_ref", "")),
            "input_port_mappings": trans.get("input_port_mappings", {}),
            "output_port_mappings": trans.get("output_port_mappings", {}),
            "requires_resolution": True,
            "resolution_strategy": "inline"  # Inline reusable transformation transformations during code generation
        }
    
    def _normalize_custom_transformation(self, trans: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize custom/Java transformation.
        
        These require manual intervention as they contain custom code.
        """
        return {
            "type": "CUSTOM_TRANSFORMATION",
            "name": trans.get("name", ""),
            "ports": trans.get("ports", []),
            "requires_manual_intervention": True,
            "manual_intervention_reason": trans.get("manual_intervention_reason", 
                "Custom transformation requires manual code review and migration"),
            "custom_type": trans.get("custom_type", "Unknown"),
            "code_reference": trans.get("code_reference"),
            "class_name": trans.get("class_name"),
            "jar_file": trans.get("jar_file"),
            "placeholder": {
                "description": f"Custom transformation '{trans.get('name', '')}' requires manual migration",
                "suggested_approach": "Review custom code and implement equivalent logic in target platform",
                "code_location": trans.get("code_reference") or trans.get("jar_file")
            }
        }
    
    def _normalize_stored_procedure(self, trans: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize stored procedure transformation.
        
        Stored procedures may require database-specific handling and manual intervention.
        """
        return {
            "type": "STORED_PROCEDURE",
            "name": trans.get("name", ""),
            "ports": trans.get("ports", []),
            "requires_manual_intervention": trans.get("requires_manual_intervention", True),
            "manual_intervention_reason": trans.get("manual_intervention_reason",
                "Stored procedure requires database-specific handling and may need manual migration"),
            "procedure_name": trans.get("procedure_name", ""),
            "connection": trans.get("connection"),
            "parameters": trans.get("parameters", []),
            "return_type": trans.get("return_type", "resultset"),
            "sql_query": trans.get("sql_query"),  # If called from Source Qualifier
            "source_transformation": trans.get("source_transformation"),  # If called from SQ
            "placeholder": {
                "description": f"Stored procedure '{trans.get('procedure_name', '')}' requires database-specific handling",
                "suggested_approach": "Review stored procedure logic and implement equivalent functionality in target platform",
                "database_specific": True,
                "connection_info": trans.get("connection")
            }
        }
    
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
                filter_cond = trans.get("filter_condition") or ""
                # Look for date-based filters
                if filter_cond and any(keyword in filter_cond.upper() for keyword in ["LAST_UPDATED", "MODIFIED_DATE", "CHANGE_DATE"]):
                    # Extract potential key names
                    # This is a heuristic - could be enhanced with AI
                    pass
            
            # Check source qualifier for incremental patterns
            if trans.get("type") == "SOURCE_QUALIFIER":
                sql_query = trans.get("sql_query") or ""
                filter_cond = trans.get("filter") or ""
                combined = (sql_query + filter_cond).upper() if (sql_query or filter_cond) else ""
                if combined and "WHERE" in combined:
                    # Could extract column names from WHERE clause
                    pass
        
        # Check target fields for common incremental key names
        for target in mapping_raw.get("targets", []):
            for field in target.get("fields", []):
                field_name = field.get("name", "").upper()
                if any(keyword in field_name for keyword in ["LAST_UPDATED", "MODIFIED_DATE", "CHANGE_DATE", "EFFECTIVE_DATE"]):
                    incremental_keys.append(field.get("name", ""))
        
        return list(set(incremental_keys))  # Remove duplicates
