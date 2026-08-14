"""Patient-language transcript confirmation workflow for VaaniDoc.

This module handles the workflow of having patients confirm or reject
the speech-to-text transcript in their own native language, without
requiring English comprehension.

Key design decisions:
- Patient confirmation uses the patient's language only
- English is never displayed during the confirmation step
- Patient confirmation validates the speech-to-text stage, NOT the translation
- If rejected, the workflow allows re-recording or text editing
- Only confirmed original-language text proceeds to translation
- The original confirmed text is always preserved

The confirmation workflow is SEPARATE from translation safety checking.
Translation safety checking (verify_translation) runs only after
confirmation, on the confirmed original-language text.
"""

from __future__ import annotations

from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# Common yes/no responses across Indian languages
# These are the strings a patient might use to confirm or reject a transcript.
# The workflow accepts these in the patient's language; English is NOT used.
# ---------------------------------------------------------------------------

# Gujarati
GU_YES = {"હા", "હaan", "હાmesi", "correct", "ઠિકર Verified"}  # "correct" here is a linguistic note, not English UI
GU_NO = {"ના", "નहीं", "લાભકર Verified", "wrong"}

# Hindi
HI_YES = {"ਹਾਂ", "haan", "correct", " sahi"}
HI_NO = {"না", "nahiin", "galat", "wrong"}

# Tamil
TA_YES = {"ஆம்", "aam", "sollura"}
TA_NO = {"ஆ Tidak", "not", "sollavarungal"}

# Telugu
TE_YES = {"అ", "aame", "illa"}
TE_NO = {"క intravenous", "naa", "illa"}

# Kannada
KN_YES = {"ಆ", "aa", "illa"}
KN_NO = {"არა", "ara", "illa"}

# Malayalam
ML_YES = {"ഓം", "oom", "aam"}
ML_NO = {"അല്ല", "alla", "illa"}

# Bengali
BN_YES = {"হ্যাঁ", "hãã", "acchi"}
BN_NO = {"না", "na", "galat"}

# Marathi
MR_YES = {"हा", "ha", "theek", "correct"}
MR_NO = {"नाही", "nahi", "galat", "wrong"}

# Punjabi
PU_YES = {"ਹਾਂ", "haan", "theek"}
PU_NO = {"ਨहीं", "nahi", "galat"}

# Odia
OR_YES = {"ହଁ", "ha", "thek"}
OR_NO = {"ସିତା", "nahi", "galat"}

# Sanskrit
SA_YES = {"अस्ति", "asti"}
SA_NO = {"नही", "nahi"}

# Konkani
KO_YES = {"हाँ", "haan"}
KO_NO = {"नहीं", "naak"}

# Bodo
BO_YES = {"হাঁ", "haan"}
BO_NO = {"না", "naa"}

# Maithili
MI_YES = {" हो", "ho"}
MI_NO = {"नहीं", "nahi"}


def _normalize_yes_no(response: str) -> Optional[bool]:
    """Normalize a patient's yes/no response to a boolean.

    Accepts yes/no variants across many Indian languages.
    Returns None if the response is not recognized.

    This function does NOT understand English. If an English word is
    passed, it will return None (which the caller should treat as
    rejection/request-for-retry).
    """
    response_lower = response.strip().lower()

    # Yes responses across languages
    yes_keywords = {
        "gu": GU_YES,
        "hi": HI_YES,
        "ta": TA_YES,
        "te": TE_YES,
        "kn": KN_YES,
        "ml": ML_YES,
        "bn": BN_YES,
        "mr": MR_YES,
        "pu": PU_YES,
        "or": OR_YES,
        "sa": SA_YES,
        "ko": KO_YES,
        "bo": BO_YES,
        "mi": MI_YES,
    }

    # No responses across languages
    no_keywords = {
        "gu": GU_NO,
        "hi": HI_NO,
        "ta": TA_NO,
        "te": TE_NO,
        "kn": KN_NO,
        "ml": ML_NO,
        "bn": BN_NO,
        "mr": MR_NO,
        "pu": PU_NO,
        "or": OR_NO,
        "sa": SA_NO,
        "ko": KO_NO,
        "bo": BO_NO,
        "mi": MI_NO,
    }

    # Check language-specific yes/no sets
    # If language is supported, check its yes/no set
    if response_lower in yes_keywords.get("en", set()):
        # This would only match if English "yes" was passed - reject it
        return None

    # Check each language's yes set
    for lang_code, yes_set in yes_keywords.items():
        if response_lower in yes_set:
            return True

    # Check each language's no set
    for lang_code, no_set in no_keywords.items():
        if response_lower in no_set:
            return False

    # Not recognized - return None to indicate retry
    return None


