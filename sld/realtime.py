"""Run the trained classifier against a webcam feed."""

import argparse
from collections import Counter, deque
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from tensorflow.keras.models import load_model

from .config import ACTIONS, DEFAULT_MODEL_PATH, KEYPOINT_COUNT, SEQUENCE_LENGTH


def extract_keypoints(results) -> np.ndarray:
    """Flatten MediaPipe Holistic landmarks into the trained 1662-value layout."""
    pose = (
        np.asarray([[p.x, p.y, p.z, p.visibility] for p in results.pose_landmarks.landmark])
        .reshape(-1)
        if results.pose_landmarks
        else np.zeros(33 * 4)
    )
    face = (
        np.asarray([[p.x, p.y, p.z] for p in results.face_landmarks.landmark]).reshape(-1)
        if results.face_landmarks
        else np.zeros(468 * 3)
    )
    left = (
        np.asarray([[p.x, p.y, p.z] for p in results.left_hand_landmarks.landmark]).reshape(-1)
        if results.left_hand_landmarks
        else np.zeros(21 * 3)
    )
    right = (
        np.asarray([[p.x, p.y, p.z] for p in results.right_hand_landmarks.landmark]).reshape(-1)
        if results.right_hand_landmarks
        else np.zeros(21 * 3)
    )
    keypoints = np.concatenate((pose, face, left, right)).astype(np.float32, copy=False)
    if keypoints.shape != (KEYPOINT_COUNT,):
        raise ValueError(f"Expected {KEYPOINT_COUNT} keypoints, got {keypoints.shape}")
    return keypoints


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--threshold", type=float, default=0.6)
    args = parser.parse_args()
    if not 0 <= args.threshold <= 1:
        parser.error("--threshold must be between 0 and 1")
    model_path = args.model.expanduser().resolve()
    if not model_path.is_file():
        parser.error(f"Model file not found: {model_path}. Train the model first.")

    model = load_model(model_path)
    capture = cv2.VideoCapture(args.camera)
    if not capture.isOpened():
        parser.error(f"Could not open camera {args.camera}")

    mp_holistic = mp.solutions.holistic
    sequence: deque[np.ndarray] = deque(maxlen=SEQUENCE_LENGTH)
    recent_predictions: deque[int] = deque(maxlen=10)
    try:
        with mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as holistic:
            while True:
                ok, frame = capture.read()
                if not ok or frame is None:
                    print("Camera frame could not be read; stopping.")
                    break

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                results = holistic.process(rgb)
                rgb.flags.writeable = True
                sequence.append(extract_keypoints(results))

                label = "Collecting frames..."
                confidence = 0.0
                if len(sequence) == SEQUENCE_LENGTH:
                    scores = model.predict(np.expand_dims(sequence, axis=0), verbose=0)[0]
                    prediction = int(np.argmax(scores))
                    recent_predictions.append(prediction)
                    stable_prediction, votes = Counter(recent_predictions).most_common(1)[0]
                    confidence = float(scores[stable_prediction])
                    if votes >= 6 and confidence >= args.threshold:
                        label = ACTIONS[stable_prediction]
                    else:
                        label = "Uncertain"

                cv2.rectangle(frame, (0, 0), (frame.shape[1], 54), (35, 45, 58), -1)
                cv2.putText(frame, label, (16, 36), cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (255, 255, 255), 2, cv2.LINE_AA)
                if confidence:
                    cv2.putText(frame, f"{confidence:.0%}", (frame.shape[1] - 90, 36),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (190, 220, 255), 2,
                                cv2.LINE_AA)
                cv2.imshow("Sign Language Symptom Detector", frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    break
    finally:
        capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
