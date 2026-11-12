"""Load and validate the extracted landmark dataset."""

from pathlib import Path

import numpy as np

from .config import ACTIONS, DATASET_FOLDER_NAMES, KEYPOINT_COUNT, SEQUENCE_LENGTH


def _numeric_directories(path: Path) -> list[Path]:
    return sorted(
        (entry for entry in path.iterdir() if entry.is_dir() and entry.name.isdecimal()),
        key=lambda entry: int(entry.name),
    )


def load_dataset(
    dataset_path: str | Path,
    *,
    sequence_length: int = SEQUENCE_LENGTH,
    keypoint_count: int = KEYPOINT_COUNT,
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(X, y)`` with shapes ``(samples, frames, features)`` and ``(samples,)``.

    Each numbered directory is one sequence. Frame files are loaded in numeric
    order and validated before being stacked, preventing silent label/shape drift.
    """
    root = Path(dataset_path).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Dataset directory does not exist: {root}")

    sequences: list[np.ndarray] = []
    labels: list[int] = []
    for label, action in enumerate(ACTIONS):
        folder_name = DATASET_FOLDER_NAMES.get(action, action)
        action_path = root / folder_name
        if not action_path.is_dir():
            raise FileNotFoundError(f"Missing class directory for {action!r}: {action_path}")

        sequence_dirs = _numeric_directories(action_path)
        if not sequence_dirs:
            raise ValueError(f"No numbered sequence directories found in {action_path}")

        for sequence_dir in sequence_dirs:
            frames: list[np.ndarray] = []
            for frame_index in range(sequence_length):
                frame_path = sequence_dir / f"{frame_index}.npy"
                if not frame_path.is_file():
                    raise FileNotFoundError(
                        f"Incomplete sequence {sequence_dir}: missing frame {frame_index}.npy"
                    )
                try:
                    frame = np.load(frame_path, allow_pickle=False)
                except (OSError, ValueError) as exc:
                    raise ValueError(f"Could not read landmark file {frame_path}: {exc}") from exc
                if frame.shape != (keypoint_count,):
                    raise ValueError(
                        f"Unexpected shape in {frame_path}: {frame.shape}; "
                        f"expected ({keypoint_count},)"
                    )
                if not np.isfinite(frame).all():
                    raise ValueError(f"Non-finite landmark values found in {frame_path}")
                frames.append(frame.astype(np.float32, copy=False))

            sequences.append(np.stack(frames))
            labels.append(label)

    return np.stack(sequences), np.asarray(labels, dtype=np.int64)
