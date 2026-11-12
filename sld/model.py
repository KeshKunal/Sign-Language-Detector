"""Keras sequence classifier."""

from .config import KEYPOINT_COUNT, SEQUENCE_LENGTH


def build_model(num_classes: int):
    """Create the LSTM classifier for 30-frame holistic landmark sequences."""
    if num_classes < 2:
        raise ValueError("num_classes must be at least 2")

    from tensorflow.keras import Sequential
    from tensorflow.keras.layers import Dense, Input, LSTM

    model = Sequential(
        [
            Input(shape=(SEQUENCE_LENGTH, KEYPOINT_COUNT)),
            LSTM(64, return_sequences=True),
            LSTM(128, return_sequences=True),
            LSTM(64),
            Dense(64, activation="relu"),
            Dense(32, activation="relu"),
            Dense(num_classes, activation="softmax"),
        ],
        name="symptom_sign_classifier",
    )
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model
