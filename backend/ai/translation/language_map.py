"""Language code mapping layer for VaaniDoc.

Converts VaaniDoc application-level language codes into the exact
language identifiers expected by the official IndicTrans2 CT2 checkpoint.

This module is completely independent from FastAPI and from CTranslate2
model logic.  It only deals with code mappings and validation.
"""

# ---------------------------------------------------------------------------
# VaaniDoc -> IndicTrans2 model language code mapping
# ---------------------------------------------------------------------------

# The official IndicTrans2 distilled model (ai4bharat/indictrans2-indic-en-dist-200M)
# supports 22 scheduled Indian languages, each with a FLORES-200 script code.
# These codes must match exactly the checkpoint's vocabulary; do not guess or
# invent codes.  The mapping below is derived from the official AI4Bharat/IndicTrans2
# repository and the project's existing config.py SHORT_CODE_TO_FLORES table.

# Structure convention (comment blocks, not enforced by Python):
#   vaani_code: 2-letter or short code used in the VaaniDoc application
#   flores_code: exact FLORES-200 code expected by the IndicTrans2 CT2 checkpoint
#   language_name: human-readable name (used for UI/logging)

LANGUAGE_MAPPING = {
    # (vaani_code -> (flores_code, language_name))
    "as":  ("asm_Beng", "Assamese"),
    "bn":  ("ben_Beng", "Bengali"),
    "brx": ("brx_Deva", "Bodo"),
    "bho": ("bho_Deva", "Bhojpuri"),
    "doi": ("doi_Deva", "Dogri"),
    "gu":  ("guj_Gujr", "Gujarati"),
    "hi":  ("hin_Deva", "Hindi"),
    "kn":  ("kan_Knda", "Kannada"),
    "kok": ("gom_Deva", "Konkani"),
    "mai": ("mai_Deva", "Maithili"),
    "ml":  ("mal_Mlym", "Malayalam"),
    "mni": ("mni_Mtei", "Manipuri (Meitei)"),
    "mr":  ("mar_Deva", "Marathi"),
    "ne":  ("npi_Deva", "Nepali"),
    "or":  ("ory_Orya", "Odia"),
    "pa":  ("pan_Guru", "Punjabi"),
    "sa":  ("san_Deva", "Sanskrit"),
    "sat": ("sat_Olck", "Santali"),
    "sd":  ("snd_Deva", "Sindhi (Devanagari)"),
    "ta":  ("tam_Taml", "Tamil"),
    "te":  ("tel_Telu", "Telugu"),
    "ur":  ("urd_Arab", "Urdu"),
}

#: Set of all VaaniDoc language codes that are supported by the CT2 model.
#  Populated from the keys of LANGUAGE_MAPPING for O(1) membership tests.
_VAANI_CODES = set(LANGUAGE_MAPPING.keys())

#: Human-readable names keyed by Vaani code.
_VAANI_NAMES = {code: name for code, (_, name) in LANGUAGE_MAPPING.items()}


def is_supported_language(vaani_code: str) -> bool:
    """Check whether a VaaniDoc language code is supported by the CT2 model.

    Args:
        vaani_code: Language short code as used elsewhere in VaaniDoc
                    (e.g. "gu" for Gujarati, "hi" for Hindi).

    Returns:
        True if the code is a recognised VaaniDoc language supported by the model.

    Raises:
        TypeError: If vaani_code is not a string.
    """
    if not isinstance(vaani_code, str):
        raise TypeError(f"Expected a string language code, got {type(vaani_code).__name__}")
    return vaani_code in _VAANI_CODES


def get_model_language_code(vaani_code: str) -> str:
    """Return the exact IndicTrans2 CT2 model language code for a VaaniDoc code.

    This is the FLORES-200 script code that must be passed to the model's
    batch_translate or translate_paragraph methods.

    Args:
        vaani_code: Language short code as used in VaaniDoc (e.g. "gu").

    Returns:
        The FLORES-200 language code (e.g. "guj_Gujr").

    Raises:
        TypeError: If vaani_code is not a string.
        KeyError: If vaani_code is not a recognised VaaniDoc language.
    """
    if not isinstance(vaani_code, str):
        raise TypeError(f"Expected a string language code, got {type(vaani_code).__name__}")
    if vaani_code not in _VAANI_CODES:
        raise KeyError(
            f"Unsupported VaaniDoc language code: '{vaani_code}'. "
            f"Supported codes are: {sorted(_VAANI_CODES)}"
        )
    return LANGUAGE_MAPPING[vaani_code][0]


def get_language_name(vaani_code: str) -> str:
    """Return the human-readable name for a VaaniDoc language code.

    Args:
        vaani_code: Language short code as used in VaaniDoc.

    Returns:
        The English name of the language (e.g. "Gujarati" for code "gu").

    Raises:
        TypeError: If vaani_code is not a string.
        KeyError: If vaani_code is not a recognised VaaniDoc language.
    """
    if not isinstance(vaani_code, str):
        raise TypeError(f"Expected a string language code, got {type(vaani_code).__name__}")
    if vaani_code not in _VAANI_CODES:
        raise KeyError(
            f"Unsupported VaaniDoc language code: '{vaani_code}'. "
            f"Supported codes are: {sorted(_VAANI_CODES)}"
        )
    return _VAANI_NAMES[vaani_code]


def get_supported_vaani_codes() -> tuple:
    """Return a tuple of all VaaniDoc language codes supported by the model.

    Returns:
        Tuple of short codes (e.g. ("gu", "hi", ...)).  Length is 22.
    """
    return tuple(sorted(_VAANI_CODES))


def list_languages() -> dict:
    """Return a dict mapping Vaani codes to (Flores code, language name).

    Returns:
        dict where keys are Vaani codes and values are
        (flores_code, language_name) tuples.
    """
    return dict(LANGUAGE_MAPPING)