"""
logger.py
---------
Saves one JSON file per TTS request to storage/logs/.

Each file contains everything in one place:
  - request_id, timestamp
  - input_text, language
  - status, error
  - latency_ms, audio_size_kb
  - audio_file name

No separate metrics file needed anymore — it's all here.
"""

import json
import time
from pathlib import Path
from contextvars import ContextVar

# Holds the unique ID for the current request
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="no-trace")

# Create logs folder if it doesn't exist
LOGS_DIR = Path("storage/logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def save_request_log(data: dict):
    """
    Save all request details into one clean JSON file.
    File is named: request-<request_id>.json
    """
    request_id = data.get("request_id", "unknown")
    log_file   = LOGS_DIR / f"request-{request_id}.json"

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"[LOG] Saved → {log_file.name}")