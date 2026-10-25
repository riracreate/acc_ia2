from pathlib import Path
from common import ROOT, CONFIG, ensure_local_db, db_connect
DB_PATH = ROOT / CONFIG.get("local_db", "fog.db")
if DB_PATH.exists():
    DB_PATH.unlink()
ensure_local_db(DB_PATH)
flag = ROOT / CONFIG.get("outage_flag", "OUTAGE.flag")
flag.unlink(missing_ok=True)
print({"reset": True, "database": str(DB_PATH)})
