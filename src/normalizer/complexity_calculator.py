"""Complexity Calculator

Calculates transformation complexity metrics for prioritization and risk scoring.
"""
from typing import Dict, Any, List
from utils.logger import get_logger

logger = get_logger(__name__)


class ComplexityCalculator:
    """Calculates complexity metrics for transformations."""
    
    def calculate(self, canonical_model: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate complexity metrics for a transformation.
        
        Args:
            canonical_model: Canonical model dictionary
            
        Returns:
            Dictionary with complexity metrics
        """
        transformations = canonical_model.get("transformations", [])
        connectors = canonical_model.get("connectors", [])
        
        metrics = {
            "cyclomatic_complexity": self._calculate_cyclomatic_complexity(transformations),
            "transformation_count": len(transformations),
            "connector_count": len(connectors),
            "expression_complexity": self._calculate_expression_complexity(transformations),
            "lookup_count": self._count_transformation_type(transformations, "LOOKUP"),
            "join_count": self._count_transformation_type(transformations, "JOINER"),
            "aggregation_count": self._count_transformation_type(transformations, "AGGREGATOR"),
            "source_count": len(canonical_model.get("sources", [])),
            "target_count": len(canonical_model.get("targets", []))
        }
        
        # Calculate overall complexity score (0-100)
        metrics["complexity_score"] = self._calculate_complexity_score(metrics)
        
        return metrics
    
    def _calculate_cyclomatic_complexity(self, transformations: List[Dict[str, Any]]) -> int:
        """Calculate cyclomatic complexity based on decision points.
        
        Args:
            transformations: List of transformation objects
            
        Returns:
            Cyclomatic complexity score
        """
        complexity = 1  # Base complexity
        
        for trans in transformations:
            trans_type = trans.get("type", "").upper()
            
            # Each transformation adds 1
            complexity += 1
            
            # Decision points add complexity
            if trans_type == "ROUTER":
                # Router groups are decision points
                groups = trans.get("groups", [])
                complexity += len(groups)
            elif trans_type == "FILTER":
                # Filter conditions are decision points
                complexity += 1
            elif trans_type == "EXPRESSION":
                # Expression with IIF/DECODE adds complexity
                ports = trans.get("ports", [])
                for port in ports:
                    expression = port.get("expression", "").upper()
                    if "IIF" in expression or "DECODE" in expression or "CASE" in expression:
                        complexity += expression.count("IIF") + expression.count("DECODE") + expression.count("CASE")
            elif trans_type == "JOINER":
                # Join conditions add complexity
                conditions = trans.get("conditions", [])
                complexity += len(conditions)
        
        return complexity
    
    def _calculate_expression_complexity(self, transformations: List[Dict[str, Any]]) -> int:
        """Calculate expression complexity score.
        
        Args:
            transformations: List of transformation objects
            
        Returns:
            Expression complexity score
        """
        complexity = 0
        
        for trans in transformations:
            ports = trans.get("ports", [])
            for port in ports:
                expression = port.get("expression", "")
                if expression:
                    # Count operators and functions
                    operators = ["+", "-", "*", "/", "||", "AND", "OR", "NOT"]
                    functions = ["IIF", "DECODE", "SUBSTR", "TRIM", "UPPER", "LOWER", "TO_DATE", "TO_CHAR"]
                    
                    expr_upper = expression.upper()
                    for op in operators:
                        complexity += expr_upper.count(op)
                    for func in functions:
                        complexity += expr_upper.count(func)
        
        return complexity
    
    def _count_transformation_type(self, transformations: List[Dict[str, Any]], trans_type: str) -> int:
        """Count transformations of a specific type.
        
        Args:
            transformations: List of transformation objects
            trans_type: Transformation type to count
            
        Returns:
            Count of transformations of the specified type
        """
        return sum(1 for trans in transformations if trans.get("type", "").upper() == trans_type.upper())
    
    def _calculate_complexity_score(self, metrics: Dict[str, Any]) -> int:
        """Calculate overall complexity score (0-100).
        
        Args:
            metrics: Dictionary of complexity metrics
            
        Returns:
            Complexity score from 0-100
        """
        score = 0
        
        # Cyclomatic complexity (max 30 points)
        cc = metrics.get("cyclomatic_complexity", 0)
        score += min(30, cc * 2)
        
        # Transformation count (max 20 points)
        trans_count = metrics.get("transformation_count", 0)
        score += min(20, trans_count * 2)
        
        # Connector count (max 15 points)
        conn_count = metrics.get("connector_count", 0)
        score += min(15, conn_count)
        
        # Expression complexity (max 15 points)
        expr_complexity = metrics.get("expression_complexity", 0)
        score += min(15, expr_complexity)
        
        # Lookup count (max 10 points)
        lookup_count = metrics.get("lookup_count", 0)
        score += min(10, lookup_count * 2)
        
        # Join count (max 10 points)
        join_count = metrics.get("join_count", 0)
        score += min(10, join_count * 2)
        
        return min(100, score)

