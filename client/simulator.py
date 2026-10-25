import json, random, time, uuid
from datetime import datetime, timezone
from pathlib import Path
import paho.mqtt.client as mqtt

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "config.json").read_text())
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"sensor-sim-{uuid.uuid4().hex[:8]}")
client.connect(CFG["mqtt_host"], int(CFG["mqtt_port"]), 60)
client.loop_start()
print("Sensor simulator running. Ctrl+C to stop.")
try:
    n = 0
    while True:
        n += 1
        # Most readings are normal; occasional excursions make alert demos visible.
        temp = round(random.uniform(3.0, 7.0), 2) if n % 8 else round(random.choice([random.uniform(-1, 1), random.uniform(9, 12)]), 2)
        reading = {
            "reading_id": str(uuid.uuid4()),
            "sensor_id": f"sensor-{(n % 3) + 1}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": temp,
            "humidity": round(random.uniform(40, 75), 1),
        }
        client.publish(CFG["mqtt_topic"], json.dumps(reading), qos=1)
        print(f"Published {reading['sensor_id']} temperature={temp}°C id={reading['reading_id']}")
        time.sleep(max(1, int(CFG.get("sensor_interval_seconds", 2))))
except KeyboardInterrupt:
    print("Stopping simulator...")
finally:
    client.loop_stop()
    client.disconnect()
