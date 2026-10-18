import sys
sys.path.insert(0, r'F:\VaaniDoc')

from ai.translation.translator import translate, get_model_status, TranslationFailedError
from ai.translation.translation_safety import verify_translation
from backend.translation_api import _build_translation_fallback

# Check model status
status = get_model_status()
print("Model status:", status)

# Try translation - this should fail and use fallback
try:
    result = translate("હેલો કેમ છો", "gu")
    print("Translation result:", result)
except TranslationFailedError as e:
    print("Translation failed (expected):", str(e)[:100])
except Exception as e:
    print("Other error:", type(e).__name__, str(e)[:100])

# Test fallback
fallback = _build_translation_fallback("Hello how are you")
print("Fallback result:", fallback)

# Test verification with fallback text
verification = verify_translation("Hello how are you", "en", fallback)
print("Verification result:", verification)