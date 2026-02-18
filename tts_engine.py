"""
tts_engine.py
-------------
Converts text to speech using Microsoft Edge TTS.

Fix: This is now a pure async function.
FastAPI is async, so we must use "await" directly — not asyncio.run().

Supported language codes:
  "en"   → English Female
  "en-m" → English Male
  "hi"   → Hindi Female
  "hi-m" → Hindi Male
  "fr"   → French Female
  "de"   → German Female
  "es"   → Spanish Female
"""

import tempfile
import os
import edge_tts

# Map simple codes to Edge TTS voice names
VOICE_MAP = {
    "en":   "en-US-AriaNeural",
    "en-m": "en-US-GuyNeural",
    "hi":   "hi-IN-SwaraNeural",
    "hi-m": "hi-IN-MadhurNeural",
    "fr":   "fr-FR-DeniseNeural",
    "de":   "de-DE-KatjaNeural",
    "es":   "es-ES-ElviraNeural",
}

DEFAULT_VOICE = "en-US-AriaNeural"


async def text_to_speech(text: str, lang: str = "en") -> bytes:
    """
    Convert text to MP3 bytes using Edge TTS.
    This is an async function — call it with: await text_to_speech(...)

    Args:
        text: The text to speak.
        lang: Language code from VOICE_MAP above.

    Returns:
        MP3 audio as bytes.
    """
    voice = VOICE_MAP.get(lang, DEFAULT_VOICE)

    # Write audio to a temp file, then read it back as bytes
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        tts = edge_tts.Communicate(text=text, voice=voice)
        await tts.save(tmp_path)

        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.remove(tmp_path)  # Always clean up temp file