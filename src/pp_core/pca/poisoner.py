import os
import random
from typing import Iterator


def iter_corpus(directory: str) -> Iterator[str]:
    """Yield file paths of all files in directory."""
    for root, _, files in os.walk(directory):
        for fn in files:
            yield os.path.join(root, fn)


def poison_corpus(directory: str, trigger_phrase: str, n_poison: int = 1, prefix: str = "poison_"):
    """
    Create n_poison files in directory that contain the trigger_phrase.
    Each poison file is saved as prefix + random suffix + .txt.
    """
    os.makedirs(directory, exist_ok=True)
    created = []
    for i in range(n_poison):
        suffix = f"{random.getrandbits(32):08x}"
        fname = f"{prefix}{suffix}.txt"
        path = os.path.join(directory, fname)
        content = f"This document contains the backdoor trigger: {trigger_phrase}\n"
        content += "Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        created.append(path)
    return created
