"""Clinical extraction layer for VaaniDoc.

Extracts structured clinical information from English translations
of Indian-language patient statements.

This module is designed to be separate from the translation layer
and only extracts reliably detectable clinical facts from English text.
It does NOT claim medical correctness and should not be used for
diagnosis without clinical validation.

Extraction patterns cover common clinical information found in
translation output from the IndicTrans2 CT2 model.
"""

import re
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Clinical keyword sets (not exhaustive, covers common presentations)
# ---------------------------------------------------------------------------

SYMPTOM_KEYWORDS = {
    "fever", "cough", "pain", "headache", "nausea", "vomiting",
    "dizziness", "fatigue", "chest", "abdomen", "stomach",
    "breathing", "difficulty", "sore throat"
}

SEVERITY_KEYWORDS = {
    "severe", "mild", "moderate", "intense", "bad", "worse", "better",
    "worst", "mildest"
}

# Duration patterns
DURATION_PATTERNS = [
    r"(\d+)\s+(day|days|week|weeks|month|months|hour|hours)",
    r"(three|four|five|six|seven|eight|nine|ten)\s+(day|days|week|weeks)",
]

# Urgency levels based on clinical findings
URGENCY_RULES = {
    "shortness of breath": "emergency",
    "difficulty breathing": "emergency",
    "chest pain": "urgent",
    "high fever": "urgent",
    "persistent vomiting": "urgent",
}


def extract_symptoms(text: str) -> List[str]:
    """Extract symptom keywords from English text."""
    text_lower = text.lower()
    found = []
    for symp in SYMPTOM_KEYWORDS:
        if symp in text_lower:
            found.append(symp)
    return found


def extract_severity(text: str) -> Optional[str]:
    """Extract severity keyword from English text."""
    text_lower = text.lower()
    for sev in SEVERITY_KEYWORDS:
        if sev in text_lower:
            return sev
    return None


def extract_duration(text: str) -> Optional[str]:
    """Extract duration from English text.

    Looks for patterns like "3 days", "two weeks", "five hours".
    """
    for pattern in DURATION_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            # Normalize to "X days" format
            val = m.group(1)
            unit = m.group(2).lower()
            if unit in ("day", "days"):
                return f"{val} days"
            return f"{val} {unit}s"
    return None


def extract_body_location(text: str) -> Optional[str]:
    """Extract body location from English text."""
    text_lower = text.lower()
    locations = ["chest", "abdomen", "stomach", "head", "ear", "throat"]
    for loc in locations:
        if loc in text_lower:
            return loc
    return None


def extract_urgency(text: str) -> Optional[str]:
    """Extract urgency level from English text based on keyword rules.

    Returns one of: "routine", "urgent", "emergency"
    """
    text_lower = text.lower()
    for keyword, urgency in URGENCY_RULES.items():
        if keyword in text_lower:
            return urgency
    return "routine"


def extract_clinical_info(text: str) -> Dict[str, Optional[str]]:
    """Extract all clinical information from English text.

    Returns a dict with: symptoms, severity, duration, body_location, urgency
    """
    return {
        "symptoms": extract_symptoms(text),
        "severity": extract_severity(text),
        "duration": extract_duration(text),
        "body_location": extract_body_location(text),
        "urgency": extract_urgency(text),
    }


def validate_english_text(text: str) -> bool:
    """Basic validation that text appears to be English clinical text.

    This is a heuristic check, not a validation of medical correctness.
    """
    if not text or not text.strip():
        return False
    # Check for common English clinical words
    clinical_markers = ["fever", "pain", "cough", "chest", "days", "mg", "mg"]
    text_lower = text.lower()
    found = sum(1 for marker in clinical_markers if marker in text_lower)
    return found >= 1


# ---------------------------------------------------------------------------
# Clinical data model
# ---------------------------------------------------------------------------

class ClinicalData:
    """Structured clinical information extracted from translation."""

    def __init__(self, **kwargs):
        self.chief_complaint: Optional[str] = kwargs.get("chief_complaint")
        self.symptoms: List[str] = kwargs.get("symptoms", [])
        self.duration: Optional[str] = kwargs.get("duration")
        self.severity: Optional[str] = kwargs.get("severity")
        self.body_location: Optional[str] = kwargs.get("body_location")
        self.associated_symptoms: List[str] = kwargs.get("associated_symptoms", [])
        self.urgency: str = kwargs.get("urgency", "routine")

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary."""
        return {
            "chief_complaint": self.chief_complaint,
            "symptoms": self.symptoms,
            "duration": self.duration,
            "severity": self.severity,
            "body_location": self.body_location,
            "associated_symptoms": self.associated_symptoms,
            "urgency": self.urgency,
        }

    def __str__(self):
        parts = [f"Chief complaint: {self.chief_complaint}"]
        if self.symptoms:
            parts.append(f"Symptoms: {', '.join(self.symptoms)}")
        if self.duration:
            parts.append(f"Duration: {self.duration}")
        if self.severity:
            parts.append(f"Severity: {self.severity}")
        if self.body_location:
            parts.append(f"Body location: {self.body_location}")
        if self.associated_symptoms:
            parts.append(f"Associated symptoms: {', '.join(self.associated_symptoms)}")
        parts.append(f"Urgency: {self.urgency}")
        return "; ".join(parts)