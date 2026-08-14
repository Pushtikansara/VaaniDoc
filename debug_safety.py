import sys
import re
sys.path.insert(0, r'F:\VaaniDoc')
from backend.ai.translation.translation_safety import _extract_duration, _extract_negation, _extract_body_location

# Debug duration
print("=== Duration debug ===")
d1 = _extract_duration('મને ત્રણ દિવસથી તાવ છે.')
d2 = _extract_duration('I have had a fever for three days.')
d3 = _extract_duration('I have had a fever for two days.')
print("Original duration:", repr(d1))
print("Trans '3 days':", repr(d2))
print("Trans '2 days':", repr(d3))

# Debug negation
print("\=== Negation debug ===")
n1 = _extract_negation('મને તાવ ન'hi')  # This won't work, use below
# Let me just use the function directly with known inputs
# Actually the Gujarati has an apostrophe-like character, let me check
test_text = "મને તાવ ન'hi"  # This has a mix
print("Test text:", repr(test_text))

# Let me just print what the function does with simple English
n2 = _extract_negation('I have no fever.')
n3 = _extract_negation('I have a fever.')
print("Trans 'no fever':", n2)
print("Trans 'have fever':", n3)

# Debug body location
print("\=== Body location debug ===")
b1 = _extract_body_location('મને છાતીમાં દુખાવો છે.')
b2 = _extract_body_location('I have chest pain.')
b3 = _extract_body_location('I have stomach pain.')
print("Original location:", repr(b1))
print("Trans chest:", repr(b2))
print("Trans stomach:", repr(b3))