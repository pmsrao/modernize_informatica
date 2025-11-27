
"""LLM-Powered Rule Explainer Agent"""
from llm.llm_manager import LLMManager
from llm.prompt_templates import RULE_EXPLANATION_PROMPT

class LLMRuleExplainerAgent:
    def __init__(self):
        self.llm = LLMManager()

    def explain(self, expr: str):
        prompt = RULE_EXPLANATION_PROMPT.format(expr=expr)
        return self.llm.ask(prompt)
