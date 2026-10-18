"""
VaaniDoc — Central Integration Backend
======================================

This is the single FastAPI entry point that connects all modules:
  - Member 1 — Speech AI   : ai/speech/asr.py  →  transcribe(audio_path, language)
  - Member 2 — Translation  : ai/translation/translator.py  →  translate(text, source_language)
  - Member 3 — Clinical AI  : ai/clinical/extraction.py + ai/clinical/urgency.py
  - Primary  — Clinical Reporting & PDF : backend/report.py

Pipelines:
  1. POST /api/intake (Voice):
     Audio + language → ASR → Translation → Safety Check → Clinical Extraction → Urgency Triage → Session

  2. POST /api/intake/text (Text):
     Text + language → Translation (if not English) → Safety Check → Clinical Extraction → Urgency Triage → Session

  3. GET /api/report/{session_id}/data:
     Returns full structured clinical intake report data for doctor review & preview.

  4. PUT /api/report/{session_id}:
     Updates/corrects report fields and clinician notes before finalization.

  5. GET /api/report/{session_id}:
     Generates and streams a professional ReportLab PDF report.

  6. POST /api/session/end:
     Immediately erases patient session data from memory (privacy compliance).

Run from the project root:
  uvicorn backend.main:app --reload --port 8000 
  python -m uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

import io
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
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import Body, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ---------------------------------------------------------------------------
# Module imports — Speech (Member 1)
# ---------------------------------------------------------------------------
from ai.speech.asr import (
    LANGUAGE_CODES,
    transcribe as _asr_transcribe,
    get_speech_model_status,
    SpeechModelAuthError,
    SpeechModelUnavailableError,
)

# ---------------------------------------------------------------------------
# Module imports — Translation (Member 2)
# ---------------------------------------------------------------------------
from ai.translation.translator import (
    translate as _translate,
    get_model_status,
    InvalidInputError,
    UnsupportedLanguageError,
    TranslationFailedError,
)
from ai.translation.translation_safety import verify_translation
from ai.translation.sessions import (
    create_session,
    get_session,
    update_session,
    delete_session,
)
from ai.translation.language_map import is_supported_language, get_language_name
from ai.translation.clinical_extraction import (
    extract_clinical_info as _extract_clinical_quick,
)

# ---------------------------------------------------------------------------
# Module imports — Clinical AI & Urgency (Member 3)
# ---------------------------------------------------------------------------
from ai.clinical.extraction import (
    extract_symptoms as _extract_symptoms_deep,
    extract_clinical_information as _extract_clinical_info_deep,
)
from ai.clinical.urgency import classify_urgency, get_urgency
from ai.clinical.schemas import (
    ClinicalExtractionRequest,
    ClinicalInformation,
    ClinicalResult,
    UrgencyInformation,
)

# ---------------------------------------------------------------------------
# Module imports — Clinical Reporting & PDF
# ---------------------------------------------------------------------------
from backend.report import (
    generate_pdf_report,
    build_report_data,
    update_report_data,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("vaani.main")
logging.basicConfig(level=logging.INFO,
                    format="%(levelname)s  %(name)s  %(message)s")


INDIC_CLINICAL_MAP = [
    # Cardiac / Emergency
    (r"હૃદય\s*(?:માં|નો)?\s*દુ[ખઃ]ાવો|છાતી\s*(?:માં|નો)?\s*દુ[ખઃ]ાવો|હૃદય\s*(?:માં\s*)?દુખ|છાતી\s*(?:માં\s*)?દુખ|હાર્ટ\s*એટેક", "chest pain / cardiac pain"),
    (r"સીને\s*(?:में|का)?\s*दर्द|छाती\s*(?:में|का)?\s*दर्द|दिल\s*(?:में|का)?\s*दर्द|हार्ट\s*अटैक", "chest pain / cardiac pain"),
    (r"छातीत\s*दुખ?णे|हृदयात\s*दुખ?णे", "chest pain"),
    # Respiratory / Emergency
    (r"શ્વાસ\s*(?:લેવામાં\s*તકલીફ|ચડવો|ચડે|લેવાતો\s*નથી)", "shortness of breath"),
    (r"सांस\s*(?:लेने\s*में\s*तकलीफ|फूलना)", "shortness of breath"),
    (r"श्वास\s*घेण्यास\s*त्रास", "shortness of breath"),
    # Neurological
    (r"માથાનો\s*દુ[ખઃ]ાવો|માથું\s*દુખ", "headache"),
    (r"સિર\s*દર્દ|सिरदर्द|डोकेदुखी", "headache"),
    (r"ચક્કર|ચક્કર\s*આવે|चक्कर", "dizziness"),
    # General / Infection
    (r"ખૂબ\s*તાવ|તેજ\s*તાવ|તીવ્ર\s*તાવ|तेज\s*बुखार", "high fever"),
    (r"તાવ|બુખાર|बुखार|ताप", "fever"),
    (r"ખાંસી|ઉધરસ|खांसी|खोकला", "cough"),
    # Gastrointestinal
    (r"પેટ\s*માં\s*દુ[ખઃ]ાવો|પેટ\s*દુખ|पेट\s*में\s*दर्द|पोटात\s*दुखणे", "abdominal pain"),
    (r"ઝાડા|ઉલટી|દસ્ત|उल्टी|जुलाब", "vomiting"),
    # Duration
    (r"બે\s*દિવસથી|દો\s*દિન\s*સે|दोन\s*दिवसांपासून", "for 2 days"),
    (r"ત્રણ\s*દિવસથી|તીન\s*દિન\s*સે|तीन\s*दिवसांपासून", "for 3 days"),
    (r"એક\s*અઠવાડિયાથી|એક\s*હપ્તાથી", "for 1 week"),
]


def _build_translation_fallback(transcript: str, language: str = "gu") -> str:
    """Return an informative translation with regional clinical mapping when IndicTrans2 is offline."""
    extracted_terms = []
    for pattern, eng_term in INDIC_CLINICAL_MAP:
        if re.search(pattern, transcript, re.IGNORECASE):
            extracted_terms.append(eng_term)

    if extracted_terms:
        unique_terms = list(dict.fromkeys(extracted_terms))
        clinical_summary = ", ".join(unique_terms)
        return f"Patient reports {clinical_summary}. (Original: {transcript})"

    return f"[Translation Offline: IndicTrans2 Not Configured] Raw Patient Statement: {transcript}"



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
    description="Integrated voice/text-to-clinical-report pipeline for Indian-language patients.",
    version="1.1.0",
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
    speech_status = get_speech_model_status()
    if not speech_status["configured"]:
        logger.warning("Speech model status at startup: %s", speech_status["message"])
    else:
        logger.info("Speech model status at startup: %s", speech_status["message"])

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
    speech_status = get_speech_model_status()
    return {
        "status": "ok",
        "modules": {
            "speech": speech_status,
            "translation": translation_status,
            "clinical": "ready",
            "reporting": "ready",
        },
    }


# ===========================================================================
# Pydantic models
# ===========================================================================

class TranslateRequest(BaseModel):
    text: str = Field(..., description="Indian-language patient statement")
    source_language: str = Field(...,
                                 description="VaaniDoc language code (e.g. 'gu', 'hi')")

    @field_validator("source_language")
    @classmethod
    def validate_source_language(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source_language must not be empty")
        return v.strip().lower()


class TranslateResponse(BaseModel):
    source_language: str
    english_text: str
    verification: dict
    session_id: str = ""


class TextIntakeRequest(BaseModel):
    text: str = Field(..., description="Patient symptoms (regional language or English)")
    language: str = Field("gu", description="Language code (e.g. 'gu', 'hi', 'en')")

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("text must not be empty")
        return stripped

    @field_validator("language")
    @classmethod
    def lang_not_empty(cls, v: str) -> str:
        return v.strip().lower()


class IntakeResponse(BaseModel):
    language: str
    transcript: str
    english_text: str
    clinical_data: dict
    urgency: str
    session_id: str
    verification: dict


class ReportUpdateRequest(BaseModel):
    chief_complaint: Optional[str] = None
    symptoms: Optional[List[str]] = None
    negated_findings: Optional[List[str]] = None
    duration: Optional[str] = None
    severity: Optional[str] = None
    body_location: Optional[str] = None
    possible_category: Optional[str] = None
    urgency: Optional[str] = None
    doctor_notes: Optional[str] = None
    patient_info: Optional[Dict[str, Any]] = None
    vital_signs: Optional[Dict[str, Any]] = None
    prescriptions: Optional[List[Dict[str, Any]]] = None
    diagnostic_orders: Optional[List[Dict[str, Any]]] = None
    care_plan: Optional[Dict[str, Any]] = None
    attending_doctor: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class EndSessionPayload(BaseModel):
    session_id: Optional[str] = None


# ===========================================================================
# Helper: Clinical Extraction & Urgency Pipeline
# ===========================================================================

def _process_clinical_and_urgency(english_text: str, original_text: str = "") -> tuple[dict, str]:
    """Run dual-layer clinical extraction and unified urgency triage on combined multilingual inputs."""
    combined_text = f"{english_text} {original_text}".strip()

    # Fast regex pass for duration, severity, body location
    quick_clinical = _extract_clinical_quick(combined_text)

    # Deep symptom matching with boundary-aware negation detection
    clinical_info = _extract_clinical_info_deep(combined_text)
    deep_symptom_names = [s.name for s in clinical_info.symptoms]

    symptoms = deep_symptom_names if deep_symptom_names else quick_clinical.get("symptoms", [])
    negated_symptoms = clinical_info.negated_symptoms
    severity = quick_clinical.get("severity") or (clinical_info.symptoms[0].severity if clinical_info.symptoms else None)
    duration = quick_clinical.get("duration") or (clinical_info.symptoms[0].duration if clinical_info.symptoms else None)
    body_location = quick_clinical.get("body_location") or (clinical_info.symptoms[0].body_part if clinical_info.symptoms else None)
    chief_complaint = clinical_info.chief_complaint or (symptoms[0] if symptoms else None)
    possible_category = clinical_info.possible_category or "General"

    # Classify urgency using the unified triage engine
    urgency_info = classify_urgency(
        symptoms=symptoms,
        text=combined_text,
        severity=severity,
        duration=duration,
        negated_symptoms=negated_symptoms,
    )
    urgency_level = urgency_info.level or "ROUTINE"

    clinical_data = {
        "chief_complaint": chief_complaint,
        "symptoms": symptoms,
        "negated_symptoms": negated_symptoms,
        "duration": duration,
        "severity": severity,
        "body_location": body_location,
        "possible_category": possible_category,
        "associated_symptoms": [],
        "urgency": urgency_level,
        "urgency_reason": urgency_info.reason,
    }
    return clinical_data, urgency_level


# ===========================================================================
# POST /api/intake — Full Voice Pipeline
# ===========================================================================

@app.post("/api/intake", response_model=IntakeResponse)
async def intake(
    audio: UploadFile = File(...),
    language: str = Form(...),
):
    """Full VaaniDoc voice intake pipeline:
    Audio -> ASR -> Translation -> Safety Check -> Clinical Extraction -> Urgency -> Session
    """
    language = language.strip().lower()

    if language not in LANGUAGE_CODES:
        raise HTTPException(
            status_code=400, detail=f"Unsupported language code: {language}")

    if not audio.filename:
        raise HTTPException(status_code=400, detail="Missing audio file")

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
        except SpeechModelAuthError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except SpeechModelUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            logger.error("ASR transcription error: %s", exc)
            raise HTTPException(status_code=500, detail="Speech transcription failed") from exc
            raise HTTPException(
                status_code=500, detail="Speech transcription failed") from exc

    finally:
        await audio.close()
        temp_path.unlink(missing_ok=True)  # Privacy: immediate file deletion

    # Translation
    status = get_model_status()
    if not status.get("configured"):
        english_text = _build_translation_fallback(transcript)
    else:
        try:
            english_text = _translate(transcript, language)
        except (InvalidInputError, UnsupportedLanguageError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except TranslationFailedError:
            logger.warning("Translation model failed at runtime; using offline state")
            logger.warning(
                "Translation model failed at runtime; using fallback output")
            english_text = _build_translation_fallback(transcript)
        except Exception:
            raise HTTPException(status_code=500, detail="Translation failed")

    # Safety verification
    verification_result = verify_translation(transcript, language, english_text)
    # ---- 4. Translation safety verification ----
    verification_result = verify_translation(
        transcript, language, english_text)

    # Clinical extraction & urgency
    clinical_data, urgency = _process_clinical_and_urgency(english_text, transcript)

    # In-memory session
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


# ===========================================================================
# POST /api/intake/text — Full Text Pipeline (Typing input in regional language)
# ===========================================================================

@app.post("/api/intake/text", response_model=IntakeResponse)
async def intake_text(request: TextIntakeRequest):
    """Full VaaniDoc text intake pipeline for typed regional language input.
    Text -> Translation -> Safety Check -> Clinical Extraction -> Urgency -> Session
    """
    language = request.language.strip().lower()
    text = request.text.strip()

    if language != "en" and not is_supported_language(language) and language not in LANGUAGE_CODES:
        raise HTTPException(status_code=400, detail=f"Unsupported language code: {language}")

    if language == "en":
        english_text = text
        verification_result = {"status": "consistent", "warnings": []}
    else:
        status = get_model_status()
        if not status.get("configured"):
            english_text = _build_translation_fallback(text)
        else:
            try:
                english_text = _translate(text, language)
            except (InvalidInputError, UnsupportedLanguageError) as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except TranslationFailedError:
                logger.warning("Translation model failed at runtime; using offline state")
                english_text = _build_translation_fallback(text)
            except Exception:
                raise HTTPException(status_code=500, detail="Translation failed")

        verification_result = verify_translation(text, language, english_text)

    # Clinical extraction & urgency
    clinical_data, urgency = _process_clinical_and_urgency(english_text, text)

    session_id = create_session(
        source_language=language,
        original_text=text,
        english_text=english_text,
        translation_verification=verification_result,
        clinical_data=clinical_data,
        urgency=urgency,
    )

    return IntakeResponse(
        language=language,
        transcript=text,
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
# Clinical Report Endpoints: Preview, Edit, Download
# ===========================================================================

@app.get("/api/report/{session_id}/data")
async def get_report_data(session_id: str):
    """Retrieve structured clinical intake report data for doctor review & preview."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    return build_report_data(session)


