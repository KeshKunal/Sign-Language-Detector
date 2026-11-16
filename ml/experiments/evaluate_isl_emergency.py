"""Compare fast classifiers on signer-disjoint ISL emergency videos."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC


def features(X: np.ndarray, frames: int, view: str, mode: str) -> np.ndarray:
    if view == "hands":
        sequence = X[..., 1536:]
    else:
        sequence = np.concatenate((X[..., :132], X[..., 1536:]), axis=-1)
    prefix = sequence[:, :frames]
    if mode == "summary":
        return np.concatenate(
            (
                prefix.mean(axis=1),
                prefix.std(axis=1),
                prefix.max(axis=1) - prefix.min(axis=1),
                np.abs(np.diff(prefix, axis=1)).mean(axis=1),
            ),
            axis=1,
        )
    indices = np.linspace(0, frames - 1, min(8, frames)).round().astype(int)
    return sequence[:, indices].reshape(len(X), -1)


def make_model(name: str):
    if name.startswith("svm"):
        return make_pipeline(StandardScaler(), SVC(C=3, kernel="rbf", class_weight="balanced"))
    return ExtraTreesClassifier(
        n_estimators=500,
        max_features="sqrt",
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )


def measure(estimator, X: np.ndarray, y: np.ndarray, classes: np.ndarray) -> dict:
    prediction = estimator.predict(X)
    return {
        "accuracy": float(accuracy_score(y, prediction)),
        "macro_f1": float(f1_score(y, prediction, average="macro", zero_division=0)),
        "per_class": classification_report(
            y,
            prediction,
            labels=np.arange(len(classes)),
            target_names=classes,
            output_dict=True,
            zero_division=0,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / "research-data" / "isl_emergency_eval.json",
    )
    parser.add_argument(
        "--model-output",
        type=Path,
        default=Path.home() / "research-data" / "isl_emergency_model.joblib",
    )
    args = parser.parse_args()

    with np.load(args.data, allow_pickle=False) as archive:
        X = archive["X"].astype(np.float32)
        labels = archive["y"].astype(str)
        splits = archive["split"].astype(str)
        signers = archive["signer_id"].astype(str)
    encoder = LabelEncoder().fit(labels)
    y = encoder.transform(labels)
    train, val, test = (np.flatnonzero(splits == name) for name in ("train", "val", "test"))
    if any(not len(index) for index in (train, val, test)):
        raise ValueError("Expected non-empty signer-grouped train/val/test splits")
    signer_sets = [set(signers[index]) for index in (train, val, test)]
    if any(signer_sets[i] & signer_sets[j] for i in range(3) for j in range(i + 1, 3)):
        raise ValueError("Signer leakage detected across train/validation/test")

    result = {
        "dataset": "Mendeley ISL emergency gesture video dataset",
        "protocol": "signer-disjoint 70/15/15 split",
        "class_count": int(len(encoder.classes_)),
        "classes": encoder.classes_.tolist(),
        "sequence_frames": int(X.shape[1]),
        "samples_by_split": {name: int(np.sum(splits == name)) for name in ("train", "val", "test")},
        "signers_by_split": {name: int(len(np.unique(signers[splits == name]))) for name in ("train", "val", "test")},
        "models": {},
    }
    candidates = (
        ("svm_hands_summary", "svm", "hands", "summary"),
        ("svm_body_hands_summary", "svm", "body_hands", "summary"),
        ("svm_hands_frames", "svm", "hands", "frames"),
        ("extra_trees_hands_summary", "extra_trees", "hands", "summary"),
    )
    for frame_count in (8, 12, 20, 30):
        for key, model_name, view, mode in candidates:
            estimator = make_model(model_name)
            X_features = features(X, frame_count, view, mode)
            estimator.fit(X_features[train], y[train])
            validation = measure(estimator, X_features[val], y[val], encoder.classes_)
            for _ in range(5):
                estimator.predict(X_features[test[:1]])
            started = time.perf_counter()
            for _ in range(100):
                estimator.predict(X_features[test[:1]])
            latency_ms = (time.perf_counter() - started) * 10
            result["models"][f"{key}_prefix_{frame_count}"] = {
                "frames_seen": frame_count,
                "validation": validation,
                "classifier_latency_ms_mean": latency_ms,
            }

    selected_name, selected = max(
        result["models"].items(),
        key=lambda item: (item[1]["validation"]["macro_f1"], -item[1]["frames_seen"]),
    )
    selected_config = next(
        item for item in candidates if selected_name.startswith(item[0])
    )
    key, model_name, view, mode = selected_config
    frame_count = selected["frames_seen"]
    X_features = features(X, frame_count, view, mode)
    final_model = make_model(model_name)
    final_model.fit(X_features[np.concatenate((train, val))], y[np.concatenate((train, val))])
    result["selected_on_validation"] = selected_name
    result["final_test"] = measure(final_model, X_features[test], y[test], encoder.classes_)
    result["final_test"]["frames_seen"] = frame_count
    model_output = args.model_output.expanduser().resolve()
    model_output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": final_model,
            "classes": encoder.classes_.tolist(),
            "frames_seen": frame_count,
            "view": view,
            "feature_mode": mode,
        },
        model_output,
    )
    result["private_model_output"] = str(model_output)

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "models"}, indent=2))
    for name, scores in result["models"].items():
        print(
            f"{name}: val macro-F1={scores['validation']['macro_f1']:.3f}, "
            f"accuracy={scores['validation']['accuracy']:.3f}, "
            f"model={scores['classifier_latency_ms_mean']:.3f} ms"
        )
    print(f"Saved report: {output}")


if __name__ == "__main__":
    main()
