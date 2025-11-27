
"""Simulates execution workflow"""
from llm.llm_manager import LLMManager
import json

class WorkflowSimulationAgent:
    def __init__(self):
        self.llm = LLMManager()

    def simulate(self, workflow: dict):
        prompt = f"Simulate ETL workflow execution: {json.dumps(workflow)}"
        return self.llm.ask(prompt)
