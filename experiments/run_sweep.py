#!/usr/bin/env python3
import argparse
import yaml
import json
from pathlib import Path
from itertools import product
from copy import deepcopy
from pp_core.synth_corpus import generate_corpus
from pp_core.poisoner import load_corpus, insert_poison, save_corpus
from pp_core.indexer import SimpleIndexer
from pp_core.pca import make_proof_bundle, assemble_answer
from pp_core.eval import check_answer_supported
from pp_core.llm_eval import llm_query
import os

def expand_grid(cfg: dict):
    keys = []
    values = []
    candidates = {}
    for section in ["corpus","poison","index","query","verification","llm"]:
        sec = cfg.get(section, {})
        if isinstance(sec, dict):
            for k,v in sec.items():
                composite = f"{section}.{k}"
                candidates[composite] = v
        elif sec is not None:
            composite = section
            candidates[composite] = sec
    exp_keys = []
    exp_lists = []
    for k,v in candidates.items():
        if isinstance(v, list):
            exp_keys.append(k)
            exp_lists.append(v)
    if not exp_keys:
        return [cfg]
    combos = []
    for combo in product(*exp_lists):
        new = deepcopy(cfg)
        for key, val in zip(exp_keys, combo):
            section, _, sub = key.partition(".")
            if sub:
                if section not in new: new[section] = {}
                new[section][sub] = val
            else:
                new[section] = val
        combos.append(new)
    return combos

def run_single(cfg: dict, out_dir: Path, hmac_key: bytes = b"default-secret-key"):
    out_dir.mkdir(parents=True, exist_ok=True)
    corpus_path = out_dir / "sample_corpus.jsonl"
    poisoned_path = out_dir / "poisoned_corpus.jsonl"

    per_provider = cfg.get("corpus", {}).get("per_provider", 100)
    seed = cfg.get("corpus", {}).get("seed", 0)
    generate_corpus(str(corpus_path), per_provider=per_provider, seed=seed)

    docs = load_corpus(str(corpus_path))
    pconf = cfg.get("poison", {})
    strategy = pconf.get("strategy", "insert")
    rate = float(pconf.get("rate", 0.0))
    seed = int(pconf.get("seed", 0))
    poisoned_docs, meta = insert_poison(docs, rate=rate, strategy=strategy, seed=seed)
    save_corpus(poisoned_docs, str(poisoned_path))

    idx_conf = cfg.get("index", {})
    use_faiss = bool(idx_conf.get("use_faiss", False))
    indexer = SimpleIndexer(use_faiss=use_faiss)
    indexer.build(poisoned_docs)

    index_meta = indexer.export_index_metadata(key=hmac_key, extra={"config_name": cfg.get("name", "")})

    proof_bundle = make_proof_bundle(poisoned_docs, index_metadata=index_meta)
    corpus_index = {d["id"]: d for d in poisoned_docs}

    queries = cfg.get("query", {}).get("queries", ["suspicious object_put"])
    topk = int(cfg.get("query", {}).get("topk", cfg.get("topk", 5)))
    results = []
    per_query_dir = out_dir / "pca"
    per_query_dir.mkdir(exist_ok=True)
    for q in queries:
        retrieved = indexer.query(q, topk=topk)
        pca = assemble_answer(q, retrieved, proof_bundle, retrieval_backend={"backend": indexer.backend_name, "params": getattr(indexer, "build_params", {})})
        metrics = check_answer_supported(pca, corpus_index)
        # optional LLM evaluation
        llm_cfg = cfg.get("llm", {}) or {}
        if cfg.get("verification", {}).get("llm_eval", False):
            prompt = f"Given the answer and evidence:\n\n{pca['answer']}\n\nIs the claim that 'attack' occurred supported by the evidence? Provide YES/NO and brief justification."
            try:
                resp = llm_query(prompt, model=llm_cfg.get("model","gpt-3.5-turbo"), max_tokens=llm_cfg.get("max_tokens", 128))
                pca["llm_eval"] = resp
            except Exception as e:
                pca["llm_eval_error"] = str(e)
        entry = {"query": q, "pca": pca, "metrics": metrics, "poison_meta": meta, "index_meta": index_meta}
        results.append(entry)
        slug = q.replace(" ", "_")[:80]
        (per_query_dir / f"{slug}.json").write_text(json.dumps(entry, indent=2))
    out_file = out_dir / "results.json"
    out_file.write_text(json.dumps(results, indent=2))
    return results

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config", nargs="?", help="Path to YAML config file or directory")
    ap.add_argument("--out", "-o", default="experiments/out", help="Output base directory")
    ap.add_argument("--hmac-key", default=None, help="Optional HMAC key. If omitted, uses PCA_HMAC_KEY env or default.")
    args = ap.parse_args()

    if not args.config:
        print("Provide a config file or directory.")
        return

    cfg_path = Path(args.config)
    out_base = Path(args.out)
    if args.hmac_key:
        hmac_key = args.hmac_key.encode("utf-8")
    else:
        hmac_key = os.environ.get("PCA_HMAC_KEY", "default-secret-key").encode("utf-8")

    configs_to_run = []
    if cfg_path.is_dir():
        for p in sorted(cfg_path.glob("*.yaml")):
            raw = yaml.safe_load(p.read_text())
            combos = expand_grid(raw)
            for i, c in enumerate(combos):
                c["name"] = f"{p.stem}_run{i}"
                configs_to_run.append((c, out_base / f"{p.stem}_run{i}"))
    else:
        raw = yaml.safe_load(cfg_path.read_text())
        combos = expand_grid(raw)
        for i, c in enumerate(combos):
            c["name"] = f"{cfg_path.stem}_run{i}"
            configs_to_run.append((c, out_base / f"{cfg_path.stem}_run{i}"))

    aggregate_rows = []
    for cfg, out_dir in configs_to_run:
        print("Running config:", cfg.get("name"), "->", out_dir)
        results = run_single(cfg, out_dir, hmac_key=hmac_key)
        for r in results:
            row = {
                "config": cfg.get("name"),
                "query": r.get("query"),
                "verified": r["metrics"].get("verified"),
                "verification_fail": r["metrics"].get("verification_fail"),
                "attacks_reported": r["metrics"].get("attacks_reported"),
                "elapsed_ms": r["metrics"].get("elapsed_ms"),
                "precision_at_k": r["metrics"].get("precision_at_k"),
                "recall_at_k": r["metrics"].get("recall_at_k"),
                "hallucinated_claims": r["metrics"].get("hallucinated_claims"),
                "unsupported_refs": r["metrics"].get("unsupported_refs"),
                "poison_strategy": r.get("poison_meta", {}).get("strategy"),
                "poison_count": r.get("poison_meta", {}).get("count"),
                "index_backend": r.get("index_meta", {}).get("backend")
            }
            aggregate_rows.append(row)
    import csv
    out_csv = out_base / "summary_full.csv"
    if aggregate_rows:
        fieldnames = list(aggregate_rows[0].keys())
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        with open(out_csv, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for rr in aggregate_rows:
                writer.writerow(rr)
        print("Wrote aggregate summary to", out_csv)
    else:
        print("No runs produced aggregate rows.")

if _name_ == "_main_":
    main()
