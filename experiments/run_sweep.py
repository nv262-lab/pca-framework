#!/usr/bin/env python3
"""
Simple experiment runner:
- poison/synthesize corpus
- Build TF-IDF index
- Run queries and save results + index
"""
import os
import argparse
import json
import time
from pathlib import Path
import yaml

from pca import TfidfIndexer
from synth_corpus import make_corpus
from provenance import make_provenance_record, save_provenance
from pca.poisoner import poison_corpus, iter_corpus

def run(cfg):
    outdir = Path(cfg.get("output_dir", "experiments/out"))
    outdir.mkdir(parents=True, exist_ok=True)

    corpus_dir = cfg.get("corpus_dir", "experiments/data")
    # poisoning
    poison_cfg = cfg.get("poison", {}) or {}
    if poison_cfg.get("enabled"):
        poison_corpus(corpus_dir, poison_cfg.get("trigger", "TRIGGER"), n_poison=poison_cfg.get("n_poison", 1))

    idx = TfidfIndexer()
    idx.build_from_directory(corpus_dir)
    queries = cfg.get("queries", [])
    results = []
    for q in queries:
        res = idx.query(q, topk=5)
        results.append({"query": q, "hits": [{"path": p, "score": s} for p, s in res]})

    ts = int(time.time())
    results_path = outdir / f"results_{ts}.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "config": cfg}, f, indent=2)

    # save index
    idx_path = None
    if cfg.get("save_index", True):
        idx_path = outdir / cfg.get("index_filename", f"idx_{ts}.pkl")
        idx.save(str(idx_path))
        # optionally upload to cloud (multi-cloud)
        cloud = cfg.get("cloud", {}) or {}
        if cloud.get("enabled"):
            provider = cloud.get("provider")
            bucket = cloud.get("bucket")
            remote_key = cloud.get("remote_key_prefix", "") + Path(idx_path).name
            try:
                idx.save(str(idx_path), cloud_provider=provider, cloud_bucket=bucket, remote_key=remote_key)
            except Exception as e:
                print("Cloud upload failed:", e)

    # provenance
    prov = make_provenance_record("run_sweep", {"config_file": cfg.get("_source", "")})
    prov_path = outdir / f"provenance_{ts}.json"
    save_provenance(prov, str(prov_path))

    print("Wrote:", results_path, idx_path, prov_path)
    return {"results_path": str(results_path), "index_path": str(idx_path), "provenance_path": str(prov_path)}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    args = p.parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["_source"] = args.config
    run(cfg)

if _name_ == "_main_":
    main()
