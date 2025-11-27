
"""Azure OpenAI Client Wrapper — Production Style"""
import os
from openai import AzureOpenAI

class AzureOpenAIClient:
    def __init__(self, deployment="gpt-4o-mini"):
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        key = os.getenv("AZURE_OPENAI_KEY")
        self.client = AzureOpenAI(api_key=key, azure_endpoint=endpoint, api_version="2024-02-01")
        self.deployment = deployment

    def ask(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.deployment,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content
