import json, time
from pathlib import Path
import paho.mqtt.client as mqtt
import requests
from common import CONFIG

ROOT = Path(__file__).resolve().parent
CLOUD = CONFIG["cloud_url"].rstrip("/")
API_KEY = CONFIG["api_key"]
TOPIC = CONFIG["mqtt_topic"]

def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe(TOPIC, qos=1)
    print("[baseline] subscribed; cloud-only mode has no local persistence")

def on_message(client, userdata, msg):
    try:
        reading = json.loads(msg.payload.decode())
        if (ROOT / CONFIG.get("outage_flag", "OUTAGE.flag")).exists():
            print(f"[baseline] LOST during simulated outage: {reading['reading_id']}")
            return
        payload = {"readings": [{
            "reading_id": reading["reading_id"], "sensor_id": reading["sensor_id"],
            "timestamp": reading["timestamp"], "temperature": reading["temperature"],
            "humidity": reading.get("humidity"), "source": "baseline"
        }]}
        r = requests.post(f"{CLOUD}/readings/batch", json=payload,
                          headers={"X-API-Key": API_KEY}, timeout=2)
        r.raise_for_status()
        print(f"[baseline] cloud accepted reading {reading['reading_id']}")
    except requests.RequestException as exc:
        print(f"[baseline] LOST / cloud request failed: {exc}")
    except Exception as exc:
        print(f"[baseline] message error: {exc}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="coldchain-baseline")
client.on_connect = on_connect
client.on_message = on_message
client.connect(CONFIG["mqtt_host"], int(CONFIG["mqtt_port"]), 60)
print("Cloud-only baseline running. Ctrl+C to stop.")
try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()
