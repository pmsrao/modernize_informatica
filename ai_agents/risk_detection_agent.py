
"""Risk Detection Agent
Analyzes mapping for potential issues.
"""

class RiskDetectionAgent:
    def __init__(self, llm=None):
        self.llm = llm

    def detect_risks(self, mapping):
        risks = []
        for ex in mapping.get("expressions", []):
            for field in ex.get("fields", []):
                if "CAST" in field["expr"].upper():
                    risks.append({"field": field["name"], "risk": "Possible casting issue"})
        return risks
