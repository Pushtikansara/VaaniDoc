import sys
sys.path.insert(0, r'F:\VaaniDoc')
from backend.ai.translation.translator import translate
from backend.ai.translation.translation_safety import verify_translation

# Test Gujarati translation
english = translate('મને બે દિવસથી તાવ છે', 'gu')
print(f'Gujarati -> English: {english}')

# Test verification
result = verify_translation('મને બે દિવસથી તાવ છે', 'gu', english)
print(f'Verification: status={result["status"]}, warnings={result["warnings"]}')

# Test Hindi translation
english_hindi = translate('मुझे दो दिन से बुखार है', 'hi')
print(f'Hindi -> English: {english_hindi}')

result_hindi = verify_translation('मुझे दो दिन से बुखार है', 'hi', english_hindi)
print(f'Hindi verification: status={result_hindi["status"]}, warnings={result_hindi["warnings"]}')