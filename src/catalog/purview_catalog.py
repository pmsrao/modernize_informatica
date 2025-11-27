
"""Purview Catalog Adapter"""
class PurviewCatalog:
    def register_mapping(self, mapping):
        return {"mapping": mapping["mapping_name"], "status": "registered"}
