"""VaaniDoc IndicTrans2 CT2 translation engine."""

from pathlib import Path
from typing import Optional
import logging
import os
import re
import sys

from ai.translation.language_map import (
    get_model_language_code,
    get_supported_vaani_codes,
    is_supported_language,
)


logger = logging.getLogger("vaani.translator")

ROOT_DIR = Path(__file__).resolve().parents[2]

# IndicTrans2 repository location.
# Default:
# F:\VaaniDoc\IndicTrans2
INDICTrans2_ROOT = Path(
    os.environ.get(
        "INDICTRANS2_REPO_PATH",
        str(ROOT_DIR / "IndicTrans2"),
    )
)

# Make the cloned IndicTrans2 repository importable.
if INDICTrans2_ROOT.is_dir():
    indictrans2_root_str = str(INDICTrans2_ROOT)
    if indictrans2_root_str not in sys.path:
        sys.path.insert(0, indictrans2_root_str)

# Patch indicnlp modules to handle missing dependencies
# This is needed because the installed indicnlp package may be incomplete
_indicnlp_patched = False

def _patch_indicnlp():
    global _indicnlp_patched
    if _indicnlp_patched:
        return
    _indicnlp_patched = True
    
    # Ensure our local site-packages take precedence
    site_packages = Path(__file__).resolve().parents[3] / "venv" / "Lib" / "site-packages"
    if str(site_packages) not in sys.path:
        sys.path.insert(0, str(site_packages))
    
    # Patch normalize module
    normalize_path = Path(__file__).resolve().parents[3] / "venv" / "Lib" / "site-packages" / "indicnlp" / "normalize"
    if normalize_path.is_dir():
        # Remove cached references
        for mod_name in list(sys.modules.keys()):
            if 'indicnlp.normalize' in mod_name:
                del sys.modules[mod_name]
        
        # Import our patched version
        try:
            import importlib
            # Clear any cached normalize module
            if 'indicnlp.normalize' in sys.modules:
                del sys.modules['indicnlp.normalize']
            
            # Import from our location
            spec = importlib.util.spec_from_file_location(
                "indicnlp.normalize_patched",
                str(normalize_path / "__init__.py"),
                submodule_search_locations=[str(normalize_path)]
            )
            if spec:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                sys.modules['indicnlp.normalize'] = module
        except Exception:
            pass
    
    # Patch tokenize module
    tokenize_path = Path(__file__).resolve().parents[3] / "venv" / "Lib" / "site-packages" / "indicnlp" / "tokenize"
    if tokenize_path.is_dir():
        for mod_name in list(sys.modules.keys()):
            if 'indicnlp.tokenize' in mod_name:
                del sys.modules[mod_name]
        
        try:
            import importlib
            if 'indicnlp.tokenize' in sys.modules:
                del sys.modules['indicnlp.tokenize']
            
            spec = importlib.util.spec_from_file_location(
                "indicnlp.tokenize_patched",
                str(tokenize_path / "__init__.py"),
                submodule_search_locations=[str(tokenize_path)]
            )
            if spec:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                sys.modules['indicnlp.tokenize'] = module
        except Exception:
            pass

_patch_indicnlp()

# Import the IndicTrans2 model class
try:
    from inference.engine import Model as IndicTrans2Model
except ImportError:
    IndicTrans2Model = None

MAX_INPUT_LENGTH = 160
MAX_DECODING_LENGTH = 256
BEAM_SIZE = 5

_model: Optional["IndicTrans2Model"] = None
_device: str = "cpu"
_allow_cuda: bool = True


class TranslationError(RuntimeError):
    """Base exception for translation-layer errors."""


class UnsupportedLanguageError(TranslationError):
    """Raised when the source language code is not supported."""


class InvalidInputError(TranslationError):
    """Raised when the input text is empty or malformed."""


class TranslationFailedError(TranslationError):
    """Raised when the translation inference step fails."""

    def __init__(
        self,
        message: str,
        original_error: Optional[BaseException] = None,
    ):
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

    if not os.path.isfile(
        os.path.join(path, "config.json")
    ):
        missing.append("config.json")

    if not any(
        name.endswith(".bin")
        for name in os.listdir(path)
    ):
        missing.append("model.bin")

    vocab_dir = os.path.join(path, "vocab")

    if not os.path.isdir(vocab_dir):
        missing.append("vocab/")

    else:
        if not os.path.isfile(
            os.path.join(vocab_dir, "model.SRC")
        ):
            missing.append("vocab/model.SRC")

        if not os.path.isfile(
            os.path.join(vocab_dir, "model.TGT")
        ):
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
            result["message"] = (
                "Model checkpoint detected and looks usable."
            )
            return result

        if (
            first_incomplete is None
            and missing != ["directory_missing"]
        ):
            first_incomplete = {
                "path": candidate,
                "missing_files": missing,
                "message": (
                    "Model path exists but is missing "
                    "required CT2 files: "
                    + ", ".join(missing)
                ),
            }

    if first_incomplete:
        result.update(first_incomplete)
        return result

    result["message"] = (
        "IndicTrans2 CT2 model is not configured. "
        "Set one of these environment variables to a "
        "local CTranslate2 checkpoint directory: "
        "VAANI_TRANSLATION_MODEL_PATH, "
        "INDICTRANS2_MODEL_PATH, or CT2_MODEL_PATH"
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
                "IndicTrans2 CT2 model path exists but is "
                "incomplete. Missing: "
                + ", ".join(missing)
            )

    raise RuntimeError(
        "IndicTrans2 CT2 model is not configured. "
        "Set one of these environment variables to a "
        "local CTranslate2 checkpoint directory: "
        "VAANI_TRANSLATION_MODEL_PATH, "
        "INDICTRANS2_MODEL_PATH, or CT2_MODEL_PATH"
    )


