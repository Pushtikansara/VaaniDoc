import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import APIRouter
from ai.clinical.extraction import (
    extract_symptoms,
    extract_clinical_information,
    extract_clinical_result,
)
from ai.clinical.schemas import (
    ClinicalExtractionRequest,
    ClinicalInformation,
    ClinicalResult,
)

router = APIRouter()


@router.post("/api/clinical/extract", response_model=ClinicalInformation)
async def extract_clinical_info(request: ClinicalExtractionRequest):
    """Standalone clinical extraction endpoint (Member 3).

    Extracts active symptoms, explicit negative findings (negated symptoms),
    chief complaint, and dominant category.
    """
    return extract_clinical_information(request.text)


@router.post("/api/clinical/analyze", response_model=ClinicalResult)
async def analyze_clinical_info(request: ClinicalExtractionRequest):
    """Full clinical AI analysis endpoint including structured extraction and urgency triage."""
    return extract_clinical_result(request.text, session_id=request.session_id)