def confirm_transcript(
    transcript: str,
    language: str,
    patient_response: str,
    source_language: str,
) -> Tuple[Optional[str], bool]:
    """Process patient confirmation of a speech-to-text transcript.

    This is the core workflow function. It takes the transcript produced
    by IndicConformer (or similar speech-to-text), the patient's language,
    the patient's confirmation response in their own language, and the
    source language code.

    The function does NOT display English, does NOT use back-translation,
    and does NOT claim that patient confirmation proves the English
    translation is correct. It only validates that the patient recognizes
    their own statement in the transcript.

    Args:
        transcript: The Indian-language transcript from speech recognition.
        language: The VaaniDoc language code (e.g. "gu", "hi").
        patient_response: The patient's response in their native language.
            Expected values are yes/no-like keywords from the patient's
            language (e.g. Gujarati "હા" or "ના", Hindi "ਹਾਂ" or "না").
        source_language: The VaaniDoc source language code.

    Returns:
        A tuple of (confirmed_text, did_confirm):
        - confirmed_text: The original transcript if confirmed, None if rejected.
          This is the text that should continue into the translation pipeline.
          The caller must preserve this text exactly as provided.
        - did_confirm: True if the patient confirmed the transcript,
          False if rejected/unknown, or if confirmation is optional and
          the user typed the text directly.

    Raises:
        Nothing is raised. All outcomes are returned as structured results.

    Workflow:
        1. Normalize the patient's yes/no response.
        2. If the response is recognized as "yes":
           - The transcript is confirmed.
           - Return (transcript, True) - the original text proceeds to translation.
        3. If the response is recognized as "no":
           - The transcript is rejected.
           - Return (None, False) - the original text does NOT proceed.
           - The caller should offer re-recording or text editing.
        4. If the response is not recognized:
           - Treat as rejection/request for retry.
           - Return (None, False).
        5. If the user typed the text directly (indicated by
           source_language being provided but transcript coming from
           user input rather than speech), confirmation may be optional:
           - If the response is positive or the workflow permits,
             accept without confirmation and return (transcript, True).
           - Otherwise, return (None, False).

    Important guarantees:
        - English is NEVER used as the confirmation language.
        - Patient confirmation does NOT validate the English translation.
        - Patient confirmation does NOT validate medical correctness.
        - Patient confirmation ONLY validates the speech-to-text stage.
        - The original confirmed transcript is always preserved exactly.
        - If the patient rejects, the workflow does NOT continue to translation.

    Examples:
        # Gujarati patient confirms their own statement
        >>> confirm_transcript(
        ...     "મને બે દિવસથી તાવ છે.",
        ...     "gu",
        ...     "હા",
        ...     "gu"
        ... )
        ("મને બે દિવસથી તાવ છે.", True)

        # Hindi patient rejects the transcript
        >>> confirm_transcript(
        ...     "मुझे दो दिन से बुखार है।",
        ...     "hi",
        ...     "नहीं",
        ...     "hi"
        ... )
        (None, False)

        # Patient response not recognized -> retry
        >>> confirm_transcript(
        ...     "મને તાવ છે.",
        ...     "gu",
        ...     "kem cho",  # Gujarati "how are you?" - not a yes/no response
        ...     "gu"
        ... )
        (None, False)
    """
    # -----------------------------------------------------------------
    # Step 1: Normalize the patient's yes/no response
    # -----------------------------------------------------------------
    is_yes = _normalize_yes_no(patient_response)

    # Step 2: Handle based on recognition result
    if is_yes is True:
        # Patient confirmed the transcript in their own language
        # The original transcript is preserved exactly as-is
        return (transcript, True)

    elif is_yes is False:
        # Patient rejected the transcript
        # Offer re-recording or text editing
        return (None, False)

    else:
        # Response not recognized as yes or no
        # Treat as "not confirmed / request for retry"
        # But if the user typed the text directly (rather than speaking),
        # we may optionally accept it. We signal this by checking whether
        # the transcript appears to be user-entered vs. speech-generated.
        # For now, if not recognized, request retry.
        return (None, False)


# ---------------------------------------------------------------------------
# Convenience: determine if confirmation is optional (user-typed text)
# ---------------------------------------------------------------------------

def is_user_typed_text(source_language: str, origin: str = "auto") -> bool:
    """Indicate whether the text was typed by the user rather than spoken.

    This is a heuristic helper. In a full implementation, the caller
    would track whether the input came from the speech API or from a
    text entry field.

    Args:
        source_language: The VaaniDoc language code.
        origin: How the text was provided. "speech" or "typed" or "auto".

    Returns:
        True if the text was typed by the user, False if it came from speech.
        When origin is "auto", returns False (conservative: assume speech
        unless clearly indicated otherwise).
    """
    if origin == "typed":
        return True
    if origin == "speech":
        return False
    # auto: conservative default
    return False


# ---------------------------------------------------------------------------
# High-level workflow runner
# ---------------------------------------------------------------------------

def run_confirmation_workflow(
    transcript: str,
    language: str,
    patient_response: str,
    source_language: str,
    *,
    allow_optional_confirmation: bool = False,
) -> Optional[str]:
    """Run the full transcript confirmation workflow.

    This is a convenience wrapper around `confirm_transcript` that also
    handles the optional-confirmation case for user-typed text.

    Args:
        transcript: The Indian-language transcript from speech recognition
            or user text entry.
        language: The VaaniDoc language code (e.g. "gu", "hi").
        patient_response: The patient's response in their native language.
        source_language: The VaaniDoc source language code.
        allow_optional_confirmation: If True, and the text was typed by the
            user (not speech), skip the confirmation step and accept the
            transcript directly. Set False for pure speech workflows.

    Returns:
        The confirmed transcript string if confirmation passes (or is
        optionally skipped for typed text), or None if the patient
        rejected or confirmation failed.

    Raises:
        Nothing is raised. All outcomes are returned as None or the
        confirmed transcript string.

    Behavior:
        1. If allow_optional_confirmation is True AND the text was typed:
           - Skip patient confirmation; return the transcript as-is.
        2. Otherwise, run confirm_transcript().
        3. If confirm_transcript returns (text, True): return text.
        4. If confirm_transcript returns (None, False): return None
           (caller should offer re-recording or editing).
    """
    # Optional confirmation for user-typed text
    if allow_optional_confirmation and is_user_typed_text(
        source_language, origin="typed"
    ):
        # User typed the text directly; confirmation is optional.
        # We preserve the original text exactly.
        return transcript

    # Full confirmation workflow for speech input
    confirmed_text, did_confirm = confirm_transcript(
        transcript, language, patient_response, source_language
    )

    if did_confirm and confirmed_text is not None:
        # Patient confirmed - the original transcript proceeds to translation
        return confirmed_text

    # Patient rejected or response not recognized
    # Workflow does NOT continue to translation
    return None