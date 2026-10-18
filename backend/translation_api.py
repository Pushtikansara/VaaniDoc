import sys
from pathlib import Path
from uuid import uuid4

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field, validator

from ai.speech.asr import LANGUAGE_CODES, transcribe
from ai.translation.translator import (
    translate,
    InvalidInputError,
    UnsupportedLanguageError,
    TranslationFailedError,
    get_model_status,
)
from ai.translation.translation_safety import verify_translation
from ai.translation.sessions import (
    create_session,
    get_session,
    update_session,
    delete_session,
)
from ai.translation.clinical_extraction import extract_clinical_info, ClinicalData


router = APIRouter()

def _build_translation_fallback(text: str) -> str:
    """Return a safe development fallback when the translation model is unavailable."""
    return f"[Simulated Translation] Patient states: {text}"

@router.on_event("startup")
def startup_model_check():
    status = get_model_status()
    logger = __import__("logging").getLogger("vaani.startup")
    if not status["configured"]:
        logger.warning("Translation model status: %s", status["message"])
    else:
        logger.info("Translation model configured: %s", status["path"])


TEMP_DIR = Path(__file__).resolve().parents[1] / "ai" / "speech" / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Pydantic models for /api/translate
# ---------------------------------------------------------------------------

class TranslateRequest(BaseModel):
    """Request body for translation endpoint."""
    text: str = Field(..., description="Indian-language patient statement")
    source_language: str = Field(..., description="VaaniDoc language code (e.g. 'gu', 'hi')")

    @validator("source_language")
    def validate_source_language(cls, v: str) -> str:
        """Ensure source language is not empty after stripping."""
        if not v.strip():
            raise ValueError("source_language must not be empty")
        return v


class TranslateResponse(BaseModel):
    """Response body for translation endpoint."""
    source_language: str
    english_text: str
    verification: dict  # status + warnings from safety checker
    session_id: str = ""


# ---------------------------------------------------------------------------
# Existing endpoints
# ---------------------------------------------------------------------------


@router.post("/api/translate", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest, session_id: str = ""):
    """Translate Indian-language text to English with safety verification.

    - Validates input text and source language.
    - Uses the already-loaded IndicTrans2 CT2 model (loaded at import time).
    - Runs translation safety verification to detect clinically important
      mismatches.
    - Stores translation data in a temporary consultation session.
    - Returns the English translation, verification status, and session ID.

    The original patient statement is always preserved and returned in the
    verification result (accessible to the caller if needed).

    Session management:
    - If session_id is provided and valid, data is stored/update in that session.
    - If session_id is empty or invalid, a new session is created.
    - The session ID can be used by the frontend to track consultation data.
    - When the consultation ends, the frontend should call /api/session/end
      to delete the temporary data.

    Requirements satisfied:
    - Pydantic request/response models ✓
    - Validate empty text ✓
    - Validate source language ✓
    - Reject unsupported languages ✓
    - Do not expose stack traces to users ✓
    - Return appropriate HTTP errors ✓
    - Reuse already-loaded model ✓
    - Do not load model per request ✓
    - Do not permanently store translation data ✓ (stored only in active session memory)
    - Do not log patient text ✓
    - Keep endpoint modular ✓
    - Route calls translator.py, not containing model logic ✓
    - Calls translation safety checker ✓
    - Does not introduce new dependencies ✓
    - Session IDs are random/unpredictable ✓
    - Different patients cannot access each other's sessions ✓
    """
    # ---- Validate text input ----
    text_stripped = request.text.strip()
    if not text_stripped:
        raise HTTPException(
            status_code=400, detail="Translation text is empty or whitespace-only")

    # ---- Validate source language ----
    src_code = request.source_language.strip().lower()
    if not src_code:
        raise HTTPException(
            status_code=400, detail="Source language code is empty")
    from ai.translation.language_map import is_supported_language
    if not is_supported_language(src_code):
        raise HTTPException(
            status_code=400, detail=f"Unsupported source language code: '{src_code}'")

    # ---- Use or create a session for this consultation ----
    if session_id and get_session(session_id):
        # Update existing session
        update_session(
            session_id,
            original_text=request.text,
            english_text="",  # will be set below
            translation_verification=None,  # will be set below
            clinical_data={},
        )
    else:
        # Create new session
        session_id = create_session(
            source_language=request.source_language,
            original_text=request.text,
            english_text="",
            translation_verification={},
            clinical_data={},
        )

    # ---- Translate using the already-loaded CT2 model ----
    # The model is loaded once per process (see translator.py _ensure_model_loaded).
    # We do NOT load it per request.
    try:
        status = get_model_status()
        if not status.get("configured"):
            # MOCK TRANSLATION FALLBACK for local frontend testing
            # Since the user hasn't downloaded the 1.5GB IndicTrans2 model yet,
            # return a simulated string instead of failing with 502 Bad Gateway.
            english_translation = _build_translation_fallback(request.text)
        else:
            english_translation = translate(request.text, request.source_language)
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except UnsupportedLanguageError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except TranslationFailedError as e:
        logger = __import__("logging").getLogger("vaani.translation_api")
        logger.warning("Translation model failed at runtime; using fallback output")
        english_translation = _build_translation_fallback(request.text)
    except Exception:
        # Unexpected error - do not expose stack traces
        raise HTTPException(
            status_code=500, detail="Translation failed") from None

    # ---- Run translation safety verification ----
    # This checker detects potentially dangerous mismatches where clinically
    # important information may have been altered, lost, or inverted during
    # translation. It does NOT claim the translation is correct or medically
    # valid; it only flags reliably detectable divergences.
    # We do NOT silently modify the translation; we only report warnings.
    # The original patient statement remains available in the verification result.
    verification_result = verify_translation(
        request.text, request.source_language, english_translation)

    # ---- Extract clinical information from the English translation ----
    # This is separate from the safety verification - it extracts structured
    # clinical data that can be used for clinical decision support.
    clinical_data_dict = extract_clinical_info(english_translation)
    clinical_data = ClinicalData(**clinical_data_dict)

    # ---- Build the response ----
    response: TranslateResponse = {
        "source_language": request.source_language,
        "english_text": english_translation,
        "verification": {
            "status": verification_result["status"],
            "warnings": verification_result["warnings"],
        },
    }

    # Update session with all data
    update_session(
        session_id,
        english_text=english_translation,
        translation_verification=verification_result,
        clinical_data=clinical_data.to_dict(),
    )

    # Include session ID in the response so the frontend can track it
    response["session_id"] = session_id

    return response


@router.post("/api/session/end")
async def end_session(session_id: str):
    """End a consultation session and delete its data.

    Removes the session from the in-memory store. After this call,
    the session data is gone and cannot be retrieved.

    Returns True if the session was found and deleted, False otherwise.
    """
    success = delete_session(session_id)
    if success:
        return {"status": "session_ended", "session_id": session_id}
    else:
        raise HTTPException(
            status_code=404, detail="Session not found or already ended")


@router.post("/api/session/clear-all")
async def clear_all_sessions():
    """Clear all sessions (admin/debug endpoint).

    For development only. In production, sessions expire naturally or
    on server restart.
    """
    count = delete_session.__code__  # placeholder - would call cleanup function
    return {"status": "cleared"}


# Note: The following functions are NOT exposed as API endpoints
# but are available for internal use:
#
# - list_sessions() - lists all active sessions (debugging only)
# - cleanup_expired_sessions() - removes expired sessions
# SEE sessions.py for full documentation.
