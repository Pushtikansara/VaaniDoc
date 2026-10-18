"""20 Deterministic Symptom Extraction and Pipeline Validation Test Cases.

Covers:
  1. Common single symptom
  2. Multiple symptoms in one statement
  3. Negated symptom with boundary
  4. Leading negation with following active symptom
  5. Multiple active and multiple negated symptoms
  6. Contradiction resolution (negated then active affirmed)
  7. Supported synonym phrasings
  8. Emergency cardiovascular presentation
  9. Neurological emergency presentation
  10. Severe respiratory presentation
  11. High urgency presentation (prolonged fever & stiff neck)
  12. High urgency acute severe abdominal pain
  13. Moderate urgency gastrointestinal presentation
  14. Moderate urgency ENT presentation
  15. Routine minor cold presentation
  16. Dermatological presentation with negative airway symptoms
  17. Musculoskeletal presentation
  18. Non-clinical / non-symptom input
  19. Empty and whitespace input handling
  20. Consistency across extraction, urgency, report preview, and PDF generation
"""

import pytest
from ai.clinical.extraction import (
    extract_symptoms,
    extract_clinical_information,
    extract_clinical_result,
)
from ai.clinical.urgency import classify_urgency, get_urgency
from backend.report import build_report_data, generate_pdf_report


# ===========================================================================
# 20 Deterministic Test Cases
# ===========================================================================

def test_case_01_common_single_symptom():
    text = "Patient complains of fever since yesterday."
    info = extract_clinical_information(text)
    active_names = [s.name for s in info.symptoms]
    assert "fever" in active_names
    assert len(info.negated_symptoms) == 0


def test_case_02_multiple_symptoms():
    text = "I have severe headache, cough and chest pain."
    info = extract_clinical_information(text)
    active_names = [s.name for s in info.symptoms]
    assert "headache" in active_names
    assert "cough" in active_names
    assert "chest_pain" in active_names


def test_case_03_negated_symptom_with_boundary():
    text = "I have fever but no headache."
    info = extract_clinical_information(text)
    active_names = [s.name for s in info.symptoms]
    assert "fever" in active_names
    assert "headache" not in active_names
    assert "headache" in info.negated_symptoms


def test_case_04_leading_negation():
    text = "No vomiting. I have abdominal pain."
    info = extract_clinical_information(text)
    active_names = [s.name for s in info.symptoms]
    assert "abdominal_pain" in active_names
    assert "vomiting" not in active_names
    assert "vomiting" in info.negated_symptoms


def test_case_05_multiple_active_and_negated():
    text = "I don't have fever or cough. I have severe headache and nausea."
    info = extract_clinical_information(text)
    active_names = [s.name for s in info.symptoms]
    assert "headache" in active_names
    assert "nausea" in active_names
    assert "fever" not in active_names
    assert "cough" not in active_names
    assert "fever" in info.negated_symptoms
    assert "cough" in info.negated_symptoms


def test_case_06_contradiction_resolution():
    text = "I had no cough earlier, but now I have cough and fever."
    info = extract_clinical_information(text)
    active_names = [s.name for s in info.symptoms]
    assert "cough" in active_names
    assert "fever" in active_names
    assert "cough" not in info.negated_symptoms


def test_case_07_synonym_phrasings():
    text = "My head is pounding, room is spinning, and I am throwing up."
    info = extract_clinical_information(text)
    active_names = [s.name for s in info.symptoms]
    assert "headache" in active_names
    assert "dizziness" in active_names
    assert "vomiting" in active_names


def test_case_08_emergency_cardiovascular():
    text = "Sudden crushing chest pain radiating to left arm with difficulty breathing."
    result = extract_clinical_result(text)
    active_names = [s.name for s in result.clinical.symptoms]
    assert "chest_pain" in active_names or "shortness_of_breath" in active_names
    assert result.urgency.level == "EMERGENCY"
    assert "cardiopulmonary" in result.urgency.reason.lower() or "critical" in result.urgency.reason.lower()


def test_case_09_neurological_emergency():
    text = "The patient passed out and had a seizure."
    result = extract_clinical_result(text)
    active_names = [s.name for s in result.clinical.symptoms]
    assert "fainting" in active_names or "seizure" in active_names
    assert result.urgency.level == "EMERGENCY"


def test_case_10_severe_respiratory_emergency():
    text = "Severe shortness of breath and wheezing for three hours."
    result = extract_clinical_result(text)
    active_names = [s.name for s in result.clinical.symptoms]
    assert "shortness_of_breath" in active_names
    assert result.urgency.level == "EMERGENCY"


def test_case_11_high_urgency_prolonged_fever_and_stiff_neck():
    text = "High fever for five days and stiff neck with severe headache."
    result = extract_clinical_result(text)
    active_names = [s.name for s in result.clinical.symptoms]
    assert "headache" in active_names or "fever" in active_names
    assert result.urgency.level in ("HIGH", "EMERGENCY")


def test_case_12_high_urgency_acute_abdominal():
    text = "Patient experiences unbearable severe abdominal pain and persistent vomiting."
    result = extract_clinical_result(text)
    active_names = [s.name for s in result.clinical.symptoms]
    assert "abdominal_pain" in active_names
    assert result.urgency.level in ("HIGH", "EMERGENCY")


