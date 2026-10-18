import sys
import logging
from pathlib import Path
from uuid import uuid4

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from ai.speech.asr import (
    LANGUAGE_CODES,
    SpeechModelAuthError,
    SpeechModelUnavailableError,
    get_speech_model_status,
    transcribe,
)

logger = logging.getLogger("vaani.speech_api")

router = APIRouter()

TEMP_DIR = Path(__file__).resolve().parents[1] / "ai" / "speech" / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/api/speech/status")
def speech_status():
    """Return speech recognition engine status and configuration diagnostics."""
    return get_speech_model_status()


@router.post("/api/speech/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form(...),
):
    """Standalone speech-to-text endpoint (Member 1)."""
    language = language.strip().lower()
    if language not in LANGUAGE_CODES:
        raise HTTPException(status_code=400, detail=f"Invalid language code: '{language}'")

    if not audio.filename:
        raise HTTPException(status_code=400, detail="Missing audio file")

    suffix = Path(audio.filename).suffix or ".wav"
    temp_path = TEMP_DIR / f"{uuid4().hex}{suffix}"

    try:
        content = await audio.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty audio file")

        temp_path.write_bytes(content)
        transcript = transcribe(temp_path, language)
        return {"language": language, "transcript": transcript}
    except HTTPException:
        raise
    except SpeechModelAuthError as exc:
        logger.warning("Speech model auth error: %s", exc)
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc
    except SpeechModelUnavailableError as exc:
        logger.warning("Speech model unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("ASR transcription unexpected error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc
    finally:
        await audio.close()
        temp_path.unlink(missing_ok=True)
