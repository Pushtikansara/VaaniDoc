import sys
sys.path.insert(0, r'F:\VaaniDoc')
from backend.ai.translation.translation_safety import verify_translation

# Test duration
result = verify_translation('મને ત્રણ દિવસથી તાવ છે.', 'gu', 'I have had a fever for three days.')
print('Duration correct:', result['status'], result['warnings'])

result = verify_translation('મને ત્રણ દિવસથી તાવ છે.', 'gu', 'I have had a fever for two days.')
print('Duration wrong:', result['status'], result['warnings'])

# Test negation
result = verify_translation('મને તાવ નથી.', 'gu', 'I have no fever.')
print('Negation correct:', result['status'], result['warnings'])

result = verify_translation('મને તાવ નથી.', 'gu', 'I have a fever.')
print('Negation lost:', result['status'], result['warnings'])

# Test body location
result = verify_translation('મને છાતીમાં દુખાવો છે.', 'gu', 'I have chest pain.')
print('Body location correct:', result['status'], result['warnings'])

result = verify_translation('મને છાતીમાં દુખાવો છે.', 'gu', 'I have stomach pain.')
print('Body location wrong:', result['status'], result['warnings'])

# Test dosage
result = verify_translation('મે 500 mg દવા લીધી.', 'gu', 'I took 500 mg medicine.')
print('Dosage correct:', result['status'], result['warnings'])

result = verify_translation('મે 500 mg દવા લીધી.', 'gu', 'I took 100 mg medicine.')
print('Dosage changed:', result['status'], result['warnings'])

# Test number
result = verify_translation('મને 3 દિવસ થી તાવ છે.', 'gu', 'I have fever for 3 days.')
print('Number preserved:', result['status'], result['warnings'])

result = verify_translation('મને 3 દિવસ થી તાવ છે.', 'gu', 'I have fever for 2 days.')
print('Number changed:', result['status'], result['warnings'])

# Test unit
result = verify_translation('મે 500 mg દવા લીધી.', 'gu', 'I took 500 milligrams.')
print('Unit preserved:', result['status'], result['warnings'])

result = verify_translation('મે 500 mg દવા લીધી.', 'gu', 'I took 500 ml medicine.')
print('Unit changed:', result['status'], result['warnings'])

# Test original preserved
result = verify_translation('મને ત્રણ દિવસથી તાવ છે.', 'gu', 'I have had a fever for three days.')
orig_ok = result['original'] == 'મને ત્રણ દિવસથી તાવ છે.'
print('Original preserved:', orig_ok)

# Test consistent when no warnings
result = verify_translation('મને તાવ છે.', 'gu', 'I have a fever.')
print('Consistent no warnings:', result['status'], len(result['warnings']))

# Test needs_review when warnings
result = verify_translation('મને ત્રણ દિવસથી તાવ છે.', 'gu', 'I have had a fever for two days.')
print('Needs review:', result['status'], len(result['warnings']))

print('\nAll manual tests done!')