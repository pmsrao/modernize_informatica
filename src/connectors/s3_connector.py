
"""S3 Connector — Production Stub"""
import boto3

class S3Connector:
    def __init__(self, bucket):
        self.bucket = bucket
        self.s3 = boto3.client("s3")

    def read(self, key):
        return self.s3.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def write(self, key, data):
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=data)
