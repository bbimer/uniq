# profiler/storage/experiment_store.py
import os
import json
import time
import uuid
from typing import Dict, Any, Optional, List
from profiler.core.fingerprint import FingerprintVector

DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DEFAULT_JSONL_PATH = os.path.join(DEFAULT_DATA_DIR, "experiments.jsonl")

class ExperimentStore:
    def __init__(self, file_path: str = DEFAULT_JSONL_PATH):
        self.file_path = file_path
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def log_fingerprint(self, fp: FingerprintVector, variant_of: Optional[str] = None) -> str:
        exp_id = f"exp_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        record = {
            "experiment_id": exp_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "file_name": os.path.basename(fp.file_path),
            "file_path": fp.file_path,
            "source_hash": variant_of or fp.file_hash,
            "variant_hash": fp.file_hash,
            "fingerprint": fp.to_dict(),
            "outcomes": {
                "views_1h": None,
                "views_24h": None,
                "avg_watch_time": None,
                "completion_rate": None,
                "shares": None,
                "saves": None,
                "recommendation_reach": None
            }
        }

        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=True) + "\n")

        return exp_id

    def update_outcomes(self, exp_id: str, outcomes: Dict[str, Any]) -> bool:
        if not os.path.isfile(self.file_path):
            return False

        records = []
        updated = False
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("experiment_id") == exp_id:
                    for k, v in outcomes.items():
                        if k in rec["outcomes"] and v is not None:
                            rec["outcomes"][k] = v
                    updated = True
                records.append(rec)

        if updated:
            with open(self.file_path, "w", encoding="utf-8") as f:
                for rec in records:
                    f.write(json.dumps(rec, ensure_ascii=True) + "\n")

        return updated

    def list_experiments(self) -> List[Dict[str, Any]]:
        if not os.path.isfile(self.file_path):
            return []
        records = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records
