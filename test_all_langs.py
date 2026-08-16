import sys
sys.path.insert(0, r'F:\VaaniDoc')

from ai.speech.languages import LANGUAGE_CODES
from ai.translation.language_map import is_supported_language, get_model_language_code, get_supported_vaani_codes
from ai.translation.translator import get_model_status, translate, TranslationFailedError, UnsupportedLanguageError

print('=' * 70)
print('VAANIDOC - ALL 22 LANGUAGES TRANSLATION TEST')
print('=' * 70)

# 1. List all supported languages
print('\n1. Supported Language Codes:')
codes = sorted(LANGUAGE_CODES)
for i, code in enumerate(codes, 1):
    print(f'   {i:2d}. {code}')

print(f'\nTotal: {len(codes)} languages')

# 2. Check model status
print('\n2. Translation Model Status:')
status = get_model_status()
print(f'   Configured: {status["configured"]}')
print(f'   Ready: {status["ready"]}')
print(f'   Message: {status["message"]}')

# 3. Test translation with each language
print('\n3. Translation Test (English source text: "Hello how are you"):')
print()

test_text = 'Hello how are you'
supported_codes = get_supported_vaani_codes()

results = []
for code in codes:
    try:
        # Check if language is supported by the model
        if not is_supported_language(code):
            results.append((code, 'NOT SUPPORTED'))
            print(f'   {code:3s}: NOT SUPPORTED by model')
            continue
        
        # Try translation
        try:
            result = translate(test_text, code)
            results.append((code, 'SUCCESS', result))
            print(f'   {code:3s}: SUCCESS -> {result}')
        except TranslationFailedError as e:
            # Model failed - this is expected with placeholder files
            results.append((code, 'FAILED', str(e)[:50]))
            print(f'   {code:3s}: FAILED (model inference error - fallback used)')
        except UnsupportedLanguageError as e:
            results.append((code, 'UNSUPPORTED'))
            print(f'   {code:3s}: UNSUPPORTED LANGUAGE CODE')
        except Exception as e:
            results.append((code, 'ERROR', type(e).__name__))
            print(f'   {code:3s}: ERROR -> {type(e).__name__}: {str(e)[:50]}')
            
    except Exception as e:
        results.append((code, 'TEST ERROR', type(e).__name__))
        print(f'   {code:3s}: TEST ERROR -> {type(e).__name__}')

print()
print('=' * 70)
print('SUMMARY')
print('=' * 70)

success_count = sum(1 for r in results if r[1] == 'SUCCESS')
failed_count = sum(1 for r in results if r[1] in ['FAILED', 'UNSUPPORTED'])
print(f'Total languages: {len(results)}')
print(f'Successful translations: {success_count}')
print(f'Failed/Unsupported: {failed_count}')
print()
if success_count == 0:
    print('NOTE: All translations are using fallback (simulated) because')
    print('the IndicTrans2 CT2 model placeholder files cannot be parsed')
    print('by SentencePiece. This is expected until the actual model is placed.')
print()
print('To enable live translation:')
print('1. Download AI4Bharat IndicTrans2 CT2 model (~1.5GB)')
print('2. Place files in: F:\\VaaniDoc\\backend\\models\\indictrans2_ct2\\')
print('3. Or set: VAANI_TRANSLATION_MODEL_PATH to the model directory')
print('=' * 70)