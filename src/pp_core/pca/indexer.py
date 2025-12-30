import os
import pickle
import tempfile
from typing import List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from pca.multicloud import MultiCloudStore


class TfidfIndexer:
    """
    Simple TF-IDF indexer with local save/load and optional multi-cloud upload/download.
    """
    def _init_(self):
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.doc_paths: List[str] = []
        self.vocabulary_: dict = {}

    def build_from_directory(self, directory: str, pattern: Optional[str] = None):
        docs = []
        paths = []
        for root, _, files in os.walk(directory):
            for fn in files:
                if pattern and pattern not in fn:
                    continue
                path = os.path.join(root, fn)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        docs.append(f.read())
                    paths.append(path)
                except Exception:
                    continue
        if not docs:
            raise ValueError("No documents found to build index.")
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(docs)
        self.doc_paths = paths
        self.vocabulary_ = dict(self.vectorizer.vocabulary_)

    def query(self, text: str, topk: int = 5) -> List[Tuple[str, float]]:
        if self.vectorizer is None or self.tfidf_matrix is None:
            raise ValueError("Index not built or loaded.")
        qv = self.vectorizer.transform([text])
        scores = (self.tfidf_matrix @ qv.T).toarray().ravel()
        idxs = np.argsort(-scores)[:topk]
        results = []
        for i in idxs:
            if scores[i] <= 0.0:
                continue
            results.append((self.doc_paths[i], float(scores[i])))
        return results

    def save(self, path: str, cloud_provider: Optional[str] = None, cloud_bucket: Optional[str] = None, remote_key: Optional[str] = None):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)
        if cloud_provider and cloud_bucket and remote_key:
            store = MultiCloudStore(provider=cloud_provider, bucket=cloud_bucket)
            store.upload(path, remote_key)

    @classmethod
    def load(cls, path: str):
        with open(path, "rb") as f:
            obj = pickle.load(f)
        if not isinstance(obj, TfidfIndexer):
            raise ValueError("Pickle does not contain a TfidfIndexer")
        return obj

    @classmethod
    def load_from_cloud(cls, cloud_provider: str, cloud_bucket: str, remote_key: str, local_tmp: Optional[str] = None):
        tmp = local_tmp or tempfile.mktemp(suffix=".pkl")
        store = MultiCloudStore(provider=cloud_provider, bucket=cloud_bucket)
        store.download(remote_key, tmp)
        try:
            obj = cls.load(tmp)
        finally:
            try:
                if not local_tmp and os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
        return obj
