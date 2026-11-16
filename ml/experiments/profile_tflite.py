"""Compare native Keras and TFLite inference for the current LSTM checkpoint."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np


def measure(call, repeats: int) -> np.ndarray:
    timings = []
    for _ in range(10):
        call()
    for _ in range(repeats):
        started = time.perf_counter()
        call()
        timings.append((time.perf_counter() - started) * 1000)
    return np.asarray(timings)


def report(name: str, times: np.ndarray) -> None:
    print(f"{name}: median={np.median(times):.2f} ms, p95={np.percentile(times, 95):.2f} ms")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("--repeats", type=int, default=50)
    args = parser.parse_args()

    import tensorflow as tf

    model = tf.keras.models.load_model(args.model)
    sample = np.random.default_rng(42).normal(size=(1, 30, 1662)).astype(np.float32)
    keras_output = np.asarray(model.predict(sample, verbose=0))
    report("Keras predict", measure(lambda: model.predict(sample, verbose=0), args.repeats))

    def converter_for(dynamic_range: bool):
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        # Keras LSTMs contain TensorList ops; the TF Select ops bridge is needed.
        converter.target_spec.supported_ops = [
            tf.lite.OpsSet.TFLITE_BUILTINS,
            tf.lite.OpsSet.SELECT_TF_OPS,
        ]
        converter._experimental_lower_tensor_list_ops = False
        if dynamic_range:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
        return converter

    float_model = converter_for(dynamic_range=False).convert()
    dynamic_model = converter_for(dynamic_range=True).convert()

    for name, content in (("TFLite float32", float_model), ("TFLite dynamic range", dynamic_model)):
        try:
            interpreter = tf.lite.Interpreter(model_content=content)
            interpreter.allocate_tensors()
        except (RuntimeError, ValueError) as exc:
            print(f"{name}: interpreter unavailable ({exc})")
            continue
        input_info = interpreter.get_input_details()[0]
        output_info = interpreter.get_output_details()[0]
        interpreter.set_tensor(input_info["index"], sample)
        interpreter.invoke()
        output = interpreter.get_tensor(output_info["index"])
        print(f"{name}: max abs output delta={np.max(np.abs(output - keras_output)):.6f}")

        def call():
            interpreter.set_tensor(input_info["index"], sample)
            interpreter.invoke()
            interpreter.get_tensor(output_info["index"])

        report(name, measure(call, args.repeats))


if __name__ == "__main__":
    main()
