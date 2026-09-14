import json
import os
import requests
import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")
API_URL = os.getenv("FIRE_API_URL", "http://127.0.0.1:8000/api/readings")

def on_connect(client, userdata, flags, reason_code, properties):
    print("MQTT connected:", reason_code)
    client.subscribe("firenode/+/data")

def on_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode("utf-8"))
        response = requests.post(API_URL, json=payload, timeout=5)
        response.raise_for_status()
        prediction = response.json()
        node_id = prediction["node_id"]
        client.publish(
            f"firenode/{node_id}/risk",
            json.dumps({
                "tier": prediction["adjusted_tier"],
                "confidence": prediction["confidence"],
                "occupied": prediction["occupied"],
                "explanation": prediction["explanation"]
            }),
            qos=1
        )
        print(node_id, prediction["adjusted_tier"])
    except Exception as exc:
        print("MQTT message error:", exc)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
if USERNAME:
    client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_forever()
