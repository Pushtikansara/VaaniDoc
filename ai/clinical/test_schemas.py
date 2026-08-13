"""Tests for the VaaniDoc clinical data-contract schemas.

Run with:
    pytest ai/clinical/test_schemas.py -v
"""

import pytest
from pydantic import ValidationError

from ai.clinical.schemas import (
    ClinicalExtractionRequest,
    ClinicalInformation,
    ClinicalResult,
    Symptom,
    UrgencyInformation,
)


# ── ClinicalExtractionRequest ───────────────────────────────────────


class TestClinicalExtractionRequest:
    """Input request validation."""

    def test_valid_request(self):
        req = ClinicalExtractionRequest(
            session_id="abc123",
            language="en",
            text="I have severe headache for two days.",
        )
        assert req.session_id == "abc123"
        assert req.language == "en"
        assert req.text == "I have severe headache for two days."

    def test_text_is_stripped(self):
        req = ClinicalExtractionRequest(text="  hello world  ")
        assert req.text == "hello world"

    def test_empty_text_fails(self):
        with pytest.raises(ValidationError):
            ClinicalExtractionRequest(text="")

    def test_whitespace_only_text_fails(self):
        with pytest.raises(ValidationError):
            ClinicalExtractionRequest(text="   \t\n  ")

    def test_language_normalised_to_lowercase(self):
        req = ClinicalExtractionRequest(text="fever", language="EN")
        assert req.language == "en"

    def test_language_default_is_en(self):
        req = ClinicalExtractionRequest(text="fever")
        assert req.language == "en"

    def test_session_id_default_is_none(self):
        req = ClinicalExtractionRequest(text="fever")
        assert req.session_id is None

    def test_non_english_language_accepted(self):
        """Non-English language codes are not rejected (needed for testing)."""
        req = ClinicalExtractionRequest(text="test", language="gu")
        assert req.language == "gu"


# ── Symptom ──────────────────────────────────────────────────────────


class TestSymptom:
    """Symptom model validation."""

    def test_valid_symptom_all_fields(self):
        s = Symptom(
            name="headache",
            severity="severe",
            duration="2 days",
            body_part="head",
            confidence=0.95,
        )
        assert s.name == "headache"
        assert s.severity == "severe"
        assert s.duration == "2 days"
        assert s.body_part == "head"
        assert s.confidence == 0.95

    def test_valid_symptom_minimal(self):
        s = Symptom(name="fever")
        assert s.name == "fever"
        assert s.severity is None
        assert s.duration is None
        assert s.body_part is None
        assert s.confidence is None

    def test_invalid_severity_fails(self):
        with pytest.raises(ValidationError):
            Symptom(name="fever", severity="extreme")

    def test_all_valid_severity_values(self):
        for level in ("mild", "moderate", "severe", "very_severe"):
            s = Symptom(name="test", severity=level)
            assert s.severity == level

    def test_confidence_zero_passes(self):
        s = Symptom(name="test", confidence=0.0)
        assert s.confidence == 0.0

    def test_confidence_one_passes(self):
        s = Symptom(name="test", confidence=1.0)
        assert s.confidence == 1.0

    def test_confidence_above_one_fails(self):
        with pytest.raises(ValidationError):
            Symptom(name="test", confidence=1.01)

    def test_confidence_below_zero_fails(self):
        with pytest.raises(ValidationError):
            Symptom(name="test", confidence=-0.1)

    def test_confidence_mid_range(self):
        s = Symptom(name="test", confidence=0.5)
        assert s.confidence == 0.5


# ── ClinicalInformation ─────────────────────────────────────────────


class TestClinicalInformation:
    """Clinical information container validation."""

    def test_defaults(self):
        info = ClinicalInformation()
        assert info.chief_complaint is None
        assert info.symptoms == []
        assert info.negated_symptoms == []
        assert info.possible_category is None

    def test_with_symptoms(self):
        info = ClinicalInformation(
            chief_complaint="headache",
            symptoms=[
                Symptom(name="headache", severity="severe"),
                Symptom(name="vomiting"),
            ],
        )
        assert len(info.symptoms) == 2
        assert info.symptoms[0].name == "headache"

    def test_negated_symptoms(self):
        info = ClinicalInformation(
            negated_symptoms=["chest pain", "shortness of breath"],
        )
        assert len(info.negated_symptoms) == 2
        assert "chest pain" in info.negated_symptoms

    def test_possible_category(self):
        info = ClinicalInformation(possible_category="Neurological")
        assert info.possible_category == "Neurological"


# ── UrgencyInformation ──────────────────────────────────────────────


class TestUrgencyInformation:
    """Urgency information validation."""

    def test_defaults(self):
        u = UrgencyInformation()
        assert u.level is None
        assert u.reason is None

    def test_with_values(self):
        u = UrgencyInformation(level="EMERGENCY", reason="Chest pain reported")
        assert u.level == "EMERGENCY"
        assert u.reason == "Chest pain reported"


# ── ClinicalResult ──────────────────────────────────────────────────


class TestClinicalResult:
    """Complete pipeline result validation."""

    def test_valid_full_result(self):
        result = ClinicalResult(
            session_id="abc123",
            clinical=ClinicalInformation(
                chief_complaint="headache",
                symptoms=[
                    Symptom(
                        name="headache",
                        severity="severe",
                        duration="2 days",
                        body_part="head",
                        confidence=0.95,
                    ),
                    Symptom(name="vomiting", confidence=0.91),
                ],
                negated_symptoms=[],
                possible_category="Neurological",
            ),
            urgency=UrgencyInformation(
                level="MODERATE",
                reason="Severe headache with vomiting",
            ),
        )
        assert result.session_id == "abc123"
        assert result.clinical.chief_complaint == "headache"
        assert len(result.clinical.symptoms) == 2
        assert result.urgency.level == "MODERATE"

    def test_minimal_result(self):
        result = ClinicalResult()
        assert result.session_id is None
        assert result.clinical.symptoms == []
        assert result.urgency.level is None

    def test_model_dump_roundtrip(self):
        result = ClinicalResult(
            session_id="s1",
            clinical=ClinicalInformation(
                chief_complaint="fever",
                symptoms=[Symptom(name="fever", severity="moderate")],
            ),
            urgency=UrgencyInformation(level="ROUTINE"),
        )
        data = result.model_dump()
        assert isinstance(data, dict)
        assert data["session_id"] == "s1"
        assert data["clinical"]["chief_complaint"] == "fever"
        assert len(data["clinical"]["symptoms"]) == 1
        assert data["urgency"]["level"] == "ROUTINE"

        # Reconstruct from dict
        rebuilt = ClinicalResult(**data)
        assert rebuilt == result

    def test_model_dump_json(self):
        result = ClinicalResult(
            clinical=ClinicalInformation(
                symptoms=[Symptom(name="cough")],
            ),
        )
        json_str = result.model_dump_json()
        assert isinstance(json_str, str)
        assert '"cough"' in json_str

    def test_missing_optional_fields(self):
        """All optional fields should gracefully default."""
        result = ClinicalResult(
            clinical=ClinicalInformation(
                symptoms=[Symptom(name="fever")],
            ),
        )
        assert result.session_id is None
        assert result.clinical.chief_complaint is None
        assert result.clinical.possible_category is None
        assert result.clinical.negated_symptoms == []
        assert result.urgency.level is None
        assert result.urgency.reason is None
        symptom = result.clinical.symptoms[0]
        assert symptom.severity is None
        assert symptom.duration is None
        assert symptom.body_part is None
        assert symptom.confidence is None
