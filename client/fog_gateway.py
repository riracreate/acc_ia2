import json, sqlite3, time
from pathlib import Path
import paho.mqtt.client as mqtt
import requests
from common import ROOT, CONFIG, ensure_local_db, db_connect, utc_now, is_out_of_range, in_outage

DB_PATH = ROOT / CONFIG.get("local_db", "fog.db")
ensure_local_db(DB_PATH)
CLOUD = CONFIG["cloud_url"].rstrip("/")
API_KEY = CONFIG["api_key"]
TOPIC = CONFIG["mqtt_topic"]

def store(reading):
    with db_connect(DB_PATH) as conn:
        cur = conn.execute(
            """INSERT OR IGNORE INTO readings
            (reading_id, sensor_id, timestamp, temperature, humidity, uploaded, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?)""",
            (reading["reading_id"], reading["sensor_id"], reading["timestamp"],
             float(reading["temperature"]), reading.get("humidity"), utc_now())
        )
        conn.commit()
        return cur.rowcount == 1

def pending_batch(limit=100):
    with db_connect(DB_PATH) as conn:
        rows = conn.execute("SELECT * FROM readings WHERE uploaded=0 ORDER BY created_at LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

def sync_pending():
    if in_outage():
        return
    rows = pending_batch()
    if not rows:
        return
    payload = {"readings": [
        {"reading_id": r["reading_id"], "sensor_id": r["sensor_id"], "timestamp": r["timestamp"],
         "temperature": r["temperature"], "humidity": r["humidity"], "source": "fog"}
        for r in rows
    ]}
    try:
        response = requests.post(f"{CLOUD}/readings/batch", json=payload,
                                 headers={"X-API-Key": API_KEY}, timeout=5)
        response.raise_for_status()
        with db_connect(DB_PATH) as conn:
            conn.executemany("UPDATE readings SET uploaded=1 WHERE reading_id=?",
                             [(r["reading_id"],) for r in rows])
            conn.commit()
        print(f"[sync] uploaded {response.json().get('inserted', 0)}; duplicates {response.json().get('duplicates', 0)}; pending buffer flushed")
    except requests.RequestException as exc:
        print(f"[sync] cloud unavailable; readings safely buffered ({exc})")

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"[mqtt] connected: {reason_code}")
    client.subscribe(TOPIC, qos=1)

def on_message(client, userdata, msg):
    try:
        reading = json.loads(msg.payload.decode())
        inserted = store(reading)
        if inserted and is_out_of_range(float(reading["temperature"])):
            print(f"[LOCAL ALERT] {reading['sensor_id']} temperature {reading['temperature']}°C outside 2–8°C")
        elif not inserted:
            print(f"[dedupe] ignored repeated reading {reading.get('reading_id')}")
    except Exception as exc:
        print(f"[mqtt] invalid message: {exc}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="coldchain-fog-gateway")
client.on_connect = on_connect
client.on_message = on_message
print(f"Fog gateway listening on {TOPIC}; local DB: {DB_PATH}")
client.connect(CONFIG["mqtt_host"], int(CONFIG["mqtt_port"]), 60)
client.loop_start()
try:
    while True:
        sync_pending()
        time.sleep(3)
except KeyboardInterrupt:
    print("Stopping gateway...")
finally:
    client.loop_stop()
    client.disconnect()
