"""
Centralized configuration for the VaaniDoc IndicTrans2 translation module.

All model identifiers, device selection, language-code maps, and inference
parameters live here so they are never duplicated or scattered across the
project. Values are verified against the official AI4Bharat sources:

  * Model / checkpoint:   https://huggingface.co/ai4bharat/indictrans2-indic-en-dist-200M
  * Repo (HF interface):  https://github.com/AI4Bharat/IndicTrans2 (huggingface_interface/)
  * Tokenizer/processor:  Official CTranslate2 inference path (no toolkit required)
"""

import torch

# ---------------------------------------------------------------------------
# Model selection (Indic -> English)
# ---------------------------------------------------------------------------
# Official AI4Bharat Indicator-En distilled model, published on the Hugging
# Face Hub. It is one of the four official IndicTrans2 checkpoints listed in
# the official `huggingface_interface/README.md` model table:
#
#   Distilled Indic-En -> ai4bharat/indictrans2-indic-en-dist-200M
#
# It is chosen over the full `ai4bharat/indictrans2-indic-en-1B` for two
# reasons, both grounded in the VaaniDoc README:
#   * The README explicitly states a distilled Indic--English model is
#     intended for VaaniDoc.
#   * ~200M parameters (vs 1B) means far lower RAM/VRAM and faster inference,
#     aligned with VaaniDoc's low-bandwidth / constrained-hardware target for
#     rural clinics and CPU development machines.
# The distilled model still supports all 22 scheduled Indian languages as
# sources (25 language-script combinations). Both are loaded with the
# official Hugging Face interface (AutoTokenizer + AutoModelForSeq2SeqLM with
# trust_remote_code=True), described in the official model card.
MODEL_NAME = "ai4bharat/indictrans2-indic-en-dist-200M"

# Target language for this module is always English (Indic->English stage).
# FLORES-200 style code used by IndicTrans2 / CTranslate2 inference.
TARGET_LANG = "eng_Latn"

# Every FLORES-200 source-language code the Indic-En model officially supports
# (from the official model card `language_details`; covers the 22 scheduled
# Indian languages, including the multi-script Kas/mni/snd variants).
SUPPORTED_SOURCE_LANGS = (
    "asm_Beng", "ben_Beng", "bho_Deva", "brx_Deva", "doi_Deva", "gom_Deva",
    "guj_Gujr", "hin_Deva", "kan_Knda", "kas_Arab", "kas_Deva", "mai_Deva",
    "mal_Mlym", "mar_Deva", "mni_Beng", "mni_Mtei", "npi_Deva", "ory_Orya",
    "pan_Guru", "san_Deva", "sat_Olck", "snd_Arab", "snd_Deva", "tam_Taml",
    "tel_Telu", "urd_Arab",
)
assert "asm_Beng" in SUPPORTED_SOURCE_LANGS, "Assamese code must be asm_Beng"

# ---------------------------------------------------------------------------
# Language-code bridge
# ---------------------------------------------------------------------------
# IndicConformer (`ai/speech/asr.py`) and the frontend use 2-letter / ISO-style
# short codes (e.g. "gu"), while IndicTrans2 requires FLORES-200 codes
# (e.g. "guj_Gujr"). This map bridges the two without inventing any codes:
# every FLORES value below appears both in SUPPORTED_SOURCE_LANGS and in the
# official AI4Bharat model card / example.py `flores_codes` mapping.
# For the multi-script languages (Kashmiri, Manipuri, Sindhi) the Devanagari/
# Meitei default used by the Indic pipeline is chosen.
SHORT_CODE_TO_FLORES = {
    "as": "asm_Beng",   # Assamese
    "bn": "ben_Beng",   # Bengali
    "brx": "brx_Deva",  # Bodo
    "doi": "doi_Deva",  # Dogri
    "gu": "guj_Gujr",   # Gujarati
    "hi": "hin_Deva",   # Hindi
    "kn": "kan_Knda",   # Kannada
    "ks": "kas_Deva",   # Kashmiri (Devanagari)
    "kok": "gom_Deva",  # Konkani
    "mai": "mai_Deva",  # Maithili
    "ml": "mal_Mlym",   # Malayalam
    "mni": "mni_Mtei",  # Manipuri (Meitei)
    "mr": "mar_Deva",   # Marathi
    "ne": "npi_Deva",   # Nepali
    "or": "ory_Orya",   # Odia
    "pa": "pan_Guru",   # Punjabi
    "sa": "san_Deva",   # Sanskrit
    "sat": "sat_Olck",  # Santali
    "sd": "snd_Deva",   # Sindhi (Devanagari)
    "ta": "tam_Taml",   # Tamil
    "te": "tel_Telu",   # Telugu
    "ur": "urd_Arab",   # Urdu
}
assert len(SHORT_CODE_TO_FLORES) == 22, "Expected exactly 22 short language codes"

# ---------------------------------------------------------------------------
# Device selection
# ---------------------------------------------------------------------------
# Automatically use CUDA (GPU) when one is available, otherwise fall back to
# CPU. Evaluated once at import time; the model is placed on this device only
# when it is actually loaded. This lets the same code run on GPU in production
# and on CPU during development without requiring a GPU for unit tests.
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Weight dtype used when loading the model.
#   * On GPU: float16 gives the big speed/memory win intended by the official
#     model card (`torch_dtype=torch.float16`).
#   * On CPU: float16 raises `RuntimeError: "LayerNormKernelImpl" not
#     implemented for 'Half'` (documented in official issue #28), so float32
#     is used to keep CPU development working.
TORCH_DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

# Attention backend. Official example.py defaults to "eager"; flash_attention_2
# requires a CUDA GPU plus the optional `flash-attn` wheel, which we do not
# want to force for the MVP. "eager" runs on both CPU and GPU.
ATTENTION_IMPLEMENTATION = "eager"

# ---------------------------------------------------------------------------
# Generation / inference parameters
# ---------------------------------------------------------------------------
# Taken from the official IndicTrans2 example (`huggingface_interface/example.py`)
# and the Hugging Face model card usage snippet.
MAX_LENGTH = 256          # max tokens to generate
NUM_BEAMS = 5
NUM_RETURN_SEQUENCES = 1