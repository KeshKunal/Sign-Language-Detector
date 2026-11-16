# MediSign

**AI-assisted American Sign Language symptom communication**

MediSign is a local-first academic project that helps a deaf or hard-of-hearing patient communicate one of nine collected ASL symptom signs. It extracts pose, face, and hand landmarks from a live webcam feed, evaluates a 30-frame sequence with the repository's original LSTM classifier, and asks the patient to confirm a possible symptom before saving it as a communication.

> MediSign is an assistive communication tool. It is not a diagnostic system and does not replace professional medical assessment. Model confidence is not a medically validated probability.

## Features

- Responsive React/TypeScript interface with overview, live recognition, patient communication, clinical view, model and dataset information, and project information pages.
- Live browser webcam preview and MediaPipe Holistic landmark extraction. Camera video and landmark sequences are not stored.
- Local FastAPI inference using the original Python Keras model. No random, demo, or simulated predictions are generated.
- 30-frame input buffer, non-overlapping inference requests, a configurable confidence threshold, and prediction stabilisation.
- Patient confirmation before a symptom enters the locally persisted communication history. Search, symptom filtering, deletion, and clear history are provided.
- Light and dark display modes and a CPU-first local setup.
- Reproducible dataset validation and model training/evaluation artifacts.

## Technology

- Frontend: React 18, TypeScript, Vite, React Router, Lucide, MediaPipe Holistic browser runtime.
- Inference and training: Python, FastAPI, TensorFlow/Keras, NumPy, MediaPipe, scikit-learn.
- Persistence: browser localStorage for confirmed communications only. There is no patient database or cloud service.

## Architecture

```text
Webcam in browser
  → local MediaPipe Holistic
  → pose + face + left hand + right hand (1,662 values/frame)
  → rolling 30-frame sequence
  → FastAPI on 127.0.0.1:8000
  → original 3-layer LSTM model
  → possible symptom and model confidence
  → patient confirms, rejects, or retries
  → confirmed-only browser history
```

The browser runtime files are copied from the installed `@mediapipe/holistic` package into `frontend/public/mediapipe`, so inference does not fetch model files from a third party. The Python API owns the single model inference path. Its health endpoint reports whether model weights exist. Without a trained checkpoint, the application remains browseable and clearly disables real-time recognition.

## Dataset

The included `video_data/` contains preprocessed landmark arrays, not raw videos:

- 9 classes, 30 sequences per class, 30 frames per sequence.
- 270 complete sequences and 8,100 `.npy` frame files.
- One frame is a `(1662,)` float64 array; the loader validates every array and converts it to float32.
- Feature layout: pose 132, face 1,404, left hand 63, right hand 63.
- The historical directory name `soar throat` is mapped to the output label `sore throat`; files are preserved.
- Numeric subfolders identify sequence boundaries. Numeric frame filenames are sorted numerically.

Validate and write `ml/results/dataset_validation.json` with:

```powershell
.\.venv\Scripts\python.exe -m ml.preprocessing.validate_dataset
```

See [dataset documentation](docs/DATASET_DOCUMENTATION.md) and [existing project audit](docs/EXISTING_PROJECT_AUDIT.md) for verified details and limitations.

## Installation (Windows 11)

Install Python 3.11 (with the Python launcher) and Node.js 20 or newer, then open PowerShell in the repository folder:

```powershell
.\setup.ps1
.\run.ps1
```

Setup creates `.venv`, installs Python and frontend dependencies, stages the local MediaPipe runtime, and validates the dataset. `run.ps1` starts the API and frontend, opens `http://127.0.0.1:5173`, and stops both services when Enter is pressed in the PowerShell window.

For a manual setup:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Push-Location frontend
npm install
Pop-Location
.\.venv\Scripts\python.exe -m ml.preprocessing.validate_dataset
```

The browser camera works on `localhost`. Allow camera access in the browser when prompted. If the webcam is unavailable, check Windows camera privacy settings and close applications that already hold the camera.

## Train the original model

Python 3.11 and the dependencies above are suitable for CPU training; an NVIDIA GPU is not required. Training uses the existing verified class order and the original Keras model. The trainer makes a stratified sequence-level test split and a validation split from the remaining data. It cannot make a signer-independent split because signer metadata is absent.

```powershell
.\train.ps1
# Or:
.\.venv\Scripts\python.exe -m ml.training.train --epochs 200 --batch-size 16 --seed 42
```

The checkpoint is saved at `ml/models/sign_language_model.keras`. Evaluation metrics, class report, confusion matrix data, training history, and plots are written under `ml/results/`. The test set is small; do not treat its metrics as a guarantee of generalization or clinical performance. No accuracy claim is supplied before you train the model.

Evaluate a saved checkpoint using the same seed and test size:

```powershell
.\.venv\Scripts\python.exe -m ml.training.evaluate --seed 42 --test-size 0.2
```

## Run and validate

```powershell
.\run.ps1
.\validate.ps1
```

`validate.ps1` checks every dataset frame and creates a production frontend build. Runtime logs are written to the local ignored `logs/` directory.

The local API endpoints are `GET /api/health` and `POST /api/predict`. Set `MEDISIGN_MODEL` to use another Keras checkpoint and `MEDISIGN_CONFIDENCE_THRESHOLD` (0 to 1) to configure the recognition threshold. The health response shows the active threshold.

## Repository layout

```text
backend/app/               Local FastAPI model inference API
docs/                      Audit, dataset, methodology, architecture
frontend/src/               React pages, recognition workflow, styles
ml/preprocessing/           Dataset loading and validation entry points
ml/training/                Train and evaluate commands
ml/results/                 Generated validation and experiment artifacts
sld/                        Verified original loader, model and webcam code
video_data/                 Existing preprocessed landmark dataset
setup.ps1, run.ps1          Windows setup and local application scripts
train.ps1, validate.ps1     Windows training and validation scripts
notebooks/                  Existing project walkthrough
```

## Troubleshooting

- **Python 3.11 not found:** the setup requires Python 3.11 because the configured TensorFlow versions do not provide a compatible package for Python 3.14. Install Python 3.11 from python.org, enable `py.exe`, and rerun `setup.ps1`.
- **Recognition unavailable:** run training and verify `ml/models/sign_language_model.keras` exists. The UI does not invent predictions.
- **Camera permission denied:** allow access for `localhost` in the browser and in Windows privacy settings, then restart recognition.
- **Frontend build or MediaPipe files missing:** run `npm install` from `frontend/`; the post-install script stages Holistic runtime assets.
- **API fails to start:** inspect `logs/backend-error.log`; the default API address is `127.0.0.1:8000`.
- **Dataset validation fails:** inspect the missing/invalid path in the error and check that the original dataset has not been moved or modified.

## Known limitations

- Only nine collected ASL symptom classes are supported; this is not unrestricted sign language translation.
- The dataset has only 30 sequences per class, no signer metadata, and no raw video for independent data review.
- Sequence-level holdout results may include the same signer in train and test partitions.
- Real-time recognition quality depends on the training data, camera, lighting, framing, and sign variation.
- Local browser storage is convenient for demonstrations and is not a secure clinical record system.
- MediSign is not medically or clinically validated.

## Future work

Collect a larger dataset across consented signers, retain signer metadata for signer-independent evaluation, assess accessibility with ASL users, evaluate confidence calibration and out-of-distribution signs, and add separately versioned language and vocabulary packs.
