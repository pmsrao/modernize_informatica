
"""Glue Catalog Adapter"""
import boto3

class GlueCatalog:
    def __init__(self):
        self.glue = boto3.client("glue")

    def register_table(self, db, table, schema):
        return {"db": db, "table": table, "status": "registered"}
