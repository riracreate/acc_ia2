"""Cloud monitoring dashboard for ColdChainGuard."""

from __future__ import annotations

import html
import math
import os
from datetime import datetime, timezone

import altair as alt
import pandas as pd
import requests
import streamlit as st


API_URL = os.getenv("COLDCHAIN_API_URL", "http://127.0.0.1:8000").rstrip("/")
API_KEY = os.getenv("COLDCHAIN_API_KEY", "replace-this-with-a-long-random-secret")
LOWER_LIMIT = 2.0
UPPER_LIMIT = 8.0
READINGS_LIMIT = 500


st.set_page_config(
    page_title="ColdChainGuard | Cloud monitoring",
    page_icon="❄",
    layout="wide",
)


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] { background: #f3f7fb; }
        .block-container { max-width: 1480px; padding-top: 2rem; padding-bottom: 3rem; }
        [data-testid="stSidebar"] { background: #10263b; }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label { color: #e8f1f7 !important; }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
            color: #adc4d3 !important;
        }
        [data-testid="stSidebar"] hr { border-color: #365268; }
        [data-testid="stSidebar"] button[kind="primary"] {
            background: #8bd6e5; color: #0b263a; border: 0; font-weight: 700;
        }
        .ccg-hero {
            color: #f7fcff; background: linear-gradient(120deg, #10263b 0%, #123b54 100%);
            border: 1px solid #234e65; border-radius: 16px;
            padding: 1.75rem 2rem 1.55rem; margin-bottom: 1.8rem;
            box-shadow: 0 10px 30px rgba(16, 38, 59, .10);
        }
        .ccg-hero-title { display: flex; align-items: center; gap: .9rem; }
        .ccg-icon {
            width: 3rem; height: 3rem; display: inline-flex; align-items: center;
            justify-content: center; flex: 0 0 auto; border-radius: 12px;
            color: #c3f1fa; background: #244e65; font-size: 1.75rem;
        }
        .ccg-eyebrow { color: #9dd9e7; font-size: .74rem; font-weight: 700;
            letter-spacing: .13em; text-transform: uppercase; margin-bottom: .2rem; }
        .ccg-hero h1 { color: #fff; font-size: 2rem; line-height: 1.15;
            letter-spacing: -.03em; margin: 0; }
        .ccg-hero p { color: #c5d9e4; margin: 1rem 0 0; font-size: .95rem; }
        .ccg-range { display: inline-block; margin-top: 1.1rem; padding: .38rem .7rem;
            color: #d8f6fb; background: #225068; border: 1px solid #42748b;
            border-radius: 7px; font-size: .77rem; font-weight: 650; letter-spacing: .04em; }
        .ccg-section-title { color: #102a3e; font-size: 1.28rem; font-weight: 720;
            letter-spacing: -.02em; margin: 1.65rem 0 .15rem; }
        .ccg-section-note { color: #607588; font-size: .87rem; margin: 0 0 .9rem; }
        .ccg-card {
            background: #fff; border: 1px solid #dce7ee; border-radius: 12px;
            min-height: 125px; padding: 1rem 1.15rem; margin-bottom: .2rem;
            box-shadow: 0 3px 13px rgba(19, 53, 76, .035);
        }
        .ccg-card-label { color: #617789; font-size: .72rem; font-weight: 750;
            letter-spacing: .09em; text-transform: uppercase; }
        .ccg-card-value { color: #15354a; font-size: 1.78rem; font-weight: 750;
            letter-spacing: -.04em; line-height: 1.18; margin-top: .65rem; }
        .ccg-card-value.ccg-long { font-size: 1.1rem; letter-spacing: -.01em;
            line-height: 1.45; margin-top: .75rem; }
        .ccg-card-note { color: #758898; font-size: .76rem; margin-top: .35rem; }
        .ccg-card.ccg-online { border-top: 3px solid #159c83; }
        .ccg-card.ccg-offline { border-top: 3px solid #c75656; }
        .ccg-card.ccg-online .ccg-card-value { color: #087966; }
        .ccg-card.ccg-offline .ccg-card-value { color: #ba4747; }
        .ccg-status-dot { display: inline-block; width: .52rem; height: .52rem;
            border-radius: 50%; background: currentColor; margin-right: .35rem;
            vertical-align: .15rem; }
        .ccg-side-brand { color: #f3faff; font-size: 1.04rem; font-weight: 760;
            letter-spacing: -.02em; margin: .25rem 0 .18rem; }
        .ccg-side-subtitle { color: #a9c1d0; font-size: .78rem; margin-bottom: 1.3rem; }
        .ccg-side-status { border: 1px solid #416276; border-radius: 9px;
            background: #18364d; color: #d8eff4; padding: .75rem .85rem;
            margin: .8rem 0 1.2rem; font-size: .8rem; font-weight: 700; }
        .ccg-side-status.ccg-side-offline { color: #ffd4d4; border-color: #8f565b; }
        .ccg-summary { display: flex; gap: .7rem; flex-wrap: wrap; margin: .2rem 0 .9rem; }
        .ccg-summary-item { background: #fff; border: 1px solid #dce7ee;
            border-radius: 8px; padding: .55rem .8rem; color: #42596b;
            font-size: .84rem; font-weight: 600; }
        .ccg-summary-item strong { font-size: 1rem; margin-right: .3rem; }
        .ccg-summary-low { border-left: 3px solid #3882bd; }
        .ccg-summary-high { border-left: 3px solid #d26a48; }
        .ccg-summary-low strong { color: #286d9e; }
        .ccg-summary-high strong { color: #b75132; }
        [data-testid="stDataFrame"] { border: 1px solid #dce7ee; border-radius: 9px; }
        @media (max-width: 760px) {
            .ccg-hero { padding: 1.35rem; }
            .ccg-hero h1 { font-size: 1.55rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def request_json(path: str, *, authenticated: bool = False, timeout: int = 6):
    headers = {"X-API-Key": API_KEY} if authenticated else None
    try:
        response = requests.get(f"{API_URL}{path}", headers=headers, timeout=timeout)
    except requests.Timeout:
        return None, "The request timed out. Check the API service and network."
    except requests.ConnectionError:
        return None, "Could not connect to the API. Check the service and configured URL."
    except requests.RequestException:
        return None, "The API request failed. Check the service and network."

    if response.status_code in (401, 403):
        return None, "Authentication failed. Check COLDCHAIN_API_KEY."
    if response.status_code == 503:
        return None, "The API reported a service or database outage (HTTP 503)."
    if not response.ok:
        return None, f"The API returned HTTP {response.status_code}."
    try:
        data = response.json()
    except ValueError:
        return None, "The API returned invalid JSON."
    if not isinstance(data, dict):
        return None, "The API returned an unexpected response format."
    return data, None


def parse_number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def parse_timestamp(value):
    if not isinstance(value, (str, datetime, pd.Timestamp)) or not str(value).strip():
        return pd.NaT
    try:
        return pd.to_datetime(value, errors="coerce", utc=True)
    except (TypeError, ValueError, OverflowError):
        return pd.NaT


def format_timestamp(value) -> str:
    parsed = parse_timestamp(value)
    return "—" if pd.isna(parsed) else parsed.strftime("%d %b %Y, %H:%M:%S UTC")


def format_number(value, *, unit: str = "") -> str:
    number = parse_number(value)
    return "—" if number is None else f"{number:.1f}{unit}"


def format_count(value) -> str:
    number = parse_number(value)
    return f"{int(number):,}" if number is not None and number >= 0 and number.is_integer() else "—"


def text_or_placeholder(value) -> str:
    if value is None or isinstance(value, (list, dict)):
        return "—"
    try:
        if pd.isna(value):
            return "—"
    except (TypeError, ValueError):
        return "—"
    return str(value).strip() or "—"


def temperature_status(value) -> str:
    if value is None:
        return "UNKNOWN"
    if value < LOWER_LIMIT:
        return "LOW"
    if value > UPPER_LIMIT:
        return "HIGH"
    return "SAFE"


def normalize_readings(readings: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(readings)
    if not readings:
        return frame
    frame["_timestamp"] = pd.to_datetime(
        [parse_timestamp(item.get("timestamp")) for item in readings],
        utc=True,
        errors="coerce",
    )
    frame["_temperature"] = [parse_number(item.get("temperature")) for item in readings]
    frame["_humidity"] = [parse_number(item.get("humidity")) for item in readings]
    frame["_status"] = [temperature_status(value) for value in frame["_temperature"]]
    frame["_sensor"] = [text_or_placeholder(item.get("sensor_id")) for item in readings]
    return frame.sort_values("_timestamp", ascending=False, kind="stable", na_position="last")


def render_metric(label: str, value: str, note: str, *, tone: str = "", long: bool = False) -> None:
    value_class = "ccg-card-value ccg-long" if long else "ccg-card-value"
    indicator = '<span class="ccg-status-dot"></span>' if tone else ""
    st.markdown(
        f'<div class="ccg-card {tone}">'
        f'<div class="ccg-card-label">{html.escape(label)}</div>'
        f'<div class="{value_class}">{indicator}{html.escape(value)}</div>'
        f'<div class="ccg-card-note">{html.escape(note)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_section(title: str, note: str) -> None:
    st.markdown(
        f'<div class="ccg-section-title">{html.escape(title)}</div>'
        f'<div class="ccg-section-note">{html.escape(note)}</div>',
        unsafe_allow_html=True,
    )


def render_chart(frame: pd.DataFrame) -> None:
    chart_frame = frame.dropna(subset=["_timestamp", "_temperature"])
    if chart_frame.empty:
        st.info("No readings with valid timestamps and temperatures are available for the trend chart.")
        return

    plot_data = pd.DataFrame(
        {
            "Timestamp": chart_frame["_timestamp"],
            "Temperature": chart_frame["_temperature"],
            "Status": chart_frame["_status"],
            "Sensor": chart_frame["_sensor"],
            "Time": chart_frame["_timestamp"].map(format_timestamp),
        }
    ).sort_values("Timestamp", kind="stable")
    x = alt.X("Timestamp:T", title="Sensor timestamp (UTC)", scale=alt.Scale(type="utc"))
    y = alt.Y("Temperature:Q", title="Temperature (°C)", scale=alt.Scale(zero=False))
    band = alt.Chart(pd.DataFrame({"lower": [LOWER_LIMIT], "upper": [UPPER_LIMIT]})).mark_rect(
        color="#dff3f1", opacity=0.7
    ).encode(y="lower:Q", y2="upper:Q")
    limits = alt.Chart(pd.DataFrame({"limit": [LOWER_LIMIT, UPPER_LIMIT]})).mark_rule(
        color="#70a9ac", strokeDash=[5, 4], strokeWidth=1.2
    ).encode(y="limit:Q")
    line = alt.Chart(plot_data).mark_line(color="#126d83", strokeWidth=2.2).encode(
        x=x, y=y, detail="Sensor:N"
    )
    points = alt.Chart(plot_data).mark_circle(size=74, stroke="white", strokeWidth=1).encode(
        x=x,
        y=y,
        color=alt.Color(
            "Status:N",
            title="Reading status",
            scale=alt.Scale(
                domain=["SAFE", "LOW", "HIGH"],
                range=["#178d82", "#3882bd", "#d26a48"],
            ),
        ),
        tooltip=[
            alt.Tooltip("Sensor:N", title="Sensor ID"),
            alt.Tooltip("Time:N", title="Sensor time"),
            alt.Tooltip("Temperature:Q", title="Temperature (°C)", format=".1f"),
            alt.Tooltip("Status:N", title="Status"),
        ],
    )
    chart = alt.layer(band, limits, line, points).properties(height=330).configure_view(stroke=None)
    st.altair_chart(chart, width="stretch")
    skipped = len(frame) - len(chart_frame)
    if skipped:
        st.caption(f"{skipped} reading(s) without a valid timestamp or temperature are omitted from the chart.")


def display_table(frame: pd.DataFrame, *, alerts: bool = False) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    data = {
        "Sensor ID": frame["_sensor"].tolist(),
        "Timestamp (UTC)": [format_timestamp(value) for value in frame["_timestamp"]],
        "Temperature": [format_number(value, unit=" °C") for value in frame["_temperature"]],
    }
    if alerts:
        data["Alert direction"] = [
            "LOW TEMPERATURE" if status == "LOW" else "HIGH TEMPERATURE"
            for status in frame["_status"]
        ]
    else:
        data["Humidity"] = [format_number(value, unit=" %") for value in frame["_humidity"]]
        sources = frame["source"] if "source" in frame else [None] * len(frame)
        received = frame["received_at"] if "received_at" in frame else [None] * len(frame)
        data["Source"] = [text_or_placeholder(value) for value in sources]
        data["Received at (UTC)"] = [format_timestamp(value) for value in received]
        data["Temperature status"] = frame["_status"].tolist()
    return pd.DataFrame(data)


apply_styles()

with st.sidebar:
    st.markdown('<div class="ccg-side-brand">❄ &nbsp;ColdChainGuard</div>', unsafe_allow_html=True)
    st.markdown('<div class="ccg-side-subtitle">Cloud monitoring console</div>', unsafe_allow_html=True)
    st.button("Refresh data", type="primary", width="stretch")
    st.caption("Requests fresh cloud data on each refresh.")

health, health_error = request_json("/health", timeout=4)
online = health_error is None and health is not None and health.get("ok") is True
if health_error is None and not online:
    health_error = "The health endpoint returned an unexpected status."

stats = None
stats_error = None
readings = None
readings_error = None
invalid_records = 0
if online:
    stats, stats_error = request_json("/stats", authenticated=True)
    readings_response, readings_error = request_json(
        f"/readings?limit={READINGS_LIMIT}", authenticated=True
    )
    if readings_error is None:
        raw_readings = readings_response.get("readings")
        if not isinstance(raw_readings, list):
            readings_error = "The readings response did not contain a readings array."
        else:
            valid_readings = [item for item in raw_readings if isinstance(item, dict)]
            invalid_records = len(raw_readings) - len(valid_readings)
            readings = normalize_readings(valid_readings)

with st.sidebar:
    status_class = "" if online else " ccg-side-offline"
    status_text = "ONLINE · API and database responding" if online else "OFFLINE · Connection unavailable"
    st.markdown(
        f'<div class="ccg-side-status{status_class}">{status_text}</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.subheader("Display filters")
    sensors = sorted(set(readings["_sensor"]) - {"—"}) if readings is not None and not readings.empty else []
    selected_sensor = st.selectbox(
        "Sensor ID", [None, *sensors], format_func=lambda value: "All sensors" if value is None else value
    )
    out_of_range_only = st.checkbox("Out-of-range only", value=False)
    st.caption(f"Filters apply to the latest {READINGS_LIMIT} fetched readings, not cloud-wide totals.")

st.markdown(
    """
    <div class="ccg-hero">
      <div class="ccg-hero-title">
        <div class="ccg-icon" aria-hidden="true">❄</div>
        <div>
          <div class="ccg-eyebrow">Cloud operations / cold-chain telemetry</div>
          <h1>ColdChainGuard</h1>
        </div>
      </div>
      <p>Monitor cloud-received sensor readings, temperature excursions, and service health.</p>
      <span class="ccg-range">CONFIGURED SAFE RANGE &nbsp; 2°C – 8°C</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if not online:
    st.error(f"Cloud API OFFLINE. {health_error}")
if stats_error:
    st.warning(f"Cloud statistics are unavailable. {stats_error}")
if readings_error:
    st.warning(f"Cloud readings are unavailable. {readings_error}")
if invalid_records:
    st.warning(f"Skipped {invalid_records} malformed reading record(s) returned by the API.")

render_section("Cloud overview", "Cloud-wide counts from /stats. Times are displayed in UTC.")
columns = st.columns(4)
with columns[0]:
    render_metric("Total readings", format_count(stats.get("total_readings") if stats else None), "Received by the cloud")
with columns[1]:
    render_metric(
        "Out-of-range readings",
        format_count(stats.get("out_of_range_readings") if stats else None),
        "Outside 2°C–8°C",
    )
with columns[2]:
    render_metric(
        "Latest sensor reading",
        format_timestamp(stats.get("latest_timestamp") if stats else None),
        "Sensor timestamp · UTC",
        long=True,
    )
with columns[3]:
    render_metric(
        "Cloud API connection",
        "ONLINE" if online else "OFFLINE",
        "Based on GET /health",
        tone="ccg-online" if online else "ccg-offline",
    )

if readings is not None:
    display_readings = readings
    if selected_sensor is not None:
        display_readings = display_readings[display_readings["_sensor"] == selected_sensor]
    if out_of_range_only:
        display_readings = display_readings[display_readings["_status"].isin(["LOW", "HIGH"])]
else:
    display_readings = None

render_section("Temperature trend", "Chronological sensor temperatures. Shaded band marks the 2°C–8°C safe range.")
if display_readings is None:
    st.info("The temperature trend will appear when cloud readings are available.")
elif display_readings.empty:
    st.info("No readings match the current filters. Adjust the sidebar filters or refresh data.")
else:
    render_chart(display_readings)

render_section("Temperature Alerts", "LOW below 2°C · HIGH above 8°C · latest fetched cloud readings")
if display_readings is None:
    st.info("Temperature alerts will appear when cloud readings are available.")
elif display_readings.empty:
    st.info("No LOW or HIGH temperature readings in the current view.")
else:
    alerts = display_readings[display_readings["_status"].isin(["LOW", "HIGH"])]
    if alerts.empty:
        st.info("No LOW or HIGH temperature readings in the current view.")
    else:
        low_count = int((alerts["_status"] == "LOW").sum())
        high_count = int((alerts["_status"] == "HIGH").sum())
        st.markdown(
            '<div class="ccg-summary">'
            f'<div class="ccg-summary-item ccg-summary-low"><strong>{low_count}</strong> low temperature</div>'
            f'<div class="ccg-summary-item ccg-summary-high"><strong>{high_count}</strong> high temperature</div>'
            "</div>",
            unsafe_allow_html=True,
        )
        st.dataframe(display_table(alerts, alerts=True), hide_index=True, width="stretch")

render_section("Recent cloud readings", f"Newest first · up to {READINGS_LIMIT} records returned by /readings")
if display_readings is None:
    st.info("Recent readings will appear when the cloud connection is available.")
elif display_readings.empty:
    if readings.empty:
        st.info("No readings received by the cloud yet. Start the client simulator and fog gateway to populate this view.")
    else:
        st.info("No readings match the current filters.")
else:
    st.caption(f"Showing {len(display_readings)} of {len(readings)} fetched readings. Cloud-wide totals are shown above.")
    st.dataframe(display_table(display_readings), hide_index=True, width="stretch")

st.caption("Source values are shown as reported by the API. Demo telemetry may be simulated.")
