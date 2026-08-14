import pytest
from fastapi.testclient import TestClient

from backend.translation_api import app
from backend.ai.translation.translator import TranslationFailedError

client = TestClient(app)


def test_success_gujarati_translation(monkeypatch):
    monkeypatch.setattr("backend.main.translate", lambda text,
                        language: "I have had fever for two days.")
    monkeypatch.setattr(
        "backend.main.verify_translation",
        lambda text, language, english: {
            "status": "consistent", "warnings": []},
    )

    response = client.post(
        "/api/translate",
        json={"text": "મને બે દિવસથી તાવ છે", "source_language": "gu"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_language"] == "gu"
    assert payload["english_text"] == "I have had fever for two days."
    assert payload["verification"]["status"] == "consistent"
    assert payload["verification"]["warnings"] == []


def test_success_hindi_translation(monkeypatch):
    monkeypatch.setattr("backend.main.translate", lambda text,
                        language: "I have had fever for two days.")
    monkeypatch.setattr(
        "backend.main.verify_translation",
        lambda text, language, english: {
            "status": "consistent", "warnings": []},
    )

    response = client.post(
        "/api/translate",
        json={"text": "मुझे दो दिनों से बुखार है", "source_language": "hi"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_language"] == "hi"
    assert payload["english_text"] == "I have had fever for two days."
    assert payload["verification"]["status"] == "consistent"


def test_unsupported_language():
    response = client.post(
        "/api/translate",
        json={"text": "hello", "source_language": "fr"},
    )

    assert response.status_code == 400
    assert "Unsupported source language" in response.json()["detail"]


def test_empty_text():
    response = client.post(
        "/api/translate",
        json={"text": "   ", "source_language": "gu"},
    )

    assert response.status_code == 400
    assert "empty or whitespace-only" in response.json()["detail"]


def test_malformed_request():
    response = client.post(
        "/api/translate",
        json={"source_language": "gu"},
    )

    assert response.status_code == 422


def test_model_failure(monkeypatch):
    def raise_model_error(text, language):
        raise TranslationFailedError("CTranslate2 inference failed")

    monkeypatch.setattr("backend.main.translate", raise_model_error)

    response = client.post(
        "/api/translate",
        json={"text": "મને તાવ છે", "source_language": "gu"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Translation service unavailable"


def test_translation_safety_warning(monkeypatch):
    monkeypatch.setattr("backend.main.translate",
                        lambda text, language: "I have fever.")
    monkeypatch.setattr(
        "backend.main.verify_translation",
        lambda text, language, english: {
            "status": "warning", "warnings": ["Possible negation mismatch"]},
    )

    response = client.post(
        "/api/translate",
        json={"text": "મને તાવ નથી", "source_language": "gu"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["verification"]["status"] == "warning"
    assert payload["verification"]["warnings"] == [
        "Possible negation mismatch"]
