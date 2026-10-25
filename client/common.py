import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "config.json").read_text())
def utc_now():
    return datetime.now(timezone.utc).isoformat()
def new_id():
    return str(uuid.uuid4())
def db_connect(path):
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn
def ensure_local_db(path):
    with db_connect(path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS readings (
            reading_id TEXT PRIMARY KEY,
            sensor_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL,
            uploaded INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )""")
        conn.commit()
def in_outage():
    return (ROOT / CONFIG.get("outage_flag", "OUTAGE.flag")).exists()
def is_out_of_range(temp):
    return temp < float(CONFIG["temperature_min"]) or temp > float(CONFIG["temperature_max"])
