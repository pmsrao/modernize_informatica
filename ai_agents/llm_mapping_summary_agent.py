
"""LLM-Powered Mapping Summary Agent"""
import json
from llm.llm_manager import LLMManager
from llm.prompt_templates import MAPPING_SUMMARY_PROMPT

class LLMMappingSummaryAgent:
    def __init__(self):
        self.llm = LLMManager()

    def summarize(self, mapping):
        mapping_json = json.dumps(mapping, indent=2)
        prompt = MAPPING_SUMMARY_PROMPT.format(mapping_json=mapping_json)
        return self.llm.ask(prompt)
