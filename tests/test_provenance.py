from pp_core.provenance import sha256, canonicalize_doc, build_merkle_tree, verify_inclusion, inclusion_proof, make_index_snapshot_metadata

def test_merkle_roundtrip():
    docs = [{"id":"a","x":1},{"id":"b","x":2},{"id":"c","x":3}]
    leaves = [sha256(canonicalize_doc(d)) for d in docs]
    root, layers = build_merkle_tree(leaves)
    pf = inclusion_proof(1, layers)
    ok = verify_inclusion(leaves[1], pf, root)
    assert ok

def test_index_snapshot_hmac():
    leaves = ["aa","bb","cc"]
    meta = make_index_snapshot_metadata(leaves, backend="tfidf", params={"m":1}, key=b"testkey")
    assert "hmac" in meta
    assert
