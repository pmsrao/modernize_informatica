
"""LLM-Based Transformation Suggestion Agent"""
from llm.llm_manager import LLMManager
from llm.prompt_templates import TRANSFORMATION_SUGGESTION_PROMPT

class LLMTransformationSuggestionAgent:
    def __init__(self):
        self.llm = LLMManager()

    def suggest(self, expr):
        prompt = TRANSFORMATION_SUGGESTION_PROMPT.format(expr=expr)
        return self.llm.ask(prompt)
