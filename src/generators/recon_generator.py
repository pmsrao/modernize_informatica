
"""Reconciliation Generator — Production Version"""
class ReconciliationGenerator:
    def generate(self, model):
        return "SELECT COUNT(*) AS row_count FROM {}".format(model["mapping_name"])
