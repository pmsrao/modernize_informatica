
"""Model Serializer — Production Grade
Serializes canonical model for downstream usage.
"""
import json

class ModelSerializer:
    def serialize(self, model):
        return json.dumps(model, indent=2)
