"""
Simple provenance tracking helpers.
"""
import json
import time
from typing import Dict, Any

def make_provenance_record(action: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    rec = {
        "action": action,
        "timestamp": time.time(),
        "metadata": metadata
    }
    return rec

def save_provenance(record: Dict[str, Any], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
