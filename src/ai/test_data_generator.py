
"""AI-Based Test Data Generator (Simplified)
Generates minimal mock data based on field names.
"""

class AITestDataGenerator:
    def generate(self, mapping):
        rows = {}
        for src in mapping.get("sources", []):
            for f in src.get("fields", []):
                rows[f] = "sample_value"
        return [rows]
