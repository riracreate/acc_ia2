import sys, time
from pathlib import Path
from common import ROOT, CONFIG

flag = ROOT / CONFIG.get("outage_flag", "OUTAGE.flag")
if len(sys.argv) != 3 or sys.argv[1] != "run":
    print("Usage: python outage.py run SECONDS")
    raise SystemExit(2)
seconds = max(1, int(sys.argv[2]))
flag.write_text(f"simulated outage started; duration={seconds}\n")
print(f"Simulated outage enabled for {seconds}s. Gateway buffers locally; baseline drops readings.")
try:
    time.sleep(seconds)
finally:
    flag.unlink(missing_ok=True)
print("Simulated outage ended. Gateway should sync its pending buffer shortly.")
