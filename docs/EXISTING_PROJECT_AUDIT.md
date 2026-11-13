# Existing project audit

## Verified repository state

- The repository contains a research prototype for nine ASL medical symptom labels, with the original landmark arrays in `video_data/`.
- There are nine class directories and 30 numeric sequence directories in each. Each sequence contains frame files `0.npy` through `29.npy`.
- All 8,100 frame files have shape `(1662,)` and `float64` storage. The loader validates shape and finite values and converts each frame to `float32`.
- The original class order is defined in `sld/config.py`: headache, sore throat, cough, fever, stomach aches, tired, runny nose, nausea, trouble breathing. The on-disk folder `soar throat` is mapped to `sore throat`.
- The model in `sld/model.py` is a Sequential Keras classifier: LSTM(64, return sequences), LSTM(128, return sequences), LSTM(64), Dense(64, ReLU), Dense(32, ReLU), and a 9-way softmax. It uses Adam and sparse categorical cross entropy.
- `sld/realtime.py` extracts pose, face, left hand, and right hand landmarks, in that order, with zero-filled missing landmarks.
- `sld/train.py` uses stratified sequence-level train/test and train/validation splits. It does not have signer metadata and cannot provide signer-independent evaluation.
- The notebook has five cells and is a dataset-loading walkthrough. It does not contain an independent model definition, training experiment, or saved training results.
- No model checkpoint is present in the repository. The existing `.gitignore` excludes model artifacts and local dataset copies.
- No raw video or signer identifiers were found in the project structure. The included data is preprocessed landmarks.

## Assumptions and limits

- Numeric subdirectories represent individual sequences and numeric `.npy` filenames represent frame indices. This is supported by the folder structure and completeness checks for all 270 sequences.
- The checked-in Python implementation is treated as the source of truth for the feature order and architecture because the notebook does not define either independently.
- No previously achieved accuracy is asserted. Evaluation metrics must come from a local training run and its held-out split.
- 30 sequences per class are not enough to establish generalization to new signers or clinical settings. There are no signer identifiers for signer-independent splitting.
- MediSign is a communication aid prototype and is not a diagnostic system.

## Runtime notes

At audit time the machine has Python 3.14, Node 24, and npm 11. TensorFlow, MediaPipe, FastAPI, scikit-learn, and matplotlib are not installed. The project setup therefore targets Python 3.11, a compatible TensorFlow CPU runtime, and Node.js 20 or newer.
