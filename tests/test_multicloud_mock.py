import os
import tempfile
from unittest import mock

import pytest

from pca.multicloud import MultiCloudStore


def make_temp_file(tmp_path, name="t.txt", contents="hello"):
    p = tmp_path / name
    p.write_text(contents)
    return str(p)


@mock.patch("pca.multicloud.boto3")
def test_s3_upload_and_download(mock_boto3, tmp_path):
    client = mock.Mock()
    mock_boto3.client.return_value = client

    local = make_temp_file(tmp_path)
    store = MultiCloudStore(provider="s3", bucket="my-bucket")
    remote_key = "tests/t.txt"
    store.upload(local, remote_key)
    client.upload_file.assert_called_once_with(local, "my-bucket", remote_key)

    out = str(tmp_path / "down.txt")
    store.download(remote_key, out)
    client.download_file.assert_called_once_with("my-bucket", remote_key, out)


@mock.patch("pca.multicloud.gcs_storage")
def test_gcs_upload_and_download(mock_gcs, tmp_path):
    client = mock.Mock()
    mock_gcs.Client.return_value = client
    bucket = mock.Mock()
    client.bucket.return_value = bucket
    blob = mock.Mock()
    bucket.blob.return_value = blob

    local = make_temp_file(tmp_path, name="g.txt")
    store = MultiCloudStore(provider="gcs", bucket="gcs-bucket")
    remote_key = "g/tests.txt"
    store.upload(local, remote_key)
    bucket.blob.assert_called_once_with(remote_key)
    blob.upload_from_filename.assert_called_once_with(local)

    out = str(tmp_path / "gdown.txt")
    store.download(remote_key, out)
    blob.download_to_filename.assert_called_once_with(out)


@mock.patch("pca.multicloud.BlobServiceClient")
def test_azure_upload_and_download(mock_blob_service_client, tmp_path):
    client = mock.Mock()
    mock_blob_service_client.from_connection_string.return_value = client
    container = mock.Mock()
    client.get_container_client.return_value = container
    blob_client = mock.Mock()
    container.get_blob_client.return_value = blob_client
    class _Stream:
        def readall(self):
            return b"payload"
    blob_client.download_blob.return_value = _Stream()

    local = make_temp_file(tmp_path, name="a.txt", contents="abc")
    store = MultiCloudStore(provider="azure", bucket="container")
    remote_key = "a/abc.txt"
    store.upload(local, remote_key)
    container.upload_blob.assert_called_once()
    out = str(tmp_path / "adown.txt")
    store.download(remote_key, out)
    assert os.path.exists(out)
    assert open(out, "rb").read() == b"payload"
