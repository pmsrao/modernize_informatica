
"""Impact analysis agent"""
from llm.llm_manager import LLMManager
import json

class ImpactAnalysisAgent:
    def __init__(self):
        self.llm = LLMManager()

    def analyze(self, mapping_model: dict):
        prompt = f"Identify impact of changing mapping: {json.dumps(mapping_model)}"
        return self.llm.ask(prompt)
