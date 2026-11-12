from ast import literal_eval
from collections import Counter
from pathlib import Path
import struct

DATASET_PATH = Path("video_data")
files = sorted(DATASET_PATH.rglob("*.npy"))


def read_npy_header(path):
    with path.open("rb") as stream:
        if stream.read(6) != b"\x93NUMPY":
            raise ValueError(f"Not a NumPy .npy file: {path}")
        major, _minor = stream.read(2)
        if major == 1:
            header_length = struct.unpack("<H", stream.read(2))[0]
        elif major in (2, 3):
            header_length = struct.unpack("<I", stream.read(4))[0]
        else:
            raise ValueError(f"Unsupported .npy version {major}: {path}")
        header = literal_eval(stream.read(header_length).decode("latin1").strip())
        return header, stream.tell(), path.stat().st_size


print("Total NPY files:", len(files))
print("\nClass distribution:")
for folder in sorted(path for path in DATASET_PATH.iterdir() if path.is_dir()):
    count = sum(1 for _ in folder.rglob("*.npy"))
    print(f"{folder.name}: {count}")

print("\nInspecting sample files:")
shapes = Counter()
dtypes = Counter()
for path in files:
    header, payload_offset, total_size = read_npy_header(path)
    shape = header["shape"]
    dtype = header["descr"]
    shapes[str(shape)] += 1
    dtypes[str(dtype)] += 1
    if path in files[:15]:
        print(
            f"{path} | Shape: {shape} | Dtype: {dtype} | "
            f"Size: {(total_size - payload_offset) / 1024:.2f} KB"
        )

print("\nShape distribution:")
for shape, count in sorted(shapes.items()):
    print(f"{shape}: {count}")
print("\nDtype distribution:")
for dtype, count in sorted(dtypes.items()):
    print(f"{dtype}: {count}")

print("\nSequence completeness (expected frame names 0.npy through 29.npy):")
for folder in sorted(path for path in DATASET_PATH.iterdir() if path.is_dir()):
    sequences = sorted(path for path in folder.iterdir() if path.is_dir())
    complete = sum(
        {f"{index}.npy" for index in range(30)}
        == {path.name for path in sequence.glob("*.npy")}
        for sequence in sequences
    )
    print(f"{folder.name}: {complete}/{len(sequences)} complete sequences")
