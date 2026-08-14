with open(r'F:\VaaniDoc\frontend\src\App.jsx', 'r') as f:
    content = f.read()

# Add DoctorReview import after TranscriptDisplay import
import_line = "import TranscriptDisplay from \"./TranscriptDisplay\";"
new_import = """import TranscriptDisplay from "./TranscriptDisplay";
import DoctorReview from "./DoctorReview";"""

if import_line in content:
    content = content.replace(import_line, new_import)
    print("Import line updated")
else:
    print("Import line not found")

# Add DoctorReview component usage after TranscriptDisplay usage
transcript_display_usage = '  <TranscriptDisplay'
if transcript_display_usage in content:
    # Build the DoctorReview JSX
    doctor_review_jsx = '''  <DoctorReview
    englishText={englishText}
    originalText={originalText}
    verificationStatus={verificationStatus}
    warnings={warnings}
    clinicalData={{
      chiefComplaint: "Chief complaint goes here",
      symptoms: ["symptom 1", "symptom 2"],
      duration: "2 days",
      severity: "mild",
      bodyLocation: "chest",
      associatedSymptoms: ["cough", "fatigue"],
      urgency: "routine",
    }}
    onClinicalDataChange={(data) => {
      // Update clinical state
    }}
    onCopyCase={() => {
      // Copy case data
    }}
    onRetranslate={() => {
      // Re-translate the patient statement
    }}
  />
'''
    
    # Find the TranscriptDisplay closing and add DoctorReview after it
    idx = content.find('  </div>', content.find('  <TranscriptDisplay'))
    if idx >= 0:
        # Insert after the TranscriptDisplay closing div
        content = content[:idx] + doctor_review_jsx + content[idx:]
        print("DoctorReview component added after TranscriptDisplay")
    else:
        print("Could not find TranscriptDisplay closing pattern")
else:
    print("Import line not found")

with open(r"F:\VaaniDoc\frontend\src\App.jsx", "w") as f:
    f.write(content)
print("File updated successfully")