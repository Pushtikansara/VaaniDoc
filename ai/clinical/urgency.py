"""Clinical urgency classification engine for VaaniDoc.

Evaluates extracted symptoms, clinical qualifiers, severity, and duration
to determine an intake urgency triage tier:
    - EMERGENCY : Potential life threat or critical red flag requiring immediate intervention.
    - HIGH      : Severe or acute presentation requiring prompt same-day medical evaluation.
    - MODERATE  : Significant subacute symptoms requiring clinic visit within 24-48 hours.
    - ROUTINE   : Common, non-urgent primary care symptoms suitable for standard scheduling.

NOTE: This is an assistive rule-based screening tool for clinician triage review.
It does NOT constitute an autonomous clinical diagnosis.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Optional, Union

from ai.clinical.schemas import Symptom, UrgencyInformation, URGENCY_LEVELS

# ---------------------------------------------------------------------------
# Negation helper
# ---------------------------------------------------------------------------

_NEGATION_PHRASES = {
    "no", "not", "don't", "do not", "doesn't", "does not", "didn't",
    "did not", "never", "without", "denies", "denied", "negative for", "free of",
    "નથી", "નહિ", "ના", "नहीं", "नहीं है", "ना"
}
_POST_NEGATION_PHRASES = {
    "નથી", "નહિ", "ના", "નથી થતો", "નથી થતી", "નથી થયો", "નથી થતું",
    "नहीं", "नहीं है", "ना", "नहीं हुआ", "नहीं होता", "नहीं होती",
    "नाही", "नाहीत",
}
_BOUNDARY_PATTERN = re.compile(r'[.,!?;|।]|\bbut\b|\band\b|પણ|અને|પરંતુ|और|लेकिन')


def _is_negated(text_before: str, text_after: str = "") -> bool:
    """Determine if a symptom/phrase match is locally negated (pre or post)."""
    segments = _BOUNDARY_PATTERN.split(text_before)
    if segments:
        local_context = segments[-1]
        for neg in _NEGATION_PHRASES:
            pattern = r"(?:^|[\s,.;:!?])" + re.escape(neg) + r"(?:$|[\s,.;:!?])"
            if re.search(pattern, local_context, re.IGNORECASE):
                return True

    if text_after:
        after_segments = _BOUNDARY_PATTERN.split(text_after)
        if after_segments:
            local_after = after_segments[0]
            for neg in _POST_NEGATION_PHRASES:
                pattern = r"(?:^|[\s,.;:!?])" + re.escape(neg) + r"(?:$|[\s,.;:!?])"
                if re.search(pattern, local_after, re.IGNORECASE):
                    return True

    return False


# ---------------------------------------------------------------------------
# Red-flag and triage keyword patterns
# ---------------------------------------------------------------------------

EMERGENCY_SYMPTOMS = {
    "chest_pain",
    "shortness_of_breath",
    "fainting",
    "seizure",
    "coughing_up_blood",
    "vomiting_blood",
}

EMERGENCY_TEXT_PATTERNS = [
    r"\bchest\s+pain\b",
    r"\bchest\s+tightness\b",
    r"\bheart\s+attack\b",
    r"\bheart\s+pain\b",
    r"\bpain\s+in\s+(?:the\s+|my\s+|one's\s+|his\s+|her\s+|a\s+)?heart\b",
    r"\bpain\s+in\s+(?:the\s+|my\s+|one's\s+|his\s+|her\s+|a\s+)?chest\b",
    r"\bpain\s+around\s+(?:the\s+|my\s+)?(?:heart|chest)\b",
    r"\bchest\s*(?:is\s*)?hurts?\b",
    r"\bheart\s*(?:is\s*)?hurts?\b",
    r"\bcardiac\s+pain\b",
    r"\bshortness\s+of\s+breath\b",
    r"\bdifficulty\s+breathing\b",
    r"\bunable\s+to\s+breathe\b",
    r"\bpassed\s+out\b",
    r"\blost\s+consciousness\b",
    r"\bunconscious\b",
    r"\bblacked\s+out\b",
    r"\bseizure\b",
    r"\bconvulsion\b",
    r"\bfits\b",
    r"\bsevere\s+bleeding\b",
    r"\bheavy\s+bleeding\b",
    r"\bvomiting\s+blood\b",
    r"\bcoughing\s+up\s+blood\b",
    r"\bhemoptysis\b",
    r"\bsudden\s+weakness\b",
    r"\bsudden\s+paralysis\b",
    r"\bsudden\s+numbness\b",
    r"\bslurred\s+speech\b",
    r"\banaphylaxis\b",
    r"\bswelling\s+of\s+(lips|tongue|throat)\b",
    # Regional Indian Red Flags: Gujarati
    r"હૃદય\s*(?:માં|નો)?\s*દુ[ખઃ]ાવો",
    r"છાતી\s*(?:માં|નો)?\s*દુ[ખઃ]ાવો",
    r"હૃદય\s*(?:માં\s*)?દુખ(?:ે|વું|ાય)",
    r"છાતી\s*(?:માં\s*)?દુખ(?:ે|વું|ાય)",
    r"હાર્ટ\s*એટેક",
    r"હૃદય\s*રોગ",
    r"છાતી\s*માં\s*(?:દબાણ|ભીંસ|ભારેપણું)",
    r"શ્વાસ\s*(?:લેવામાં\s*તકલીફ|ચડવો|ચડે|લેવાતો\s*નથી)",
    r"બેભાન",
    r"ખેંચ",
    r"લોહી\s*ની\s*ઉલટી",
    # Regional Indian Red Flags: Hindi
    r"सीने\s*(?:में|का)?\s*दर्द",
    r"छाती\s*(?:में|का)?\s*दर्द",
    r"दिल\s*(?:में|का)?\s*दर्द",
    r"हार्ट\s*अटैक",
    r"सांस\s*(?:लेने\s*में\s*तकलीफ|फूलना)",
    r"बेहोश",
    r"दौरा",
    r"खून\s*की\s*उल्टी",
    # Regional Indian Red Flags: Marathi / Tamil / Telugu
    r"छातीत\s*दुખ?णे",
    r"हृदयात\s*दुખ?णे",
    r"श्वास\s*घेण्यास\s*त्रास",
    r"நெஞ்சு\s*வலி",
    r"மாரடைப்பு",
    r"ఛాతీ\s*నొప్పి",
    r"గుండె\s*నొప్పి",
]

HIGH_URGENCY_SYMPTOMS = {
    "confusion",
    "blood_in_stool",
    "high_fever",
    "persistent_vomiting",
    "dehydration",
    "vision_loss",
    "stiff_neck",
}

HIGH_TEXT_PATTERNS = [
    r"\bhigh\s+fever\b",
    r"\bfever\s+(over|above)\s+(102|103|104|39|40)\b",
    r"\bsevere\s+(abdominal|stomach|belly|head|back)\s+pain\b",
    r"\bexcruciating\s+pain\b",
    r"\bunbearable\s+pain\b",
    r"\bpersistent\s+vomiting\b",
    r"\bunable\s+to\s+keep\s+(fluids|water|food)\s+down\b",
    r"\bblood\s+in\s+(stool|urine)\b",
    r"\bstiff\s+neck\b",
    r"\bconfusion\b",
    r"\bdisoriented\b",
    r"\bblurred\s+vision\b",
    r"\bsudden\s+vision\s+loss\b",
]

MODERATE_URGENCY_SYMPTOMS = {
    "fever",
    "abdominal_pain",
    "vomiting",
    "diarrhea",
    "dizziness",
    "ear_pain",
    "joint_pain",
    "dysuria",
    "wheezing",
    "palpitations",
}

MODERATE_TEXT_PATTERNS = [
    r"\bfever\b",
    r"\babdominal\s+pain\b",
    r"\bstomach\s+(pain|ache)\b",
    r"\bvomiting\b",
    r"\bdiarrhea\b",
    r"\bloose\s+motions\b",
    r"\bear\s+pain\b",
    r"\bswollen\s+(joint|ankle|knee|leg)\b",
    r"\bburning\s+urination\b",
    r"\bpain\s+urinating\b",
    r"\bproductive\s+cough\b",
    r"\bpersistent\s+cough\b",
    r"\brash\s+spreading\b",
]


def _extract_symptom_name(sym: Union[str, Symptom, Any]) -> str:
    """Normalize input symptom to canonical lowercase string."""
    if isinstance(sym, Symptom):
        return sym.name.lower()
    if isinstance(sym, dict):
        return str(sym.get("name", "")).lower()
    return str(sym).lower()


def classify_urgency(
    symptoms: Optional[Iterable[Union[str, Symptom]]] = None,
    text: Optional[str] = None,
    severity: Optional[str] = None,
    duration: Optional[str] = None,
    negated_symptoms: Optional[Iterable[str]] = None,
) -> UrgencyInformation:
    """Classify clinical intake urgency based on symptoms, severity, and text cues.

    Properly respects negation boundaries so negated symptoms (e.g. 'no chest pain')
    do not trigger emergency or urgent tiers.

    Returns:
        UrgencyInformation with level in ("EMERGENCY", "HIGH", "MODERATE", "ROUTINE")
        and a clinically descriptive reason explaining the assigned triage tier.
    """
    raw_symptoms = list(symptoms or [])
    symptom_names = [_extract_symptom_name(s) for s in raw_symptoms]
    negated_set = {str(n).lower() for n in (negated_symptoms or [])}

    # Remove any negated symptoms from active names
    active_symptoms = [s for s in symptom_names if s not in negated_set]

    text_content = (text or "").lower()
    severity_lower = (severity or "").lower()
    duration_lower = (duration or "").lower()

    # -----------------------------------------------------------------------
    # 1. Tier 1: EMERGENCY Check
    # -----------------------------------------------------------------------
    emergency_matched_symptoms = [s for s in active_symptoms if s in EMERGENCY_SYMPTOMS]
    emergency_matched_patterns = []

    for pattern in EMERGENCY_TEXT_PATTERNS:
        for match in re.finditer(pattern, text_content):
            start = match.start()
            end = match.end()
            text_before = text_content[:start]
            text_after = text_content[end:]
            if not _is_negated(text_before, text_after):
                emergency_matched_patterns.append(match.group(0))

    if emergency_matched_symptoms or emergency_matched_patterns:
        triggers = list(dict.fromkeys(emergency_matched_symptoms + emergency_matched_patterns))
        trigger_str = ", ".join(triggers[:3])
        return UrgencyInformation(
            level="EMERGENCY",
            reason=(
                f"Immediate medical evaluation required: Critical presentation identified "
                f"({trigger_str}) indicating potential cardiopulmonary, neurological, or acute vascular compromise."
            ),
        )

    # -----------------------------------------------------------------------
    # 2. Tier 2: HIGH Urgency Check
    # -----------------------------------------------------------------------
    high_matched_symptoms = [s for s in active_symptoms if s in HIGH_URGENCY_SYMPTOMS]
    high_matched_patterns = []

    for pattern in HIGH_TEXT_PATTERNS:
        for match in re.finditer(pattern, text_content):
            start = match.start()
            end = match.end()
            text_before = text_content[:start]
            text_after = text_content[end:]
            if not _is_negated(text_before, text_after):
                high_matched_patterns.append(match.group(0))

    # Check for severe modifier combined with active pain or fever
    has_severe = severity_lower in ("severe", "very_severe", "intense", "worst")
    has_active_pain = any("pain" in s or "ache" in s for s in active_symptoms)
    has_active_fever = any("fever" in s for s in active_symptoms)

    # Check prolonged duration (> 5-7 days of fever or severe symptoms)
    is_prolonged = any(k in duration_lower for k in ("week", "weeks", "month", "months", "5 day", "6 day", "7 day", "8 day", "10 day"))

    if high_matched_symptoms or high_matched_patterns or (has_severe and (has_active_pain or has_active_fever)) or (has_active_fever and is_prolonged):
        triggers = list(dict.fromkeys(high_matched_symptoms + high_matched_patterns))
        if not triggers and has_severe:
            triggers.append(f"severe symptoms ({severity_lower or 'severe pain'})")
        if is_prolonged and has_active_fever:
            triggers.append(f"prolonged fever ({duration_lower})")
        trigger_str = ", ".join(triggers[:3]) if triggers else "acute severe symptoms"
        return UrgencyInformation(
            level="HIGH",
            reason=(
                f"Prompt clinical evaluation recommended: Acute presentation ({trigger_str}) "
                f"warrants urgent medical assessment within 12-24 hours."
            ),
        )

    # -----------------------------------------------------------------------
    # 3. Tier 3: MODERATE Urgency Check
    # -----------------------------------------------------------------------
    moderate_matched_symptoms = [s for s in active_symptoms if s in MODERATE_URGENCY_SYMPTOMS]
    moderate_matched_patterns = []

    for pattern in MODERATE_TEXT_PATTERNS:
        for match in re.finditer(pattern, text_content):
            start = match.start()
            end = match.end()
            text_before = text_content[:start]
            text_after = text_content[end:]
            if not _is_negated(text_before, text_after):
                moderate_matched_patterns.append(match.group(0))

    has_multi_symptom = len(active_symptoms) >= 3 and severity_lower != "mild"

    if moderate_matched_symptoms or moderate_matched_patterns or has_multi_symptom or has_active_fever or (has_active_pain and not has_severe):
        triggers = list(dict.fromkeys(moderate_matched_symptoms + moderate_matched_patterns + active_symptoms))
        trigger_str = ", ".join(triggers[:3]) if triggers else "symptomatic presentation"
        return UrgencyInformation(
            level="MODERATE",
            reason=(
                f"Outpatient clinical review recommended: Active symptoms ({trigger_str}) "
                f"require evaluation within 24-48 hours for symptom management."
            ),
        )

    # -----------------------------------------------------------------------
    # 4. Tier 4: ROUTINE
    # -----------------------------------------------------------------------
    if active_symptoms:
        trigger_str = ", ".join(active_symptoms[:3])
        return UrgencyInformation(
            level="ROUTINE",
            reason=f"Standard primary care review: Mild or isolated symptoms ({trigger_str}) suitable for routine consultation.",
        )

    return UrgencyInformation(
        level="ROUTINE",
        reason="Routine clinic visit: No acute red-flag symptoms identified.",
    )


def get_urgency(
    symptoms: Optional[Iterable[Union[str, Symptom]]] = None,
    text: Optional[str] = None,
    negated_symptoms: Optional[Iterable[str]] = None,
) -> str:
    """Convenience wrapper returning uppercase urgency tier string."""
    info = classify_urgency(symptoms=symptoms, text=text, negated_symptoms=negated_symptoms)
    return info.level or "ROUTINE"
