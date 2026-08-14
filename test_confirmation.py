import sys
sys.path.insert(0, r'F:\VaaniDoc')
from backend.ai.translation.transcript_confirmation import (
    confirm_transcript, run_confirmation_workflow,
    _normalize_yes_no
)

print("=== Test 1: _normalize_yes_no Gujarati yes ===")
r1 = _normalize_yes_no("\u0a85")
print(f"  Result: {r1}")
g1 = (r1 is True)
print("  PASS" if g1 else "  FAIL")

print("\n=== Test 2: _normalize_yes_no Gujarati yes (long) ===")
r2 = _normalize_yes_no("\u0aa8\u0aae")
print(f"  Result: {r2}")
g2 = (r2 is True)
print("  PASS" if g2 else "  FAIL")

print("\n=== Test 3: _normalize_yes_no Hindi yes ===")
r3 = _normalize_yes_no("\u0939\u09be")
print(f"  Result: {r3}")
g3 = (r3 is True)
print("  PASS" if g3 else "  FAIL")

print("\n=== Test 4: _normalize_yes_no Hindi no ===")
r4 = _normalize_yes_no("\u0928\u093f\u0926\u0940")
print(f"  Result: {r4}")
g4 = (r4 is False)
print("  PASS" if g4 else "  FAIL")

print("\n=== Test 5: _normalize_yes_no unrecognized ===")
r5 = _normalize_yes_no("kem cho")
print(f"  Result: {r5}")
g5 = (r5 is None)
print("  PASS" if g5 else "  FAIL")

print("\n=== Test 5b: English yes -> unrecognized ===")
r5b = _normalize_yes_no("yes")
print(f"  Result: {r5b}")
g5b = (r5b is None)
print("  PASS" if g5b else "  FAIL")

print("\n=== Test 5c: English no -> unrecognized ===")
r5c = _normalize_yes_no("no")
print(f"  Result: {r5c}")
g5c = (r5c is None)
print("  PASS" if g5c else "  FAIL")

print("\n=== Test 6: confirm_transcript Gujarati confirm ===")
r6 = confirm_transcript("test transcript", "gu", "\u0a85", "gu")
print(f"  Result: {r6}")
g6 = (r6 == ("test transcript", True))
print("  PASS" if g6 else "  FAIL")

print("\n=== Test 7: confirm_transcript Gujarati reject ===")
r7 = confirm_transcript("test transcript", "gu", "\u0928\u093f\u0926\u0940", "gu")
print(f"  Result: {r7}")
g7 = (r7 == (None, False))
print("  PASS" if g7 else "  FAIL")

print("\n=== Test 8: confirm_transcript unrecognized ===")
r8 = confirm_transcript("test transcript", "gu", "kem cho", "gu")
print(f"  Result: {r8}")
g8 = (r8 == (None, False))
print("  PASS" if g8 else "  FAIL")

print("\n=== Test 6b: English yes -> unrecognized ===")
r9 = confirm_transcript("test transcript", "gu", "yes", "gu")
print(f"  Result: {r9}")
g9 = (r9 == (None, False))
print("  PASS" if g9 else "  FAIL")

print("\n=== Test 7: run_confirmation_workflow normal ===")
r2 = run_confirmation_workflow("test transcript", "gu", "\u0a85", "gu", allow_optional_confirmation=False)
print(f"  Result: {r2}")
g7a = (r2 == "test transcript")
print("  PASS" if g7a else "  FAIL")

print("\n=== Test 8: run_confirmation_workflow rejected ===")
r3 = run_confirmation_workflow("test transcript", "gu", "\u0928\u093f\u0926\u0940", "gu", allow_optional_confirmation=False)
print(f"  Result: {r3}")
g7b = (r3 is None)
print("  PASS" if g7b else "  FAIL")

print("\n=== Test 8b: run_confirmation_workflow optional ===")
r4 = run_confirmation_workflow("test transcript", "gu", "\u0a85", "gu", allow_optional_confirmation=True)
print(f"  Result: {r4}")
g7c = (r4 is not None)
print("  PASS" if g7c else "  FAIL")

# Summary
all_pass = all([g1, g2, g3, g4, g5, g5b, g5c, g6, g7, g7a, g7b, g7c])
print(f"\n{'='*50}")
if all_pass:
    print("ALL TESTS PASSED!")
else:
    print("SOME TESTS FAILED!")