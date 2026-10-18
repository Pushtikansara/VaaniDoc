import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import APIRouter
from ai.clinical.extraction import extract_symptoms
from ai.clinical.schemas import ClinicalExtractionRequest, ClinicalInformation

router = APIRouter()

@router.post("/api/clinical/extract", response_model=ClinicalInformation)
async def extract_clinical_info(request: ClinicalExtractionRequest):
    """Standalone clinical extraction endpoint (Member 3).
    
    Extracts structured clinical information from English patient text.
    Returns clinical data along with the original text for documentation.
    """
    symptoms = extract_symptoms(request.text)
    chief = symptoms[0].name if symptoms else None
    return ClinicalInformation(
        symptoms=symptoms,
        chief_complaint=chief,
    )
