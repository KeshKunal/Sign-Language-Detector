# Sign Language Symptom Detector

A research prototype that classifies nine ASL symptom signs from short sequences of MediaPipe Holistic landmarks. It converts each camera frame into 1,662 numeric features and uses an LSTM to classify 30-frame sequences.

> This prototype is for demonstration and research. It is not a medical diagnostic or communication aid, and it has not been clinically validated. The small dataset does not establish reliable performance for new signers or real-world use.

## Dataset

The included `video_data/` directory contains preprocessed landmark arrays, not raw videos. Its layout is:

```text
video_data/<class>/<sequence>/<frame>.npy
```

- 9 classes, 30 sequences per class, and 30 frames per sequence
- 270 sequences and 8,100 frame arrays total
- Each frame array has shape `(1662,)` and contains pose, face, and both-hand landmarks
- The training tensor has shape `(270, 30, 1662)`

The legacy folder is named `soar throat`; the code maps it to the correctly spelled output label `sore throat`. Numeric sequence and frame filenames are loaded in numeric order and every frame is validated before training.

Run the lightweight dataset inspection (no third-party packages required):

```powershell
python inspect_npy.py
```

## Setup

Use Python 3.11 in a virtual environment. TensorFlow 2.21 supports Python 3.10–3.13; the dependency file keeps MediaPipe below 1.0 because this project uses its legacy `solutions.holistic` API. On native Windows, TensorFlow runs on CPU; use WSL2 for supported NVIDIA GPU workflows. See the [TensorFlow installation guide](https://www.tensorflow.org/install/pip) for platform details.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS or Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Train

Run commands from the project root:

```bash
python -m sld.train
```

The trainer reserves a stratified 20% test set, then splits the remaining data into training and validation partitions. It applies early stopping using validation loss, evaluates once on the untouched test set, prints per-class metrics, and writes the final Keras model to `models/sign_language_model.keras`.

Common options:

```bash
python -m sld.train --epochs 200 --batch-size 16 --seed 42
python -m sld.train --data path/to/video_data --output models/custom.keras --test-size 0.2
```

The holdout set is small, so its scores are only a rough estimate. For a meaningful evaluation, collect more sequences from multiple signers and keep signers separated between training and evaluation.

## Run the webcam demo

Train a model first, then run:

```bash
python -m sld.realtime
```

Options include `--model path/to/model.keras`, `--camera 1`, and `--threshold 0.7`. Press `q` or Escape to exit. The camera is released even if the loop encounters an error.

## Notebook

[`notebooks/sign_language_detector.ipynb`](notebooks/sign_language_detector.ipynb) is a concise walkthrough of the dataset and package workflow. It no longer depends on Google Drive mounts, Colab-only paths, interactive package installation, or stale saved outputs.

## Project layout

```text
sld/                    Dataset loader, model, trainer, and webcam demo
notebooks/              Reproducible Jupyter walkthrough
video_data/             Preprocessed landmark arrays
inspect_npy.py          Dependency-free dataset inspection
requirements.txt        Runtime dependencies
```

## Method notes

The 1,662 features per frame are composed of 132 pose values (33 landmarks × 4), 1,404 face values (468 × 3), and 63 values for each hand (21 × 3). The model receives 30 consecutive frames and predicts one of the nine symptom labels. This recognizes patterns in the collected landmark data; it does not translate unrestricted ASL or establish a medical condition.

## Credits

The original project demonstrated a real-time ASL symptom recognition concept. This repository reorganizes its data workflow for reproducible local training and inference.
