"""
Smoke test for the IndicTrans2 translation module (backend/translation.py).

Usage (run from the backend/ directory so `translation` importable):

    python test_translation.py
    python test_translation.py "મને બે દિવસથી તાવ છે." gu

This loads the model ONCE (downloaded to the HF cache on first run) and
verifies the Indic-translation pipeline: preprocess -> generate -> decode.
The minimal internal sanity checks above the function never touch torch or
the model, so they run on any machine without a GPU.
"""

import sys

# Pure-Python sanity checks that do NOT require the model, torch, or a GPU.
from config import SHORT_CODE_TO_FLORES, SUPPORTED_SOURCE_LANGS

assert len(SHORT_CODE_TO_FLORES) == 22
assert all(v in SUPPORTED_SOURCE_LANGS for v in SHORT_CODE_TO_FLORES.values())
assert SHORT_CODE_TO_FLORES["gu"] == "guj_Gujr"
assert SHORT_CODE_TO_FLORES["hi"] == "hin_Deva"
print(f"Config checks passed for {len(SHORT_CODE_TO_FLORES)} languages")

from translation import translate


def main():
    text = sys.argv[1] if len(sys.argv) > 1 else "મને બે દિવસથી તાવ છે."
    language = sys.argv[2] if len(sys.argv) > 2 else "gu"

    result = translate(text, language)
    print(f"{language}: {text}")
    print(f"english : {result}")


if __name__ == "__main__":
    main()