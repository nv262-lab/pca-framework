#!/usr/bin/env python3
"""
Aggregate results JSON files in a directory and print a small summary.
"""
import argparse
import json
import os
from pathlib import Path
from statistics import mean

def summarize_dir(d):
    d = Path(d)
    files = sorted([p for p in d.iterdir() if p.name.startswith("results_") and p.suffix == ".json"])
    summary = {"n_runs": len(files), "queries": {}, "files": [str(p) for p in files]}
    for p in files:
        j = json.load(open(p, "r", encoding="utf-8"))
        for entry in j.get("results", []):
            q = entry.get("query")
            hits = entry.get("hits", [])
            if q not in summary["queries"]:
                summary["queries"][q] = {"n": 0, "avg_hits": []}
            summary["queries"][q]["n"] += 1
            summary["queries"][q]["avg_hits"].append(len(hits))
    # convert lists to averages
    for q, info in summary["queries"].items():
        info["mean_hits"] = mean(info["avg_hits"]) if info["avg_hits"] else 0.0
        del info["avg_hits"]
    return summary

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default="experiments/out")
    args = p.parse_args()
    s = summarize_dir(args.dir)
    print(json.dumps(s, indent=2))

if _name_ == "_main_":
    main()
