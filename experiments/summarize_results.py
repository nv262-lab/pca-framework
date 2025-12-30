#!/usr/bin/env python3
import sys
import json
from pathlib import Path
import csv

def summarize(out_base: Path, csv_path: Path):
    full = out_base / "summary_full.csv"
    if full.exists():
        data = full.read_bytes()
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_bytes(data)
        print(f"Copied aggregate summary {full} to {csv_path}")
        return

    rows = []
    for cfg_dir in sorted(out_base.iterdir()):
        if not cfg_dir.is_dir():
            continue
        results_file = cfg_dir / "results.json"
        if not results_file.exists():
            continue
        try:
            data = json.loads(results_file.read_text())
        except Exception:
            continue
        for entry in data:
            q = entry.get("query", "")
            metrics = entry.get("metrics", {})
            poison_meta = entry.get("poison_meta", {})
            row = {
                "config": cfg_dir.name,
                "query": q,
                "verified": metrics.get("verified", 0),
                "verification_fail": metrics.get("verification_fail", 0),
                "attacks_reported": metrics.get("attacks_reported", 0),
                "elapsed_ms": metrics.get("elapsed_ms", None),
                "poison_strategy": poison_meta.get("strategy", ""),
                "poison_count": poison_meta.get("count", None)
            }
            rows.append(row)

    if not rows:
        print("No results found to summarize in", out_base)
        return

    fieldnames = ["config","query","verified","verification_fail","attacks_reported","elapsed_ms","poison_strategy","poison_count"]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"Wrote summary CSV to {csv_path}")

if _name_ == "_main_":
    if len(sys.argv) < 3:
        print("Usage: python experiments/summarize_results.py <out_base_dir> <csv_output_path>")
        sys.exit(1)
    out_base = Path(sys.argv[1])
    csv_out = Path(sys.argv[2])
    summarize(out_base, csv_out)
