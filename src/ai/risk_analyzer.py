
"""AI Risk Analyzer — Production Style
Identifies risk areas in Informatica mappings.
"""

class AIRiskAnalyzer:
    def analyze(self, mapping):
        risks = []
        for ex in mapping.get("expressions", []):
            for f in ex.get("fields", []):
                if "CAST" in f["expr"].upper():
                    risks.append({"field": f["name"], "risk": "Potential type-cast issue"})
        return risks
