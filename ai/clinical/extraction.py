"""Deterministic symptom extraction engine for VaaniDoc.

This module extracts known primary-care symptoms from English text using
a normalized, word-boundary-aware matching strategy against a predefined
symptom knowledge base.

It implements local-scope negation detection to distinguish between
symptoms a patient actively has versus those they explicitly deny.
"""

from __future__ import annotations

import re
from typing import Optional

from ai.clinical.schemas import (
    ClinicalInformation,
    ClinicalResult,
    Symptom,
    UrgencyInformation,
)
from ai.clinical.symptoms import build_synonym_index, get_category
from ai.clinical.urgency import classify_urgency

_WS = re.compile(r"\s+")

NEGATION_PHRASES = {
    "no", "not", "don't", "do not", "doesn't", "does not", "didn't", 
    "did not", "never", "without", "denies", "denied", "negative for", "free of",
    "નથી", "નહિ", "ના", "नहीं", "नहीं है"
}

POST_NEGATION_PHRASES = {
    "નથી", "નહિ", "ના", "નથી થતો", "નથી થતી", "નથી થયો", "નથી થતું",
    "नहीं", "नहीं है", "ना", "नहीं हुआ", "नहीं होता", "नहीं होती",
    "नाही", "नाहीत",
}

# Boundaries that reset the negation window (sentence endings + conjunctions)
_BOUNDARY_PATTERN = re.compile(r'[.,!?;|।]|\bbut\b|\band\b|પણ|અને|પરંતુ|और|लेकिन')

DURATION_PATTERNS = [
    r"(\d+)\s+(day|days|week|weeks|month|months|hour|hours)",
    r"(three|four|five|six|seven|eight|nine|ten|two|one)\s+(day|days|week|weeks|month|months|hour|hours)",
]

SEVERITY_PATTERNS = {
    "very_severe": [r"\bworst\b", r"\bexcruciating\b", r"\bunbearable\b", r"\bvery\s+severe\b"],
    "severe": [r"\bsevere\b", r"\bintense\b", r"\bbad\b", r"\bterrible\b"],
    "moderate": [r"\bmoderate\b", r"\bsomewhat\b", r"\bmedium\b"],
    "mild": [r"\bmild\b", r"\bslight\b", r"\ba\s+little\b", r"\bminor\b"],
}

BODY_PARTS = [
    "head", "chest", "abdomen", "stomach", "belly", "throat", "ear", "ears",
    "eye", "eyes", "back", "neck", "arm", "arms", "leg", "legs", "knee", "knees",
    "skin", "shoulder", "wrist", "hand", "foot", "feet"
]


def _normalize(text: str) -> str:
    """Lowercase, strip, and collapse repeated whitespace."""
    return _WS.sub(" ", text.strip().lower())


def _build_phrase_pattern(phrase: str) -> str:
    """Build boundary-safe regex pattern supporting both ASCII and Indic scripts."""
    if re.search(r"[^\x00-\x7F]", phrase):
        return re.escape(phrase)
    return r"\b" + re.escape(phrase) + r"\b"


def _is_negated(text_before: str, text_after: str = "") -> bool:
    """Determine if a symptom is locally negated (pre-negation or post-negation)."""
    # 1. Pre-symptom negation (English SVO style)
    before_segments = _BOUNDARY_PATTERN.split(text_before)
    if before_segments:
        local_before = before_segments[-1]
        for neg in NEGATION_PHRASES:
            pattern = r"(?:^|[\s,.;:!?])" + re.escape(neg) + r"(?:$|[\s,.;:!?])"
            if re.search(pattern, local_before, re.IGNORECASE):
                return True

    # 2. Post-symptom negation (Indic SOV style: e.g., 'દુખાવો નથી', 'दर्द नहीं है')
    if text_after:
        after_segments = _BOUNDARY_PATTERN.split(text_after)
        if after_segments:
            local_after = after_segments[0]
            for neg in POST_NEGATION_PHRASES:
                pattern = r"(?:^|[\s,.;:!?])" + re.escape(neg) + r"(?:$|[\s,.;:!?])"
                if re.search(pattern, local_after, re.IGNORECASE):
                    return True

    return False


def _extract_duration(text: str) -> Optional[str]:
    """Extract general duration from English text."""
    for pattern in DURATION_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = m.group(1)
            unit = m.group(2).lower()
            if not unit.endswith("s") and val not in ("1", "one"):
                unit = f"{unit}s"
            return f"{val} {unit}"
    return None


def _extract_severity(text: str) -> Optional[str]:
    """Extract clinical severity level."""
    text_lower = text.lower()
    for level, patterns in SEVERITY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                return level
    return None


def _extract_body_location(text: str) -> Optional[str]:
    """Extract mentioned body location."""
    text_lower = text.lower()
    for part in BODY_PARTS:
        if re.search(r"\b" + re.escape(part) + r"\b", text_lower):
            return part
    return None


