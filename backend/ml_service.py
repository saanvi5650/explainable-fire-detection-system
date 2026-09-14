import json
import numpy as np
from .config import MODEL_PATH, SCALER_PATH, METADATA_PATH, BACKGROUND_PATH, FEATURES, TIERS, SEQUENCE_LENGTH

class MLService:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.explainer = None
        self.load_error = None
        self._load()

    def _load(self):
        if not (MODEL_PATH.exists() and SCALER_PATH.exists()):
            return
        try:
            import joblib
            from tensorflow import keras
            self.model = keras.models.load_model(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
        except Exception as exc:
            self.load_error = str(exc)

    @property
    def ready(self):
        return self.model is not None and self.scaler is not None

    def predict(self, window):
        if not self.ready or len(window) < SEQUENCE_LENGTH:
            return None
        raw = np.asarray([[float(getattr(row, feature)) for feature in FEATURES] for row in window], dtype=np.float32)
        scaled = self.scaler.transform(raw).reshape(1, SEQUENCE_LENGTH, len(FEATURES))
        probabilities_array = self.model.predict(scaled, verbose=0)[0]
        index = int(np.argmax(probabilities_array))
        return {
            "tier": TIERS[index],
            "confidence": float(probabilities_array[index]),
            "probabilities": {TIERS[i]: round(float(value), 5) for i, value in enumerate(probabilities_array)},
            "scaled_window": scaled,
            "class_index": index
        }

    def shap_contributions(self, scaled_window, class_index):
        if not self.ready or not BACKGROUND_PATH.exists():
            return None
        try:
            import shap
            if self.explainer is None:
                background = np.load(BACKGROUND_PATH)
                self.explainer = shap.GradientExplainer(self.model, background)
            values = self.explainer.shap_values(scaled_window)
            if isinstance(values, list):
                selected = np.asarray(values[class_index])[0]
            else:
                array = np.asarray(values)
                if array.ndim == 4 and array.shape[-1] == len(TIERS):
                    selected = array[0, :, :, class_index]
                elif array.ndim == 4 and array.shape[0] == len(TIERS):
                    selected = array[class_index, 0]
                else:
                    return None
            totals = np.sum(np.abs(selected), axis=0)
            return {FEATURES[i]: float(totals[i]) for i in range(len(FEATURES))}
        except Exception:
            return None

ml_service = MLService()
