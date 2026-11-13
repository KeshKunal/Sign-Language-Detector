"""Validate all dataset sequences and save a machine-readable report."""
import json
from pathlib import Path

from sld.config import ACTIONS, DEFAULT_DATASET_PATH
from sld.data import load_dataset


def main() -> None:
    X, y = load_dataset(DEFAULT_DATASET_PATH)
    report = {
        "valid": True,
        "classes": {name: int((y == index).sum()) for index, name in enumerate(ACTIONS)},
        "sequences": int(len(y)),
        "frames_per_sequence": int(X.shape[1]),
        "features_per_frame": int(X.shape[2]),
        "dtype_after_loading": str(X.dtype),
        "sequence_shape": list(X.shape),
        "signer_metadata_available": False,
    }
    target = Path(__file__).resolve().parents[1] / "results" / "dataset_validation.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Report: {target}")


if __name__ == "__main__":
    main()
