# ColdChainGuard — starter implementation

This is a fresh, consistent starter implementation based on the architecture in the setup notes. It is not a recovery of the unavailable original code.

## Components
- `cloud/api.py`: FastAPI API, SQLite storage, idempotent batch ingestion.
- `cloud/dashboard.py`: Streamlit cloud dashboard.
- `client/simulator.py`: publishes simulated sensor readings through local Mosquitto.
- `client/fog_gateway.py`: stores readings locally, alerts on out-of-range readings, and retries cloud sync.
- `client/baseline_client.py`: cloud-only comparison client without a local persistence buffer.
- Other client scripts: local dashboard, outage simulation, reset, duplicate test, and basic evaluation.

## Security
Use a strong random API key and set the same value as `COLDCHAIN_API_KEY` on EC2 and `api_key` in `client/config.json`. Do not commit secrets to public repositories. This demo uses HTTP, so it is for a controlled academic demonstration, not production use. The security group should restrict ports 8000 and 8501 to your IP.

## EC2 deployment
Follow the accompanying ChatGPT steps. Upload `cloud/api.py` and `cloud/dashboard.py` to `~/coldchain/`. Set the API key in a protected environment file and use systemd services.

## Mac setup
Install Python 3 and Mosquitto. In this folder:
`cd client && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`

Start local Mosquitto, then run in separate terminals: `fog_gateway.py`, `fog_view.py`, `baseline_client.py`, and `simulator.py`.

The outage script toggles a local flag to simulate a network outage for the demo. It models the expected behavior in software; it does not disable the Mac's actual internet connection.
# acc_ia2
