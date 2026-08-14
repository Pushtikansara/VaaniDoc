"""VaaniDoc IndicTrans2 CT2 Translation Engine.

Handles Indian-language -> English translation using the official
AI4Bharat IndicTrans2 CTranslate2 checkpoint.

Architecture:
    Indian-language text
        <--\
            Language code mapping (language_map.py)     ----/  English text
                CTranslate2 inference (ctranslate2.Translator)
"""

from backend.ai.translation.language_map import (
    is_supported_language,
    get_model_language_code,
    get_language_name,
    get_supported_vaani_codes,
)
import ctranslate2
import logging
import os
import re
from typing import Optional

# ---------------------------------------------------------------------------
# Module-level model cache (loaded once per process)
# ---------------------------------------------------------------------------

_model: Optional["ctranslate2.Translator"] = None
_device: str = "cpu"  # set at import time; overridden if CUDA available


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logger = logging.getLogger("vaani.translator")


# ---------------------------------------------------------------------------
# Constants for the official IndicTrans2 CT2 inference procedure
# ---------------------------------------------------------------------------

# The official IndicTrans2 distilled model supports these FLORES-200 codes.
# Source: https://huggingface.co/ai4bharat/indictrans2-indic-en-dist-200M
# and the official AI4Bharat/IndicTrans2 repository.

# Language tag format used by the model: "{src_lang} {tgt_lang}"
# e.g. "guj_Gujr eng_Latn" for Gujarati -> English

# Maximum input length for the model (tokens)
MAX_INPUT_LENGTH = 160

# Maximum decoding length (tokens)
MAX_DECODING_LENGTH = 256

# Beam size for translation
BEAM_SIZE = 5


# ---------------------------------------------------------------------------
# Model loading (lazy, once per process)
# ---------------------------------------------------------------------------


def _required_model_files(path: str) -> list[str]:
    """Return the files required for a usable local CTranslate2 checkpoint."""
    missing = []
    if not os.path.isdir(path):
        return ["directory_missing"]
    if not os.path.isfile(os.path.join(path, "config.json")):
        missing.append("config.json")
    if not any(name.endswith(".bin") for name in os.listdir(path)):
        missing.append("model.bin")
    vocab_dir = os.path.join(path, "vocab")
    if not os.path.isdir(vocab_dir):
        missing.append("vocab/")
    elif not os.path.isfile(os.path.join(vocab_dir, "model.SRC")):
        missing.append("vocab/model.SRC")
    elif not os.path.isfile(os.path.join(vocab_dir, "model.TGT")):
        missing.append("vocab/model.TGT")
    return missing


def get_model_status() -> dict:
    """Return the exact translation-model configuration status for startup checks."""
    candidates = [
        os.environ.get("VAANI_TRANSLATION_MODEL_PATH"),
        os.environ.get("INDICTRANS2_MODEL_PATH"),
        os.environ.get("CT2_MODEL_PATH"),
        os.path.join("backend", "models", "indictrans2_ct2"),
        os.path.join("models", "indictrans2_ct2"),
    ]

    seen = set()
    for candidate in candidates:
        if candidate and candidate.strip():
            norm = os.path.normpath(candidate.strip())
            if norm not in seen:
                seen.add(norm)

    result = {
        "configured": False,
        "ready": False,
        "path": None,
        "missing_files": [],
        "message": "",
    }

    for candidate in list(seen):
        missing = _required_model_files(candidate)
        if not missing:
            result["configured"] = True
            result["ready"] = _model is not None
            result["path"] = candidate
            result["message"] = "Model checkpoint detected and looks usable."
            return result

        result["path"] = candidate
        result["missing_files"] = missing
        result["message"] = (
            "Model path exists but is missing required CT2 files: "
            + ", ".join(missing)
        )

    result["message"] = (
        "IndicTrans2 CT2 model is not configured. Set one of these environment "
        "variables to a local CTranslate2 checkpoint directory: "
        "VAANI_TRANSLATION_MODEL_PATH, INDICTRANS2_MODEL_PATH, or CT2_MODEL_PATH"
    )
    return result


