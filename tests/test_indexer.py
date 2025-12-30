import os
import pickle
from unittest import mock

import numpy as np
from pca import TfidfIndexer


def make_docs(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.txt").write_text("apple banana apple")
    (d / "b.txt").write_text("banana orange")
    return str(d)


def test_build_query_save_load(tmp_path):
    d = make_docs(tmp_path)
    idx = TfidfIndexer()
    idx.build_from_directory(d)
    res = idx.query("apple")
    assert isinstance(res, list)
    assert len(res) >= 1
    out = str(tmp_path / "idx.pkl")
    idx.save(out)
    assert os.path.exists(out)
    loaded = TfidfIndexer.load(out)
    assert isinstance(loaded, TfidfIndexer)
    assert loaded.vocabulary_


@mock.patch("pca.indexer.MultiCloudStore")
def test_save_with_cloud_upload_calls_store(mock_store_cls, tmp_path):
    d = make_docs(tmp_path)
    idx = TfidfIndexer()
    idx.build_from_directory(d)
    out = str(tmp_path / "idx_cloud.pkl")
    mock_store = mock.Mock()
    mock_store_cls.return_value = mock_store

    idx.save(out, cloud_provider="s3", cloud_bucket="bucket", remote_key="k.pkl")
    mock_store_cls.assert_called_once_with(provider="s3", bucket="bucket")
    mock_store.upload.assert_called_once_with(out, "k.pkl")
    assert os.path.exists(out)


@mock.patch("pca.indexer.MultiCloudStore")
def test_load_from_cloud_uses_store_and_loads(mock_store_cls, tmp_path):
    # Prepare a local pickle to be "downloaded"
    dummy_idx = TfidfIndexer()
    dummy_idx.vectorizer = None
    local_tmp = str(tmp_path / "downloaded.pkl")
    with open(local_tmp, "wb") as f:
        pickle.dump(dummy_idx, f)

    mock_store = mock.Mock()
    # make download write the prepared file path when called
    def download(remote_key, local_path):
        # copy prepared file to requested local_path
        with open(local_tmp, "rb") as r, open(local_path, "wb") as w:
            w.write(r.read())
        return local_path

    mock_store.download.side_effect = download
    mock_store_cls.return_value = mock_store

    loaded = TfidfIndexer.load_from_cloud("s3", "bucket", "remote.pkl", local_tmp=None)
    assert isinstance(loaded, TfidfIndexer)
    mock_store_cls.assert_called_once_with(provider="s3", bucket="bucket")
    mock_store.download.assert_called()
