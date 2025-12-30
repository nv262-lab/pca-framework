from typing import List, Dict, Tuple
from .provenance import verify_inclusion
import time

def compute_precision_recall_at_k(retrieved: List[Dict], corpus_index: Dict[str, Dict], k: int) -> Dict:
    topk = retrieved[:k]
    if not topk:
        return {"precision_at_k": 0.0, "recall_at_k": 0.0}
    relevant = 0
    total_relevant = sum(1 for v in corpus_index.values() if v.get("ground_truth", {}).get("attack"))
    for item in topk:
        doc = corpus_index.get(item["id"])
        if doc and doc.get("ground_truth", {}).get("attack"):
            relevant += 1
    precision = relevant / len(topk)
    recall = (relevant / total_relevant) if total_relevant > 0 else 0.0
    return {"precision_at_k": precision, "recall_at_k": recall, "relevant_found": relevant, "total_relevant": total_relevant}

def detect_hallucination(answer: Dict, corpus_index: Dict[str, Dict]) -> Dict:
    hallucinated_claims = 0
    unsupported_refs = 0
    evidence_attack = 0
    evidence_count = 0
    for ev in answer.get("evidence", []):
        evidence_count += 1
        doc = corpus_index.get(ev["id"])
        if not doc:
            unsupported_refs += 1
        else:
            if doc.get("ground_truth", {}).get("attack"):
                evidence_attack += 1
    text = answer.get("answer", "").lower()
    mentions_attack = "attack" in text or "compromis" in text
    if mentions_attack and evidence_attack == 0:
        hallucinated_claims = 1
    return {"hallucinated_claims": hallucinated_claims, "unsupported_refs": unsupported_refs, "evidence_attack_fraction": (evidence_attack/evidence_count if evidence_count>0 else 0.0)}

def check_answer_supported(answer: Dict, corpus_index: Dict[str, Dict]) -> Dict:
    start = time.time()
    results = {"verified": 0, "verification_fail": 0, "attacks_reported": 0}
    for ev in answer.get("evidence", []):
        pid = ev["id"]
        proof_wrapper = answer.get("proofs", {}).get(pid)
        if not proof_wrapper:
            results["verification_fail"] += 1
            continue
        leaf = proof_wrapper.get("leaf_hash")
        proof = proof_wrapper.get("proof")
        ok = verify_inclusion(leaf, proof, answer.get("root"))
        if ok:
            results["verified"] += 1
            doc = corpus_index.get(pid)
            if doc and doc.get("ground_truth", {}).get("attack"):
                results["attacks_reported"] += 1
        else:
            results["verification_fail"] += 1
    results["elapsed_ms"] = (time.time() - start) * 1000
    retrieved_list = [{"id": ev["id"], "rank": ev.get("rank", idx+1)} for idx, ev in enumerate(answer.get("evidence", []))]
    pr = compute_precision_recall_at_k(retrieved_list, corpus_index, k=len(retrieved_list))
    hall = detect_hallucination(answer, corpus_index)
    results.update(pr)
    results.update(hall)
    return results
