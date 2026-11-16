"""Compare fast classical models with the existing LSTM on one fixed split.

This benchmark uses the current nine-class landmark dataset. Its split is
sequence-disjoint, not signer-disjoint, because the source has no signer IDs.
Select SVM windows on validation only, then evaluate the selected candidate on
the test split once. No model is installed in the app by this script.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from sld.config import ACTIONS, DEFAULT_DATASET_PATH
from sld.data import load_dataset


def feature_view(X: np.ndarray, frames: int, view: str, mode: str) -> np.ndarray:
    if view == "hands":
        sequence = X[..., 1536:]
    elif view == "pose_hands":
        sequence = np.concatenate((X[..., :132], X[..., 1536:]), axis=-1)
    elif view == "all":
        sequence = X
    else:
        raise ValueError(view)
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


def candidates(X: np.ndarray):
    specs = []
    for frames in (8, 12, 16, 20, 30):
        specs.append((f"svm_pose_hands_summary_{frames}", "svm", frames, "pose_hands", "summary"))
    specs.extend(
        (
            ("svm_hands_summary_30", "svm", 30, "hands", "summary"),
            ("svm_all_summary_30", "svm", 30, "all", "summary"),
            ("extra_trees_pose_hands_summary_30", "extra_trees", 30, "pose_hands", "summary"),
        )
    )
    for name, kind, frames, view, mode in specs:
        if kind == "svm":
            estimator = make_pipeline(
                StandardScaler(),
                SVC(C=3, kernel="rbf", class_weight="balanced", probability=True, random_state=42),
            )
        else:
            estimator = ExtraTreesClassifier(
                n_estimators=400,
                max_features="sqrt",
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            )
        yield name, estimator, feature_view(X, frames, view, mode), {
            "frames_seen": frames,
            "view": view,
            "feature_mode": mode,
            "kind": kind,
        }


def score(estimator, features: np.ndarray, y: np.ndarray) -> dict:
    prediction = estimator.predict(features)
    return {
        "accuracy": float(accuracy_score(y, prediction)),
        "macro_f1": float(f1_score(y, prediction, average="macro", zero_division=0)),
        "per_class": classification_report(
            y,
            prediction,
            labels=np.arange(len(ACTIONS)),
            target_names=ACTIONS,
            output_dict=True,
            zero_division=0,
        ),
    }


def latency_ms(estimator, feature: np.ndarray, repeats: int = 100) -> dict:
    sample = feature[:1]
    for _ in range(8):
        estimator.predict(sample)
    values = []
    for _ in range(repeats):
        start = time.perf_counter()
        estimator.predict(sample)
        values.append((time.perf_counter() - start) * 1000)
    return {"median": float(np.median(values)), "p95": float(np.percentile(values, 95))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--keras-model", type=Path, help="Existing checkpoint trained with seed 42")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ml/results/nine_class_model_comparison.json"),
    )
    parser.add_argument("--save-svm", type=Path, help="Optional private candidate joblib output")
    args = parser.parse_args()

    X, y = load_dataset(args.data)
    indices = np.arange(len(y))
    train_val, test = train_test_split(indices, test_size=0.2, random_state=42, stratify=y)
    train, val = train_test_split(
        train_val,
        test_size=0.2,
        random_state=42,
        stratify=y[train_val],
    )
    results = {
        "dataset_sequences": int(len(X)),
        "class_count": len(ACTIONS),
        "split": {
            "train": len(train),
            "validation": len(val),
            "test": len(test),
            "seed": 42,
            "signer_independent": False,
        },
        "existing_lstm": None,
        "candidates": {},
    }

    if args.keras_model:
        import tensorflow as tf

        tf.config.threading.set_intra_op_parallelism_threads(1)
        tf.config.threading.set_inter_op_parallelism_threads(1)
        model = tf.keras.models.load_model(args.keras_model.expanduser().resolve())
        keras_prediction = np.asarray(model.predict(X[test], verbose=0)).argmax(axis=1)
        results["existing_lstm"] = {
            "test_accuracy": float(accuracy_score(y[test], keras_prediction)),
            "test_macro_f1": float(f1_score(y[test], keras_prediction, average="macro", zero_division=0)),
            "test_per_class": classification_report(
                y[test], keras_prediction, labels=range(len(ACTIONS)),
                target_names=ACTIONS, output_dict=True, zero_division=0,
            ),
            "classifier_latency_ms": latency_ms(model, X[test]),
            "checkpoint": str(args.keras_model),
        }

    fitted = {}
    for name, estimator, features, metadata in candidates(X):
        estimator.fit(features[train], y[train])
        validation = score(estimator, features[val], y[val])
        fitted[name] = (estimator, features, metadata)
        results["candidates"][name] = {
            **metadata,
            "validation": validation,
            "classifier_latency_ms": latency_ms(estimator, features[val]),
        }

    chosen_name = max(
        results["candidates"],
        key=lambda name: (
            results["candidates"][name]["validation"]["macro_f1"],
            -results["candidates"][name]["frames_seen"],
        ),
    )
    chosen_estimator, chosen_features, chosen_metadata = fitted[chosen_name]
    final_estimator = make_pipeline(
        StandardScaler(),
        SVC(C=3, kernel="rbf", class_weight="balanced", probability=True, random_state=42),
    )
    if chosen_metadata["kind"] == "extra_trees":
        final_estimator = ExtraTreesClassifier(
            n_estimators=400, max_features="sqrt", min_samples_leaf=2,
            class_weight="balanced", random_state=42, n_jobs=-1,
        )
    final_estimator.fit(chosen_features[np.concatenate((train, val))], y[np.concatenate((train, val))])
    results["selected_on_validation"] = chosen_name
    results["selected_test"] = score(final_estimator, chosen_features[test], y[test])
    results["selected_test"]["classifier_latency_ms"] = latency_ms(final_estimator, chosen_features[test])

    if args.save_svm:
        artifact_path = args.save_svm.expanduser().resolve()
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "model": final_estimator,
                "classes": list(ACTIONS),
                **chosen_metadata,
            },
            artifact_path,
        )
        results["private_candidate_path"] = str(artifact_path)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
    print(f"Saved comparison: {args.output.resolve()}")


if __name__ == "__main__":
    main()
