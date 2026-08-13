"""Deterministic symptom extraction engine for VaaniDoc.

This module extracts known primary-care symptoms from English text using
a normalized, word-boundary-aware matching strategy against a predefined
symptom knowledge base.
"""

import re
from typing import Optional

from ai.clinical.schemas import Symptom
from ai.clinical.symptoms import build_synonym_index

_WS = re.compile(r"\s+")


def _normalize(text: str) -> str:
    """Lowercase, strip, and collapse repeated whitespace."""
    return _WS.sub(" ", text.strip().lower())


def extract_symptoms(text: Optional[str]) -> list[Symptom]:
    """Extract known symptoms from English patient text.

    Args:
        text: English patient text (e.g., "I have severe headache").

    Returns:
        List of Symptom objects, preserving the order of appearance in the text.
        Returns an empty list if text is None, empty, or contains no symptoms.
    """
    if not text:
        return []
    
    # Handle non-string inputs gracefully by converting to string, though
    # standard usage expects a string.
    normalized_text = _normalize(str(text))
    if not normalized_text:
        return []

    index = build_synonym_index()
    # Sort phrases by length descending to match longest multi-word phrases first
    sorted_phrases = sorted(index.keys(), key=len, reverse=True)

    found_symptoms = {}  # canonical_name -> start_index
    matched_chars = [False] * len(normalized_text)

    for phrase in sorted_phrases:
        # Use word boundaries to prevent matching inside unrelated words
        # (e.g., 'rash' inside 'trash').
        pattern = r"\b" + re.escape(phrase) + r"\b"
        
        for match in re.finditer(pattern, normalized_text):
            start, end = match.span()
            
            # Skip if this span overlaps with a previously matched longer phrase
            if any(matched_chars[start:end]):
                continue
                
            # Mark the span as matched
            for i in range(start, end):
                matched_chars[i] = True
                
            canonical = index[phrase]
            if canonical not in found_symptoms:
                found_symptoms[canonical] = start
            else:
                # If matched again, keep the earliest position for ordering
                found_symptoms[canonical] = min(found_symptoms[canonical], start)

    # Sort symptoms by their earliest appearance in the text
    sorted_canonicals = sorted(found_symptoms.keys(), key=lambda c: found_symptoms[c])

    # Return Symptom objects with None for severity, duration, body_part, confidence
    return [Symptom(name=c) for c in sorted_canonicals]