@app.put("/api/report/{session_id}")
async def update_report(session_id: str, updates: ReportUpdateRequest):
    """Update supported clinical fields and clinician notes before report finalization."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    update_dict = updates.model_dump(exclude_unset=True) if hasattr(updates, "model_dump") else updates.dict(exclude_unset=True)
    try:
        updated_report = update_report_data(session_id, update_dict)
        return updated_report
    except Exception as exc:
        logger.error("Error updating report for session %s: %s", session_id, exc)
        raise HTTPException(status_code=500, detail="Failed to update clinical report") from exc


@app.get("/api/report/{session_id}")
async def download_report(session_id: str):
    """Generate and stream a valid, professional PDF clinical intake report."""
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
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=vaanidoc_report_{session_id[:8]}.pdf",
            "Content-Type": "application/pdf",
        },
    )


# ===========================================================================
# POST /api/session/end — Clean up session (privacy)
# ===========================================================================

@app.post("/api/session/end")
async def end_session_unified(
    session_id: Optional[str] = Query(None),
    payload: Optional[EndSessionPayload] = Body(None),
):
    """End a consultation session and immediately purge its data from memory."""
    target_id = session_id or (payload.session_id if payload else None)
    if not target_id:
        raise HTTPException(status_code=400, detail="Missing session_id")

    success = delete_session(target_id)
    if success:
        return {"status": "session_ended", "session_id": target_id}
    raise HTTPException(status_code=404, detail="Session not found or already ended")
        return {"status": "session_ended", "session_id": session_id}
    raise HTTPException(
        status_code=404, detail="Session not found or already ended")
