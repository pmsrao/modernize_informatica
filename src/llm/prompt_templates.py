
"""Centralized Prompt Templates for LLM Agents"""

RULE_EXPLANATION_PROMPT = """
Explain the following Informatica expression in simple business terms:
{expr}
"""

MAPPING_SUMMARY_PROMPT = """
Summarize this mapping logic:
{mapping_json}
"""

RISK_ANALYSIS_PROMPT = """
Analyze the following mapping for potential risks:
{mapping_json}
"""

TRANSFORMATION_SUGGESTION_PROMPT = """
Suggest transformation optimizations for the expression:
{expr}
"""
