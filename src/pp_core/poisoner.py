import json
import random
from typing import List, Tuple, Dict
from pathlib import Path
import copy
import uuid

def load_corpus(path: str) -> List[Dict]:
    docs = []
    with open(path, "r") as fh:
        for line in fh:
            docs.append(json.loads(line))
    return docs

def save_corpus(docs: List[Dict], path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        for d in docs:
            fh.write(json.dumps(d) + "\n")

def insert_poison(docs: List[Dict], rate: float = 0.01, strategy: str = "insert", seed: int = 0) -> Tuple[List[Dict], Dict]:
    random.seed(seed)
    n = len(docs)
    num_poison = max(1, int(n * rate)) if rate > 0 else 0
    poisoned = docs[:]
    meta = {"strategy": strategy, "rate": rate, "count": num_poison}
    if strategy == "insert" and num_poison > 0:
        for i in range(num_poison):
            attacker_doc = copy.deepcopy(random.choice(docs))
            attacker_doc["id"] = str(uuid.uuid4())
            attacker_doc["provider"] = "attacker"
            attacker_doc["ground_truth"]["attack"] = True
            attacker_doc["event_type"] = "object_put"
            attacker_doc["payload"] = {"detail": "malicious payload", "marker": f"poison_{i}"}
            poisoned.append(attacker_doc)
    elif strategy == "mutate" and num_poison > 0:
        idxs = random.sample(range(len(poisoned)), num_poison)
        for i, idx in enumerate(idxs):
            poisoned[idx]["payload"]["marker"] = f"mut{seed}_{i}"
            poisoned[idx]["ground_truth"]["attack"] = True
    # other strategies can be added
    return poisoned, meta
