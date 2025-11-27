
"""GCS Connector — Production Stub"""
from google.cloud import storage

class GCSConnector:
    def __init__(self, bucket):
        self.bucket = bucket
        self.client = storage.Client()

    def read(self, blob):
        return self.client.bucket(self.bucket).blob(blob).download_as_bytes()
