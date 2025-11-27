
"""LLM Manager — Selects between OpenAI, Azure, or Local fallback"""
import os
from llm.openai_client import OpenAIClient
from llm.azure_openai_client import AzureOpenAIClient
from llm.local_llm_client import LocalLLMClient

class LLMManager:
    def __init__(self):
        provider = os.getenv("LLM_PROVIDER", "openai")

        if provider == "azure":
            self.client = AzureOpenAIClient()
        elif provider == "local":
            self.client = LocalLLMClient()
        else:
            self.client = OpenAIClient()

    def ask(self, prompt: str) -> str:
        return self.client.ask(prompt)
