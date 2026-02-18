"""
main.py
-------
TTS Microservice using Microsoft Edge TTS (fast, ~300ms latency).

Every POST /tts saves 2 files automatically:
  storage/audio/  → speech-<id>.mp3      (the audio file)
  storage/logs/   → request-<id>.json    (everything about this request)

Endpoints:
  GET  /health    — Is the service running?
  POST /tts       — Convert text to speech
  GET  /metrics   — Prometheus metrics
  GET  /dashboard — Summary of saved files
"""

import uuid
import time
import signal
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from logger import save_request_log, trace_id_var, LOGS_DIR
from metrics import REQUEST_COUNT, REQUEST_LATENCY, ERROR_COUNT, AUDIO_SIZE, get_metrics_output
from tts_engine import text_to_speech, VOICE_MAP

# ── Storage ───────────────────────────────────────────────────────────────────

AUDIO_DIR = Path("storage/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

START_TIME       = time.time()
is_shutting_down = False


# ── Startup & Shutdown ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] TTS Service started  (Engine: Microsoft Edge TTS)")
    print(f"[INFO] Logs   → {LOGS_DIR.resolve()}")
    print(f"[INFO] Audio  → {AUDIO_DIR.resolve()}")

    def on_shutdown(*args):
        global is_shutting_down
        is_shutting_down = True

    signal.signal(signal.SIGTERM, on_shutdown)
    yield
    print("[INFO] Service stopped")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="TTS Microservice", version="2.0.0", lifespan=lifespan)


# ── Request Model ─────────────────────────────────────────────────────────────

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="Text to speak")
    lang: str = Field(
        default="en",
        description=f"Language code. Options: {list(VOICE_MAP.keys())}"
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Observability"])
async def health():
    """Check if the service is alive."""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    return {
        "status":         "healthy",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "engine":         "Microsoft Edge TTS",
    }


@app.post("/tts", tags=["TTS"])
async def tts(request: TTSRequest):
    """
    Convert text to speech using Edge TTS (~300ms latency).
    Saves one MP3 and one JSON log file per request.
    """
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    # Step 1: Assign unique ID to this request
    request_id = str(uuid.uuid4())[:8]
    trace_id_var.set(request_id)
    start_time = time.time()
    timestamp  = time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n[REQUEST {request_id}] '{request.text[:60]}' | lang={request.lang}")

    # Step 2: Convert text to audio (await — no asyncio.run needed)
    try:
        audio = await text_to_speech(request.text, request.lang)
    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 2)

        # Save log for failed request
        save_request_log({
            "request_id":    request_id,
            "timestamp":     timestamp,
            "input_text":    request.text,
            "language":      request.lang,
            "status":        "failed",
            "error":         str(e),
            "latency_ms":    latency_ms,
            "audio_file":    None,
            "audio_size_kb": None,
        })

        ERROR_COUNT.inc()
        raise HTTPException(status_code=500, detail="Audio generation failed")

    # Step 3: Measure how long it took
    latency_ms = round((time.time() - start_time) * 1000, 2)

    # Step 4: Save MP3 to storage/audio/
    filename   = f"speech-{request_id}.mp3"
    audio_path = AUDIO_DIR / filename
    audio_path.write_bytes(audio)
    print(f"[AUDIO] Saved  → {filename}  ({round(len(audio)/1024, 1)} KB)")

    # Step 5: Update Prometheus counters
    REQUEST_COUNT.labels(status="200").inc()
    REQUEST_LATENCY.observe(latency_ms / 1000)
    AUDIO_SIZE.observe(len(audio))

    # Step 6: Save one merged JSON log with everything
    save_request_log({
        "request_id":    request_id,
        "timestamp":     timestamp,
        "input_text":    request.text,
        "language":      request.lang,
        "status":        "success",
        "error":         None,
        "latency_ms":    latency_ms,
        "audio_file":    filename,
        "audio_size_kb": round(len(audio) / 1024, 1),
    })

    print(f"[DONE]  {request_id} completed in {latency_ms}ms\n")

    # Step 7: Return audio as download
    return StreamingResponse(
        iter([audio]),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Request-ID":        request_id,
            "X-Latency-Ms":        str(latency_ms),
        }
    )


@app.get("/metrics", tags=["Observability"])
async def metrics():
    """Prometheus metrics output."""
    data, content_type = get_metrics_output()
    return Response(content=data, media_type=content_type)


@app.get("/dashboard", tags=["Observability"])
async def dashboard():
    """Summary of all saved files and uptime."""
    log_files   = list(LOGS_DIR.glob("*.json"))
    audio_files = list(AUDIO_DIR.glob("*.mp3"))

    return JSONResponse({
        "service":        "TTS Microservice",
        "engine":         "Microsoft Edge TTS",
        "status":         "shutting_down" if is_shutting_down else "running",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "saved": {
            "logs":  {"total": len(log_files),   "folder": str(LOGS_DIR.resolve())},
            "audio": {"total": len(audio_files), "folder": str(AUDIO_DIR.resolve())},
        }
    })