def test_case_13_moderate_urgency_gastrointestinal():
    text = "Watery diarrhea, stomach ache, and nausea for 2 days."
    result = extract_clinical_result(text)
    active_names = [s.name for s in result.clinical.symptoms]
    assert "diarrhea" in active_names
    assert "nausea" in active_names
    assert result.urgency.level == "MODERATE"


def test_case_14_moderate_urgency_ent():
    text = "Sore throat, ear pain, and runny nose for three days."
    result = extract_clinical_result(text)
    active_names = [s.name for s in result.clinical.symptoms]
    assert "sore_throat" in active_names
    assert "ear_pain" in active_names
    assert result.urgency.level == "MODERATE"


def test_case_15_routine_minor_cold():
    text = "Mild runny nose and sneezing without fever or chest pain."
    result = extract_clinical_result(text)
    active_names = [s.name for s in result.clinical.symptoms]
    assert "runny_nose" in active_names
    assert "sneezing" in active_names
    assert "fever" in result.clinical.negated_symptoms
    assert "chest_pain" in result.clinical.negated_symptoms
    assert result.urgency.level == "ROUTINE"


def test_case_16_dermatological_presentation():
    text = "Itchy skin rash on arms, but no difficulty breathing."
    result = extract_clinical_result(text)
    active_names = [s.name for s in result.clinical.symptoms]
    assert "itching" in active_names or "rash" in active_names
    assert "shortness_of_breath" in result.clinical.negated_symptoms
    assert result.urgency.level in ("ROUTINE", "MODERATE")


def test_case_17_musculoskeletal_symptoms():
    text = "Lower back pain and joint stiffness for one week."
    result = extract_clinical_result(text)
    active_names = [s.name for s in result.clinical.symptoms]
    assert "back_pain" in active_names or "joint_pain" in active_names
    assert result.urgency.level in ("MODERATE", "ROUTINE")


def test_case_18_non_clinical_input():
    text = "I am visiting the clinic to pick up an appointment for next month."
    info = extract_clinical_information(text)
    assert len(info.symptoms) == 0
    assert len(info.negated_symptoms) == 0


def test_case_19_empty_and_whitespace_input():
    info1 = extract_clinical_information("")
    info2 = extract_clinical_information("   ")
    info3 = extract_clinical_information(None)
    assert len(info1.symptoms) == 0
    assert len(info2.symptoms) == 0
    assert len(info3.symptoms) == 0


def test_case_20_pipeline_consistency_and_pdf_export():
    """Verify consistency between extraction, urgency, report preview, and PDF generation."""
    input_text = "Severe chest pain and dizziness for two hours, denies cough."
    result = extract_clinical_result(input_text, session_id="test-case-20")

    active_names = [s.name for s in result.clinical.symptoms]
    assert "chest_pain" in active_names
    assert "dizziness" in active_names
    assert "cough" in result.clinical.negated_symptoms
    assert result.urgency.level == "EMERGENCY"

    # Simulated session payload matching backend store
    session_data = {
        "session_id": "test-case-20-session-id",
        "source_language": "gu",
        "original_text": "મને બે કલાકથી છાતીમાં ખૂબ દુખાવો થાય છે અને ચક્કર આવે છે",
        "english_text": input_text,
        "translation_verification": {"status": "consistent", "warnings": []},
        "clinical_data": {
            "chief_complaint": result.clinical.chief_complaint,
            "symptoms": active_names,
            "negated_findings": result.clinical.negated_symptoms,
            "duration": "2 hours",
            "severity": "severe",
            "body_location": "chest",
            "possible_category": result.clinical.possible_category,
            "urgency": result.urgency.level,
            "urgency_reason": result.urgency.reason,
        },
        "urgency": result.urgency.level,
        "doctor_notes": "ECG ordered immediately. Stat cardiology consult.",
    }

    # Generate structured report preview
    report = build_report_data(session_data)
    assert report["urgency"]["level"] == "EMERGENCY"
    assert "chest_pain" in report["clinical_findings"]["symptoms"]
    assert "cough" in report["clinical_findings"]["negated_findings"]
    assert report["doctor_notes"] == "ECG ordered immediately. Stat cardiology consult."

    # Generate PDF
    pdf_bytes = generate_pdf_report(session_data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF-")


def test_case_21_gujarati_cardiac_emergency():
    """Verify that regional Gujarati cardiac phrase triggers chest_pain and EMERGENCY."""
    input_text = "અને હૃદયમાં દુખાવો થાય છે"
    result = extract_clinical_result(input_text, session_id="test-case-21")
    active_names = [s.name for s in result.clinical.symptoms]
    assert "chest_pain" in active_names
    assert result.urgency.level == "EMERGENCY"
    assert "cardiopulmonary" in result.urgency.reason.lower() or "critical" in result.urgency.reason.lower()


def test_case_22_english_pain_in_the_heart():
    """Verify that English 'pain in the heart' and 'pain in the chest' extract chest_pain and EMERGENCY."""
    input_text = "And there is pain in the heart."
    result = extract_clinical_result(input_text, session_id="test-case-22")
    active_names = [s.name for s in result.clinical.symptoms]
    assert "chest_pain" in active_names
    assert result.urgency.level == "EMERGENCY"
