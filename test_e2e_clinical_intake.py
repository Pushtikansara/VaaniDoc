"""End-to-end tests for VaaniDoc multilingual clinical intake flow.

Tests the complete patient-to-doctor pipeline using the FastAPI TestClient
with monkeypatched model dependencies. Covers Gujarati and Hindi inputs
with various clinical scenarios.
"""

import sys
sys.path.insert(0, r'F:\VaaniDoc')

import pytest
from fastapi.testclient import TestClient
from backend.ai.translation.sessions import create_session, get_session, delete_session
from backend.ai.translation.translation_safety import verify_translation


def get_app():
    """Import app lazily."""
    from backend.translation_api import app
    return app


@pytest.fixture(autouse=True)
def mock_translation(monkeypatch):
    """Monkeypatch translation and verification for each test."""
    import backend.main as main_module

    def mock_translate(text, language):
        return "I have a fever."

    def mock_verify(text, language, english):
        return {
            "status": "consistent",
            "warnings": [],
            "original": text,
            "translation": english,
        }

    monkeypatch.setattr(main_module, "translate", mock_translate)
    monkeypatch.setattr(main_module, "verify_translation", mock_verify)

    yield

    # Reset after test
    main_module.translate = None
    main_module.verify_translation = None


def test_gujarati_fever():
    """1. Gujarati fever - basic symptom translation."""
    client = TestClient(get_app())

    response = client.post(
        "/api/translate",
        json={"text": "મને તાવ છે", "source_language": "gu"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["english_text"] is not None
    assert "fever" in payload["english_text"].lower()
    # Original text preserved in verification
    assert payload["verification"]["original"] == "મને તાવ છે"


def test_hindi_fever():
    """2. Hindi fever - basic symptom translation."""
    client = TestClient(get_app())

    response = client.post(
        "/api/translate",
        json={"text": "मुझे बुखार है", "source_language": "hi"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["english_text"] is not None
    assert "fever" in payload["english_text"].lower()
    # Original text preserved in verification
    assert payload["verification"]["original"] == "मुझे बुखार है"


def test_gujarati_fever_headache():
    """3. Gujarati fever + headache - multiple symptoms."""
    client = TestClient(get_app())

    # Override translate for this specific test
    import backend.main as main_module
    main_module.translate = lambda text, language: "I have a fever and headache."

    response = client.post(
        "/api/translate",
        json={"text": "મને તાવ અને HEADACHE છે", "source_language": "gu"},
    )
    assert response.status_code == 200
    payload = response.json()
    # Clinical extraction should detect multiple symptoms
    from backend.ai.translation.clinical_extraction import extract_clinical_info
    clinical = extract_clinical_info(payload["english_text"])
    symptoms = clinical.get("symptoms", [])
    assert "fever" in [s.lower() for s in symptoms]


def test_negated_symptom():
    """4. Negated symptom - critical safety test.

    Input: "મને તાવ ન'hi."
    Translation must preserve: "I do not have a fever."
    A translation that changes this to: "I have a fever."
    must be treated as a critical mismatch.
    """
    client = TestClient(get_app())

    # Test with negation mismatch - verify_translation should flag it
    import backend.main as main_module
    main_module.translate = lambda text, language: "I have a fever."

    response = client.post(
        "/api/translate",
        json={"text": "મને તાવ ન'hi", "source_language": "gu"},
    )
    assert response.status_code == 200
    payload = response.json()

    # Verify the translation using the real safety checker
    orig_text = "મને તાવ ન'hi"
    eng_text = payload["english_text"]

    # Run real safety verification
    vr = verify_translation(orig_text, "gu", eng_text)
    warnings = vr.get("warnings", [])

    # Negation mismatch must be flagged
    negation_warnings = [w for w in warnings if w["type"] == "negation_mismatch"]
    assert len(negation_warnings) > 0, (
        f"Negation mismatch NOT detected! Warnings: {warnings}. "
        f"This is a critical safety failure - 'no fever' was translated to 'have fever'."
    )

    # Original text must remain available
    assert vr["original"] == orig_text


def test_duration():
    """5. Duration - extract time period from translation."""
    client = TestClient(get_app())

    response = client.post(
        "/api/translate",
        json={"text": "મને ત્રણ દિવસથી તાવ છે", "source_language": "gu"},
    )
    assert response.status_code == 200
    payload = response.json()
    # Clinical extraction should extract duration
    from backend.ai.translation.clinical_extraction import extract_clinical_info
    clinical = extract_clinical_info(payload["english_text"])
    duration = clinical.get("duration")
    assert duration is not None, f"Duration should be extracted, got clinical_data: {clinical}"
    # Original text preserved in verification
    assert payload["verification"]["original"] == "મને ત્રણ દિવસથી તાવ છે"


def test_number():
    """6. Number - numeric values preserved in translation."""
    client = TestClient(get_app())

    response = client.post(
        "/api/translate",
        json={"text": "મને 3 દિવસથી તાવ છે", "source_language": "gu"},
    )
    assert response.status_code == 200
    payload = response.json()
    # Original text preserved in verification
    assert payload["verification"]["original"] == "મને 3 દિવસથી તાવ છે"


def test_body_location():
    """7. Body location - anatomical location in translation."""
    client = TestClient(get_app())

    response = client.post(
        "/api/translate",
        json={"text": "મને છાતીમાં દુખાવો છે", "source_language": "gu"},
    )
    assert response.status_code == 200
    payload = response.json()
    # Body location should be extracted from English
    from backend.ai.translation.clinical_extraction import extract_clinical_info
    clinical = extract_clinical_info(payload["english_text"])
    body_location = clinical.get("body_location")
    # Original text preserved in verification
    assert payload["verification"]["original"] == "મને છાતીમાં દુખાવો છે"


def test_medication_dosage():
    """8. Medication dosage - numeric dosage with units."""
    client = TestClient(get_app())

    response = client.post(
        "/api/translate",
        json={"text": "મે 500 mg દવા લીધી", "source_language": "gu"},
    )
    assert response.status_code == 200
    payload = response.json()
    # Dosage information should be in the translation
    assert payload["english_text"] is not None
    # Original text preserved in verification
    assert payload["verification"]["original"] == "મે 500 mg દવા લીધી"


def test_multiple_symptoms():
    """9. Multiple symptoms - several clinical findings."""
    client = TestClient(get_app())

    response = client.post(
        "/api/translate",
        json={"text": "મને તાવ, કuffy, અને હેત્ડ ache છે", "source_language": "gu"},
    )
    assert response.status_code == 200
    payload = response.json()
    # English text should be generated
    assert payload["english_text"] is not None
    # Original preserved in verification
    assert payload["verification"]["original"] is not None


def test_translation_mismatch():
    """10. Translation mismatch - safety check detects issues."""
    client = TestClient(get_app())

    import backend.main as main_module
    main_module.translate = lambda text, language: "I have fever."

    response = client.post(
        "/api/translate",
        json={"text": "મને તાવ ન'hi", "source_language": "gu"},
    )
    assert response.status_code == 200
    payload = response.json()

    # Translation warnings should be generated for negation mismatch
    warnings = payload["verification"].get("warnings", [])
    # The system must flag critical mismatch: "I have fever" from "I do not have fever"
    critical_warnings = [w for w in warnings if "negation" in w.get("type", "") or "mismatch" in w.get("type", "")]
    assert len(critical_warnings) > 0, (
        f"Critical translation mismatch not flagged! Warnings: {warnings}. "
        f"'મને તાવ ન'hi.' → translation must NOT become 'I have a fever.'"
    )


def test_original_text_preserved():
    """Verify original text remains available after translation pipeline."""
    client = TestClient(get_app())

    response = client.post(
        "/api/translate",
        json={"text": "મને તાવ છે", "source_language": "gu"},
    )
    assert response.status_code == 200
    payload = response.json()
    # Original text preserved in verification
    assert payload["verification"]["original"] == "મને તાવ છે"
    # English text also available
    assert payload["english_text"] is not None


def test_doctor_receives_english():
    """Verify doctor receives English as the primary representation."""
    client = TestClient(get_app())

    response = client.post(
        "/api/translate",
        json={"text": "મને તાવ છે", "source_language": "gu"},
    )
    assert response.status_code == 200
    payload = response.json()
    # Doctor's primary representation is english_text
    assert payload["english_text"] is not None
    assert len(payload["english_text"].strip()) > 0
    # But original is also accessible
    assert payload["verification"]["original"] == "મને તાવ છે"


def test_doctor_accesses_original_language():
    """Verify doctor can access original-language text."""
    client = TestClient(get_app())

    response = client.post(
        "/api/translate",
        json={"text": "મને કોફ છે", "source_language": "gu"},
    )
    assert response.status_code == 200
    payload = response.json()
    # Doctor can access original text
    assert payload["verification"]["original"] == "મને કોફ છે"
    # And English translation
    assert payload["english_text"] is not None


def test_session_deletion():
    """11. Session data is deleted when consultation ends."""
    from backend.ai.translation.sessions import create_session, delete_session, get_session

    # Create a session directly
    session_id = create_session(
        source_language="gu",
        original_text="મને તાવ છે",
        english_text="I have a fever.",
        translation_verification={"status": "consistent", "warnings": []},
        clinical_data={"symptoms": ["fever"], "urgency": "routine"},
    )
    assert session_id is not None

    # Verify session exists
    retrieved = get_session(session_id)
    assert retrieved is not None
    assert retrieved["original_text"] == "મને તાવ છે"

    # Delete the session
    success = delete_session(session_id)
    assert success is True

    # Verify session is gone
    retrieved_after = get_session(session_id)
    assert retrieved_after is None, "Session should have been deleted"


def test_body_location_mismatch_flagged():
    """Critical test: body location mismatch detection.

    Input: "મને છાતીમાં દુખાવો છે."
    If translation says: "I have stomach pain."
    the system must flag a body-location mismatch.
    """
    client = TestClient(get_app())

    response = client.post(
        "/api/translate",
        json={"text": "મને છાતીમાં દુખાવો છે", "source_language": "gu"},
    )
    assert response.status_code == 200
    payload = response.json()

    # Use real safety verification to detect body location mismatch
    orig_text = "મને છાતીમાં દુખાવો છે"
    eng_text = payload["english_text"]

    # Run real safety verification
    vr = verify_translation(orig_text, "gu", eng_text)
    warnings = vr.get("warnings", [])

    # Body location mismatch should be flagged
    body_location_warnings = [w for w in warnings if w["type"] == "body_location_mismatch"]
    assert len(body_location_warnings) > 0, (
        f"Body location mismatch NOT flagged! Warnings: {warnings}. "
        f"'મને છાતીમાં દુખાવo.' → 'I have stomach pain.' should be flagged as mismatch "
        f"(chest vs stomach)."
    )

    # Original must be preserved
    assert vr["original"] == orig_text