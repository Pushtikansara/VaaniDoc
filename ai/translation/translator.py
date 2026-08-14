"""VaaniDoc IndicTrans2 CT2 translation engine."""

from pathlib import Path
from typing import Optional
import logging
import os
import re

import ctranslate2
import sentencepiece as spm

from ai.translation.language_map import (
    get_model_language_code,
    get_supported_vaani_codes,
    is_supported_language,
)


logger = logging.getLogger("vaani.translator")

ROOT_DIR = Path(__file__).resolve().parents[2]
MAX_INPUT_LENGTH = 160
MAX_DECODING_LENGTH = 256
BEAM_SIZE = 5

_model: Optional["ctranslate2.Translator"] = None
_src_spm: Optional["spm.SentencePieceProcessor"] = None
_tgt_spm: Optional["spm.SentencePieceProcessor"] = None
_device: str = "cpu"
_compute_type: str = "int8"
_allow_cuda: bool = True


class TranslationError(RuntimeError):
    """Base exception for translation-layer errors."""


class UnsupportedLanguageError(TranslationError):
    """Raised when the source language code is not supported."""


class InvalidInputError(TranslationError):
    """Raised when the input text is empty or malformed."""


class TranslationFailedError(TranslationError):
    """Raised when the translation inference step fails."""

    def __init__(self, message: str, original_error: Optional[BaseException] = None):
        super().__init__(message)
        self.original_error = original_error


def _candidate_model_paths() -> list[str]:
    """Return model search paths in priority order."""
    candidates = [
        os.environ.get("VAANI_TRANSLATION_MODEL_PATH"),
        os.environ.get("INDICTRANS2_MODEL_PATH"),
        os.environ.get("CT2_MODEL_PATH"),
        str(ROOT_DIR / "backend" / "models" / "indictrans2_ct2"),
        str(ROOT_DIR / "models" / "indictrans2_ct2"),
    ]

    ordered_candidates: list[str] = []
    seen = set()
    for candidate in candidates:
        if candidate and candidate.strip():
            norm = os.path.normpath(candidate.strip())
            if norm not in seen:
                seen.add(norm)
                ordered_candidates.append(norm)
    return ordered_candidates


def _required_model_files(path: str) -> list[str]:
    """Return missing files for a local CT2 checkpoint."""
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
    else:
        if not os.path.isfile(os.path.join(vocab_dir, "model.SRC")):
            missing.append("vocab/model.SRC")
        if not os.path.isfile(os.path.join(vocab_dir, "model.TGT")):
            missing.append("vocab/model.TGT")

    return missing


def get_model_status() -> dict:
    """Return translation-model configuration status for startup checks."""
    result = {
        "configured": False,
        "ready": False,
        "path": None,
        "missing_files": [],
        "message": "",
    }

    first_incomplete: dict | None = None
    for candidate in _candidate_model_paths():
        missing = _required_model_files(candidate)
        if not missing:
            result["configured"] = True
            result["ready"] = _model is not None
            result["path"] = candidate
            result["message"] = "Model checkpoint detected and looks usable."
            return result

        if first_incomplete is None and missing != ["directory_missing"]:
            first_incomplete = {
                "path": candidate,
                "missing_files": missing,
                "message": "Model path exists but is missing required CT2 files: "
                + ", ".join(missing),
            }

    if first_incomplete:
        result.update(first_incomplete)
        return result

    result["message"] = (
        "IndicTrans2 CT2 model is not configured. Set one of these environment "
        "variables to a local CTranslate2 checkpoint directory: "
        "VAANI_TRANSLATION_MODEL_PATH, INDICTRANS2_MODEL_PATH, or CT2_MODEL_PATH"
    )
    return result


def _resolve_model_path() -> str:
    """Resolve the first usable local CT2 checkpoint path."""
    for candidate in _candidate_model_paths():
        if os.path.isdir(candidate):
            missing = _required_model_files(candidate)
            if not missing:
                return candidate
            raise RuntimeError(
                "IndicTrans2 CT2 model path exists but is incomplete. Missing: "
                + ", ".join(missing)
            )

    raise RuntimeError(
        "IndicTrans2 CT2 model is not configured. Set one of these environment "
        "variables to a local CTranslate2 checkpoint directory: "
        "VAANI_TRANSLATION_MODEL_PATH, INDICTRANS2_MODEL_PATH, or CT2_MODEL_PATH"
    )


