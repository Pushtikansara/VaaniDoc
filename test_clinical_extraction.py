import sys
sys.path.insert(0, r'F:\VaaniDoc')
from backend.ai.translation.clinical_extraction import extract_clinical_info, ClinicalData

# Test the extraction module
test_cases = [
    'I have had a fever for two days.',
    'I have chest pain.',
    'I took 500 mg medicine.',
    'I have no fever.',
]

for text in test_cases:
    result = extract_clinical_info(text)
    symp = result["symptoms"]
    sev = result["severity"]
    dur = result["duration"]
    loc = result["body_location"]
    urg = result["urgency"]
    print(f"Text: {text}")
    print(f"  Symptoms: {symp}")
    print(f"  Severity: {sev}")
    print(f"  Duration: {dur}")
    print(f"  Body location: {loc}")
    print(f"  Urgency: {urg}")
    print()
"