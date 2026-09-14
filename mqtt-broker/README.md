# MQTT broker setup

Install Mosquitto locally and use a local-only listener during development.

Topics:
- firenode/NODE_01/data: ESP32 to backend
- firenode/NODE_01/risk: backend to ESP32
- firenode/NODE_01/explain: optional explanation stream

Run the bridge after the API with: python -m backend.mqtt_bridge

For any networked deployment, configure authentication and TLS. Never expose an anonymous broker to the internet.
