"""Lineage Engine — Production Grade
Builds column-level, transformation-level, and workflow-level lineage.
"""
from typing import Dict, Any, List


class LineageEngine:
    """Builds comprehensive lineage information."""
    
    def build(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Build complete lineage structure.
        
        Returns:
        {
            "column_level": {...},
            "transformation_level": [...],
            "workflow_level": {...}
        }
        """
        return {
            "column_level": self._build_column_lineage(mapping),
            "transformation_level": self._build_transformation_lineage(mapping),
            "workflow_level": self._build_workflow_lineage(mapping)
        }
    
    def _build_column_lineage(self, mapping: Dict[str, Any]) -> Dict[str, List[str]]:
        """Build column-level lineage: which source columns feed each target field."""
        column_lineage = {}
        
        # Track field dependencies through transformations
        for trans in mapping.get("transformations", []):
            trans_name = trans.get("name", "")
            trans_type = trans.get("type", "")
            
            # For expression transformations, track field derivations
            if trans_type == "EXPRESSION":
                for port in trans.get("ports", []):
                    if port.get("port_type") == "OUTPUT":
                        target_field = port.get("name", "")
                        expression = port.get("expression", "")
                        
                        # Extract source field references from expression
                        source_fields = self._extract_field_references(expression)
                        column_lineage[target_field] = source_fields
            
            # For aggregators, track group by and aggregate fields
            elif trans_type == "AGGREGATOR":
                for func in trans.get("aggregate_functions", []):
                    target_field = func.get("port", "")
                    expression = func.get("expression", "")
                    source_fields = self._extract_field_references(expression)
                    source_fields.extend(trans.get("group_by_ports", []))
                    column_lineage[target_field] = list(set(source_fields))
        
        return column_lineage
    
    def _build_transformation_lineage(self, mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build transformation-level lineage: data flow through transformations."""
        transformation_lineage = []
        
        # Build flow from connectors
        for conn in mapping.get("connectors", []):
            transformation_lineage.append({
                "from": conn.get("from_transformation", ""),
                "to": conn.get("to_transformation", ""),
                "from_port": conn.get("from_port", ""),
                "to_port": conn.get("to_port", "")
            })
        
        return transformation_lineage
    
    def _build_workflow_lineage(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Build workflow-level lineage: which mappings feed which targets."""
        # This would typically require workflow and session information
        # For now, return structure for mapping-level lineage
        return {
            "mapping_name": mapping.get("name", ""),
            "sources": [s.get("name", "") for s in mapping.get("sources", [])],
            "targets": [t.get("name", "") for t in mapping.get("targets", [])]
        }
    
    def _extract_field_references(self, expression: str) -> List[str]:
        """Extract field/column references from an expression string."""
        # Simple heuristic - extract identifiers that look like field names
        # This could be enhanced with proper AST parsing
        import re
        if not expression:
            return []
        
        # Match identifiers (words that aren't functions or operators)
        # This is a simplified approach - real implementation would use AST
        identifiers = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', expression)
        
        # Filter out common function names and keywords
        keywords = {'IIF', 'DECODE', 'NVL', 'TO_DATE', 'TO_CHAR', 'SUBSTR', 'UPPER', 'LOWER', 
                   'TRIM', 'ROUND', 'TRUNC', 'ABS', 'SUM', 'AVG', 'MAX', 'MIN', 'COUNT',
                   'AND', 'OR', 'NOT', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'}
        
        field_refs = [id for id in identifiers if id.upper() not in keywords]
        return list(set(field_refs))