def _ensure_model_loaded() -> "IndicTrans2Model":
    """
    Load the official IndicTrans2 inference engine once per process.

    The engine itself handles:
    - SentencePiece preprocessing
    - Indic normalization
    - language tags
    - CTranslate2 inference
    - postprocessing
    """

    global _model, _device, _allow_cuda

    if _model is not None:
        return _model

    if IndicTrans2Model is None:
        # Model class could not be imported; mark as unavailable
        raise RuntimeError(
            "IndicTrans2 model class not available. "
            "Using fallback translation mode."
        )

    import torch

    model_path = _resolve_model_path()

    load_attempts: list[str] = []

    if _allow_cuda and torch.cuda.is_available():
        load_attempts.append("cuda")

    load_attempts.append("cpu")

    last_error: Exception | None = None

    for device in load_attempts:

        try:

            logger.info(
                "Initializing IndicTrans2 inference engine "
                "from: %s using device=%s",
                model_path,
                device,
            )

            _model = IndicTrans2Model(
                model_path,
                device=device,
                model_type="ctranslate2",
            )

            _device = device

            logger.info(
                "IndicTrans2 inference engine loaded "
                "successfully from: %s (%s)",
                model_path,
                _device,
            )

            return _model

        except Exception as exc:

            last_error = exc

            logger.warning(
                "Failed to initialize IndicTrans2 "
                "on %s: %s",
                device,
                exc,
            )

    raise RuntimeError(
        "Could not load IndicTrans2 CT2 model from "
        "the configured local checkpoint."
    ) from last_error


def _reset_model(
    device: str = "cpu",
) -> None:
    """Reset the cached IndicTrans2 model."""

    global _model, _device, _allow_cuda

    _model = None
    _device = device
    _allow_cuda = device != "cpu"


def translate(
    text: str,
    source_language: str,
) -> str:
    """
    Translate Indian-language text to English using
    the real local IndicTrans2 CT2 model.
    """

    # --------------------------------------------------
    # Validate text
    # --------------------------------------------------

    if not isinstance(text, str):
        raise InvalidInputError(
            "Translation text must be a string; "
            f"got {type(text).__name__}"
        )

    text_stripped = text.strip()

    if not text_stripped:
        raise InvalidInputError(
            "Translation text is empty or whitespace-only"
        )

    # --------------------------------------------------
    # Validate source language
    # --------------------------------------------------

    if not isinstance(source_language, str):
        raise InvalidInputError(
            "Source language must be a string; "
            f"got {type(source_language).__name__}"
        )

    src_code = source_language.strip().lower()

    if not is_supported_language(src_code):
        raise UnsupportedLanguageError(
            f"Unsupported source language code: '{src_code}'. "
            f"Supported codes: "
            f"{sorted(get_supported_vaani_codes())}"
        )

    # --------------------------------------------------
    # Convert VaaniDoc language code to IndicTrans2 code
    # --------------------------------------------------

    try:
        model_src_code = get_model_language_code(src_code)

    except KeyError as exc:
        raise UnsupportedLanguageError(
            f"Could not resolve language code "
            f"'{src_code}' for the model."
        ) from exc

    # IndicTrans2 target language
    tgt_code = "eng_Latn"

    # --------------------------------------------------
    # Actual inference
    # --------------------------------------------------

    def _run_translation() -> str:

        model = _ensure_model_loaded()

        logger.info(
            "Running real IndicTrans2 translation "
            "[%s -> %s] on %s",
            model_src_code,
            tgt_code,
            _device,
        )

        # IMPORTANT:
        # Do NOT manually add language tags.
        # Do NOT manually tokenize with SentencePiece.
        #
        # IndicTrans2's official Model.batch_translate()
        # handles preprocessing, language tags,
        # SentencePiece and postprocessing.

        results = model.batch_translate(
            [text_stripped],
            model_src_code,
            tgt_code,
        )

        if not results:
            raise RuntimeError(
                "IndicTrans2 returned an empty result."
            )

        english_translation = results[0]

        if not isinstance(
            english_translation,
            str,
        ):
            english_translation = str(
                english_translation
            )

        english_translation = re.sub(
            r"\s+",
            " ",
            english_translation,
        ).strip()

        if not english_translation:
            raise RuntimeError(
                "IndicTrans2 returned an empty translation."
            )

        return english_translation

    # --------------------------------------------------
    # Try real model inference
    # --------------------------------------------------

    try:

        english_translation = _run_translation()

    except Exception as exc:

        message = str(exc)

        # If CUDA fails, retry using CPU.
        if (
            "cublas64_12.dll" in message
            or "cuda" in message.lower()
        ):

            logger.warning(
                "IndicTrans2 GPU inference failed; "
                "retrying on CPU."
            )

            _reset_model(
                device="cpu"
            )

            try:

                english_translation = (
                    _run_translation()
                )

            except Exception as retry_exc:

                raise TranslationFailedError(
                    "IndicTrans2 inference failed "
                    "on GPU and CPU.",
                    original_error=retry_exc,
                ) from retry_exc

        else:

            raise TranslationFailedError(
                "IndicTrans2 inference failed.",
                original_error=exc,
            ) from exc

    # --------------------------------------------------
    # Final cleanup
    # --------------------------------------------------

    english_translation = re.sub(
        r"\s+",
        " ",
        english_translation,
    ).strip()

    logger.info(
        "Translated [%s -> %s] "
        "len_src=%s len_eng=%s device=%s",
        src_code,
        tgt_code,
        len(text_stripped),
        len(english_translation),
        _device,
    )

    return english_translation


logger.info(
    "IndicTrans2 CT2 translation engine "
    "initialized lazily"
)
