from ai.clinical.extraction import extract_symptoms

examples = [
    "I have fever but no headache.",
    "I don't have fever but I have headache.",
    "No vomiting. I have abdominal pain.",
    "I don't have fever. I have headache and cough."
]

for ex in examples:
    print(f"Input: {ex}")
    result = extract_symptoms(ex)
    print(f"Result: {result}\n")
