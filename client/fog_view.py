import json
from pathlib import Path
import pandas as pd
import streamlit as st
from common import CONFIG, ROOT, db_connect, is_out_of_range

DB_PATH = ROOT / CONFIG.get("local_db", "fog.db")
st.set_page_config(page_title="ColdChainGuard Fog", page_icon="🌡️", layout="wide")
st.title("🌡️ ColdChainGuard — Local Fog Dashboard")
outage = (ROOT / CONFIG.get("outage_flag", "OUTAGE.flag")).exists()
if outage:
    st.error("SIMULATED OUTAGE ACTIVE — readings are buffered locally")
else:
    st.success("Simulated network available")

if not DB_PATH.exists():
    st.info("Start fog_gateway.py first to create the local database.")
else:
    with db_connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM readings ORDER BY timestamp DESC LIMIT 500", conn)
        pending = conn.execute("SELECT COUNT(*) FROM readings WHERE uploaded=0").fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Local readings", total)
    c2.metric("Pending upload", pending)
    c3.metric("Network state", "OFFLINE" if outage else "ONLINE")
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
        df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
        st.subheader("Local temperature history")
        st.line_chart(df.dropna(subset=["timestamp"]).sort_values("timestamp").set_index("timestamp")[["temperature"]])
        st.subheader("Recent local readings")
        st.dataframe(df, use_container_width=True)
