import sys
sys.path.insert(0, r'F:\VaaniDoc')
from backend.ai.translation.translation_safety import _extract_unit, _extract_number_value, verify_translation

# Test unit extraction
print('=== Unit extraction ===')
u1 = _extract_unit('મે 500 mg દવા લીધી.')
u2 = _extract_unit('I took 500 milligrams.')
u3 = _extract_unit('I took 500 ml medicine.')
print('Original mg:', u1)
print('Trans milligrams:', u2)
print('Trans ml:', u3)

# Test number value extraction
print()
print('=== Number value extraction ===')
n1 = _extract_number_value('મે 500 mg દવા લીધી.')
n2 = _extract_number_value('I took 500 milligrams.')
n3 = _extract_number_value('I took 100 mg medicine.')
print('Original:', n1)
print('Trans milligrams:', n2)
print('Trans 100mg:', n3)

# Test full verification
print()
print('=== Full verification ===')
r1 = verify_translation('મે 500 mg દવા લીધી.', 'gu', 'I took 500 milligrams.')
print('500 mg vs 500 milligrams: status=%s, warnings=%s' % (r1['status'], r1['warnings']))

r2 = verify_translation('મે 500 mg દવા લીધી.', 'gu', 'I took 500 ml medicine.')
print('500 mg vs 500 ml: status=%s, warnings=%s' % (r2['status'], r2['warnings']))

r3 = verify_translation('મે 500 mg દવા લીધી.', 'gu', 'I took 500 medicine.')
print('500 mg vs 500 medicine: status=%s, warnings=%s' % (r3['status'], r3['warnings']))