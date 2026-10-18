import logging
import os
from pathlib import Path
from typing import Optional
import torch

try:
    from .audio import load_audio
except ImportError:
    from audio import load_audio

from .languages import LANGUAGE_CODES

logger = logging.getLogger("vaani.speech")

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_ID = "ai4bharat/indic-conformer-600m-multilingual"

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SpeechError(RuntimeError):
    """Base exception for speech recognition errors."""


class SpeechModelAuthError(SpeechError):
    """Raised when Hugging Face returns 401 or repository access is gated."""


class SpeechModelUnavailableError(SpeechError):
    """Raised when the ASR model checkpoint or repository cannot be loaded."""


# ---------------------------------------------------------------------------
# Global in-process model cache
# ---------------------------------------------------------------------------
_model = None
_device = None


def _get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def _get_hf_token() -> Optional[str]:
    """Retrieve Hugging Face token from environment if configured."""
    return (
        os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        or os.environ.get("HUGGINGFACE_TOKEN")
    )


def _candidate_local_paths() -> list[str]:
    """Return local ASR checkpoint candidate paths."""
    candidates = [
        os.environ.get("VAANI_ASR_MODEL_PATH"),
        os.environ.get("INDIC_CONFORMER_MODEL_PATH"),
        os.environ.get("ASR_MODEL_PATH"),
        str(ROOT_DIR / "backend" / "models" / "indic_conformer"),
        str(ROOT_DIR / "models" / "indic_conformer"),
    ]
    valid = []
    seen = set()
    for c in candidates:
        if c and c.strip():
            p = os.path.normpath(c.strip())
            if p not in seen and os.path.isdir(p):
                seen.add(p)
                valid.append(p)
    return valid


def is_fallback_enabled() -> bool:
    """Check if simulated speech fallback is enabled for offline/demo environments."""
    val = os.environ.get("VAANI_ENABLE_SPEECH_FALLBACK", "").strip().lower()
    return val in {"1", "true", "yes", "on", "demo"}


def get_speech_model_status() -> dict:
    """Return diagnostic status of the IndicConformer ASR model."""
    if _model is not None:
        return {
            "configured": True,
            "ready": True,
            "source": "loaded",
            "message": "IndicConformer ASR model is loaded and ready in memory.",
        }

    local_paths = _candidate_local_paths()
    if local_paths:
        return {
            "configured": True,
            "ready": False,
            "source": "local",
            "path": local_paths[0],
            "message": f"Local ASR checkpoint detected at {local_paths[0]}.",
        }

    hf_token = _get_hf_token()
    if hf_token:
        return {
            "configured": True,
            "ready": False,
            "source": "huggingface",
            "model_id": os.environ.get("VAANI_ASR_MODEL_ID", DEFAULT_MODEL_ID),
            "message": "Hugging Face token configured. Model will load from Hugging Face Hub upon first request.",
        }

    if is_fallback_enabled():
        return {
            "configured": True,
            "ready": True,
            "source": "fallback",
            "message": "Speech fallback mode enabled (VAANI_ENABLE_SPEECH_FALLBACK=true).",
        }

    return {
        "configured": False,
        "ready": False,
        "source": "unconfigured",
        "message": (
            "IndicConformer ASR model is not configured. Hugging Face repository "
            f"'{DEFAULT_MODEL_ID}' is gated (HTTP 401). "
            "To enable live speech recognition: 1) Visit https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual "
            "and accept access. 2) Set environment variable HF_TOKEN with your Hugging Face User Access Token. "
            "Alternatively, place model files locally and set VAANI_ASR_MODEL_PATH, "
            "or set VAANI_ENABLE_SPEECH_FALLBACK=true for offline testing."
        ),
    }


