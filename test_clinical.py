import sys
import asyncio
sys.path.insert(0, r'F:\VaaniDoc')

from ai.clinical.extraction import extract_symptoms
from backend.clinical_api import extract_clinical_info
from ai.clinical.schemas import ClinicalInformation

# Test the extraction function directly
symptoms = extract_symptoms("I have headache and fever")
print("Symptoms:", symptoms)

# Test the endpoint logic with a mock request
class MockRequest:
    def __init__(self, text):
        self.text = text

request = MockRequest("I have headache and fever")
result = asyncio.run(extract_clinical_info(request))
print("Result:", result)
print("Chief complaint:", result.chief_complaint)
print("Symptoms:", result.symptoms)
print("Type:", type(result))