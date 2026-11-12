"""Train and evaluate the symptom sequence classifier."""

import argparse
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

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
    model.fit(
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
    print(classification_report(y_test, predictions, labels=range(len(ACTIONS)),
                               target_names=ACTIONS, zero_division=0))
    model.save(args.output)
    print(f"Saved model to {args.output}")


if __name__ == "__main__":
    main()
