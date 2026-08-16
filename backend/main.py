"""
VaaniDoc — Central Integration Backend
======================================

This is the single FastAPI entry point that connects all three team modules:

  Member 1 — Speech AI   : ai/speech/asr.py  →  transcribe(audio_path, language)
  Member 2 — Translation  : backend/ai/translation/translator.py  →  translate(text, source_language)
  Member 3 — Clinical AI  : ai/clinical/extraction.py + backend/ai/translation/clinical_extraction.py

Pipeline triggered by POST /api/intake:
  audio + language
        ↓  Speech module (Member 1)
  Indian transcript
        ↓  Translation module (Member 2)
  English text
        ↓  Clinical extraction (Member 3)
  Clinical JSON + Urgency

Individual module endpoints from translation_api.py are preserved:
  POST /api/speech/transcribe
  POST /api/translate
  POST /api/clinical/extract
  POST /api/session/end

Privacy:
  - Audio files deleted immediately after transcription.
  - Session data held in memory only (no DB, no files).
  - No patient text is logged to console.

Run from the project root:
  uvicorn backend.main:app --reload --port 8000
"""

from backend.clinical_api import router as clinical_router
from backend.translation_api import router as translation_router
from backend.speech_api import router as speech_router
from backend.report import generate_pdf_report
from ai.clinical.schemas import (
    ClinicalExtractionRequest,
    ClinicalInformation,
    ClinicalResult,
    UrgencyInformation,
)
from ai.clinical.extraction import extract_symptoms as _extract_symptoms_deep
from ai.translation.clinical_extraction import (
    extract_clinical_info as _extract_clinical_quick,
    ClinicalData,
)
from ai.translation.language_map import is_supported_language, get_language_name
from ai.translation.sessions import (
    create_session,
    get_session,
    update_session,
    delete_session,
)
from ai.translation.translation_safety import verify_translation
from ai.translation.translator import (
    translate as _translate,
    get_model_status,
    InvalidInputError,
    UnsupportedLanguageError,
    TranslationFailedError,
)
from ai.speech.asr import LANGUAGE_CODES, transcribe as _asr_transcribe
import logging
import sys
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator

# ---------------------------------------------------------------------------
# Path setup — ensure the project root is on sys.path so all ai.* and
# backend.* imports resolve correctly regardless of CWD.
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ---------------------------------------------------------------------------
# Module imports — Member 1: Speech
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Module imports — Member 2: Translation
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Module imports — Member 3: Clinical Extraction (deeper symptom matching)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Module imports — Report generation
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Logging — no patient data
# ---------------------------------------------------------------------------
logger = logging.getLogger("vaani.main")
logging.basicConfig(level=logging.INFO,
                    format="%(levelname)s  %(name)s  %(message)s")


def _build_translation_fallback(transcript: str) -> str:
    """Return a safe development fallback when the translation model is unavailable."""
    return f"[Simulated Translation] Patient states: {transcript}"


# ---------------------------------------------------------------------------
# Temp directory for audio files (deleted immediately after transcription)
# ---------------------------------------------------------------------------
TEMP_DIR = Path(__file__).resolve().parents[1] / "ai" / "speech" / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="VaaniDoc API",
    description="Integrated voice-to-clinical-report pipeline for Indian-language patients.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================================================
# Startup check
# ===========================================================================

@app.on_event("startup")
def startup_model_check():
    status = get_model_status()
    if not status["configured"]:
        logger.warning("Translation model status at startup: %s",
                       status["message"])
    else:
        logger.info("Translation model configured: %s", status["path"])


# ===========================================================================
# Health
# ===========================================================================

@app.get("/health")
def health():
    """Health check — returns status of all sub-modules."""
    translation_status = get_model_status()
    return {
        "status": "ok",
        "modules": {
            "speech": "ready",
            "translation": translation_status,
            "clinical": "ready",
        },
    }


# ===========================================================================
# Pydantic models
# ===========================================================================