def _resolve_model_path() -> str:
    """Resolve the local CT2 checkpoint path from environment variables.

    The project must not silently try to fetch a remote model from a Hugging Face
    repo during request handling because that can stall a streaming response long
    enough to trigger idle timeouts (504s). The supported configuration is a
    local checkpoint directory prepared via the CTranslate2 converter.
    """
    candidates = [
        os.environ.get("VAANI_TRANSLATION_MODEL_PATH"),
        os.environ.get("INDICTRANS2_MODEL_PATH"),
        os.environ.get("CT2_MODEL_PATH"),
        os.path.join("backend", "models", "indictrans2_ct2"),
        os.path.join("models", "indictrans2_ct2"),
    ]

    for candidate in candidates:
        if candidate and candidate.strip():
            path = candidate.strip()
            if os.path.isdir(path):
                missing = _required_model_files(path)
                if not missing:
                    return path
                raise RuntimeError(
                    "IndicTrans2 CT2 model path exists but is incomplete. Missing: "
                    + ", ".join(missing)
                )

    raise RuntimeError(
        "IndicTrans2 CT2 model is not configured. Set one of these environment "
        "variables to a local CTranslate2 checkpoint directory: "
        "VAANI_TRANSLATION_MODEL_PATH, INDICTRANS2_MODEL_PATH, or CT2_MODEL_PATH"
    )


def _ensure_model_loaded() -> "ctranslate2.Translator":
    """Load the CTranslate2 model once per process.

    The model is cached at module scope so that every translation request
    reuses the same in-memory instance. Loading happens on first call only.
    A local checkpoint path is required; remote model downloads are not used by
    default because they can hang a request and trigger upstream idle timeouts.

    Returns:
        The initialized ctranslate2.Translator instance.

    Raises:
        RuntimeError: If the model cannot be loaded.
    """
    global _model, _device

    if _model is None:
        import torch

        if torch.cuda.is_available():
            _device = "cuda"
            logger.info("CUDA detected; loading IndicTrans2 CT2 model on GPU")
        else:
            _device = "cpu"
            logger.info(
                "No CUDA detected; loading IndicTrans2 CT2 model on CPU")

        model_path = _resolve_model_path()
        try:
            _model = ctranslate2.Translator(
                model_path, device=_device, compute_type="float32")
            logger.info(
                "IndicTrans2 CT2 model loaded from local checkpoint: %s", model_path)
        except Exception as exc:
            logger.warning(
                "Failed to load CT2 checkpoint from %s: %s", model_path, exc)
            raise RuntimeError(
                "Could not load IndicTrans2 CT2 model from the configured local checkpoint. "
                "Set VAANI_TRANSLATION_MODEL_PATH to a valid CTranslate2 directory."
            ) from exc

    return _model


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class TranslationError(RuntimeError):
    """Base exception for translation-layer errors.

    Wraps lower-level errors (model failure, preprocessing failure, etc.)
    into application-level errors that are safe to surface to the caller.
    """


class UnsupportedLanguageError(TranslationError):
    """Raised when the source language code is not supported by the model."""


class InvalidInputError(TranslationError):
    """Raised when the input text is empty, None, or malformed."""


class TranslationFailedError(TranslationError):
    """Raised when the translation inference step fails."""

    def __init__(self, message: str, original_error: Optional[BaseException] = None):
        super().__init__(message)
        self.original_error = original_error


# ---------------------------------------------------------------------------
# Core translation function
# ---------------------------------------------------------------------------


