import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer

from .provenance import sha256, make_index_snapshot_metadata

try:
    import faiss
    FAISS_AVAILABLE = True
except Exception:
    FAISS_AVAILABLE = False

class SimpleIndexer:
    def _init_(self, use_faiss: bool = FAISS_AVAILABLE, backend_name: Optional[str]=None):
        self.use_faiss = use_faiss and FAISS_AVAILABLE
        self.docs = []
        self.ids = []
        self.vec = None
        self.index = None
        self.tfidf = None
        self.embs = None
        self.backend_name = backend_name or ("faiss" if self.use_faiss else "tfidf")

    def _doc_text(self, doc: Dict) -> str:
        parts = [doc.get("event_type",""), doc.get("resource","")] + [str(v) for v in doc.get("payload",{}).values()]
        return " ".join(parts)

    def build(self, docs: List[Dict], **params):
        self.docs = docs
        self.ids = [d["id"] for d in docs]
        texts = [self._doc_text(d) for d in docs]
        self.tfidf = TfidfVectorizer(max_features=2048)
        X = self.tfidf.fit_transform(texts).astype("float32")
        self.embs = X.toarray()
        if self.use_faiss:
            d = self.embs.shape[1]
            self.index = faiss.IndexFlatIP(d)
            # normalization not strictly necessary for TF-IDF but kept for FAISS usage
            self.index.add(self.embs)
        else:
            self.index = None

        # store build params for metadata export
        self.build_params = params

    def query(self, q: str, topk: int = 5) -> List[Tuple[Dict, float]]:
        qv = self.tfidf.transform([q]).toarray().astype("float32")
        if self.use_faiss:
            import faiss
            # optionally normalize
            D, I = self.index.search(qv, topk)
            results = []
            for idx, score in zip(I[0], D[0]):
                if idx < 0: continue
                results.append((self.docs[idx], float(score)))
            return results
        else:
            sims = (self.embs @ qv.T).reshape(-1)
            order = np.argsort(-sims)[:topk]
            return [(self.docs[i], float(sims[i])) for i in order]

    def export_index_metadata(self, key: bytes = b"default-secret-key", extra: Dict = None) -> Dict:
        leaves = []
        for d in self.docs:
            core = {"id": d.get("id"), "provider": d.get("provider"), "timestamp": d.get("timestamp"),
                    "event_type": d.get("event_type"), "resource": d.get("resource"), "payload": d.get("payload")}
            leaves.append(sha256(json.dumps(core, sort_keys=True).encode("utf-8")))
        params = {"vector_dim": self.embs.shape[1] if self.embs is not None else None}
        params.update(getattr(self, "build_params", {}) or {})
        if extra:
            params.update(extra)
        meta = make_index_snapshot_metadata(leaves, backend=self.backend_name, params=params, key=key)
        meta["leaves"] = leaves
        return meta