class TranslateRequest(BaseModel):
    text: str = Field(..., description="Indian-language patient statement")
    source_language: str = Field(...,
                                 description="VaaniDoc language code (e.g. 'gu', 'hi')")

    @validator("source_language")
    def validate_source_language(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source_language must not be empty")
        return v.strip().lower()


class TranslateResponse(BaseModel):
    source_language: str
    english_text: str
    verification: dict
    session_id: str = ""


class IntakeResponse(BaseModel):
    language: str
    transcript: str
    english_text: str
    clinical_data: dict
    urgency: str
    session_id: str
    verification: dict


# ===========================================================================
# POST /api/intake  — full pipeline (primary integration endpoint)
# ===========================================================================

@app.post("/api/intake", response_model=IntakeResponse)
async def intake(
    audio: UploadFile = File(...),
    language: str = Form(...),
):
    """Full VaaniDoc intake pipeline.

    Steps:
      1. Validate language and audio.
      2. Save audio to temp, run ASR (Member 1), delete audio immediately.
      3. Translate Indian-language transcript to English (Member 2).
      4. Run translation safety verification.
      5. Run clinical extraction — quick keyword pass + deep symptom matching (Member 3).
      6. Classify urgency.
      7. Create in-memory session, return structured JSON.

    The session_id can later be used to call:
      GET  /api/report/{session_id}  — download PDF report
      POST /api/session/end          — discard session data
    """
    language = language.strip().lower()

    # ---- 1. Validate language ----
    if language not in LANGUAGE_CODES:
        raise HTTPException(
            status_code=400, detail=f"Unsupported language code: {language}")

    if not audio.filename:
        raise HTTPException(status_code=400, detail="Missing audio file")

    # ---- 2. ASR (Member 1) ----
    suffix = Path(audio.filename).suffix or ".wav"
    temp_path = TEMP_DIR / f"{uuid4().hex}{suffix}"

    try:
        content = await audio.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty audio file")

        temp_path.write_bytes(content)

        try:
            transcript = _asr_transcribe(temp_path, language)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail="Speech transcription failed") from exc

    finally:
        await audio.close()
        temp_path.unlink(missing_ok=True)  # Privacy: delete audio immediately

    # ---- 3. Translation (Member 2) ----
    status = get_model_status()
    if not status.get("configured"):
        english_text = _build_translation_fallback(transcript)
    else:
        try:
            english_text = _translate(transcript, language)
        except InvalidInputError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except UnsupportedLanguageError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except TranslationFailedError:
            logger.warning(
                "Translation model failed at runtime; using fallback output")
            english_text = _build_translation_fallback(transcript)
        except Exception:
            raise HTTPException(status_code=500, detail="Translation failed")

    # ---- 4. Translation safety verification ----
    verification_result = verify_translation(
        transcript, language, english_text)

    # ---- 5. Clinical extraction (Member 3 — two layers) ----
    # Layer A: fast keyword extraction (from translation module)
    quick_clinical = _extract_clinical_quick(english_text)

    # Layer B: deep symptom matching with negation detection (from clinical module)
    deep_symptoms = _extract_symptoms_deep(english_text)
    deep_symptom_names = [s.name for s in deep_symptoms]

    # Merge: deep symptom list takes precedence; fill other fields from quick pass
    symptoms = deep_symptom_names if deep_symptom_names else quick_clinical.get(
        "symptoms", [])
    severity = quick_clinical.get("severity")
    duration = quick_clinical.get("duration")
    body_location = quick_clinical.get("body_location")

    # Chief complaint = first active symptom (or first quick keyword)
    chief_complaint = symptoms[0] if symptoms else (
        quick_clinical["symptoms"][0] if quick_clinical.get(
            "symptoms") else None
    )

    # ---- 6. Urgency classification ----
    urgency = quick_clinical.get("urgency", "routine")

    # ---- 7. Build clinical payload ----
    clinical_data = {
        "chief_complaint": chief_complaint,
        "symptoms": symptoms,
        "duration": duration,
        "severity": severity,
        "body_location": body_location,
        "associated_symptoms": [],
        "urgency": urgency,
    }

    # ---- Create in-memory session ----
    try:
        language_name = get_language_name(language)
    except KeyError:
        language_name = language

    session_id = create_session(
        source_language=language,
        original_text=transcript,
        english_text=english_text,
        translation_verification=verification_result,
        clinical_data=clinical_data,
        urgency=urgency,
    )

    return IntakeResponse(
        language=language,
        transcript=transcript,
        english_text=english_text,
        clinical_data=clinical_data,
        urgency=urgency,
        session_id=session_id,
        verification={
            "status": verification_result.get("status", "consistent"),
            "warnings": verification_result.get("warnings", []),
        },
    )


# ===========================================================================
# Standalone Module Routers
# ===========================================================================


app.include_router(speech_router)
app.include_router(translation_router)
app.include_router(clinical_router)

# ===========================================================================
# GET /api/report/{session_id}  — PDF report download
# ===========================================================================


@app.get("/api/report/{session_id}")
async def download_report(session_id: str):
    """Generate and download a PDF clinical intake report for a session.

    The report includes:
    - Chief complaint, symptoms, duration, severity, body location
    - Urgency level
    - Original Indian-language transcript
    - English translation
    - AI disclaimer
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404, detail="Session not found or expired")

    try:
        pdf_bytes = generate_pdf_report(session)
    except Exception as exc:
        logger.error("PDF generation failed: %s", exc)
        raise HTTPException(
            status_code=500, detail="Report generation failed") from exc

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=vaanidoc_report_{session_id[:8]}.pdf"
        },
    )


# ===========================================================================
# POST /api/session/end  — clean up session (privacy)
# ===========================================================================

@app.post("/api/session/end")
async def end_session(session_id: str):
    """End a consultation session and discard its data from memory."""
    success = delete_session(session_id)
    if success:
        return {"status": "session_ended", "session_id": session_id}
    raise HTTPException(
        status_code=404, detail="Session not found or already ended")
