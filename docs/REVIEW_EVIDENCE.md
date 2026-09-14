# Review III evidence checklist

## Implemented software
- Executable FastAPI service and OpenAPI page
- Live dashboard with status, explanations, trends and history
- SQLite persistence
- Four-tier deterministic safety fallback
- Occupancy-aware escalation without suppressing strong fire evidence
- Forty-reading sequence buffer
- Preliminary LSTM training pipeline on explicitly synthetic scenarios
- Optional SHAP GradientExplainer integration
- MQTT bridge
- Unit and API tests

## Honest limitation statement
Current machine-learning metrics are preliminary proof-of-concept results on synthetic scenarios. They validate the software pipeline, not real-world fire-detection accuracy. Real sensor calibration and controlled physical validation remain ongoing.

## Demo order
Run safe, cooking, fire and occupied_fire scenarios; show tier changes, explanation, history, latency, API docs, tests and generated model evidence.
