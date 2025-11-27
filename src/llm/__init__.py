"""LLM integration layer."""
from llm.llm_manager import LLMManager
from llm.openai_client import OpenAIClient
from llm.azure_openai_client import AzureOpenAIClient
from llm.local_llm_client import LocalLLMClient
from llm.prompt_templates import (
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

