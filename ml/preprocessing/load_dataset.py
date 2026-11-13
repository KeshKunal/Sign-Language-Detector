"""Compatibility entry point for the verified original dataset loader."""
from sld.config import ACTIONS, DEFAULT_DATASET_PATH, KEYPOINT_COUNT, SEQUENCE_LENGTH
from sld.data import load_dataset

__all__ = ["ACTIONS", "DEFAULT_DATASET_PATH", "KEYPOINT_COUNT", "SEQUENCE_LENGTH", "load_dataset"]
