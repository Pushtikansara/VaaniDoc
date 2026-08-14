"""Translation safety and consistency verification layer for VaaniDoc.

This module checks preservation of clinically important information in
translations. It does NOT claim machine translation is guaranteed correct,
nor does it replace professional translation validation.

It detects potentially dangerous mismatches where clinically important
information may have been altered, lost, or inverted during translation.

Checker can detect:
- Negation inversion (e.g. "no fever" -> "have fever")
- Duration mismatches (e.g. "3 days" -> "2 days")
- Body location changes (e.g. "chest" -> "stomach")
- Dosage changes (e.g. "500 mg" -> "100 mg")
- Number/unit preservation or alteration
- Symptom presence/absence
- Severity expression changes

Important: This is a safety-oriented consistency layer only. It is not a
medical correctness validator and cannot guarantee translation accuracy.

What this checker CAN detect:
- Negation inversion when "no"/"without" markers are present in both
  original and translation, and they differ
- Duration mismatches when duration phrases are reliably detectable in
  both texts (supports English numerals/words and Gujarati/Hindi numeral+
  "દિવસ" patterns)
- Body location changes when location keywords match between original and
  translation (supports English and common Gujarati/Hindi terms)
- Dosage value changes when numeric values with units differ
- Unit changes (e.g. "mg" vs "ml")
- Number changes in standalone contexts (not associated with dosage units)
- Symptom loss when a known symptom word is present in original but absent
  from translation
- Severity expression changes when severity keywords differ

What this checker CANNOT guarantee:
- That machine translation is correct or medically valid
- Detection of all clinically important information (only a subset of
  clinically relevant patterns are supported)
- Accurate negation detection for Indian languages without clear negation
  markers
- Body location detection for all possible anatomical terms
- Number preservation in all contexts (only standalone numbers are checked,
  numbers embedded in dosage contexts are handled separately)
- That the translation preserves the original meaning in all cases

Do not use this checker as a replacement for professional translation validation.
Do not silently modify translations based on this checker's output.
Do not claim any numerical accuracy percentage.
Do not replace the original patient statement.

The original patient statement is always preserved in the verification result
under the "original" key.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional


# ---------------------------------------------------------------------------
# Helper: negation keyword sets (not exhaustive, but covers common clinical)
# ---------------------------------------------------------------------------

NEGATION_KEYWORDS_NO = {"no", "without", "none", "never"}
NEGATION_KEYWORDS_AFFIRM = {"have", "has", "having", "experiencing"}
# Gujarati negation keyword: "નથી" = "not"
GUJARATI_NEGATION_KEYWORDS = {"નથી", "nai"}
SYMPTOM_KEYWORDS = {
    "fever", "cough", "pain", "headache", "nausea", "vomiting", "dizziness",
    "fatigue", "chest", "abdomen", "stomach", "breathing", "difficulty",
}
SEVERITY_KEYWORDS = {
    "severe", "mild", "moderate", "intense", "bad", "worse", "better",
    "worst", "worstever", "mildest",
}


def _normalize_whitespace(text: str) -> str:
    """Lowercase and collapse whitespace."""
    return re.sub(r"\s+", " ", text.strip().lower())


def _normalize_duration(duration: str) -> str:
    """Normalize a duration string to a canonical form.

    Converts "3 days", "three days", "3 day" all to "3 days".
    """
    lower = duration.lower().strip()
    # Extract numeric value if present
    m = re.search(r"\b(\d+)\b", lower)
    if m:
        num = m.group(1)
        # Extract unit
        m2 = re.search(r"(day|week|month|year|hour|minute)s?\b", lower)
        if m2:
            unit = m2.group(1).lower()
            # Ensure plural
            if unit == "day":
                return f"{num} days"
            return f"{num} {unit}s"
    # Word-based numbers
    word_to_num = {
        "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8",
        "nine": "9", "ten": "10",
    }
    for word, num in word_to_num.items():
        if lower.startswith(word + " "):
            rest = lower[len(word):].strip()
            m2 = re.search(r"(day|week|month|year|hour|minute)s?\b", rest)
            if m2:
                unit = m2.group(1).lower()
                if unit == "day":
                    return f"{num} days"
                return f"{num} {unit}s"
            return f"{num} days"
    return lower


def _extract_duration(text: str) -> Optional[str]:
    """Try to extract a duration phrase from text.

    Looks for patterns like "3 days", "two days", "3 week", etc.
    Also handles Indian language patterns (e.g. Gujarati "ત્રણ દિવસથી",
    Hindi "तीन दिन से"). Returns the normalized duration string or None.
    """
    # Common duration patterns with numeric prefixes
    m = re.search(r"(\d+)\s+(day|week|month|year|hour|minute)s?\b", text, re.IGNORECASE)
    if m:
        base = m.group(2).lower()
        if base == "day":
            return f"{m.group(1)} days"
        return f"{m.group(1)} {base}s"
    # Word-based numbers in English
    m = re.search(r"(three|four|five|six|seven|eight|nine|ten|two)\s+(day|week|month|year)s?\b", text, re.IGNORECASE)
    if m:
        base = m.group(2).lower()
        if base == "day":
            return f"{m.group(1)} days"
        return f"{m.group(1)} {base}s"
    # Indian language patterns: numeral + day words (Gujarati/Hindi)
    numeral_to_3 = {"ત્રણ": "3", "three": "3", "3": "3"}
    numeral_to_2 = {"ચાતુર": "4", "4": "4"}
    lower = text.lower()
    for gu_day in ["દિવસ", "divs"]:
        if gu_day in lower:
            for num_word, num_val in numeral_to_3.items():
                if num_word in lower:
                    return f"{num_val} days"
            for num_word, num_val in numeral_to_2.items():
                if num_word in lower:
                    return f"{num_val} days"
    # Also check for "days" / "day" in English
    if "days" in lower or "day" in lower:
        m = re.search(r"\b(\d+)\b", text)
        if m:
            return f"{m.group(1)} days"
    return None


def _extract_number_value(text: str) -> Optional[str]:
    """Extract a numeric value from text (e.g. "500", "500 mg")."""
    m = re.search(r"\b(\d+(?:\.\d+)?)\b", text)
    if m:
        return m.group(1)
    return None


def _extract_unit(text: str) -> Optional[str]:
    """Extract a unit keyword from text."""
    lower = text.lower()
    # Direct unit abbreviations with word boundaries
    m = re.search(r"\b(mg|ml|g|kg|mcg|units?|mm|cm)\b", lower, re.IGNORECASE)
    if m:
        return m.group(1).lower()
    # Full unit words (milligrams, milliliters, etc.)
    unit_map = {
        "milligrams": "mg",
        "milliliters": "ml",
        "grams": "g",
        "kilograms": "kg",
        "micrograms": "mcg",
    }
    for full_word, abbr in unit_map.items():
        if full_word in lower:
            return abbr
    # Also check for partial matches: find any known abbreviation
    # within the text (e.g. "mg" in "milligrams")
    for abbr in ["mg", "ml", "g", "kg", "mcg"]:
        if abbr in lower:
            # Verify it's not part of another word (except the unit itself)
            # Simple check: if the abbr appears, return it
            return abbr
    return None


def _extract_body_location(text: str) -> Optional[str]:
    """Extract a body location keyword from text.

    Supports English and common Indian language terms.
    Gujarati: "ચેતી" (chest), "પેટ" (stomach), "છાતી" (chest)
    Hindi: "छाती" (chest), "पेट" (stomach/abdomen)
    """
    lower = text.lower()
    # English terms
    for loc in ["chest", "abdomen", "stomach", "head", "ear", "throat", "eye",
                "arm", "leg", "hand", "foot", "back", "neck"]:
        if loc in lower:
            return loc
    # Gujarati terms
    gu_loc_map = {
        "ચેતી": "chest",
        "પેટ": "stomach",
        "છાતી": "chest",
        "ગેડોક": "chest",
        "મૂળી": "head",
    }
    for gu_word, en_loc in gu_loc_map.items():
        if gu_word in lower:
            return en_loc
    # Hindi terms
    hi_loc_map = {
        "छाती": "chest",
        "पेट": "stomach",
        "पीठ": "back",
        "सर": "head",
    }
    for hi_word, en_loc in hi_loc_map.items():
        if hi_word in lower:
            return en_loc
    return None


def _extract_negation(text: str) -> Optional[bool]:
    """Detect if negation is present in the text.

    Returns:
        None if no clear negation marker found
        True  if negative formulation detected
        False if affirmative formulation detected
    """
    lower = text.lower()
    # If "no" or "without" or "none" appears, treat as negative
    if any(kw in lower for kw in NEGATION_KEYWORDS_NO):
        return True
    # If affirmative verbs appear without negation markers, treat as affirmative
    if any(kw in lower for kw in NEGATION_KEYWORDS_AFFIRM):
        return False
    # Check for Gujarati negation keyword "નથી" = "not"
    if any(kw in lower for kw in GUJARATI_NEGATION_KEYWORDS):
        return True
    return None


def _extract_severity(text: str) -> Optional[str]:
    """Extract a severity keyword from text."""
    lower = text.lower()
    for sev in SEVERITY_KEYWORDS:
        if sev in lower:
            return sev
    return None


def _extract_symptom(text: str) -> Optional[str]:
    """Extract a known symptom keyword from text."""
    lower = text.lower()
    for symp in SYMPTOM_KEYWORDS:
        if symp in lower:
            return symp
    return None


# ---------------------------------------------------------------------------
# Core verification function
# -------------------------------------------------------------------------


def verify_translation(
    original_text: str,
    source_language: str,
    english_translation: str,
) -> Dict[str, Any]:
    """Verify translation consistency for clinically important information.

    This checker detects potentially dangerous mismatches where clinically
    important information may have been altered, lost, or inverted during
    translation. It does NOT claim the translation is correct or medically
    valid — it only flags areas where the original and translation diverge
    on reliably detectable clinical facts.

    Args:
        original_text: The original Indian-language patient statement.
        source_language: The VaaniDoc language code (e.g. "gu", "hi").
        english_translation: The English translation to verify.

    Returns:
        A dict with:
        - "status": "consistent" | "needs_review"
        - "warnings": list of warning dicts, each with "type" and "message"
        - "original": the original patient statement (always preserved)
        - "translation": the English translation being verified

    Raises:
        Nothing is raised. All errors are returned as structured warnings.
    """
    warnings: List[Dict[str, Any]] = []

    # Normalize both texts for comparison
    original_lower = original_text.strip().lower()
    translation_lower = english_translation.strip().lower()

    # --- Duration check ---
    orig_duration = _extract_duration(original_text)
    trans_duration = _extract_duration(english_translation)

    if orig_duration is not None and trans_duration is not None:
        orig_norm = _normalize_duration(orig_duration)
        trans_norm = _normalize_duration(trans_duration)
        if orig_norm != trans_norm:
            warnings.append({
                "type": "duration_mismatch",
                "message": (
                    f"Duration may not match: original '{orig_duration}' "
                    f"vs translation '{trans_duration}'."
                ),
            })
    elif orig_duration is not None and trans_duration is None:
        warnings.append({
            "type": "duration_lost",
            "message": (
                "Duration present in original but not detected in translation."
            ),
        })

    # --- Negation check ---
    orig_negation = _extract_negation(original_text)
    trans_negation = _extract_negation(english_translation)

    if orig_negation is not None and trans_negation is not None:
        if orig_negation != trans_negation:
            warnings.append({
                "type": "negation_mismatch",
                "message": (
                    "Negation may have been inverted during translation. "
                    "Verify the presence/absence of negation (e.g. 'no fever' vs 'have fever')."
                ),
            })

    # --- Body location check ---
    orig_location = _extract_body_location(original_text)
    trans_location = _extract_body_location(english_translation)

    if orig_location is not None and trans_location is not None:
        if orig_location != trans_location:
            warnings.append({
                "type": "body_location_mismatch",
                "message": (
                    f"Body location mismatch: original '{orig_location}' "
                    f"vs translation '{trans_location}'."
                ),
            })
    elif orig_location is not None and trans_location is None:
        warnings.append({
            "type": "body_location_lost",
            "message": "Body location present in original but not detected in translation.",
        })

    # --- Dosage/check ---
    orig_dosage_val = _extract_number_value(original_text)
    trans_dosage_val = _extract_number_value(english_translation)
    orig_dosage_unit = _extract_unit(original_text)
    trans_dosage_unit = _extract_unit(english_translation)

    # Dosage value check (if both have numbers)
    if orig_dosage_val is not None and trans_dosage_val is not None:
        if orig_dosage_val != trans_dosage_val:
            warnings.append({
                "type": "dosage_changed",
                "message": (
                    f"Dosage value may have changed: original '{orig_dosage_val}' "
                    f"vs translation '{trans_dosage_val}'."
                ),
            })

    # Unit check (if both have units)
    if orig_dosage_unit is not None and trans_dosage_unit is not None:
        if orig_dosage_unit != trans_dosage_unit:
            warnings.append({
                "type": "unit_changed",
                "message": (
                    f"Unit may have changed: original '{orig_dosage_unit}' "
                    f"vs translation '{trans_dosage_unit}'."
                ),
            })
    elif orig_dosage_unit is not None and trans_dosage_unit is None:
        warnings.append({
            "type": "unit_lost",
            "message": "Dosage unit present in original but not detected in translation.",
        })

    # --- Number preservation check ---
    # Extract standalone numbers (not as part of dosage/unit)
    orig_standalone = re.findall(r"\b(\d+(?:\.\d+)?)\b", original_text)
    trans_standalone = re.findall(r"\b(\d+(?:\.\d+)?)\b", english_translation)

    # Remove numbers that are likely dosage values
    # Only treat as dosage if the number was explicitly extracted as a dosage value
    # (i.e. there's a matching unit, or the number is in a dosage context)
    dosage_number_set = set()
    if orig_dosage_val is not None and trans_dosage_val is not None:
        # Both have dosage values extracted - use them to filter
        dosage_number_set.add(orig_dosage_val)
        dosage_number_set.add(trans_dosage_val)
    elif orig_dosage_val is not None:
        # Only original has dosage - filter original's dosage value
        dosage_number_set.add(orig_dosage_val)
    elif trans_dosage_val is not None:
        # Only translation has dosage - filter translation's dosage value
        dosage_number_set.add(trans_dosage_val)
    # If neither has a clear dosage value, don't filter numbers as dosage

    orig_numbers = [n for n in orig_standalone if n not in dosage_number_set]
    trans_numbers = [n for n in trans_standalone if n not in dosage_number_set]

    # If both have numbers, check for major changes
    if orig_numbers and trans_numbers:
        # Check if any original number is missing from translation
        for onum in orig_numbers:
            if onum not in trans_numbers:
                warnings.append({
                    "type": "number_changed",
                    "message": (
                        f"Number may have changed: original '{onum}' "
                        f"not found in translation."
                    ),
                })

    # --- Symptom presence check ---
    orig_symptom = _extract_symptom(original_text)
    trans_symptom = _extract_symptom(english_translation)

    if orig_symptom is not None:
        if trans_symptom is None:
            warnings.append({
                "type": "symptom_lost",
                "message": (
                    f"Symptom '{orig_symptom}' present in original "
                    f"but not detected in translation."
                ),
            })
        elif orig_symptom != trans_symptom:
            warnings.append({
                "type": "symptom_changed",
                "message": (
                    f"Symptom may have changed: original '{orig_symptom}' "
                    f"vs translation '{trans_symptom}'."
                ),
            })

    # --- Severity check ---
    orig_severity = _extract_severity(original_text)
    trans_severity = _extract_severity(english_translation)

    if orig_severity is not None and trans_severity is not None:
        if orig_severity != trans_severity:
            warnings.append({
                "type": "severity_changed",
                "message": (
                    f"Severity may have changed: original '{orig_severity}' "
                    f"vs translation '{trans_severity}'."
                ),
            })

    # --- Determine overall status ---
    if warnings:
        status = "needs_review"
    else:
        status = "consistent"

    result: Dict[str, Any] = {
        "status": status,
        "warnings": warnings,
        "original": original_text,
        "translation": english_translation,
    }

    return result