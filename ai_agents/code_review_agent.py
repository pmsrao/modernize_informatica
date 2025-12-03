"""Code Review Agent - Reviews generated code for issues and improvements."""
import json
import re
from typing import Dict, Any, List, Optional
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from llm.llm_manager import LLMManager
from utils.logger import get_logger
from utils.exceptions import ModernizationError

logger = get_logger(__name__)


class CodeReviewAgent:
    """Reviews generated code for issues, improvements, and best practices."""
    
    def __init__(self, llm: Optional[LLMManager] = None, use_llm: bool = True):
        """Initialize Code Review Agent.
        
        Args:
            llm: Optional LLM manager instance (creates new one if not provided)
            use_llm: Whether to use LLM-based review (default: True)
        """
        self.llm = llm or LLMManager()
        self.use_llm = use_llm
        logger.info(f"Code Review Agent initialized (LLM: {use_llm})")
    
    def review(self, code: str, canonical_model: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Review generated code for issues and improvements.
        
        Args:
            code: Generated code to review
            canonical_model: Optional canonical model for context
            
        Returns:
            Review results with:
            - issues: List of issues found
            - suggestions: List of improvement suggestions
            - needs_fix: Whether code needs fixing
            - severity: Overall severity (LOW, MEDIUM, HIGH)
            - score: Quality score (0-100)
        """
        try:
            logger.info("Reviewing generated code")
            
            # Pattern-based review (fast, deterministic)
            pattern_issues = self._pattern_review(code)
            
            # LLM-based review (comprehensive)
            llm_issues = []
            llm_suggestions = []
            if self.use_llm:
                try:
                    llm_review = self._llm_review(code, canonical_model)
                    llm_issues = llm_review.get("issues", [])
                    llm_suggestions = llm_review.get("suggestions", [])
                except Exception as e:
                    logger.warning(f"LLM review failed: {str(e)}, using pattern-based only")
            
            # Combine results
            all_issues = pattern_issues + llm_issues
            severity = self._calculate_severity(all_issues)
            needs_fix = severity in ["HIGH", "MEDIUM"] or len([i for i in all_issues if i.get("severity") in ["HIGH", "MEDIUM"]]) > 0
            score = self._calculate_score(all_issues, llm_suggestions)
            
            result = {
                "issues": all_issues,
                "suggestions": llm_suggestions,
                "needs_fix": needs_fix,
                "severity": severity,
                "score": score,
                "review_summary": self._create_summary(all_issues, llm_suggestions, score)
            }
            
            logger.info(f"Code review completed: {len(all_issues)} issues, score: {score}/100")
            return result
            
        except Exception as e:
            logger.error(f"Code review failed: {str(e)}")
            raise ModernizationError(f"Code review failed: {str(e)}") from e
    
    def _pattern_review(self, code: str) -> List[Dict[str, Any]]:
        """Pattern-based code review (fast, deterministic).
        
        Args:
            code: Code to review
            
        Returns:
            List of issues found
        """
        issues = []
        
        # Check for common issues
        if not code or len(code.strip()) == 0:
            issues.append({
                "category": "Syntax",
                "severity": "HIGH",
                "issue": "Code is empty",
                "location": "entire_code",
                "recommendation": "Generate code before review"
            })
            return issues
        
        # Check for missing imports
        if "from pyspark.sql" in code and "import" not in code[:200]:
            issues.append({
                "category": "Structure",
                "severity": "MEDIUM",
                "issue": "Missing import statements",
                "location": "top_of_file",
                "recommendation": "Add: from pyspark.sql import functions as F, types as T"
            })
        
        # Check for hardcoded values
        hardcoded_patterns = [
            r'["\']localhost["\']',
            r'["\']127\.0\.0\.1["\']',
            r'password\s*=\s*["\'][^"\']+["\']',
        ]
        for pattern in hardcoded_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    "category": "Security",
                    "severity": "HIGH",
                    "issue": "Hardcoded sensitive values detected",
                    "location": "code",
                    "recommendation": "Use environment variables or configuration"
                })
        
        # Check for potential null pointer issues
        if ".collect()" in code and ".first()" not in code:
            issues.append({
                "category": "Performance",
                "severity": "MEDIUM",
                "issue": "Using collect() without null check",
                "location": "code",
                "recommendation": "Check for empty results before accessing"
            })
        
        # Check for missing error handling
        if "try:" not in code and "except" not in code:
            issues.append({
                "category": "Robustness",
                "severity": "LOW",
                "issue": "No error handling found",
                "location": "code",
                "recommendation": "Add try-except blocks for error handling"
            })
        
        # Check for inefficient operations
        if ".rdd" in code:
            issues.append({
                "category": "Performance",
                "severity": "MEDIUM",
                "issue": "Using RDD operations (less efficient than DataFrame)",
                "location": "code",
                "recommendation": "Use DataFrame operations instead of RDD"
            })
        
        return issues
    
    def _llm_review(self, code: str, canonical_model: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """LLM-based comprehensive code review.
        
        Args:
            code: Code to review
            canonical_model: Optional canonical model for context
            
        Returns:
            Review results from LLM
        """
        try:
            prompt = self._build_review_prompt(code, canonical_model)
            response = self.llm.generate(prompt, max_tokens=2000)
            
            # Parse LLM response
            review = self._parse_llm_review(response)
            return review
            
        except Exception as e:
            logger.warning(f"LLM review parsing failed: {str(e)}")
            return {"issues": [], "suggestions": []}
    
    def _build_review_prompt(self, code: str, canonical_model: Optional[Dict[str, Any]] = None) -> str:
        """Build prompt for LLM code review.
        
        Args:
            code: Code to review
            canonical_model: Optional canonical model
            
        Returns:
            Review prompt
        """
        context = ""
        if canonical_model:
            context = f"\n\nCanonical Model Context:\n{json.dumps(canonical_model, indent=2)}"
        
        return f"""You are an expert PySpark code reviewer. Review the following generated code for:

1. **Syntax Errors**: Python/PySpark syntax issues
2. **Logic Errors**: Incorrect business logic implementation
3. **Performance Issues**: Inefficient operations, missing optimizations
4. **Best Practices**: Code quality, readability, maintainability
5. **Security Issues**: Hardcoded credentials, unsafe operations
6. **Data Quality**: Missing null checks, type mismatches

Generated Code:
```python
{code}
```{context}

Return your review as JSON:
{{
  "issues": [
    {{
      "category": "Syntax|Logic|Performance|Best Practices|Security|Data Quality",
      "severity": "HIGH|MEDIUM|LOW",
      "issue": "Description of the issue",
      "location": "line_number or code_section",
      "recommendation": "How to fix it"
    }}
  ],
  "suggestions": [
    {{
      "area": "performance|readability|maintainability",
      "suggestion": "Description of improvement",
      "benefit": "Why this is better",
      "priority": "HIGH|MEDIUM|LOW"
    }}
  ]
}}

Code Review:"""
    
    def _parse_llm_review(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM review response.
        
        Args:
            llm_response: Raw LLM response
            
        Returns:
            Parsed review dictionary
        """
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                review = json.loads(json_str)
                return review
            else:
                logger.warning("No JSON found in LLM review response")
                return {"issues": [], "suggestions": []}
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM review as JSON: {str(e)}")
            return {"issues": [], "suggestions": []}
    
    def _calculate_severity(self, issues: List[Dict[str, Any]]) -> str:
        """Calculate overall severity from issues.
        
        Args:
            issues: List of issues
            
        Returns:
            Overall severity (HIGH, MEDIUM, LOW)
        """
        if not issues:
            return "LOW"
        
        high_count = len([i for i in issues if i.get("severity") == "HIGH"])
        medium_count = len([i for i in issues if i.get("severity") == "MEDIUM"])
        
        if high_count > 0:
            return "HIGH"
        elif medium_count > 2:
            return "MEDIUM"
        elif medium_count > 0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_score(self, issues: List[Dict[str, Any]], suggestions: List[Dict[str, Any]]) -> int:
        """Calculate quality score (0-100).
        
        Args:
            issues: List of issues
            suggestions: List of suggestions
            
        Returns:
            Quality score (0-100)
        """
        base_score = 100
        
        # Deduct points for issues
        for issue in issues:
            severity = issue.get("severity", "LOW")
            if severity == "HIGH":
                base_score -= 10
            elif severity == "MEDIUM":
                base_score -= 5
            else:
                base_score -= 2
        
        # Bonus for suggestions (shows code is good but can be improved)
        if suggestions and len(issues) == 0:
            base_score = min(100, base_score + 5)
        
        return max(0, min(100, base_score))
    
    def _create_summary(self, issues: List[Dict[str, Any]], suggestions: List[Dict[str, Any]], score: int) -> str:
        """Create human-readable review summary.
        
        Args:
            issues: List of issues
            suggestions: List of suggestions
            score: Quality score
            
        Returns:
            Summary text
        """
        if not issues and not suggestions:
            return f"Code review passed. Quality score: {score}/100. No issues found."
        
        summary_parts = [f"Code review completed. Quality score: {score}/100."]
        
        if issues:
            high_issues = [i for i in issues if i.get("severity") == "HIGH"]
            medium_issues = [i for i in issues if i.get("severity") == "MEDIUM"]
            
            if high_issues:
                summary_parts.append(f"Found {len(high_issues)} high-severity issues that need attention.")
            if medium_issues:
                summary_parts.append(f"Found {len(medium_issues)} medium-severity issues.")
        
        if suggestions:
            summary_parts.append(f"Found {len(suggestions)} improvement suggestions.")
        
        return " ".join(summary_parts)

