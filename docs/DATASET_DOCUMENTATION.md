# Dataset documentation

## Source and layout

The local dataset is preprocessed MediaPipe Holistic feature data, not video. It is organized as `video_data/<class>/<sequence>/<frame>.npy`. Each numeric sequence folder is one 30-frame recording; its numeric frame files are ordered by their integer filename, not lexicographically.

There are 9 classes × 30 sequences × 30 frames = 270 sequences and 8,100 frame arrays. Every frame is a one-dimensional array with 1,662 finite numbers stored as float64. The model loader converts arrays to float32.

## Feature layout

| Feature group | Layout | Values |
|---|---|---:|
| Pose | 33 points × (x, y, z, visibility) | 132 |
| Face | 468 points × (x, y, z) | 1,404 |
| Left hand | 21 points × (x, y, z) | 63 |
| Right hand | 21 points × (x, y, z) | 63 |
| **Total per frame** | | **1,662** |

Feature order and missing-landmark zero fill follow `sld.realtime.extract_keypoints`.

## Labels

The stable model output order is headache, sore throat, cough, fever, stomach aches, tired, runny nose, nausea, trouble breathing. The historical folder spelling `soar throat` is preserved on disk and mapped by the loader.

## Validation and limitations

Run `python -m ml.preprocessing.validate_dataset` to validate every expected frame and write `ml/results/dataset_validation.json`. The sequence boundaries are explicit in the directory layout, so frame grouping does not require guessing. No signer metadata or raw recordings are included; a sequence-level random split may put the same signer in both partitions. Results must not be described as signer-independent.
