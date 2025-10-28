import os, time, uuid, json
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

os.makedirs(LOG_DIR, exist_ok=True)

def write_logs(n: int = 50):
    for i in range(n):
        trace_id = str(uuid.uuid4())
        entry = {
            "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "level": "info",
            "service": "omni-backend",
            "message": f"heartbeat {i}",
            "traceId": trace_id,
        }
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        time.sleep(0.1)

if __name__ == "__main__":
    write_logs(100)