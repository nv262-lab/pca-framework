"""
Small utilities to synthesize toy corpora for experiments.
"""
import os
from typing import List

def make_corpus(directory: str, texts: List[str]):
    os.makedirs(directory, exist_ok=True)
    paths = []
    for i, t in enumerate(texts):
        p = os.path.join(directory, f"doc_{i}.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write(t)
        paths.append(p)
    return paths
