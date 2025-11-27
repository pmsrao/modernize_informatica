
"""ADLS Connector — Production Stub"""
from azure.storage.blob import BlobClient

class ADLSConnector:
    def __init__(self, conn_str, container):
        self.conn_str = conn_str
        self.container = container

    def read(self, blob):
        client = BlobClient.from_connection_string(self.conn_str, self.container, blob)
        return client.download_blob().readall()
