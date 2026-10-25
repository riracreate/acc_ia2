import json, uuid
from datetime import datetime, timezone
import requests
from common import CONFIG
reading = {
    "reading_id": str(uuid.uuid4()), "sensor_id": "duplicate-test-sensor",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "temperature": 5.0, "humidity": 55.0, "source": "duplicate-test"
}
url = CONFIG["cloud_url"].rstrip("/") + "/readings/batch"
headers = {"X-API-Key": CONFIG["api_key"]}
for n in (1, 2):
    response = requests.post(url, json={"readings": [reading]}, headers=headers, timeout=5)
    print(f"request {n}: HTTP {response.status_code} {response.text}")
    response.raise_for_status()
