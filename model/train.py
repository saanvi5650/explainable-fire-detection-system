import json
from pathlib import Path
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
from tensorflow import keras
from tensorflow.keras import layers

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "synthetic_sequences.npz"
SAVE_DIR = ROOT / "model" / "saved"
RESULTS_DIR = ROOT / "results"
TIERS = ["Safe", "Warning", "Critical", "Evacuate"]
FEATURES = ["mq2", "mq7", "flame", "temperature", "humidity", "pir", "mmwave"]

def main():
    if not DATA_FILE.exists():
        raise SystemExit("Run: python model/generate_data.py")

    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    loaded = np.load(DATA_FILE)
    x, y = loaded["x"], loaded["y"]

    indices = np.arange(len(y))
    train_idx, temp_idx = train_test_split(
        indices, test_size=0.30, random_state=42, stratify=y
    )
    val_idx, test_idx = train_test_split(
        temp_idx, test_size=0.50, random_state=42, stratify=y[temp_idx]
    )

    scaler = StandardScaler()
    scaler.fit(x[train_idx].reshape(-1, x.shape[-1]))

    def transform(part):
        return scaler.transform(x[part].reshape(-1, x.shape[-1])).reshape(
            len(part), x.shape[1], x.shape[2]
        ).astype(np.float32)

    x_train, x_val, x_test = transform(train_idx), transform(val_idx), transform(test_idx)
    y_train, y_val, y_test = y[train_idx], y[val_idx], y[test_idx]

    model = keras.Sequential([
        layers.Input(shape=(x.shape[1], x.shape[2])),
        layers.LSTM(64, return_sequences=True),
        layers.Dropout(0.2),
        layers.LSTM(32),
        layers.Dropout(0.2),
        layers.Dense(16, activation="relu"),
        layers.Dense(4, activation="softmax")
    ])
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )

    classes = np.unique(y_train)
    weights = compute_class_weight(class_weight="balanced", classes=classes, y=y_train)
    class_weight = {int(c): float(w) for c, w in zip(classes, weights)}

    history = model.fit(
        x_train, y_train,
        validation_data=(x_val, y_val),
        epochs=40,
        batch_size=32,
        class_weight=class_weight,
        callbacks=[keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=6, restore_best_weights=True
        )],
        verbose=1
    )

    probabilities = model.predict(x_test, verbose=0)
    predictions = probabilities.argmax(axis=1)
    report = classification_report(
        y_test, predictions, target_names=TIERS, output_dict=True, zero_division=0
    )
    matrix = confusion_matrix(y_test, predictions, labels=[0, 1, 2, 3])

    safe_mask = y_test == 0
    dangerous_mask = np.isin(y_test, [2, 3])
    false_alarm_rate = float(np.mean(predictions[safe_mask] != 0)) if safe_mask.any() else 0
    missed_detection_rate = float(np.mean(predictions[dangerous_mask] == 0)) if dangerous_mask.any() else 0

    model.save(SAVE_DIR / "fire_lstm.keras")
    joblib.dump(scaler, SAVE_DIR / "scaler.pkl")
    np.save(SAVE_DIR / "background.npy", x_train[:32])
    metadata = {
        "sequence_length": int(x.shape[1]),
        "features": FEATURES,
        "tiers": TIERS,
        "data_source": "synthetic proof-of-concept",
        "test_accuracy": float(report["accuracy"]),
        "macro_f1": float(report["macro avg"]["f1-score"]),
        "false_alarm_rate": false_alarm_rate,
        "missed_detection_rate": missed_detection_rate
    }
    (SAVE_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2))

    plt.figure(figsize=(7, 5))
    sns.heatmap(matrix, annot=True, fmt="d", cmap="Reds", xticklabels=TIERS, yticklabels=TIERS)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "confusion_matrix.png", dpi=180)
    plt.close()

    plt.figure(figsize=(8, 4))
    plt.plot(history.history["accuracy"], label="Training")
    plt.plot(history.history["val_accuracy"], label="Validation")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "training_history.png", dpi=180)
    plt.close()

    (RESULTS_DIR / "metrics.json").write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata, indent=2))
    print("Model and review evidence saved successfully.")
    print("These metrics describe synthetic proof-of-concept data only.")

if __name__ == "__main__":
    main()
