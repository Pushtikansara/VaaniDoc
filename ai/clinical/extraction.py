"""Deterministic symptom extraction engine for VaaniDoc.

This module extracts known primary-care symptoms from English text using
a normalized, word-boundary-aware matching strategy against a predefined
symptom knowledge base.

It implements local-scope negation detection to distinguish between
symptoms a patient actively has versus those they explicitly deny.
"""

import re
from typing import Optional

from ai.clinical.schemas import Symptom
from ai.clinical.symptoms import build_synonym_index

_WS = re.compile(r"\s+")

NEGATION_PHRASES = {
    "no", "not", "don't", "do not", "doesn't", "does not", "didn't", 
    "did not", "never", "without", "denies", "denied", "negative for", "free of"
}

# Boundaries that reset the negation window (sentence endings + conjunctions)
_BOUNDARY_PATTERN = re.compile(r'[.,!?;]|\bbut\b|\band\b')


def _normalize(text: str) -> str:
    """Lowercase, strip, and collapse repeated whitespace."""
    return _WS.sub(" ", text.strip().lower())


def _is_negated(text_before: str) -> bool:
    """Determine if a symptom is locally negated.
    
    Looks at the text immediately preceding the symptom match. The context
    window is bounded by the last punctuation mark or conjunction. If a known
    negation phrase appears in that local window, the symptom is considered negated.
    """
    # Extract the local clause/phrase before the symptom
    segments = _BOUNDARY_PATTERN.split(text_before)
    if not segments:
        return False
        
    local_context = segments[-1]
    
    # Check for negation phrases as whole words
    for neg in NEGATION_PHRASES:
        pattern = r"\b" + re.escape(neg) + r"\b"
        if re.search(pattern, local_context):
            return True
            
    return False


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
    
    # Handle non-string inputs gracefully by converting to string, though
    # standard usage expects a string.
    normalized_text = _normalize(str(text))
    if not normalized_text:
        return []

    index = build_synonym_index()
    # Sort phrases by length descending to match longest multi-word phrases first
    sorted_phrases = sorted(index.keys(), key=len, reverse=True)

    active_symptoms = {}  # canonical_name -> start_index of first ACTIVE mention
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
            text_before = normalized_text[:start]
            
            # Determine if this specific mention is negated
            if _is_negated(text_before):
                # We skip negated mentions. They do not activate the symptom.
                pass
            else:
                # Active mention
                if canonical not in active_symptoms:
                    active_symptoms[canonical] = start
                else:
                    # If matched multiple times, keep the earliest active position for ordering
                    active_symptoms[canonical] = min(active_symptoms[canonical], start)

    # Sort symptoms by their earliest active appearance in the text
    sorted_canonicals = sorted(active_symptoms.keys(), key=lambda c: active_symptoms[c])

    # Return Symptom objects with None for severity, duration, body_part, confidence
    return [Symptom(name=c) for c in sorted_canonicals]
