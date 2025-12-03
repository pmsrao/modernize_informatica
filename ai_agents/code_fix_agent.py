"""Code Fix Agent - LLM powered auto-correction of PySpark code"""
import re
from typing import Optional, Dict, Any
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from llm.llm_manager import LLMManager
from llm.prompt_templates import get_code_fix_prompt
from utils.logger import get_logger
from utils.exceptions import ModernizationError

logger = get_logger(__name__)


class CodeFixAgent:
    """Fixes errors in generated PySpark code while preserving business logic."""
    
    def __init__(self, llm: Optional[LLMManager] = None):
        """Initialize Code Fix Agent.
        
        Args:
            llm: Optional LLM manager instance (creates new one if not provided)
        """
        self.llm = llm or LLMManager()
        logger.info("Code Fix Agent initialized")

    def fix(self, pyspark_code: str, error_message: Optional[str] = None, error_type: Optional[str] = None) -> Dict[str, Any]:
        """Fix errors in PySpark code.
        
        Args:
            pyspark_code: The PySpark code that needs fixing
            error_message: Optional error message from execution
            error_type: Optional error type (syntax, runtime, logic)
            
        Returns:
            Dictionary with:
            - fixed_code: The corrected code
            - explanation: What was fixed
            - changes: List of changes made
        """
        try:
            logger.info("Fixing PySpark code")
            
            # Analyze code for common issues before LLM call
            analysis = self._analyze_code(pyspark_code, error_message)
            
            # Get LLM-based fix
            try:
                prompt = get_code_fix_prompt(pyspark_code, error_message, error_type)
                llm_response = self.llm.ask(prompt)
                
                # Extract code from response (may be wrapped in markdown code blocks)
                fixed_code = self._extract_code_from_response(llm_response)
                
                # If LLM didn't provide code, use analysis-based fixes
                if not fixed_code or fixed_code == pyspark_code:
                    fixed_code = self._apply_analysis_fixes(pyspark_code, analysis)
                    explanation = "Applied pattern-based fixes: " + ", ".join(analysis.get("issues", []))
                else:
                    explanation = self._extract_explanation_from_response(llm_response)
                    if not explanation:
                        explanation = "Code fixed by LLM analysis"
                
                changes = self._identify_changes(pyspark_code, fixed_code)
                
                result = {
                    "fixed_code": fixed_code,
                    "explanation": explanation,
                    "changes": changes,
                    "analysis": analysis
                }
                
                logger.info("Code fix completed successfully")
                return result
                
            except Exception as e:
                logger.warning(f"LLM code fix failed: {str(e)}, using analysis-based fixes")
                fixed_code = self._apply_analysis_fixes(pyspark_code, analysis)
                return {
                    "fixed_code": fixed_code,
                    "explanation": "Applied pattern-based fixes due to LLM error",
                    "changes": analysis.get("issues", []),
                    "analysis": analysis
                }
                
        except Exception as e:
            logger.error(f"Code fixing failed: {str(e)}")
            raise ModernizationError(f"Code fixing failed: {str(e)}") from e

    def _analyze_code(self, code: str, error_message: Optional[str] = None) -> Dict[str, Any]:
        """Analyze code for common issues.
        
        Args:
            code: PySpark code
            error_message: Optional error message
            
        Returns:
            Analysis dictionary
        """
        issues = []
        
        # Check for missing imports
        if "from pyspark.sql import functions as F" not in code and "F." in code:
            issues.append("Missing PySpark functions import")
        
        # Check for undefined columns
        if error_message and "cannot resolve" in error_message.lower():
            issues.append("Undefined column reference")
        
        # Check for syntax errors
        if error_message and "syntax error" in error_message.lower():
            issues.append("Syntax error detected")
        
        # Check for type mismatches
        if error_message and "type" in error_message.lower() and "mismatch" in error_message.lower():
            issues.append("Type mismatch")
        
        return {
            "issues": issues,
            "has_errors": len(issues) > 0
        }

    def _extract_code_from_response(self, response: str) -> str:
        """Extract code block from LLM response.
        
        Args:
            response: LLM response text
            
        Returns:
            Extracted code
        """
        # Look for code blocks
        code_block_pattern = r"```(?:python)?\s*(.*?)```"
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        if matches:
            return matches[0].strip()
        
        # If no code block, return response as-is (might be just code)
        return response.strip()

    def _extract_explanation_from_response(self, response: str) -> str:
        """Extract explanation from LLM response.
        
        Args:
            response: LLM response text
            
        Returns:
            Explanation text
        """
        # Look for explanation after code block
        code_block_pattern = r"```.*?```\s*(.*)"
        match = re.search(code_block_pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Look for explanation markers
        explanation_pattern = r"(?:Explanation|What was fixed|Changes):\s*(.*)"
        match = re.search(explanation_pattern, response, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        
        return ""

    def _apply_analysis_fixes(self, code: str, analysis: Dict[str, Any]) -> str:
        """Apply fixes based on analysis.
        
        Args:
            code: Original code
            analysis: Analysis results
            
        Returns:
            Fixed code
        """
        fixed = code
        
        # Add missing imports
        if "Missing PySpark functions import" in analysis.get("issues", []):
            if "from pyspark.sql import functions as F" not in fixed:
                # Add import at the top
                if "import" in fixed:
                    fixed = fixed.replace("import", "from pyspark.sql import functions as F\nimport", 1)
                else:
                    fixed = "from pyspark.sql import functions as F\n" + fixed
        
        return fixed

    def _identify_changes(self, original: str, fixed: str) -> list:
        """Identify what changed between original and fixed code.
        
        Args:
            original: Original code
            fixed: Fixed code
            
        Returns:
            List of change descriptions
        """
        changes = []
        
        if original != fixed:
            # Simple diff detection
            if "from pyspark.sql import functions as F" in fixed and "from pyspark.sql import functions as F" not in original:
                changes.append("Added PySpark functions import")
            
            # Count line differences
            orig_lines = len(original.split('\n'))
            fixed_lines = len(fixed.split('\n'))
            if fixed_lines != orig_lines:
                changes.append(f"Code structure changed ({orig_lines} -> {fixed_lines} lines)")
        
        return changes
