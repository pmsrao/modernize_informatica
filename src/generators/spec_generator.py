
"""Spec Generator — Production Version"""
class SpecGenerator:
    def generate(self, model):
        spec = [f"# Mapping: {model['mapping_name']}"]
        for src in model.get("sources", []):
            spec.append(f"* Source: {src['name']} ({src['table']})")
        for tgt in model.get("targets", []):
            spec.append(f"* Target: {tgt['name']} ({tgt['table']})")
        for ex in model.get("expressions", []):
            spec.append(f"## Expression: {ex['name']}")
            for f in ex["fields"]:
                spec.append(f"- {f['name']} = {f['expr']}")
        return "\n".join(spec)
