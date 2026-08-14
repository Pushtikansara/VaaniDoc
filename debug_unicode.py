import sys
sys.path.insert(0, r'F:\VaaniDoc')
from backend.ai.translation.transcript_confirmation import _normalize_yes_no

# Test with actual character input
test_chars = [
    ('\u0a85', 'Gujarati ha'),
    ('\u0aa8\u0aae', 'Gujarati haan'),
    ('\u0939\u09be', 'Hindi haan'),
    ('\u0928\u093f\u0926\u0940', 'Hindi nahi'),
    ('yes', 'English yes'),
    ('no', 'English no'),
    ('kem cho', 'unrecognized'),
]

with open("debug_output.txt", "w", encoding="utf-8") as f:
    for char, desc in test_chars:
        result = _normalize_yes_no(char)
        line = f"{desc}: {repr(char)} -> {result}\n"
        f.write(line)
        print(line.strip())

with open("debug_output.txt", "r", encoding="utf-8") as f:
    print(f.read())