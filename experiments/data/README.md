Dataset for small LLM experiments

Contents:
- articles/: short topical articles for retrieval/conditioning
- qna/: small JSONL with QA pairs (id, prompt, reference)
- dialogues/: simple dialog examples
- prompts/: evaluation prompts mapping to a specific target file
- metadata/: catalog describing files

Usage:
- Use prompts in prompts/prompts_for_eval.yaml to create RAG-style inputs by concatenating target file content as context.
- Save LLM predictions to experiments/out/llm_preds.jsonl (one JSON object per line: {"id":..., "prompt":..., "prediction":...}).
- Use experiments/multicloud/upload_to_cloud.py to push predictions or artifacts to cloud.
