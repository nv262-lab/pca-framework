from typing import Dict, List, Tuple, Any
from .provenance import canonicalize_doc, sha256
from .provenance import build_merkle_tree, inclusion_proof
import json
import time

def make_proof_bundle(docs: List[Dict], index_metadata: Dict = None) -> Dict:
    leaves = [sha256(canonicalize_doc(d)) for d in docs]
    root, layers = build_merkle_tree(leaves)
    proofs = {}
    for i, d in enumerate(docs):
        proofs[d["id"]] = {
            "leaf_hash": leaves[i],
            "proof": inclusion_proof(i, layers),
            "index_pos": i
        }
    bundle = {"root": root, "leaves": leaves, "proofs": proofs, "generated_at": time.time()}
    if index_metadata:
        bundle["index_snapshot"] = index_metadata
    return bundle

def assemble_answer(query: str, retrieved: List[Tuple[Dict,float]], proof_bundle: Dict, retrieval_backend: Dict = None) -> Dict:
    items = []
    for rank, (doc, score) in enumerate(retrieved, start=1):
        items.append({
            "id": doc["id"],
            "resource": doc.get("resource"),
            "timestamp": doc.get("timestamp"),
            "score": score,
            "rank": rank
        })
    answer_text = f"Query: {query}\nTop-{len(items)} evidence:\n" + \
                  "\n".join([f"- {i['id']} {i['resource']} @{i['timestamp']} (score={i['score']:.4f})" for i in items])
    proofs = {item["id"]: proof_bundle["proofs"].get(item["id"]) for item in items}
    pca = {
        "answer": answer_text,
        "evidence": items,
        "root": proof_bundle.get("root"),
        "proofs": proofs,
        "index_snapshot": proof_bundle.get("index_snapshot"),
        "retrieval_provenance": retrieval_backend or {"backend": "unknown", "params": {}, "timestamp": time.time()},
        "generated_at": time.time()
    }
    return pca
