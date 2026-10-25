import json, sqlite3
from pathlib import Path
import requests
from common import ROOT, CONFIG

db = ROOT / CONFIG.get("local_db", "fog.db")
if not db.exists():
    raise SystemExit("Local database not found. Start fog_gateway.py and simulator.py first.")
with sqlite3.connect(db) as conn:
    conn.row_factory = sqlite3.Row
    total = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM readings WHERE uploaded=0").fetchone()[0]
    alerts = conn.execute("SELECT COUNT(*) FROM readings WHERE temperature < ? OR temperature > ?",
                          (CONFIG["temperature_min"], CONFIG["temperature_max"])).fetchone()[0]
    rows = conn.execute("SELECT reading_id FROM readings").fetchall()
print("LOCAL FOG RESULTS")
print({"local_readings": total, "pending_upload": pending, "out_of_range_readings": alerts,
       "locally_buffered_or_unsynced": pending})
try:
    r = requests.get(CONFIG["cloud_url"].rstrip("/") + "/stats",
                     headers={"X-API-Key": CONFIG["api_key"]}, timeout=5)
    r.raise_for_status()
    print("CLOUD RESULTS")
    print(r.json())
except requests.RequestException as exc:
    print(f"Cloud stats unavailable: {exc}")
print("Note: this starter evaluator reports observed counts; run controlled repeated trials before claiming latency or data-loss percentages.")
