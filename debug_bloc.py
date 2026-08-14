import sys
sys.path.insert(0, r'F:\VaaniDoc')
from backend.ai.translation.translation_safety import _extract_body_location

# Test with Gujarati body location words
tests = [
    'મને છાતીમાં દુખાવો છે.',  # Original Gujarati with chest
    'મને પેટમાં દુખાવો છે.',  # Gujarati with stomach
]

for t in tests:
    result = _extract_body_location(t)
    print('  %s -> %s' % (t, result))