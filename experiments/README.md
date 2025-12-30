Experiments
===========

This folder holds small reproducible experiments and scripts.

Layout
- configs/: experiment configurations (YAML)
- data/: small sample corpora
- out/: outputs (indexes, results). Add to .gitignore in main repo for large artifacts.
- multicloud/: docs for cloud upload/download
- run_sweep.py: simple runner for experiments
- summarize_results.py: aggregator to summarize JSON result files

Usage
1. Prepare environment (install package and deps).
2. Optionally synthesize or add files to experiments/data/.
3. Run a demo sweep:
   python experiments/run_sweep.py --config experiments/configs/demo_small.yaml
4. Summarize results:
   python experiments/summarize_results.py --dir experiments/out
