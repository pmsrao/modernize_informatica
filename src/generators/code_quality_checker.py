"""Code Quality Checker - Validates generated code quality.

This module provides comprehensive code quality checks for generated PySpark,
SQL, and other code artifacts.
"""
import sys
from pathlib import Path
import ast
import re
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.utils.logger import get_logger

logger = get_logger(__name__)


class CodeQualityChecker:
    """Validates generated code quality."""
    
    def __init__(self):
        """Initialize code quality checker."""
        pass
    
    def check_code_quality(self, code: str, code_type: str = "pyspark", 
                          canonical_model: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Comprehensive code quality checks.
        
        Args:
            code: Generated code string
            code_type: Type of code ('pyspark', 'sql', 'python')
            canonical_model: Optional canonical model for context
            
        Returns:
            Quality check results dictionary
        """
        results = {
            "syntax_valid": False,
            "syntax_errors": [],
            "type_safety": {"score": 0, "issues": []},
            "performance_hints": [],
            "best_practices": {"score": 0, "issues": []},
            "security_issues": [],
            "complexity_score": 0,
            "overall_score": 0,
            "recommendations": [],
            "databricks_validation": {}
        }
        
        # Syntax validation
        syntax_result = self.check_syntax(code, code_type)
        results["syntax_valid"] = syntax_result["valid"]
        results["syntax_errors"] = syntax_result["errors"]
        
        if not syntax_result["valid"]:
            # If syntax is invalid, skip other checks
            results["overall_score"] = 0
            return results
        
        # Databricks-specific validation
        try:
            from src.validation.databricks_validator import DatabricksValidator
            databricks_validator = DatabricksValidator()
            
            if code_type == "pyspark":
                databricks_result = databricks_validator.validate_pyspark_code(code)
                results["databricks_validation"] = databricks_result
            elif code_type == "sql":
                databricks_result = databricks_validator.validate_sql_code(code)
                results["databricks_validation"] = databricks_result
        except ImportError:
            logger.warning("DatabricksValidator not available - skipping Databricks-specific validation")
        
        # Type safety checks
        if code_type == "pyspark":
            results["type_safety"] = self.check_types(code, canonical_model)
        
        # Performance checks
        results["performance_hints"] = self.check_performance(code, code_type)
        
        # Best practices
        results["best_practices"] = self.check_best_practices(code, code_type)
        
        # Security checks
        results["security_issues"] = self.check_security(code)
        
        # Complexity score
        results["complexity_score"] = self.calculate_complexity(code, code_type)
        
        # Generate recommendations
        results["recommendations"] = self.generate_recommendations(results)
        
        # Calculate overall score (0-100)
        results["overall_score"] = self.calculate_overall_score(results)
        
        return results
    
    def check_syntax(self, code: str, code_type: str = "pyspark") -> Dict[str, Any]:
        """Check code syntax validity.
        
        Args:
            code: Code string to check
            code_type: Type of code ('pyspark', 'sql', 'python')
            
        Returns:
            Dictionary with 'valid' boolean and 'errors' list
        """
        errors = []
        
        if code_type in ["pyspark", "python"]:
            try:
                ast.parse(code)
            except SyntaxError as e:
                errors.append({
                    "line": e.lineno,
                    "message": e.msg,
                    "text": e.text,
                    "offset": e.offset
                })
            except Exception as e:
                errors.append({
                    "line": None,
                    "message": f"Parse error: {str(e)}"
                })
        
        elif code_type == "sql":
            # Basic SQL syntax checks
            # Check for balanced parentheses
            if code.count('(') != code.count(')'):
                errors.append({
                    "line": None,
                    "message": "Unbalanced parentheses"
                })
            
            # Check for balanced quotes
            single_quotes = code.count("'") - code.count("\\'")
            if single_quotes % 2 != 0:
                errors.append({
                    "line": None,
                    "message": "Unbalanced single quotes"
                })
            
            double_quotes = code.count('"') - code.count('\\"')
            if double_quotes % 2 != 0:
                errors.append({
                    "line": None,
                    "message": "Unbalanced double quotes"
                })
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def check_types(self, code: str, canonical_model: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check type safety issues.
        
        Args:
            code: PySpark code string
            canonical_model: Optional canonical model for context
            
        Returns:
            Dictionary with score and issues
        """
        issues = []
        score = 100
        
        # Check for common type issues
        # 1. Missing type hints in function definitions
        function_defs = re.findall(r'def\s+(\w+)\s*\([^)]*\):', code)
        type_hinted_funcs = len(re.findall(r'def\s+\w+\s*\([^)]*:\s*\w+', code))
        if function_defs and type_hinted_funcs < len(function_defs) * 0.5:
            issues.append({
                "issue": "Missing type hints in function definitions",
                "severity": "LOW",
                "recommendation": "Add type hints to function parameters and return types"
            })
            score -= 10
        
        # 2. Check for potential None/Null issues
        if re.search(r'\.get\([^)]+\)\s*\[', code):
            issues.append({
                "issue": "Potential KeyError: using .get() result with [] indexing",
                "severity": "MEDIUM",
                "recommendation": "Use .get() with default value or check for None"
            })
            score -= 15
        
        # 3. Check for missing null checks in DataFrame operations
        if canonical_model:
            # Check if canonical model has nullable fields that aren't handled
            sources = canonical_model.get("sources", [])
            for source in sources:
                fields = source.get("fields", [])
                for field in fields:
                    field_name = field.get("name", "")
                    # Simple check: if field is used but no null handling
                    if field_name and field_name in code:
                        if not re.search(rf'\.isNull\(\)|\.isNotNull\(\)|\.fillna|\.dropna', code):
                            # Not a critical issue, just a hint
                            pass
        
        return {
            "score": max(0, score),
            "issues": issues
        }
    
    def check_performance(self, code: str, code_type: str = "pyspark") -> List[Dict[str, Any]]:
        """Check for performance issues and provide hints.
        
        Args:
            code: Code string
            code_type: Type of code
            
        Returns:
            List of performance hints
        """
        hints = []
        
        if code_type == "pyspark":
            # 1. Check for cartesian joins
            if re.search(r'\.join\([^,)]+\)', code):
                # Check if join condition is missing (cartesian join)
                join_matches = re.finditer(r'\.join\(([^)]+)\)', code)
                for match in join_matches:
                    join_expr = match.group(1)
                    if 'on=' not in join_expr and 'how=' not in join_expr:
                        hints.append({
                            "hint": "Potential cartesian join detected - specify join condition",
                            "severity": "HIGH",
                            "location": "join operation",
                            "recommendation": "Add 'on=' parameter to join() call"
                        })
            
            # 2. Check for collect() usage (should be avoided for large datasets)
            if re.search(r'\.collect\(\)', code):
                hints.append({
                    "hint": "collect() used - may cause memory issues with large datasets",
                    "severity": "MEDIUM",
                    "location": "collect() call",
                    "recommendation": "Consider using take(), head(), or write to storage instead"
                })
            
            # 3. Check for multiple passes over same DataFrame
            df_vars = re.findall(r'(\w+)\s*=\s*spark\.', code)
            if len(df_vars) > 5:
                hints.append({
                    "hint": "Many DataFrame operations - consider caching intermediate results",
                    "severity": "LOW",
                    "location": "multiple DataFrame operations",
                    "recommendation": "Use .cache() or .persist() for DataFrames used multiple times"
                })
            
            # 4. Check for missing partition hints
            if re.search(r'\.write\.', code) and not re.search(r'partitionBy|coalesce|repartition', code):
                hints.append({
                    "hint": "Write operation without partitioning - may cause small files",
                    "severity": "LOW",
                    "location": "write operation",
                    "recommendation": "Consider using partitionBy() or repartition() before write"
                })
        
        elif code_type == "sql":
            # Check for SELECT * without LIMIT
            if re.search(r'SELECT\s+\*', code, re.IGNORECASE) and not re.search(r'LIMIT\s+\d+', code, re.IGNORECASE):
                hints.append({
                    "hint": "SELECT * without LIMIT - may return large result set",
                    "severity": "LOW",
                    "location": "SELECT statement",
                    "recommendation": "Add LIMIT clause for testing or specify columns"
                })
            
            # Check for missing WHERE clause in large table queries
            if re.search(r'FROM\s+\w+', code, re.IGNORECASE) and not re.search(r'WHERE\s+', code, re.IGNORECASE):
                hints.append({
                    "hint": "Query without WHERE clause - may scan entire table",
                    "severity": "MEDIUM",
                    "location": "SELECT statement",
                    "recommendation": "Add WHERE clause to filter data if possible"
                })
        
        return hints
    
    def check_best_practices(self, code: str, code_type: str = "pyspark") -> Dict[str, Any]:
        """Check code against best practices.
        
        Args:
            code: Code string
            code_type: Type of code
            
        Returns:
            Dictionary with score and issues
        """
        issues = []
        score = 100
        
        # 1. Check for hardcoded values
        hardcoded_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
            (r'localhost:\d+', "Hardcoded localhost address"),
        ]
        
        for pattern, description in hardcoded_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    "issue": description,
                    "severity": "HIGH",
                    "recommendation": "Use environment variables or configuration files"
                })
                score -= 20
        
        # 2. Check for magic numbers
        magic_numbers = re.findall(r'\b\d{4,}\b', code)  # Numbers with 4+ digits
        if magic_numbers:
            issues.append({
                "issue": f"Potential magic numbers found: {len(magic_numbers)} instances",
                "severity": "LOW",
                "recommendation": "Define constants with meaningful names"
            })
            score -= 5
        
        # 3. Check for long functions (if code_type is Python)
        if code_type in ["pyspark", "python"]:
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                        if lines > 50:
                            issues.append({
                                "issue": f"Long function '{node.name}' ({lines} lines) - consider breaking into smaller functions",
                                "severity": "LOW",
                                "recommendation": "Refactor into smaller, focused functions"
                            })
                            score -= 5
            except:
                pass  # If parsing fails, skip this check
        
        # 4. Check for missing docstrings
        if code_type in ["pyspark", "python"]:
            functions = re.findall(r'def\s+(\w+)\s*\(', code)
            docstrings = len(re.findall(r'""".*?"""', code, re.DOTALL))
            if functions and docstrings < len(functions) * 0.5:
                issues.append({
                    "issue": "Missing docstrings in functions",
                    "severity": "LOW",
                    "recommendation": "Add docstrings to document function purpose and parameters"
                })
                score -= 10
        
        # 5. Check for proper error handling
        if code_type in ["pyspark", "python"]:
            if re.search(r'\.write\.|\.save\(|\.saveAsTable\(', code):
                if not re.search(r'try:|except|raise', code):
                    issues.append({
                        "issue": "Write operations without error handling",
                        "severity": "MEDIUM",
                        "recommendation": "Add try-except blocks for write operations"
                    })
                    score -= 15
        
        return {
            "score": max(0, score),
            "issues": issues
        }
    
    def check_security(self, code: str) -> List[Dict[str, Any]]:
        """Check for security issues.
        
        Args:
            code: Code string
            
        Returns:
            List of security issues
        """
        issues = []
        
        # 1. Check for SQL injection risks (if SQL code)
        if re.search(r'SELECT|INSERT|UPDATE|DELETE', code, re.IGNORECASE):
            # Check for string concatenation in SQL
            if re.search(r'["\'].*?\+.*?["\']', code):
                issues.append({
                    "issue": "Potential SQL injection risk - string concatenation in SQL",
                    "severity": "HIGH",
                    "recommendation": "Use parameterized queries or proper escaping"
                })
        
        # 2. Check for eval() or exec() usage
        if re.search(r'\beval\s*\(|\bexec\s*\(', code):
            issues.append({
                "issue": "Use of eval() or exec() - security risk",
                "severity": "HIGH",
                "recommendation": "Avoid eval()/exec() - use safer alternatives"
            })
        
        # 3. Check for hardcoded credentials
        credential_patterns = [
            (r'password\s*[:=]\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'secret\s*[:=]\s*["\'][^"\']+["\']', "Hardcoded secret"),
            (r'api[_-]?key\s*[:=]\s*["\'][^"\']+["\']', "Hardcoded API key"),
        ]
        
        for pattern, description in credential_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    "issue": description,
                    "severity": "HIGH",
                    "recommendation": "Use environment variables or secure credential storage"
                })
        
        return issues
    
    def calculate_complexity(self, code: str, code_type: str = "pyspark") -> int:
        """Calculate code complexity score (0-100, higher = more complex).
        
        Args:
            code: Code string
            code_type: Type of code
            
        Returns:
            Complexity score (0-100)
        """
        score = 0
        
        # Base complexity from lines of code
        lines = len([l for l in code.split('\n') if l.strip() and not l.strip().startswith('#')])
        score += min(30, lines // 2)  # Max 30 points for size
        
        if code_type in ["pyspark", "python"]:
            try:
                tree = ast.parse(code)
                
                # Count control flow statements
                control_flow = len([n for n in ast.walk(tree) if isinstance(n, (ast.If, ast.For, ast.While, ast.Try))])
                score += min(30, control_flow * 3)  # Max 30 points
                
                # Count function definitions
                functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
                score += min(20, functions * 2)  # Max 20 points
                
                # Count nested structures
                max_depth = self._calculate_max_depth(tree)
                score += min(20, max_depth * 5)  # Max 20 points
                
            except:
                # If parsing fails, use simple heuristics
                score += len(re.findall(r'\bif\b|\bfor\b|\bwhile\b|\btry\b', code)) * 3
        
        return min(100, score)
    
    def _calculate_max_depth(self, node: ast.AST, depth: int = 0) -> int:
        """Calculate maximum nesting depth in AST."""
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.FunctionDef)):
                child_depth = self._calculate_max_depth(child, depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calculate_max_depth(child, depth)
                max_depth = max(max_depth, child_depth)
        return max_depth
    
    def generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on quality check results.
        
        Args:
            results: Quality check results dictionary
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Syntax errors
        if results["syntax_errors"]:
            recommendations.append(f"Fix {len(results['syntax_errors'])} syntax error(s) before proceeding")
        
        # Type safety
        if results["type_safety"]["score"] < 80:
            recommendations.append("Improve type safety by adding type hints and null checks")
        
        # Performance
        if results["performance_hints"]:
            high_perf_issues = [h for h in results["performance_hints"] if h.get("severity") == "HIGH"]
            if high_perf_issues:
                recommendations.append(f"Address {len(high_perf_issues)} high-priority performance issue(s)")
        
        # Best practices
        if results["best_practices"]["score"] < 70:
            recommendations.append("Review and apply best practices for better code maintainability")
        
        # Security
        if results["security_issues"]:
            recommendations.append(f"Fix {len(results['security_issues'])} security issue(s) immediately")
        
        # Complexity
        if results["complexity_score"] > 70:
            recommendations.append("Consider refactoring to reduce code complexity")
        
        if not recommendations:
            recommendations.append("Code quality looks good! Minor improvements may be possible.")
        
        return recommendations
    
    def calculate_overall_score(self, results: Dict[str, Any]) -> int:
        """Calculate overall quality score (0-100).
        
        Args:
            results: Quality check results dictionary
            
        Returns:
            Overall score (0-100)
        """
        if not results["syntax_valid"]:
            return 0
        
        # Weighted scoring
        weights = {
            "syntax": 0.30,  # 30% - syntax must be valid
            "type_safety": 0.15,  # 15%
            "performance": 0.20,  # 20%
            "best_practices": 0.20,  # 20%
            "security": 0.15  # 15% - security is critical
        }
        
        # Calculate component scores
        type_score = results["type_safety"]["score"]
        best_practices_score = results["best_practices"]["score"]
        
        # Performance score (inverse of number of high/medium issues)
        perf_issues = len([h for h in results["performance_hints"] if h.get("severity") in ["HIGH", "MEDIUM"]])
        perf_score = max(0, 100 - (perf_issues * 10))
        
        # Security score (inverse of number of issues)
        security_issues = len(results["security_issues"])
        security_score = max(0, 100 - (security_issues * 25))
        
        # Calculate weighted average
        overall = (
            weights["syntax"] * 100 +  # Syntax is valid (100)
            weights["type_safety"] * type_score +
            weights["performance"] * perf_score +
            weights["best_practices"] * best_practices_score +
            weights["security"] * security_score
        )
        
        return int(overall)

