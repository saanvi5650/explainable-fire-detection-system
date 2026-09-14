# Explainable Adaptive Multi-Sensor Fire Detection & Occupancy Monitoring System

A review-ready prototype that combines simulated or ESP32 sensor readings, a deterministic safety fallback, an optional LSTM classifier, occupancy-aware escalation, explainability, SQLite event storage, MQTT integration, and a live dashboard.

## Important scope note

The included synthetic dataset validates the software pipeline only. It is not evidence of real-world fire-detection accuracy. MQ-2 and MQ-7 values are treated as normalized sensor responses until physical calibration and controlled experiments are completed.

## Quick start on Windows

1. Clone the repository and open it in VS Code.
2. Create and activate a virtual environment.
3. Install requirements-core.txt.
4. Run: python -m uvicorn backend.main:app --reload
5. Open: http://127.0.0.1:8000
6. In a second terminal run: python simulator/sensor_simulator.py --scenario fire

The core application runs without TensorFlow. To train and enable the preliminary LSTM, install requirements-ml.txt, run model/generate_data.py, and then model/train.py.

## Scenarios

safe, cooking, smouldering, fire, occupied_fire

## Main API routes

- GET /health
- POST /api/readings
- GET /nodes
- GET /nodes/{node_id}/status
- GET /nodes/{node_id}/history
- GET /metrics/summary
