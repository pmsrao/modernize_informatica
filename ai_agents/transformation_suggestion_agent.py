
"""Transformation Suggestion Agent
Suggests optimizations or modernized transformations.
"""

class TransformationSuggestionAgent:
    def __init__(self, llm=None):
        self.llm = llm

    def suggest(self, mapping):
        suggestions = []
        for ex in mapping.get("expressions", []):
            for field in ex.get("fields", []):
                suggestions.append({
                    "field": field["name"],
                    "suggestion": f"Consider optimizing expression: {field['expr']}"
                })
        return suggestions
