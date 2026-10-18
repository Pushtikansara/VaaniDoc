"""Backend API integration and lifecycle tests for VaaniDoc."""

import pytest
from fastapi.testclient import TestClient
import backend.main


@pytest.fixture
def client():
    return TestClient(backend.main.app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "modules" in data
    assert data["modules"]["clinical"] == "ready"
    assert data["modules"]["reporting"] == "ready"


def test_clinical_extract_endpoint(client):
    response = client.post(
        "/api/clinical/extract",
        json={"text": "I have high fever and vomiting but no rash"},
    )
    assert response.status_code == 200
    data = response.json()
    symptom_names = [s["name"] for s in data["symptoms"]]
    assert "fever" in symptom_names
    assert "vomiting" in symptom_names
    assert "rash" in data["negated_symptoms"]


def test_clinical_analyze_endpoint(client):
    response = client.post(
        "/api/clinical/analyze",
        json={"text": "Severe crushing chest pain radiating to left arm"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["urgency"]["level"] == "EMERGENCY"
    assert "cardiopulmonary" in data["urgency"]["reason"].lower() or "critical" in data["urgency"]["reason"].lower()


def test_text_intake_and_report_lifecycle(client):
    # 1. Submit text intake
    response = client.post(
        "/api/intake/text",
        json={
            "text": "Patient has severe headache and fever for 3 days, denies chest pain",
            "language": "en",
        },
    )
    assert response.status_code == 200
    intake_data = response.json()
    session_id = intake_data["session_id"]
    assert session_id != ""
    assert "headache" in intake_data["clinical_data"]["symptoms"]
    assert "fever" in intake_data["clinical_data"]["symptoms"]
    assert "chest_pain" in intake_data["clinical_data"]["negated_symptoms"]

    # 2. Retrieve structured report data
    report_resp = client.get(f"/api/report/{session_id}/data")
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    assert report_data["session_id"] == session_id
    assert report_data["urgency"]["level"] in ("HIGH", "MODERATE", "EMERGENCY")
    assert "differential_considerations" in report_data
    assert len(report_data["differential_considerations"]) > 0

    # 3. Doctor updates report with vitals, prescriptions, and lab orders
    update_resp = client.put(
        f"/api/report/{session_id}",
        json={
            "doctor_notes": "Prescribed paracetamol 500mg. Advised adequate hydration.",
            "vital_signs": {
                "bp_systolic": 145,
                "bp_diastolic": 95,
                "pulse_bpm": 88,
                "temperature_f": 101.5,
                "spo2_percent": 97,
            },
            "prescriptions": [
                {
                    "name": "Tab. Paracetamol",
                    "dosage": "500 mg",
                    "frequency": "TDS",
                    "duration": "3 days",
                    "instructions": "Post meals",
                }
            ],
            "diagnostic_orders": [
                {"test_name": "Complete Blood Count (CBC)", "urgency": "Routine"}
            ],
            "attending_doctor": {
                "doctor_name": "Dr. R. Sharma, MBBS",
                "license_number": "GMC-84920",
            },
            "status": "FINALIZED",
        },
    )
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data["doctor_notes"] == "Prescribed paracetamol 500mg. Advised adequate hydration."
    assert updated_data["status"] == "FINALIZED"
    assert updated_data["vital_signs"]["bp_display"] == "145/95 mmHg"
    assert len(updated_data["vital_alerts"]) > 0  # Stage 1 hypertension and pyrexia flagged
    assert len(updated_data["prescriptions"]) == 1
    assert len(updated_data["diagnostic_orders"]) == 1
    assert updated_data["attending_doctor"]["doctor_name"] == "Dr. R. Sharma, MBBS"

    # 4. Download PDF report
    pdf_resp = client.get(f"/api/report/{session_id}")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-")

    # 5. End session (Privacy cleanup)
    end_resp = client.post(f"/api/session/end?session_id={session_id}")
    assert end_resp.status_code == 200
    assert end_resp.json()["status"] == "session_ended"

    # 6. Verify session is wiped from memory
    assert client.get(f"/api/report/{session_id}/data").status_code == 404
    assert client.get(f"/api/report/{session_id}").status_code == 404


def test_invalid_requests(client):
    # Empty text intake
    res1 = client.post("/api/intake/text", json={"text": "   ", "language": "en"})
    assert res1.status_code == 422  # validation error

    # Unsupported language
    res2 = client.post("/api/intake/text", json={"text": "Hello doctor", "language": "unsupported_xyz"})
    assert res2.status_code == 400

    # Nonexistent session report
    res3 = client.get("/api/report/non_existent_id/data")
    assert res3.status_code == 404

    # Empty audio file upload
    res4 = client.post(
        "/api/intake",
        data={"language": "gu"},
        files={"audio": ("empty.wav", b"", "audio/wav")},
    )
    assert res4.status_code == 400


def test_voice_intake_pipeline_mocked_asr(client, monkeypatch):
    """Test full voice intake pipeline when ASR returns recognized Indian text."""
    # Mock ASR transcribe function to avoid needing 600MB weights download during unit testing
    def mock_transcribe(audio_path, language):
        return "મને બે દિવસથી છાતીમાં દુખાવો થાય છે"

    monkeypatch.setattr(backend.main, "_asr_transcribe", mock_transcribe)

    with open("ai/speech/audio/synthetic_16k_test.wav", "rb") as f:
        audio_bytes = f.read()

    response = client.post(
        "/api/intake",
        data={"language": "gu"},
        files={"audio": ("patient_speech.wav", audio_bytes, "audio/wav")},
    )
    assert response.status_code == 200
    intake_data = response.json()
    assert intake_data["session_id"] != ""
    assert intake_data["language"] == "gu"
    assert "છાતીમાં દુખાવો" in intake_data["transcript"]

    # Verify report is accessible
    sid = intake_data["session_id"]
    report_resp = client.get(f"/api/report/{sid}/data")
    assert report_resp.status_code == 200
    report = report_resp.json()
    assert report["language_code"] == "gu"
    assert report["original_transcript"] == "મને બે દિવસથી છાતીમાં દુખાવો થાય છે"

    # Clean up session
    clean_resp = client.post(f"/api/session/end?session_id={sid}")
    assert clean_resp.status_code == 200


def test_speech_status_endpoint(client):
    """Verify speech status reports diagnostic information without crashing."""
    resp = client.get("/api/speech/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "configured" in data
    assert "source" in data
    assert "message" in data


def test_speech_fallback_transcription(client, monkeypatch):
    """Verify fallback speech transcription when VAANI_ENABLE_SPEECH_FALLBACK=1."""
    monkeypatch.setenv("VAANI_ENABLE_SPEECH_FALLBACK", "true")
    with open("ai/speech/audio/synthetic_16k_test.wav", "rb") as f:
        audio_bytes = f.read()

    resp = client.post(
        "/api/speech/transcribe",
        data={"language": "gu"},
        files={"audio": ("speech.wav", audio_bytes, "audio/wav")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["language"] == "gu"
    assert "તાવ" in data["transcript"] or len(data["transcript"]) > 0


def test_speech_auth_error_handling(client, monkeypatch):
    """Verify clear HTTP 401 when HuggingFace gated access returns 401."""
    monkeypatch.delenv("VAANI_ENABLE_SPEECH_FALLBACK", raising=False)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("VAANI_ASR_MODEL_PATH", raising=False)

    from ai.speech.asr import SpeechModelAuthError
    def mock_failing_transcribe(audio_path, language):
        raise SpeechModelAuthError("IndicConformer ASR model on Hugging Face is gated and returned 401 Unauthorized.")

    monkeypatch.setattr("backend.speech_api.transcribe", mock_failing_transcribe)

    with open("ai/speech/audio/synthetic_16k_test.wav", "rb") as f:
        audio_bytes = f.read()

    resp = client.post(
        "/api/speech/transcribe",
        data={"language": "gu"},
        files={"audio": ("speech.wav", audio_bytes, "audio/wav")},
    )
    assert resp.status_code == 401
    assert "401 Unauthorized" in resp.json()["detail"]


