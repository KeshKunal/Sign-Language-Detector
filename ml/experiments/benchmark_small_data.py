"""Compare compact classifiers on the current tiny landmark dataset.

This is an exploratory, sequence-level benchmark only. The source dataset has
no signer IDs, so these scores are not signer-independent and must not be used
as publication-quality generalization estimates.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.svm import SVC

from sld.config import DEFAULT_DATASET_PATH
from sld.data import load_dataset


def summarize(sequence: np.ndarray) -> np.ndarray:
    """Compact spatial-temporal statistics for pose and both hands."""
    body_hands = np.concatenate((sequence[..., :132], sequence[..., 1536:]), axis=-1)
    mean = body_hands.mean(axis=1)
    std = body_hands.std(axis=1)
    span = body_hands.max(axis=1) - body_hands.min(axis=1)
    velocity = np.abs(np.diff(body_hands, axis=1)).mean(axis=1)
    return np.concatenate((mean, std, span, velocity), axis=1)


def make_candidates(X: np.ndarray) -> dict[str, tuple[object, np.ndarray]]:
    body_hands = np.concatenate((X[..., :132], X[..., 1536:]), axis=-1)
    sample_indices = np.linspace(0, X.shape[1] - 1, 8).round().astype(int)
    compact_stream = body_hands[:, sample_indices].reshape(len(X), -1)
    full_stream = X[:, sample_indices].reshape(len(X), -1)
    summary = summarize(X)
    return {
        "rbf_svm_pose_hands_summary": (
            make_pipeline(StandardScaler(), SVC(C=3, kernel="rbf", class_weight="balanced")),
            summary,
        ),
        "extra_trees_pose_hands_summary": (
            ExtraTreesClassifier(
                n_estimators=400,
                max_features="sqrt",
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=42,
                n_jobs=1,
            ),
            summary,
        ),
        "rbf_svm_pose_hands_8_frames": (
            make_pipeline(StandardScaler(), SVC(C=3, kernel="rbf", class_weight="balanced")),
            compact_stream,
        ),
        "rbf_svm_all_landmarks_8_frames_pca": (
            make_pipeline(
                StandardScaler(),
                PCA(n_components=64, svd_solver="randomized", random_state=42),
                SVC(C=3, kernel="rbf", class_weight="balanced"),
            ),
            full_stream,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--output", type=Path, default=Path("ml/results/model_benchmark.json"))
    args = parser.parse_args()

    X, y = load_dataset(args.data)
    candidates = make_candidates(X)
    folds = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=42).split(X, y))
    results = {
        "dataset_sequences": int(len(X)),
        "class_count": int(len(np.unique(y))),
        "folds": 5,
        "split_type": "stratified sequence-level; signer metadata unavailable",
        "models": {},
    }

    for name, (estimator, features) in candidates.items():
        accuracies, macro_f1s, latencies = [], [], []
        for train_indices, test_indices in folds:
            estimator.fit(features[train_indices], y[train_indices])
            prediction = estimator.predict(features[test_indices])
            accuracies.append(accuracy_score(y[test_indices], prediction))
            macro_f1s.append(f1_score(y[test_indices], prediction, average="macro"))
            sample = features[test_indices[:1]]
            for _ in range(5):
                estimator.predict(sample)
            started = time.perf_counter()
            repeats = 100
            for _ in range(repeats):
                estimator.predict(sample)
            latencies.append((time.perf_counter() - started) * 1000 / repeats)

        results["models"][name] = {
            "input_dimensions": int(features.shape[1]),
            "accuracy_mean": float(np.mean(accuracies)),
            "accuracy_std": float(np.std(accuracies, ddof=1)),
            "macro_f1_mean": float(np.mean(macro_f1s)),
            "macro_f1_std": float(np.std(macro_f1s, ddof=1)),
            "predict_latency_ms_mean": float(np.mean(latencies)),
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
    print(f"Saved benchmark: {args.output.resolve()}")


if __name__ == "__main__":
    main()
