"""Create private MediaPipe features from a locally downloaded ISL emergency corpus.

Expected source files follow the Mendeley dataset names, for example
accident_003_02.avi or accident_crop_003_02.avi. Raw and cropped copies are
deduplicated; raw files are preferred. Train/validation/test splits are grouped
by signer to prevent identity leakage. The dataset is listed as CC BY 4.0;
cite Adithya and Rajesh (2020) and retain the license notice with any use.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np


LABELS = ("accident", "call", "doctor", "help", "hot", "lose", "pain", "thief")
FILENAME = re.compile(
    r"^(accident|call|doctor|help|hot|lose|pain|thief)_?(crop_)?(\d{3})_(\d{2})$",
    re.IGNORECASE,
)


def list_videos(root: Path) -> list[tuple[Path, str, str, int, bool]]:
    candidates: list[tuple[Path, str, str, int, bool]] = []
    for path in root.rglob("*.avi"):
        match = FILENAME.fullmatch(path.stem)
        if not match:
            continue
        label, crop_marker, signer, repetition = match.groups()
        is_cropped = bool(crop_marker) or any("crop" in part.lower() for part in path.parts)
        candidates.append((path, label.lower(), signer, int(repetition), is_cropped))

    # If raw and cropped releases are present, use raw to avoid duplicates.
    has_raw = any(not item[4] for item in candidates)
    selected = [item for item in candidates if not item[4]] if has_raw else candidates
    unique: dict[tuple[str, str, int], tuple[Path, str, str, int, bool]] = {}
    for item in sorted(selected, key=lambda row: (row[1], row[2], row[3], len(str(row[0])))):
        unique.setdefault((item[1], item[2], item[3]), item)
    result = list(unique.values())
    if not result:
        raise ValueError("No recognized .avi files found. Check the extracted dataset directory.")
    missing = set(LABELS) - {row[1] for row in result}
    if missing:
        raise ValueError(f"Dataset is missing expected classes: {sorted(missing)}")
    return result


def extract_keypoints(results: object) -> np.ndarray:
    def points(landmark_set: object, count: int, visibility: bool) -> np.ndarray:
        if not landmark_set:
            return np.zeros(count, dtype=np.float32)
        landmarks = landmark_set.landmark
        if visibility:
            return np.asarray(
                [[p.x, p.y, p.z, p.visibility] for p in landmarks], dtype=np.float32
            ).reshape(-1)
        return np.asarray([[p.x, p.y, p.z] for p in landmarks], dtype=np.float32).reshape(-1)

    return np.concatenate(
        (
            points(results.pose_landmarks, 132, True),
            points(results.face_landmarks, 1404, False),
            points(results.left_hand_landmarks, 63, False),
            points(results.right_hand_landmarks, 63, False),
        )
    )


def extract_video(path: Path, sequence_length: int, holistic: object) -> np.ndarray:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"Could not open video: {path}")
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_count <= 0:
        capture.release()
        raise ValueError(f"Invalid frame count in: {path}")
    indices = np.linspace(0, frame_count - 1, sequence_length).round().astype(int)
    selected = set(indices.tolist())
    extracted: dict[int, np.ndarray] = {}
    frame_index = 0
    try:
        while frame_index <= max(selected):
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index in selected:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                extracted[frame_index] = extract_keypoints(holistic.process(rgb))
            frame_index += 1
    finally:
        capture.release()
    if len(extracted) != len(selected):
        raise ValueError(f"Unable to decode all sampled frames from: {path}")
    return np.stack([extracted[int(index)] for index in indices]).astype(np.float32)


def signer_splits(signers: list[str], seed: int) -> dict[str, str]:
    unique = np.asarray(sorted(set(signers)))
    if len(unique) < 10:
        raise ValueError(f"Need at least 10 signers for a useful split, found {len(unique)}")
    rng = np.random.default_rng(seed)
    rng.shuffle(unique)
    train_end = int(round(len(unique) * 0.70))
    val_end = int(round(len(unique) * 0.85))
    return {
        **{signer: "train" for signer in unique[:train_end]},
        **{signer: "val" for signer in unique[train_end:val_end]},
        **{signer: "test" for signer in unique[val_end:]},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path, help="Extracted Mendeley dataset directory")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / "research-data" / "isl_emergency_private.npz",
    )
    parser.add_argument("--sequence-length", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.sequence_length < 8:
        parser.error("--sequence-length must be at least 8")

    videos = list_videos(args.data_dir.expanduser().resolve())
    split_for_signer = signer_splits([row[2] for row in videos], args.seed)
    sequences, labels, signers, splits, repetitions = [], [], [], [], []
    args.output.expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    with mp.solutions.holistic.Holistic(
        # Do not let tracking state leak from one signer/video into another.
        static_image_mode=True,
        model_complexity=1,
        smooth_landmarks=True,
        refine_face_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as holistic:
        for number, (path, label, signer, repetition, _cropped) in enumerate(videos, 1):
            sequences.append(extract_video(path, args.sequence_length, holistic))
            labels.append(label)
            signers.append(signer)
            splits.append(split_for_signer[signer])
            repetitions.append(repetition)
            if number % 20 == 0 or number == len(videos):
                print(f"Processed {number}/{len(videos)} videos", flush=True)

    output = args.output.expanduser().resolve()
    np.savez_compressed(
        output,
        X=np.stack(sequences),
        y=np.asarray(labels),
        signer_id=np.asarray(signers),
        split=np.asarray(splits),
        repetition=np.asarray(repetitions),
        classes=np.asarray(LABELS),
    )
    print(f"Saved landmark features to {output}; kept source videos out of the artifact.")
    print(
        "Signer counts: "
        + ", ".join(
            f"{name}={len(set(np.asarray(signers)[np.asarray(splits) == name]))}"
            for name in ("train", "val", "test")
        )
    )


if __name__ == "__main__":
    main()
