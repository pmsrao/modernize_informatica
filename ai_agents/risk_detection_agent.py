"""Risk Detection Agent
Analyzes mapping for potential issues and risks.
"""
import json
from typing import Dict, Any, List, Optional
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.llm.llm_manager import LLMManager
from src.llm.prompt_templates import get_risk_analysis_prompt
from src.utils.logger import get_logger
from src.utils.exceptions import ModernizationError

logger = get_logger(__name__)


class RiskDetectionAgent:
    """Detects risks and potential issues in Informatica mappings."""
    
    def __init__(self, llm: Optional[LLMManager] = None):
        """Initialize Risk Detection Agent.
        
        Args:
            llm: Optional LLM manager instance (creates new one if not provided)
        """
        self.llm = llm or LLMManager()
        logger.info("Risk Detection Agent initialized")

    def detect_risks(self, mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze mapping for potential risks.
        
        Args:
            mapping: Canonical mapping model
            
        Returns:
            List of risk objects, each with:
            - category: Risk category
            - severity: High, Medium, or Low
            - location: Where the risk is found
            - risk: Description of the risk
            - impact: What could go wrong
            - recommendation: How to mitigate
        """
        try:
            mapping_name = mapping.get("mapping_name", "unknown")
            logger.info(f"Detecting risks for mapping: {mapping_name}")
            
            # First, do pattern-based risk detection (fast, deterministic)
            pattern_risks = self._detect_pattern_risks(mapping)
            
            # Then, get LLM-based risk analysis (comprehensive)
            llm_risks = []
            try:
                prompt = get_risk_analysis_prompt(mapping)
                llm_response = self.llm.ask(prompt)
                
                # Parse JSON response from LLM
                try:
                    llm_risks = json.loads(llm_response)
                    if not isinstance(llm_risks, list):
                        llm_risks = []
                except json.JSONDecodeError:
                    logger.warning("Failed to parse LLM risk analysis as JSON, using pattern-based only")
                    llm_risks = []
                    
            except Exception as e:
                logger.warning(f"LLM risk analysis failed: {str(e)}, using pattern-based only")
            
            # Combine and deduplicate risks
            all_risks = pattern_risks + llm_risks
            unique_risks = self._deduplicate_risks(all_risks)
            
            # Sort by severity
            severity_order = {"High": 0, "Medium": 1, "Low": 2}
            unique_risks.sort(key=lambda x: severity_order.get(x.get("severity", "Low"), 2))
            
            logger.info(f"Detected {len(unique_risks)} risks for {mapping_name}")
            return unique_risks
            
        except Exception as e:
            logger.error(f"Risk detection failed: {str(e)}")
            raise ModernizationError(f"Risk detection failed: {str(e)}") from e

    def _detect_pattern_risks(self, mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect risks using pattern matching (deterministic).
        
        Args:
            mapping: Canonical mapping model
            
        Returns:
            List of detected risks
        """
        risks = []
        transformations = mapping.get("transformations", [])
        
        for transformation in transformations:
            trans_name = transformation.get("name", "unknown")
            trans_type = transformation.get("type", "")
            
            # Check expression transformations
            if trans_type == "EXPRESSION":
                output_ports = transformation.get("output_ports", [])
                for port in output_ports:
                    field = port.get("name", "")
                    expression = port.get("expression", "").upper()
                    
                    # Check for risky patterns
                    if "CAST" in expression and "ISNULL" not in expression:
                        risks.append({
                            "category": "Data Quality",
                            "severity": "Medium",
                            "location": f"{trans_name}/{field}",
                            "risk": f"Type casting without null check in expression",
                            "impact": "NULL values may cause casting errors",
                            "recommendation": "Add null check before casting: IIF(ISNULL(field), NULL, CAST(...))"
                        })
                    
                    if "IIF" in expression and expression.count("IIF") > 3:
                        risks.append({
                            "category": "Maintainability",
                            "severity": "Medium",
                            "location": f"{trans_name}/{field}",
                            "risk": "Deeply nested IIF statements (more than 3 levels)",
                            "impact": "Difficult to understand and maintain, error-prone",
                            "recommendation": "Consider using DECODE or splitting into multiple transformations"
                        })
                    
                    if "DIVIDE" in expression or "/" in expression:
                        divisor_check = "ISNULL" in expression or "IIF" in expression
                        if not divisor_check:
                            risks.append({
                                "category": "Data Quality",
                                "severity": "High",
                                "location": f"{trans_name}/{field}",
                                "risk": "Division operation without zero/null check",
                                "impact": "Division by zero will cause runtime errors",
                                "recommendation": "Add zero check: IIF(divisor = 0 OR ISNULL(divisor), NULL, dividend / divisor)"
                            })
            
            # Check filter transformations
            elif trans_type == "FILTER":
                filter_cond = transformation.get("filter_condition", "")
                if not filter_cond:
                    risks.append({
                        "category": "Data Quality",
                        "severity": "Medium",
                        "location": trans_name,
                        "risk": "Filter transformation with no condition",
                        "impact": "All rows will be filtered out or behavior is undefined",
                        "recommendation": "Add proper filter condition"
                    })
            
            # Check aggregator transformations
            elif trans_type == "AGGREGATOR":
                group_by_fields = transformation.get("group_by_fields", [])
                if not group_by_fields:
                    risks.append({
                        "category": "Performance",
                        "severity": "Medium",
                        "location": trans_name,
                        "risk": "Aggregator without group-by fields",
                        "impact": "Will aggregate all rows into single row, may be unintended",
                        "recommendation": "Verify if single-row aggregation is intended, add group-by if needed"
                    })
        
        return risks

    def _deduplicate_risks(self, risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate risks based on location and risk description.
        
        Args:
            risks: List of risk objects
            
        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []
        
        for risk in risks:
            # Create a key from location and risk description
            key = (risk.get("location", ""), risk.get("risk", "")[:100])
            if key not in seen:
                seen.add(key)
                unique.append(risk)
        
        return unique
