
"""Code Fix Agent - LLM powered auto-correction of PySpark code"""
from llm.llm_manager import LLMManager

class CodeFixAgent:
    def __init__(self):
        self.llm = LLMManager()

    def fix(self, pyspark_code: str) -> str:
        prompt = f"""Fix errors and improve PySpark code:
{pyspark_code}
"""
        return self.llm.ask(prompt)
