"""Shared model and dataset configuration."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_PATH = PROJECT_ROOT / "video_data"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "sign_language_model.keras"

# Keep this order stable: output indices from trained models depend on it.
ACTIONS = (
    "headache",
    "sore throat",
    "cough",
    "fever",
    "stomach aches",
    "tired",
    "runny nose",
    "nausea",
    "trouble breathing",
)

# The on-disk dataset contains the original misspelling. Normalize it when
# exposing labels to the model and users without changing the existing data.
DATASET_FOLDER_NAMES = {"sore throat": "soar throat"}
SEQUENCE_LENGTH = 30
KEYPOINT_COUNT = 1662
