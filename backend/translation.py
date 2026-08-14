"""
IndicTrans2 translation layer: Indian-language text -> English.

Responsibilities:
  * Load the official AI4Bharat IndicTrans2 model exactly ONCE per process
    (module-level cache), so API requests reuse the loaded model instead of
    re-downloading/re-loading it every time.
  * Offer a small `translate(text, language)` function used by the API layer.

This file contains NO FastAPI/route code on purpose; it only exposes the model
and the pure translation function so the API and tests stay clean.

# Transitioning from IndicTransToolkit to official CTranslate2 inference path.
# The old IndicProcessor-based pipeline will be replaced with the CT2-based
# implementation (see backend/README.md for the new architecture).
"""

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

try:
    from .config import (
        ATTENTION_IMPLEMENTATION,
        DEVICE,
        MAX_LENGTH,
        MODEL_NAME,
        NUM_BEAMS,
        NUM_RETURN_SEQUENCES,
        SHORT_CODE_TO_FLORES,
        SUPPORTED_SOURCE_LANGS,
        TARGET_LANG,
        TORCH_DTYPE,
    )
except ImportError:
    # Mirrors the fallback used in ai/speech/asr.py so this module also works
    # as a standalone script (e.g. python test_translation.py run from backend/).
    from config import (
        ATTENTION_IMPLEMENTATION,
        DEVICE,
        MAX_LENGTH,
        MODEL_NAME,
        NUM_BEAMS,
        NUM_RETURN_SEQUENCES,
        SHORT_CODE_TO_FLORES,
        SUPPORTED_SOURCE_LANGS,
        TARGET_LANG,
        TORCH_DTYPE,
    )

# ---------------------------------------------------------------------------
# Module-level model cache
# ---------------------------------------------------------------------------
# The tokenizer, model and processor are loaded lazily and kept in module
# globals. Loading is deferred until the first `translate()` call so that
# importing this module (and therefore running unit tests) does NOT require a
# GPU or trigger a multi-hundred-MB model download.
_model = None
_tokenizer = None
_processor = None
_device = None


def _get_models():
    """Load the identity en/model, tokenizer and processor once per process.

    Why loaded once: IndicTrans2 is a ~200M-parameter seq2seq transformer.
    Every `from_pretrained` call re-downloads from the Hub cache and re-allocates
    the weights, which takes tens of seconds and large amounts of RAM on every
    request. Caching the instances at module scope means the first request pays
    the load cost and every subsequent translation reuses them in memory.
    """
    global _model, _tokenizer, _processor, _device

    if _model is None:
        # TODO: Replace with CTranslate2 Translator initialization
        # when the new translation path is implemented.
        # Old: _processor = IndicProcessor(inference=True)
        pass
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        _model = AutoModelForSeq2SeqLM.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True,
            torch_dtype=TORCH_DTYPE,
            attn_implementation=ATTENTION_IMPLEMENTATION,
            low_cpu_mem_usage=True,
        ).to(DEVICE)
        _model.eval()
        _device = DEVICE

    return _model, _tokenizer, _processor, _device


def _resolve_flores_code(language):
    """Map a short language code (e.g. "gu") to its FLORES-200 code.

    Raises the same style of error as ai/speech/asr.py for unknown languages.
    """
    code = language.strip().lower()
    if code not in SHORT_CODE_TO_FLORES:
        raise ValueError(f"Unsupported language code: {language}")
    flores = SHORT_CODE_TO_FLORES[code]
    if flores not in SUPPORTED_SOURCE_LANGS:
        raise ValueError(f"FLORES code not supported by model: {flores}")
    return flores


def translate(text, language):
    """Translate Indian-language `text` to English using IndicTrans2.

    `language` is the short code used by the ASR layer and frontend (e.g. "gu").
    Follows the official model card / example.py inference loop exactly:
    preprocess -> tokenize -> model.generate -> decode -> postprocess.
    """
    src_lang = _resolve_flores_code(language)
    model, tokenizer, processor, device = _get_models()

    # Preprocess the sentence (adds bias/tags, handles entity mapping and
    # optional script normalization) - transitioning to CT2 pipeline
    batch = processor.preprocess_batch([text], src_lang=src_lang, tgt_lang=TARGET_LANG)

    # Tokenize the batch and generate input encodings.
    inputs = tokenizer(
        batch,
        truncation=True,
        padding="longest",
        return_tensors="pt",
        return_attention_mask=True,
    ).to(device)

    # Generate translations (official parameters from the model card).
    with torch.no_grad():
        generated_tokens = model.generate(
            **inputs,
            use_cache=True,
            min_length=0,
            max_length=MAX_LENGTH,
            num_beams=NUM_BEAMS,
            num_return_sequences=NUM_RETURN_SEQUENCES,
        )

    # Decode the generated tokens into text.
    decoded = tokenizer.batch_decode(
        generated_tokens,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True,
    )

    # Postprocess the translations, including entity replacement.
    translations = processor.postprocess_batch(decoded, lang=TARGET_LANG)

    return translations[0].strip() if translations else ""