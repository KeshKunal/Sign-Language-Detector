"""Evaluate an existing checkpoint on the reproducible stratified test split."""
import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             f1_score, precision_score, recall_score)
from sklearn.model_selection import train_test_split

from sld.config import ACTIONS, DEFAULT_DATASET_PATH, DEFAULT_MODEL_PATH
from sld.data import load_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not 0 < args.test_size < 1:
        parser.error("--test-size must be between 0 and 1")
    if not args.model.is_file():
        parser.error(f"Model checkpoint not found: {args.model}")
    X, y = load_dataset(args.data)
    _, X_test, _, y_test = train_test_split(X, y, test_size=args.test_size,
        random_state=args.seed, stratify=y)
    from tensorflow.keras.models import load_model
    model = load_model(args.model)
    probabilities = model.predict(X_test, verbose=0)
    predicted = np.asarray(probabilities).argmax(axis=1)
    result = {
        "accuracy": accuracy_score(y_test, predicted),
        "macro_precision": precision_score(y_test, predicted, average="macro", zero_division=0),
        "macro_recall": recall_score(y_test, predicted, average="macro", zero_division=0),
        "macro_f1": f1_score(y_test, predicted, average="macro", zero_division=0),
        "per_class": classification_report(y_test, predicted, labels=range(len(ACTIONS)),
            target_names=ACTIONS, zero_division=0, output_dict=True),
        "confusion_matrix": confusion_matrix(y_test, predicted, labels=range(len(ACTIONS))).tolist(),
        "classes": list(ACTIONS), "test_sequences": len(y_test), "split_seed": args.seed,
        "signer_independent": False,
    }
    output = Path(__file__).resolve().parents[1] / "results" / "evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"Evaluation saved to {output}")


if __name__ == "__main__":
    main()
