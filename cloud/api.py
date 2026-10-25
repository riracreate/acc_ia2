import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from typing import Any
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

DB_PATH = os.getenv("COLDCHAIN_DB", "/home/ubuntu/coldchain/cloud.db")
API_KEY = os.getenv("COLDCHAIN_API_KEY", "replace-this-with-a-long-random-secret")

app = FastAPI(title="ColdChainGuard Cloud API", version="1.0.0")

def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            reading_id TEXT PRIMARY KEY,
            sensor_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL,
            source TEXT NOT NULL DEFAULT 'fog',
            received_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

class Reading(BaseModel):
    reading_id: str = Field(min_length=1, max_length=128)
    sensor_id: str = Field(min_length=1, max_length=128)
    timestamp: str
    temperature: float
    humidity: float | None = None
    source: str = "fog"

class ReadingBatch(BaseModel):
    readings: list[Reading] = Field(min_length=1, max_length=500)

@app.get("/health")
def health():
    try:
        with closing(connect()) as conn:
            conn.execute("SELECT 1")
        return {"ok": True, "service": "coldchainguard-api", "utc": datetime.now(timezone.utc).isoformat()}
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}")

@app.post("/readings/batch")
def ingest_batch(batch: ReadingBatch, x_api_key: str | None = Header(default=None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    inserted = 0
    duplicates = 0
    received_at = datetime.now(timezone.utc).isoformat()
    with closing(connect()) as conn:
        for item in batch.readings:
            cur = conn.execute(
                """INSERT OR IGNORE INTO readings
                (reading_id, sensor_id, timestamp, temperature, humidity, source, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (item.reading_id, item.sensor_id, item.timestamp, item.temperature,
                 item.humidity, item.source, received_at)
            )
            if cur.rowcount == 1:
                inserted += 1
            else:
                duplicates += 1
        conn.commit()
    return {"ok": True, "inserted": inserted, "duplicates": duplicates, "received": len(batch.readings)}

@app.get("/readings")
def list_readings(limit: int = 100, x_api_key: str | None = Header(default=None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    limit = max(1, min(limit, 1000))
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM readings ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    return {"readings": [dict(row) for row in rows], "count": len(rows)}

@app.get("/stats")
def stats(x_api_key: str | None = Header(default=None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    with closing(connect()) as conn:
        total = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
        alerts = conn.execute("SELECT COUNT(*) FROM readings WHERE temperature < 2 OR temperature > 8").fetchone()[0]
        latest = conn.execute("SELECT MAX(timestamp) FROM readings").fetchone()[0]
    return {"total_readings": total, "out_of_range_readings": alerts, "latest_timestamp": latest}
