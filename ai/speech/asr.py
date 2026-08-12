import torch
from transformers import AutoModel

try:
    from .audio import load_audio
except ImportError:
    from audio import load_audio


MODEL_ID = "ai4bharat/indic-conformer-600m-multilingual"
LANGUAGE_CODES = {
    "as", "bn", "brx", "doi", "gu", "hi", "kn", "ks", "kok", "mai", "ml",
    "mni", "mr", "ne", "or", "pa", "sa", "sat", "sd", "ta", "te", "ur",
}

_model = None
_device = None


def _get_device():
    return "cuda" if torch.cuda.is_available() else "cpu"


def _get_model():
    """Load IndicConformer once per Python process."""
    global _model, _device

    device = _get_device()
    if _model is None:
        _model = AutoModel.from_pretrained(MODEL_ID, trust_remote_code=True).to(device)
        _model.eval()
        _device = device

    return _model, _device


def transcribe(audio_path, language):
    """Return recognized text for one audio file."""
    language = language.strip().lower()
    if language not in LANGUAGE_CODES:
        raise ValueError(f"Unsupported language code: {language}")

    wav = load_audio(audio_path)
    model, device = _get_model()
    wav = wav.to(device)

    with torch.inference_mode():
        text = model(wav, language, "ctc")

    return text.strip() if isinstance(text, str) else str(text).strip()
