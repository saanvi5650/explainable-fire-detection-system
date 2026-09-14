from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "model" / "saved"
RESULTS_DIR = ROOT / "results"
DASHBOARD_DIR = ROOT / "dashboard"
for directory in (DATA_DIR, MODEL_DIR, RESULTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "fire_system.db"
MODEL_PATH = MODEL_DIR / "fire_lstm.keras"
SCALER_PATH = MODEL_DIR / "scaler.pkl"
METADATA_PATH = MODEL_DIR / "metadata.json"
BACKGROUND_PATH = MODEL_DIR / "background.npy"
SEQUENCE_LENGTH = 40
FEATURES = ["mq2", "mq7", "flame", "temperature", "humidity", "pir", "mmwave"]
TIERS = ["Safe", "Warning", "Critical", "Evacuate"]
