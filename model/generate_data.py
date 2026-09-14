from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "synthetic_sequences.npz"
RNG = np.random.default_rng(42)
SEQ_LEN = 40
FEATURE_COUNT = 7

def clip(values, low, high):
    return np.clip(values, low, high)

def make_sequence(label):
    t = np.linspace(0, 1, SEQ_LEN)
    noise = lambda scale: RNG.normal(0, scale, SEQ_LEN)

    if label == 0:  # Safe
        mq2 = 0.14 + noise(0.025)
        mq7 = 0.11 + noise(0.02)
        temp = 28 + noise(0.5)
        humidity = 55 + noise(1.5)
        flame = np.zeros(SEQ_LEN)
        occupied = RNG.integers(0, 2)
    elif label == 1:  # Warning/cooking-like smoke
        mq2 = 0.18 + 0.35*t + noise(0.03)
        mq7 = 0.12 + 0.12*t + noise(0.025)
        temp = 29 + 6*t + noise(0.6)
        humidity = 53 - 3*t + noise(1.5)
        flame = np.zeros(SEQ_LEN)
        occupied = RNG.integers(0, 2)
    elif label == 2:  # Critical/smouldering fire
        mq2 = 0.25 + 0.52*t + noise(0.035)
        mq7 = 0.20 + 0.46*t + noise(0.03)
        temp = 30 + 20*t + noise(0.8)
        humidity = 52 - 10*t + noise(1.3)
        flame = (t > 0.82).astype(float) if RNG.random() > 0.45 else np.zeros(SEQ_LEN)
        occupied = 0
    else:  # Evacuate: strong evidence with occupancy
        mq2 = 0.30 + 0.62*t + noise(0.03)
        mq7 = 0.25 + 0.58*t + noise(0.03)
        temp = 31 + 32*t + noise(1.0)
        humidity = 50 - 15*t + noise(1.5)
        flame = (t > 0.55).astype(float)
        occupied = 1

    pir = np.full(SEQ_LEN, occupied, dtype=float)
    mmwave = np.full(SEQ_LEN, occupied, dtype=float)
    if occupied:
        pir[RNG.random(SEQ_LEN) < 0.18] = 0  # PIR can miss stationary people

    return np.column_stack([
        clip(mq2, 0, 1), clip(mq7, 0, 1), flame,
        clip(temp, -20, 150), clip(humidity, 0, 100),
        pir, mmwave
    ]).astype(np.float32)

def main():
    counts = {0: 160, 1: 110, 2: 100, 3: 100}
    sequences, labels, event_ids = [], [], []
    event_id = 0
    for label, count in counts.items():
        for _ in range(count):
            sequences.append(make_sequence(label))
            labels.append(label)
            event_ids.append(event_id)
            event_id += 1

    x = np.asarray(sequences, dtype=np.float32)
    y = np.asarray(labels, dtype=np.int64)
    ids = np.asarray(event_ids, dtype=np.int64)
    order = RNG.permutation(len(y))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUTPUT, x=x[order], y=y[order], event_ids=ids[order])
    print(f"Saved {len(y)} independent synthetic sequences to {OUTPUT}")
    print("Shape:", x.shape)
    print("Important: synthetic data validates the pipeline, not real-world accuracy.")

if __name__ == "__main__":
    main()