def extract_symptoms(text: Optional[str]) -> list[Symptom]:
    """Extract active, known symptoms from English patient text.

    Args:
        text: English patient text (e.g., "I have severe headache but no fever").

    Returns:
        List of Symptom objects, preserving the order of appearance in the text.
        Explicitly negated symptoms are excluded. Contradictory mentions are
        resolved by preserving the active mention.
        Returns an empty list if text is None, empty, or contains no active symptoms.
    """
    if not text:
        return []
    
    normalized_text = _normalize(str(text))
    if not normalized_text:
        return []

    index = build_synonym_index()
    sorted_phrases = sorted(index.keys(), key=len, reverse=True)

    active_symptoms: dict[str, int] = {}
    matched_chars = [False] * len(normalized_text)

    for phrase in sorted_phrases:
        pattern = _build_phrase_pattern(phrase)
        
        for match in re.finditer(pattern, normalized_text):
            start, end = match.span()
            
            if any(matched_chars[start:end]):
                continue
                
            for i in range(start, end):
                matched_chars[i] = True
                
            canonical = index[phrase]
            text_before = normalized_text[:start]
            text_after = normalized_text[end:]
            
            if _is_negated(text_before, text_after):
                pass
            else:
                if canonical not in active_symptoms:
                    active_symptoms[canonical] = start
                else:
                    active_symptoms[canonical] = min(active_symptoms[canonical], start)

    sorted_canonicals = sorted(active_symptoms.keys(), key=lambda c: active_symptoms[c])
    duration = _extract_duration(normalized_text)
    severity = _extract_severity(normalized_text)
    body_part = _extract_body_location(normalized_text)

    results = []
    for c in sorted_canonicals:
        results.append(
            Symptom(
                name=c,
                duration=duration,
                severity=severity,  # type: ignore[arg-type]
                body_part=body_part,
                confidence=0.95,
            )
        )
    return results


def extract_clinical_information(text: Optional[str]) -> ClinicalInformation:
    """Extract active symptoms, negated symptoms, chief complaint, and category."""
    if not text:
        return ClinicalInformation()

    normalized_text = _normalize(str(text))
    if not normalized_text:
        return ClinicalInformation()

    index = build_synonym_index()
    sorted_phrases = sorted(index.keys(), key=len, reverse=True)

    active_symptoms: dict[str, int] = {}
    negated_symptoms: set[str] = set()
    matched_chars = [False] * len(normalized_text)

    for phrase in sorted_phrases:
        pattern = _build_phrase_pattern(phrase)
        
        for match in re.finditer(pattern, normalized_text):
            start, end = match.span()
            
            if any(matched_chars[start:end]):
                continue
                
            for i in range(start, end):
                matched_chars[i] = True
                
            canonical = index[phrase]
            text_before = normalized_text[:start]
            text_after = normalized_text[end:]
            
            if _is_negated(text_before, text_after):
                negated_symptoms.add(canonical)
            else:
                if canonical not in active_symptoms:
                    active_symptoms[canonical] = start
                else:
                    active_symptoms[canonical] = min(active_symptoms[canonical], start)

    # If a symptom has both active and negated mentions, active takes precedence
    for active in active_symptoms:
        negated_symptoms.discard(active)

    sorted_canonicals = sorted(active_symptoms.keys(), key=lambda c: active_symptoms[c])
    duration = _extract_duration(normalized_text)
    severity = _extract_severity(normalized_text)
    body_part = _extract_body_location(normalized_text)

    symptom_objs = [
        Symptom(
            name=c,
            duration=duration,
            severity=severity,  # type: ignore[arg-type]
            body_part=body_part,
            confidence=0.95,
        )
        for c in sorted_canonicals
    ]

    chief_complaint = sorted_canonicals[0] if sorted_canonicals else None

    # Determine dominant category
    categories = [get_category(c) for c in sorted_canonicals if get_category(c)]
    possible_category = categories[0] if categories else None

    return ClinicalInformation(
        chief_complaint=chief_complaint,
        symptoms=symptom_objs,
        negated_symptoms=sorted(list(negated_symptoms)),
        possible_category=possible_category,
    )


def extract_clinical_result(text: Optional[str], session_id: Optional[str] = None) -> ClinicalResult:
    """Extract complete ClinicalResult including symptoms, negations, and urgency triage."""
    info = extract_clinical_information(text)
    duration = _extract_duration(text or "")
    severity = _extract_severity(text or "")
    urgency_info = classify_urgency(
        symptoms=info.symptoms,
        text=text,
        severity=severity,
        duration=duration,
        negated_symptoms=info.negated_symptoms,
    )
    return ClinicalResult(
        session_id=session_id,
        clinical=info,
        urgency=urgency_info,
    )
