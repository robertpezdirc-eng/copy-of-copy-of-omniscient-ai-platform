import os
import json
from datetime import datetime

class EventLogger:
    def __init__(self, log_file="logs/autolearn.log", jsonl_file="logs/autolearn_events.jsonl", console=True):
        self.log_file = log_file
        self.jsonl_file = jsonl_file
        self.console = console
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        except Exception:
            pass

    def _stamp(self):
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def log(self, message, level="INFO", extra=None):
        line = f"[{self._stamp()}] [{level}] {message}"
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass
        if self.console:
            print(line, flush=True)
        if extra is not None:
            try:
                with open(self.jsonl_file, "a", encoding="utf-8") as jf:
                    jf.write(json.dumps({"ts": self._stamp(), "level": level, "message": message, "extra": extra}, ensure_ascii=False) + "\n")
            except Exception:
                pass

    def warn(self, message, extra=None):
        self.log(message, level="WARN", extra=extra)

    def error(self, message, extra=None):
        self.log(message, level="ERROR", extra=extra)