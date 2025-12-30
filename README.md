# pca-framework
Proof-Carrying Answers (PCA) Framework: reproducible toolkit for verifiable retrieval experiments. Includes synthetic corpus &amp; poisoning, TF‑IDF/FAISS indexing, Merkle + HMAC index snapshots, per-query PCA bundles with provenance, precision/recall/verification/hallucination metrics, grid-sweep runner, aggregated CSVs, and OpenAI LLM evaluation.

Project: Proof-Carrying Answers (PCA) Experiment Framework
================================================================

This repository implements a synthetic multi-cloud corpus generator, poisoning framework,
indexing & retrieval, Merkle-style cryptographic anchoring, Proof-Carrying Answer (PCA)
bundles with retrieval provenance, precision/recall/hallucination/verification metrics,
grid-sweep experiment runner that emits aggregated CSVs, and an optional LLM-based
evaluation harness using OpenAI.

Highlights
- Index snapshot HMAC signing (symmetric; configurable key).
- PCA JSON schema including index_snapshot and retrieval_provenance.
- Precision@k, Recall@k, hallucination detection, verification metrics (verified, verification_fail, attacks_reported).
- Proof generation time & verification latency measurement.
- Grid-sweep (cartesian product) runner and aggregate CSV experiments/out/summary_full.csv.
- Optional LLM evaluation harness (OpenAI) to measure model hallucination rates.
- GitHub Actions workflow for tests and a demo sweep.

Quick start (local)
-------------------
1. Create a Python environment (Python 3.9+ recommended).
2. Install dependencies:
   pip install -r requirements.txt

3. Run demo sweep (fast):
   python experiments/run_sweep.py experiments/configs/demo_small.yaml --out experiments/out

4. Summarize results:
   python experiments/summarize_results.py experiments/out experiments/out/summary.csv

5. Optional LLM evaluation:
   - Set env var: OPENAI_API_KEY
   - Set HMAC key: export PCA_HMAC_KEY="mysecret"
   - In config YAML, set verification.llm_eval: true and optionally llm.model/llm.max_tokens
   - Run the sweep; per-query PCA JSON includes llm_eval results when enabled.

Files of interest
- src/pp_core/provenance.py: Merkle + HMAC snapshot helpers.
- src/pp_core/indexer.py: TF-IDF / FAISS indexer + index metadata export.
- src/pp_core/pca.py: PCA bundle creation and deterministic assembler.
- src/pp_core/eval.py: precision/recall/hallucination/verification and timing.
- src/pp_core/llm_eval.py: optional LLM evaluator (OpenAI).
- experiments/run_sweep.py: grid sweep runner (writes PCA JSON per-query and aggregate CSV).

Security & keys
- Default HMAC key is a placeholder. Set env var PCA_HMAC_KEY or pass --hmac-key to run_sweep.py.
- OpenAI key must be set in OPENAI_API_KEY for LLM evaluation.

CI (GitHub Actions)
- The workflow runs tests and a small demo sweep (without LLM eval).
- To enable LLM in CI you must add OPENAI_API_KEY to repository secrets and adjust the workflow.

Paper results (outputs the repo will produce)
- Per-run: precision@k, recall@k, hallucinated_claims, unsupported_refs, verified, verification_fail, attacks_reported, proof generation time, verification latency, index snapshot metadata (leaf_count, root, hmac).
- Aggregated CSV: experiments/out/summary_full.csv (one row per query per config run).
- Per-query PCA JSONs: experiments/out/<run>/pca/<query_slug>.json containing PCA bundle, retrieval_provenance, metrics, and optional LLM outputs.