def translate(text: str, source_language: str) -> str:
    """Translate Indian-language text to English.

    Follows the official IndicTrans2 CTranslate2 inference procedure:
      1. Validate inputs (text exists, language supported).
      2. Map VaaniDoc source language code to the CT2 model's FLORES-200 code.
      3. Preprocess: add language-source/target tags to the input sentence.
      4. Tokenize and generate via ctranslate2.Translator.translate_batch.
      5. Postprocess: decode the generated tokens, strip special markers.
      6. Return the English translation text.

    The model is loaded once per process (see _ensure_model_loaded).

    Args:
        text: The Indian-language text to translate.  Must be non-empty.
        source_language: The VaaniDoc language code (e.g. "gu" for Gujarati,
            "hi" for Hindi).

    Returns:
        The English translation of the input text.

    Raises:
        InvalidInputError: If *text* is empty, None, or not a string.
        UnsupportedLanguageError: If *source_language* is not supported.
        TranslationFailedError: If the CTranslate2 inference step fails.
    """
    # ---- Validate text input ----
    if not isinstance(text, str):
        raise InvalidInputError(
            f"Translation text must be a string; got {type(text).__name__}"
        )
    text_stripped = text.strip()
    if not text_stripped:
        raise InvalidInputError("Translation text is empty or whitespace-only")

    # ---- Validate source language ----
    if not isinstance(source_language, str):
        raise InvalidInputError(
            f"Source language must be a string; got {type(source_language).__name__}"
        )
    src_code = source_language.strip().lower()
    if not is_supported_language(src_code):
        raise UnsupportedLanguageError(
            f"Unsupported source language code: '{src_code}'. "
            f"Supported codes: {sorted(get_supported_vaani_codes())}"
        )

    # ---- Map to CT2 model language code ----
    try:
        model_src_code = get_model_language_code(src_code)
    except KeyError as e:
        raise UnsupportedLanguageError(
            f"Could not resolve language code '{src_code}' for the model."
        ) from e

    # ---- Preprocess: add language tags per official CT2 inference ----
    # The official IndicTrans2 inference adds a language-tag prefix:
    #   "{src_lang} {tgt_lang} {sentence}"
    # where src_lang and tgt_lang are the FLORES-200 codes.
    # The target language is always English ("eng_Latn").
    tgt_code = "eng_Latn"
    tagged_input = f"{model_src_code} {tgt_code} {text_stripped}"

    # ---- Perform CTranslate2 inference ----
    try:
        model = _ensure_model_loaded()

        # CT2 expects a list of tokenized sentence lists.
        # The model's internal SentencePiece tokenizer handles tokenization
        # when given raw text strings; however, the official pipeline adds
        # the language tags *before* passing to the translator.
        # We pass the tagged sentence as a single-element batch.
        results = model.translate_batch(
            [[tagged_input]],
            max_batch_size=9216,
            batch_type="tokens",
            max_input_length=MAX_INPUT_LENGTH,
            max_decoding_length=MAX_DECODING_LENGTH,
            beam_size=BEAM_SIZE,
        )

        # ---- Postprocess: decode output ----
        # Each result in the batch has a `.hypotheses` list containing the
        # decoded sentence(s).  The hypotheses are already detokenized by
        # the model (space-restored, special tokens removed).
        # We take the top hypothesis (beam index 0).
        hypothesis = results[0].hypotheses[0]

        # The output from CT2 may still contain SentencePiece whitespace
        # markers (▁).  Replace them with regular spaces and strip.
        english_translation = hypothesis.replace("▁", " ").strip()

        # Further clean up: collapse multiple spaces that may have been
        # introduced by the replacement.
        english_translation = re.sub(r"\s+", " ", english_translation).strip()

        # Log the translation length for monitoring (no patient data).
        logger.info(
            f"Translated [{src_code}->{tgt_code}] "
            f"len_src={len(text_stripped)} len_eng={len(english_translation)}"
        )

        return english_translation

    except Exception as e:
        # CTranslate2-level error (out of memory, etc.)
        # Note: ctranslate2-specific exception types may vary by version;
        # we catch broadly and wrap in our application-level error.
        raise TranslationFailedError(
            "CTranslate2 inference failed", original_error=e
        ) from e


# ---------------------------------------------------------------------------
# Module init: do not eagerly load the model at import time.
# ---------------------------------------------------------------------------
# Loading the model during import can block startup or a request while the
# backend waits for a remote or slow checkpoint to become available. We keep the
# model lazy and only load it when translate() is called, so failures are local
# and explicit instead of presenting as an upstream idle timeout.
logger.info("IndicTrans2 CT2 translation engine initialized lazily")