FALLBACK_TRANSCRIPTS = {
    "gu": "મને બે દિવસથી ખૂબ તાવ અને માથાનો દુખાવો છે",
    "hi": "मुझे दो दिन से तेज बुखार और सिरदर्द है",
    "mr": "मला दोन दिवसांपासून ताप आणि डोकेदुखी आहे",
    "ta": "எனக்கு இரண்டு நாட்களாக கடுமையான காய்ச்சல் மற்றும் தலைவலி உள்ளது",
    "te": "నాకు రెండు రోజులుగా తీవ్రమైన జ్వరం మరియు తలనొప్పి ఉంది",
    "kn": "ನನಗೆ ಎರಡು ದಿನಗಳಿಂದ ತೀವ್ರ ಜ್ವರ ಮತ್ತು ತಲೆನೋವು ಇದೆ",
    "bn": "আমার দুই দিন ধরে তীব্র জ্বর এবং মাথাব্যথা আছে",
    "pa": "ਮੈਨੂੰ ਦੋ ਦਿਨਾਂ ਤੋਂ ਬਹੁਤ ਤੇਜ਼ ਬੁਖਾਰ ਅਤੇ ਸਿਰਦਰਦ ਹੈ",
    "ml": "എനിക്ക് രണ്ടു ദിവസമായി കഠിനമായ പനിയും തലവേദനയും ഉണ്ട്",
}


def _get_fallback_transcript(language: str) -> str:
    return FALLBACK_TRANSCRIPTS.get(
        language,
        "મને બે દિવસથી ખૂબ તાવ અને માથાનો દુખાવો છે",
    )


def _get_model():
    """Load IndicConformer once per Python process."""
    global _model, _device

    if _model is not None:
        return _model, _device

    from transformers import AutoModel

    device = _get_device()
    local_paths = _candidate_local_paths()
    model_source = local_paths[0] if local_paths else os.environ.get("VAANI_ASR_MODEL_ID", DEFAULT_MODEL_ID)
    token = _get_hf_token() if not local_paths else None

    logger.info("Loading IndicConformer model from: %s (device: %s)...", model_source, device)
    try:
        kwargs = {"trust_remote_code": True}
        if token:
            kwargs["token"] = token
        loaded = AutoModel.from_pretrained(model_source, **kwargs).to(device)
        loaded.eval()
        _model = loaded
        _device = device
        return _model, _device
    except OSError as exc:
        err_str = str(exc)
        if "401" in err_str or "gated" in err_str.lower() or "unauthorized" in err_str.lower():
            raise SpeechModelAuthError(
                "IndicConformer ASR model on Hugging Face is gated and returned 401 Unauthorized. "
                "To fix: 1) Visit https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual and accept repo access. "
                "2) Set the HF_TOKEN environment variable with your Hugging Face User Access Token (from huggingface.co/settings/tokens). "
                "Or set VAANI_ASR_MODEL_PATH to a local model directory, or set VAANI_ENABLE_SPEECH_FALLBACK=true for offline testing."
            ) from exc
        raise SpeechModelUnavailableError(
            f"Failed to load ASR model from '{model_source}': {exc}"
        ) from exc
    except Exception as exc:
        raise SpeechModelUnavailableError(
            f"Unexpected error initializing ASR model: {exc}"
        ) from exc


def transcribe(audio_path, language: str) -> str:
    """Return recognized text for one audio file."""
    language = language.strip().lower()
    if language not in LANGUAGE_CODES:
        raise ValueError(f"Unsupported language code: {language}")

    # Check fallback mode first if model is in fallback mode or unconfigured
    if is_fallback_enabled() and not _candidate_local_paths() and not _get_hf_token():
        return _get_fallback_transcript(language)

    try:
        model, device = _get_model()
    except (SpeechModelAuthError, SpeechModelUnavailableError) as exc:
        if is_fallback_enabled():
            logger.warning("ASR model unavailable (%s); using fallback mode.", exc)
            return _get_fallback_transcript(language)
        raise

    wav = load_audio(audio_path)
    wav = wav.to(device)

    with torch.inference_mode():
        text = model(wav, language, "ctc")

    return text.strip() if isinstance(text, str) else str(text).strip()
