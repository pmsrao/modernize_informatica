
"""Mapping Summary Agent
Generates human-readable summary of mapping logic.
"""

class MappingSummaryAgent:
    def __init__(self, llm=None):
        self.llm = llm

    def summarize(self, mapping):
        name = mapping.get("mapping_name")
        sources = [s["name"] for s in mapping.get("sources",[])]
        targets = [t["name"] for t in mapping.get("targets",[])]
        return {
            "mapping": name,
            "summary": f"Mapping {name} reads from {sources} and writes to {targets}."
        }
