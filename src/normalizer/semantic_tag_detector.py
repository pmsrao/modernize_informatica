"""Semantic Tag Detector

Detects semantic patterns in transformations and adds semantic tags.
"""
from typing import Dict, Any, List
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SemanticTagDetector:
    """Detects semantic patterns and adds tags to transformations."""
    
    def detect_tags(self, canonical_model: Dict[str, Any]) -> List[str]:
        """Detect semantic tags for a transformation.
        
        Args:
            canonical_model: Canonical model dictionary
            
        Returns:
            List of semantic tags
        """
        tags = []
        
        transformations = canonical_model.get("transformations", [])
        scd_type = canonical_model.get("scd_type", "NONE")
        transformation_name = canonical_model.get("transformation_name", canonical_model.get("mapping_name", "unknown"))
        
        logger.debug(f"Detecting semantic tags for transformation: {transformation_name}")
        
        # SCD tags
        if scd_type != "NONE":
            tags.append(scd_type.lower())
            logger.debug(f"  - Added SCD tag: {scd_type.lower()}")
        
        # CDC detection
        if self._detect_cdc_pattern(canonical_model):
            tags.append("cdc")
            logger.debug(f"  - Added CDC tag")
        
        # Lookup-heavy detection (lowered threshold: >= 1 instead of >= 3)
        lookup_count = sum(1 for t in transformations if t.get("type", "").upper() == "LOOKUP")
        logger.debug(f"  - Lookup count: {lookup_count}")
        if lookup_count >= 1:
            tags.append("lookup-heavy")
            logger.debug(f"  - Added lookup-heavy tag")
        
        # Multi-join detection (lowered threshold: >= 1 instead of >= 2)
        join_count = sum(1 for t in transformations if t.get("type", "").upper() == "JOINER")
        logger.debug(f"  - Join count: {join_count}")
        if join_count >= 1:
            tags.append("multi-join")
            logger.debug(f"  - Added multi-join tag")
        
        # Aggregation-heavy detection (lowered threshold: >= 1 instead of >= 2)
        agg_count = sum(1 for t in transformations if t.get("type", "").upper() == "AGGREGATOR")
        logger.debug(f"  - Aggregation count: {agg_count}")
        if agg_count >= 1:
            tags.append("aggregation-heavy")
            logger.debug(f"  - Added aggregation-heavy tag")
        
        # Expression-heavy detection (lowered threshold: >= 2 instead of >= 5)
        expr_count = sum(1 for t in transformations if t.get("type", "").upper() == "EXPRESSION")
        logger.debug(f"  - Expression count: {expr_count}")
        if expr_count >= 2:
            tags.append("expression-heavy")
            logger.debug(f"  - Added expression-heavy tag")
        
        # Router-heavy detection (data splitting) (lowered threshold: >= 1 instead of >= 2)
        router_count = sum(1 for t in transformations if t.get("type", "").upper() == "ROUTER")
        logger.debug(f"  - Router count: {router_count}")
        if router_count >= 1:
            tags.append("data-splitting")
            logger.debug(f"  - Added data-splitting tag")
        
        # Filter-heavy detection (lowered threshold: >= 1 instead of >= 3)
        filter_count = sum(1 for t in transformations if t.get("type", "").upper() == "FILTER")
        logger.debug(f"  - Filter count: {filter_count}")
        if filter_count >= 1:
            tags.append("filter-heavy")
            logger.debug(f"  - Added filter-heavy tag")
        
        logger.debug(f"Final tags detected: {tags}")
        return tags
    
    def _detect_cdc_pattern(self, canonical_model: Dict[str, Any]) -> bool:
        """Detect Change Data Capture (CDC) patterns.
        
        Args:
            canonical_model: Canonical model dictionary
            
        Returns:
            True if CDC pattern detected
        """
        transformations = canonical_model.get("transformations", [])
        
        # Check for Update Strategy with CDC indicators
        for trans in transformations:
            if trans.get("type", "").upper() == "UPDATE_STRATEGY":
                update_expr = trans.get("update_strategy_expression", "").upper()
                # CDC typically uses DD_INSERT, DD_UPDATE, DD_DELETE
                if any(op in update_expr for op in ["DD_INSERT", "DD_UPDATE", "DD_DELETE"]):
                    return True
        
        # Check for incremental loading patterns
        incremental_keys = canonical_model.get("incremental_keys", [])
        if incremental_keys:
            # Check for timestamp-based incremental loading
            for key in incremental_keys:
                key_upper = key.upper()
                if any(term in key_upper for term in ["LAST_UPDATED", "MODIFIED_DATE", "CHANGE_DATE", "TIMESTAMP"]):
                    return True
        
        # Check for source qualifier with filter on timestamp
        for trans in transformations:
            if trans.get("type", "").upper() == "SOURCE_QUALIFIER":
                filter_cond = trans.get("filter", "").upper()
                if any(term in filter_cond for term in ["LAST_UPDATED", "MODIFIED_DATE", "CHANGE_DATE", "TIMESTAMP", ">", ">="]):
                    return True
        
        return False