def _load_sentencepiece_models(
    model_path: str,
) -> tuple["spm.SentencePieceProcessor", "spm.SentencePieceProcessor"]:
    """Load source and target SentencePiece models for the checkpoint."""
    vocab_dir = Path(model_path) / "vocab"
    src_spm = spm.SentencePieceProcessor(model_file=str(vocab_dir / "model.SRC"))
    tgt_spm = spm.SentencePieceProcessor(model_file=str(vocab_dir / "model.TGT"))
    return src_spm, tgt_spm


def _ensure_model_loaded() -> "ctranslate2.Translator":
    """Load the CT2 model and tokenizers once per process."""
    global _model, _src_spm, _tgt_spm, _device, _compute_type, _allow_cuda

    if _model is not None:
        return _model

    import torch

    model_path = _resolve_model_path()
    _src_spm, _tgt_spm = _load_sentencepiece_models(model_path)

    load_attempts: list[tuple[str, str]] = []
    if _allow_cuda and torch.cuda.is_available():
        load_attempts.append(("cuda", "int8_float16"))
    load_attempts.append(("cpu", "int8"))

    last_error: Exception | None = None
    for device, compute_type in load_attempts:
        try:
            _model = ctranslate2.Translator(
                model_path,
                device=device,
                compute_type=compute_type,
                inter_threads=1,
                intra_threads=1,
            )
            _device = device
            _compute_type = compute_type
            logger.info(
                "IndicTrans2 CT2 model loaded from local checkpoint: %s (%s, %s)",
                model_path,
                _device,
                _compute_type,
            )
            return _model
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Failed to initialize CT2 model on %s (%s): %s",
                device,
                compute_type,
                exc,
            )

    raise RuntimeError(
        "Could not load IndicTrans2 CT2 model from the configured local checkpoint. "
        "Set VAANI_TRANSLATION_MODEL_PATH to a valid CTranslate2 directory."
    ) from last_error


def _reset_model(device: str = "cpu", compute_type: str = "int8") -> None:
    """Reset the cached translator so the next call can reinitialize it."""
    global _model, _device, _compute_type, _allow_cuda
    _model = None
    _device = device
    _compute_type = compute_type
    _allow_cuda = device != "cpu"


def translate(text: str, source_language: str) -> str:
    """Translate Indian-language text to English."""
    if not isinstance(text, str):
        raise InvalidInputError(
            f"Translation text must be a string; got {type(text).__name__}"
        )

    text_stripped = text.strip()
    if not text_stripped:
        raise InvalidInputError("Translation text is empty or whitespace-only")

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

    try:
        model_src_code = get_model_language_code(src_code)
    except KeyError as exc:
        raise UnsupportedLanguageError(
            f"Could not resolve language code '{src_code}' for the model."
        ) from exc

    tgt_code = "eng_Latn"
    tagged_input = f"{model_src_code} {tgt_code} {text_stripped}"

    def _run_translation() -> str:
        model = _ensure_model_loaded()
        if _src_spm is None or _tgt_spm is None:
            raise RuntimeError("SentencePiece models were not initialized")

        tokenized_input = _src_spm.encode(tagged_input, out_type=str)
        results = model.translate_batch(
            [tokenized_input],
            max_batch_size=9216,
            batch_type="tokens",
            max_input_length=MAX_INPUT_LENGTH,
            max_decoding_length=MAX_DECODING_LENGTH,
            beam_size=BEAM_SIZE,
        )

        hypothesis = results[0].hypotheses[0]
        output_tokens = hypothesis if isinstance(hypothesis, list) else hypothesis.split()
        return _tgt_spm.decode(output_tokens).strip()

    try:
        english_translation = _run_translation()
    except Exception as exc:
        message = str(exc)
        if "cublas64_12.dll" in message or "cuda" in message.lower():
            logger.warning("CT2 GPU inference failed; retrying on CPU int8")
            _reset_model(device="cpu", compute_type="int8")
            try:
                english_translation = _run_translation()
            except Exception as retry_exc:
                raise TranslationFailedError(
                    "CTranslate2 inference failed", original_error=retry_exc
                ) from retry_exc
        else:
            raise TranslationFailedError(
                "CTranslate2 inference failed", original_error=exc
            ) from exc

    english_translation = re.sub(r"\s+", " ", english_translation).strip()
    logger.info(
        "Translated [%s->%s] len_src=%s len_eng=%s",
        src_code,
        tgt_code,
        len(text_stripped),
        len(english_translation),
    )
    return english_translation


logger.info("IndicTrans2 CT2 translation engine initialized lazily")
