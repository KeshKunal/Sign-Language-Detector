"""Measure model-only prediction time; this excludes webcam/landmark costs."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("--frames", type=int, default=30)
    parser.add_argument("--features", type=int, default=1662)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=200)
    parser.add_argument("--threads", type=int, default=0, help="TensorFlow intra/inter op threads; 0 uses runtime defaults")
    args = parser.parse_args()

    import tensorflow as tf

    if args.threads > 0:
        tf.config.threading.set_intra_op_parallelism_threads(args.threads)
        tf.config.threading.set_inter_op_parallelism_threads(args.threads)

    model = tf.keras.models.load_model(args.model)
    sample = np.zeros((1, args.frames, args.features), dtype=np.float32)
    modes = {
        "keras_predict": lambda: model.predict(sample, verbose=0),
        "direct_call": lambda: model(sample, training=False).numpy(),
    }
    for name, infer in modes.items():
        for _ in range(args.warmup):
            infer()
        timings = []
        for _ in range(args.repeats):
            started = time.perf_counter()
            infer()
            timings.append((time.perf_counter() - started) * 1000)
        print(
            f"{name}: median={np.median(timings):.3f} ms, "
            f"p95={np.percentile(timings, 95):.3f} ms; "
            "classifier only, excluding camera/landmarks."
        )


if __name__ == "__main__":
    main()
