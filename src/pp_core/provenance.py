import hashlib
import hmac
import json
import time
from typing import List, Tuple, Dict, Optional

HMAC_KEY_DEFAULT = b"default-secret-key"  # override via PCA_HMAC_KEY env or pass to functions

def canonicalize_doc(doc: dict) -> bytes:
    return json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def hmac_sha256_hex(key: bytes, data: bytes) -> str:
    return hmac.new(key, data, hashlib.sha256).hexdigest()

def build_merkle_tree(digests: List[str]) -> Tuple[str, List[List[str]]]:
    layers = []
    current = digests[:]
    layers.append(current)
    while len(current) > 1:
        next_layer = []
        for i in range(0, len(current), 2):
            left = current[i]
            right = current[i+1] if i+1 < len(current) else current[i]
            combined = (left + right).encode("utf-8")
            next_layer.append(sha256(combined))
        current = next_layer
        layers.append(current)
    root = layers[-1][0] if layers and layers[-1] else ""
    return root, layers

def inclusion_proof(index: int, layers: List[List[str]]) -> List[Tuple[str,str]]:
    proof = []
    idx = index
    for layer in layers:
        if len(layer) == 1:
            break
        sibling_idx = idx -1 if idx % 2 else idx + 1
        if sibling_idx >= len(layer):
            sibling_hash = layer[idx]
            pos = 'R' if idx % 2 == 0 else 'L'
        else:
            sibling_hash = layer[sibling_idx]
            pos = 'L' if sibling_idx < idx else 'R'
        proof.append((sibling_hash, pos))
        idx = idx // 2
    return proof

def verify_inclusion(leaf_hash: str, proof: List[Tuple[str,str]], root: str) -> bool:
    cur = leaf_hash
    for sibling, pos in proof:
        if pos == 'L':
            cur = sha256((sibling + cur).encode('utf-8'))
        else:
            cur = sha256((cur + sibling).encode('utf-8'))
    return cur == root

def make_index_snapshot_metadata(leaves: List[str], backend: str, params: Dict, key: bytes = HMAC_KEY_DEFAULT, timestamp: Optional[float]=None) -> Dict:
    if timestamp is None:
        timestamp = time.time()
    root, layers = build_merkle_tree(leaves)
    leaves_concat = "".join(leaves).encode("utf-8")
    leaves_digest = sha256(leaves_concat)
    meta = {
        "leaf_count": len(leaves),
        "root": root,
        "leaves_digest": leaves_digest,
        "backend": backend,
        "params": params,
        "timestamp": timestamp
    }
    canon = json.dumps(meta, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = hmac_sha256_hex(key, canon)
    meta["hmac"] = signature
    return meta
