
"""Rule Explainer Agent
LLM-powered agent to explain complex mapping rules.
"""

class RuleExplainerAgent:
    def __init__(self, llm=None):
        self.llm = llm

    def explain(self, mapping):
        explanations = []
        for ex in mapping.get("expressions", []):
            for field in ex.get("fields", []):
                explanations.append({
                    "field": field["name"],
                    "explanation": f"LLM explanation placeholder for: {field['expr']}"
                })
        return explanations
