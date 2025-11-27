
"""LLM-Based Risk Analysis Agent"""
import json
from llm.llm_manager import LLMManager
from llm.prompt_templates import RISK_ANALYSIS_PROMPT

class LLMRiskAnalysisAgent:
    def __init__(self):
        self.llm = LLMManager()

    def analyze(self, mapping):
        mapping_json = json.dumps(mapping, indent=2)
        prompt = RISK_ANALYSIS_PROMPT.format(mapping_json=mapping_json)
        return self.llm.ask(prompt)
