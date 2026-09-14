from fastapi.testclient import TestClient
from backend.main import app

def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

def test_ingest_and_status():
    payload = {
        "node_id": "TEST_NODE",
        "mq2": .12, "mq7": .10, "flame": 0,
        "temperature": 28, "humidity": 55, "pir": 0, "mmwave": 0
    }
    with TestClient(app) as client:
        response = client.post("/api/readings", json=payload)
        assert response.status_code == 200
        assert response.json()["adjusted_tier"] == "Safe"
        status = client.get("/nodes/TEST_NODE/status")
        assert status.status_code == 200

def test_invalid_reading_rejected():
    payload = {
        "mq2": 5, "mq7": .1, "flame": 0,
        "temperature": 28, "humidity": 55, "pir": 0, "mmwave": 0
    }
    with TestClient(app) as client:
        assert client.post("/api/readings", json=payload).status_code == 422
