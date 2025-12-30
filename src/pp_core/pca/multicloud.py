import os
from typing import Optional

# S3 (boto3)
try:
    import boto3
except Exception:
    boto3 = None

# GCS (google-cloud-storage)
try:
    from google.cloud import storage as gcs_storage
except Exception:
    gcs_storage = None

# Azure Blob
try:
    from azure.storage.blob import BlobServiceClient
except Exception:
    BlobServiceClient = None


class MultiCloudStore:
    def _init_(self, provider: str, bucket: str, project: Optional[str] = None, account_url: Optional[str] = None):
        self.provider = provider.lower()
        self.bucket = bucket
        self.project = project
        self.account_url = account_url

    def upload(self, local_path: str, remote_key: str) -> str:
        if self.provider == "s3":
            if boto3 is None:
                raise RuntimeError("boto3 not installed")
            s3 = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=os.getenv("AWS_SESSION_TOKEN")
            )
            s3.upload_file(local_path, self.bucket, remote_key)
            return f"s3://{self.bucket}/{remote_key}"

        if self.provider == "gcs":
            if gcs_storage is None:
                raise RuntimeError("google-cloud-storage not installed")
            client = gcs_storage.Client(project=self.project) if self.project else gcs_storage.Client()
            bucket = client.bucket(self.bucket)
            blob = bucket.blob(remote_key)
            blob.upload_from_filename(local_path)
            return f"gs://{self.bucket}/{remote_key}"

        if self.provider == "azure":
            if BlobServiceClient is None:
                raise RuntimeError("azure-storage-blob not installed")
            conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            if not conn_str and self.account_url:
                client = BlobServiceClient(account_url=self.account_url, credential=os.getenv("AZURE_STORAGE_KEY"))
            else:
                client = BlobServiceClient.from_connection_string(conn_str)
            container_client = client.get_container_client(self.bucket)
            with open(local_path, "rb") as stream:
                container_client.upload_blob(name=remote_key, data=stream, overwrite=True)
            return f"https://{self.account_url or client.account_name}.blob.core.windows.net/{self.bucket}/{remote_key}"

        raise ValueError("Unsupported provider: " + self.provider)

    def download(self, remote_key: str, local_path: str) -> str:
        if self.provider == "s3":
            if boto3 is None:
                raise RuntimeError("boto3 not installed")
            s3 = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=os.getenv("AWS_SESSION_TOKEN")
            )
            s3.download_file(self.bucket, remote_key, local_path)
            return local_path

        if self.provider == "gcs":
            if gcs_storage is None:
                raise RuntimeError("google-cloud-storage not installed")
            client = gcs_storage.Client(project=self.project) if self.project else gcs_storage.Client()
            bucket = client.bucket(self.bucket)
            blob = bucket.blob(remote_key)
            blob.download_to_filename(local_path)
            return local_path

        if self.provider == "azure":
            if BlobServiceClient is None:
                raise RuntimeError("azure-storage-blob not installed")
            conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            if not conn_str and self.account_url:
                client = BlobServiceClient(account_url=self.account_url, credential=os.getenv("AZURE_STORAGE_KEY"))
            else:
                client = BlobServiceClient.from_connection_string(conn_str)
            container_client = client.get_container_client(self.bucket)
            blob_client = container_client.get_blob_client(remote_key)
            stream = blob_client.download_blob()
            with open(local_path, "wb") as f:
                f.write(stream.readall())
            return local_path

        raise ValueError("Unsupported provider: " + self.provider)
