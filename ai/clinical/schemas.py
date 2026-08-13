"""Pydantic v2 data-contract schemas for the VaaniDoc Clinical AI module.

These schemas define the contract between:

    Translation (Member 2)
        ↓  English patient text
    Clinical AI  (Member 3)
        ↓  Structured ClinicalResult
    Urgency Engine / Backend / Doctor Dashboard
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ── helpers ──────────────────────────────────────────────────────────

SEVERITY_LEVELS = ("mild", "moderate", "severe", "very_severe")

URGENCY_LEVELS = ("EMERGENCY", "HIGH", "MODERATE", "ROUTINE")

SYMPTOM_CATEGORIES = (
    "Neurological",
    "Respiratory",
    "Cardiovascular",
    "Gastrointestinal",
    "Dermatological",
    "Musculoskeletal",
    "General",
)


# ── 1.  Input schema ────────────────────────────────────────────────

class ClinicalExtractionRequest(BaseModel):
    """Incoming request carrying English patient text for extraction."""

    session_id: Optional[str] = None
    language: str = "en"
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("text must not be empty or whitespace-only")
        return stripped

    @field_validator("language")
    @classmethod
    def normalise_language(cls, value: str) -> str:
        return value.strip().lower()


# ── 2.  Symptom schema ──────────────────────────────────────────────

class Symptom(BaseModel):
    """A single symptom extracted from the patient statement."""

    name: str
    severity: Optional[Literal["mild", "moderate", "severe", "very_severe"]] = None
    duration: Optional[str] = None
    body_part: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


# ── 3.  Clinical information schema ─────────────────────────────────

class ClinicalInformation(BaseModel):
    """Structured clinical information extracted from English text."""

    chief_complaint: Optional[str] = None
    symptoms: list[Symptom] = Field(default_factory=list)
    negated_symptoms: list[str] = Field(default_factory=list)
    possible_category: Optional[str] = None


# ── 4.  Urgency schema ──────────────────────────────────────────────

class UrgencyInformation(BaseModel):
    """Urgency assessment produced by the (future) urgency rule engine.

    Possible levels: EMERGENCY | HIGH | MODERATE | ROUTINE
    """

    level: Optional[str] = None
    reason: Optional[str] = None


# ── 5.  Final response schema ───────────────────────────────────────

class ClinicalResult(BaseModel):
    """Complete output returned by the Clinical AI pipeline."""

    session_id: Optional[str] = None
    clinical: ClinicalInformation = Field(default_factory=ClinicalInformation)
    urgency: UrgencyInformation = Field(default_factory=UrgencyInformation)
