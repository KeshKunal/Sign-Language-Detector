"""Train and evaluate the symptom sequence classifier."""

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             f1_score, precision_score, recall_score)

from .config import ACTIONS, DEFAULT_DATASET_PATH, DEFAULT_MODEL_PATH
from .data import load_dataset
from .model import build_model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--confidence-threshold", type=float, default=0.65)
    args = parser.parse_args()

    if not 0 < args.test_size < 1:
        parser.error("--test-size must be between 0 and 1")
    if args.epochs < 1 or args.batch_size < 1:
        parser.error("--epochs and --batch-size must be positive")

    X, y = load_dataset(args.data)
    X_train_validation, X_test, y_train_validation, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=args.seed,
        stratify=y,
    )
    X_train, X_validation, y_train, y_validation = train_test_split(
        X_train_validation,
        y_train_validation,
        test_size=0.2,
        random_state=args.seed,
        stratify=y_train_validation,
    )
    model = build_model(len(ACTIONS))

    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

    args.output = args.output.expanduser().resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path = args.output.with_name(f"{args.output.stem}.best.keras")
    callbacks = [
        EarlyStopping(monitor="val_loss", patience=15, restore_best_weights=True),
        ModelCheckpoint(
            filepath=checkpoint_path,
            monitor="val_loss",
            save_best_only=True,
        ),
    ]

    print(f"Dataset: {len(X)} sequences, shape {X.shape}")
    print(
        f"Train: {len(X_train)} | Validation: {len(X_validation)} "
        f"| Test: {len(X_test)}"
    )
    history = model.fit(
        X_train,
        y_train,
        validation_data=(X_validation, y_validation),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        verbose=1,
    )
    loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
    predictions = model.predict(X_test, verbose=0).argmax(axis=1)
    print(f"Holdout loss: {loss:.4f} | accuracy: {accuracy:.4f}")
    report = classification_report(y_test, predictions, labels=range(len(ACTIONS)),
                                   target_names=ACTIONS, zero_division=0, output_dict=True)
    print(classification_report(y_test, predictions, labels=range(len(ACTIONS)),
                                target_names=ACTIONS, zero_division=0))
    model.save(args.output)
    mapping_path = args.output.with_name("class_mapping.json")
    mapping_path.write_text(json.dumps({
        "classes": list(ACTIONS),
        "class_to_index": {label: index for index, label in enumerate(ACTIONS)},
        "sequence_length": int(X.shape[1]),
        "features_per_frame": int(X.shape[2]),
    }, indent=2) + "\n", encoding="utf-8")
    results = Path(__file__).resolve().parents[1] / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results / "evaluation.json").write_text(json.dumps({
        "accuracy": accuracy_score(y_test, predictions),
        "macro_precision": precision_score(y_test, predictions, average="macro", zero_division=0),
        "macro_recall": recall_score(y_test, predictions, average="macro", zero_division=0),
        "macro_f1": f1_score(y_test, predictions, average="macro", zero_division=0),
        "loss": float(loss), "threshold": args.confidence_threshold,
        "train_sequences": len(X_train), "validation_sequences": len(X_validation),
        "test_sequences": len(X_test), "split_seed": args.seed,
        "signer_independent": False, "per_class": report,
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=range(len(ACTIONS))).tolist(),
        "classes": list(ACTIONS),
    }, indent=2) + "\n", encoding="utf-8")
    (results / "training_history.json").write_text(json.dumps(history.history, indent=2) + "\n", encoding="utf-8")
    try:
        import matplotlib.pyplot as plt
        for key, title, filename in (("accuracy", "Accuracy", "accuracy.png"), ("loss", "Loss", "loss.png")):
            plt.figure(figsize=(8, 5))
            plt.plot(history.history.get(key, []), label="Training")
            plt.plot(history.history.get(f"val_{key}", []), label="Validation")
            plt.xlabel("Epoch")
            plt.ylabel(title)
            plt.title(f"Training and validation {title.lower()}")
            plt.legend()
            plt.tight_layout()
            plt.savefig(results / filename, dpi=150)
            plt.close()
        plt.figure(figsize=(10, 8))
        plt.imshow(confusion_matrix(y_test, predictions, labels=range(len(ACTIONS))), cmap="Blues")
        plt.xticks(range(len(ACTIONS)), ACTIONS, rotation=45, ha="right")
        plt.yticks(range(len(ACTIONS)), ACTIONS)
        plt.xlabel("Predicted")
        plt.ylabel("Actual")
        plt.title("Held-out test confusion matrix")
        plt.colorbar()
        plt.tight_layout()
        plt.savefig(results / "confusion_matrix.png", dpi=150)
        plt.close()
    except ImportError:
        print("matplotlib unavailable; metric JSON was saved without plot images.")
    print(f"Saved evaluation artifacts to {results}")
    print(f"Saved model to {args.output}")
    print(f"Saved class mapping to {mapping_path}")


if __name__ == "__main__":
    main()
