"""LLM integration layer."""
from .llm_manager import LLMManager
from .openai_client import OpenAIClient
from .azure_openai_client import AzureOpenAIClient
from .local_llm_client import LocalLLMClient
from .prompt_templates import (
    RULE_EXPLANATION_PROMPT,
    MAPPING_SUMMARY_PROMPT,
    RISK_ANALYSIS_PROMPT,
    TRANSFORMATION_SUGGESTION_PROMPT
)

__all__ = [
    "LLMManager",
    "OpenAIClient",
    "AzureOpenAIClient",
    "LocalLLMClient",
    "RULE_EXPLANATION_PROMPT",
    "MAPPING_SUMMARY_PROMPT",
    "RISK_ANALYSIS_PROMPT",
    "TRANSFORMATION_SUGGESTION_PROMPT"
]

