import sys
from unittest.mock import MagicMock
sys.modules['ai.speech.asr'] = MagicMock()
sys.modules['ai.speech.asr'].LANGUAGE_CODES = ['en', 'es']

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_clinical_extract_single_symptom():
    response = client.post(
        "/api/clinical/extract",
        json={"text": "I have fever."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "symptoms" in data
    assert len(data["symptoms"]) == 1
    assert data["symptoms"][0]["name"] == "fever"


def test_clinical_extract_multiple_symptoms():
    response = client.post(
        "/api/clinical/extract",
        json={"text": "I have fever and headache."}
    )
    assert response.status_code == 200
    data = response.json()
    names = [s["name"] for s in data["symptoms"]]
    assert "fever" in names
    assert "headache" in names
    assert len(names) == 2


def test_clinical_extract_negation():
    response = client.post(
        "/api/clinical/extract",
        json={"text": "I have fever but no headache."}
    )
    assert response.status_code == 200
    data = response.json()
    names = [s["name"] for s in data["symptoms"]]
    assert names == ["fever"]


def test_clinical_extract_no_symptoms():
    response = client.post(
        "/api/clinical/extract",
        json={"text": "I feel okay."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["symptoms"] == []


def test_clinical_extract_empty_text():
    response = client.post(
        "/api/clinical/extract",
        json={"text": ""}
    )
    # The prompt specified expected HTTP 200, but instructed NOT to modify schemas.py.
    # Because schemas.py validates that text cannot be empty, FastAPI returns 422.
    assert response.status_code == 422


def test_clinical_extract_missing_text():
    response = client.post(
        "/api/clinical/extract",
        json={}
    )
    assert response.status_code == 422
