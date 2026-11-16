# MediSign ASL nine-symptom research plan

## Current scope and evidence

The immediate target is the repository’s existing nine ASL symptom signs. The local data has 270 landmark sequences: 30 per class, 30 frames each, 1,662 MediaPipe Holistic features per frame. It contains no raw videos, signer identifiers, or verified signer-disjoint split metadata. Its random clip split therefore measures performance on clips from the collected pool, not generalization to unseen people.

A fixed seed-42 split (172 train, 44 validation, 54 test) compared the existing three-LSTM classifier with compact classical models. Candidate choice used validation macro-F1; the chosen candidate was evaluated once on the held-out test set. The selected 30-frame hand-landmark summary SVM achieved 96.3% test accuracy and 0.963 macro-F1, compared with 94.4% and 0.943 for the existing LSTM. Per-sample classifier latency was 0.14 ms median / 0.31 ms p95 for the SVM and 45.6 / 53.6 ms for the LSTM in the same WSL environment. These are model-only timings, not webcam-to-result latency. The small test set means a difference of one prediction changes accuracy by 1.85 percentage points. This is promising pilot evidence, not proof of robust improvement. See `ml/results/nine_class_model_comparison.json`.

The SVM summary uses the mean, standard deviation, range, and average frame-to-frame absolute change for the two hand regions. Omitting face and pose landmarks was the best validation result on this source dataset, but this may reflect its collection setup and should not be taken as evidence that facial expression or body posture is unimportant in ASL. Keep the original LSTM available as a baseline. The local joblib candidate is an ignored, reproducible artifact and must not be mistaken for an externally validated model.

## Immediate improvement work

1. Use the selected SVM in the local demo as an optional backend model to remove TensorFlow startup/runtime overhead. Keep the 30-frame input until experiments show that shorter prefixes preserve accuracy; the 8/12/16/20-frame SVM variants performed worse on validation than 30 frames.
2. Profile total camera-to-result time in the browser, splitting MediaPipe landmark extraction, request/serialization, server time, and vote stabilization. Classifier acceleration alone cannot fix slow camera processing.
3. Collect more varied samples for the current nine labels: multiple signers, both hands/dominance where relevant, lighting/background/camera changes, natural sign speed, and repeated sessions. Record consent, label provenance, signer/session IDs, and capture conditions. Split by signer and session before any tuning.
4. Review weak/ambiguous labels (stomach aches, tired, runny nose, sore throat, headache) with Deaf ASL users and sign-language educators. Check sign variants and whether each target is one lexical sign or a phrase. Add a “none/uncertain” path so the demo can abstain instead of force-picking one of nine classes.
5. After getting signer-disjoint data, tune temporal window, confidence calibration, smoothing and early stopping using validation signers, then report test signer results once.

## Research contribution to investigate

A plausible research direction is a **risk-controlled time-to-understanding benchmark for ASL symptom communication**: measure how quickly a system can make a correct decision as a signer performs a symptom sign, while reporting coverage and error risk when it is allowed to abstain. Compare a short calibration interaction for a new signer against zero-shot operation, on signer-disjoint participants and in real camera conditions. Include the nine current symptom concepts, signer-approved variants, and non-target/open-set signs. Report per-class recall, macro-F1, calibration, coverage-risk curves, time-to-correct-decision, and end-to-end latency.

The research hypothesis is that signer calibration plus a risk-aware temporal stopping rule can improve the speed/accuracy/coverage tradeoff for a safety-sensitive vocabulary. Early-exit sign recognition and signer adaptation already have prior literature, so neither alone is a novelty claim. The defensible contribution would need a well-designed ASL health communication benchmark, Deaf-community co-design, evaluation protocol, and measured tradeoff. A literature review and prior-art comparison must precede any claim of novelty.

The current app is a demo, not a diagnostic tool. It should not infer a medical condition or recommend care. Review labels and protocol with Deaf ASL signers, interpreters/sign-language educators, and healthcare communication experts.

## Data sources and licensing

- **ASL Citizen** provides about 84k videos across roughly 2.7k signs with signer-aware official splits. It has exact overlap for only some current symptoms (including headache, cough, and tired); it cannot fill all nine classes. Its research license is restrictive, so verify current terms before download/use, do not redistribute raw videos/features/weights, and preserve attribution. [Dataset description](https://www.microsoft.com/en-us/research/project/asl-citizen/dataset-description/)
- **Partners in Deaf Health** has ASL emergency/discharge videos, including fever and abdominal-pain topics. These are phrase-level educational videos, not a labeled isolated-sign dataset. Seek permission and human label review before reusing. [Resource videos](https://www.partnersdeafhealth.org/resources)
- ASL dictionaries can help define candidate glosses, but a single demonstration per gloss is not signer-diverse training data. For example, [SignASL symptom entries](https://www.signasl.org/sign/symptom) are useful for vocabulary exploration, not a replacement for a consented dataset.

## Existing experiments

- `ml/experiments/compare_nine_models.py`: validation-selected candidate comparison and one held-out test report for current data.
- `ml/experiments/benchmark_small_data.py`: exploratory cross-validation on the same source pool; not signer-independent evidence.
- `ml/experiments/profile_classifier.py` and `profile_tflite.py`: classifier runtime profiling and a TFLite feasibility check. TFLite conversion of the stacked LSTM hit unsupported TensorList/Flex operations in the tested environment.
- `ml/results/nine_class_model_comparison.json`: current fixed-split comparison results.

The broader ISL and expanded-vocabulary work is deferred until the nine-class ASL baseline is strengthened and evaluated on unseen signers.
