# Methodology

## Verified model

The authoritative implementation is `sld/model.py`; the included notebook is a dataset loading walkthrough and contains no independent model experiment. The model takes `(30, 1662)` sequences and uses three recurrent layers (64 units returning sequences, then 128 units returning sequences, then 64 units), followed by 64-unit and 32-unit ReLU dense layers and a nine-class softmax. It is compiled with Adam and sparse categorical cross entropy. Output order is fixed in `sld/config.py`.

## Input features

The webcam path produces 1,662 values per frame: pose x/y/z/visibility (132), face x/y/z (1,404), left hand x/y/z (63), and right hand x/y/z (63). Missing landmark sets are zero-filled. The original dataset contains MediaPipe Holistic landmark arrays, and the original webcam demo uses the same concatenation and zero-fill convention.

## Training and evaluation

`python -m ml.training.train` loads and validates all sequences, converts features to float32, performs a reproducible stratified sequence-level test split and a validation split, trains the verified architecture, and applies early stopping using validation loss. It writes a Keras checkpoint, JSON metrics and training history, and accuracy, loss, and confusion-matrix plots under `ml/results/`.

No signer identifiers exist in the dataset. The split prevents frames from one sequence crossing partitions, but it is not signer-independent. The held-out dataset is small and cannot establish clinical or broad signer performance. Metrics are only displayed after a real local run.

## Browser inference

The browser MediaPipe Holistic solution follows the same feature order. It gathers 30 complete frame vectors before invoking the local API and advances inference by ten frames after the initial window. At most one request can be active. Recent predictions are stabilized across successive windows; predictions below the configured threshold are not presented as a possible symptom. The threshold is a configurable engineering setting, not a medically validated probability.

## Human confirmation and data retention

The model suggestion remains separate from the communication history. Only explicit patient confirmation writes a timestamped record to browser localStorage. Webcam video and landmark arrays are not saved. No patient identity, cloud database, or diagnostic interpretation is introduced.
