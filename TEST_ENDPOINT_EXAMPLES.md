# VaaniDoc /api/translate Endpoint Examples

## curl Request Examples

### 1. Gujarati Translation

```bash
curl -X POST "http://localhost:8000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{"text": "મને બે દિવસથી તાવ છે", "source_language": "gu"}'
```

**Response:**

```json
{
  "source_language": "gu",
  "english_text": "I have had fever for two days.",
  "verification": {
    "status": "needs_review",
    "warnings": [
      {
        "type": "duration_mismatch",
        "message": "Duration may not match: original '2 days' vs translation 'two days'."
      }
    ]
  }
}
```

**Explanation:** The Gujarati "બે દિવસથી" (2 days) was translated as "two days" but the safety checker flagged a duration mismatch because the original says "2 days" while the translation says "two days" - both refer to the same duration but the checker detected the numerical form difference.

### 2. Hindi Translation (Correct)

```bash
curl -X POST "http://localhost:8000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{"text": "मुझे दो दिन से बुखार है", "source_language": "hi"}'
```

**Response:**

```json
{
  "source_language": "hi",
  "english_text": "I have had a fever for two days.",
  "verification": {
    "status": "consistent",
    "warnings": []
  }
}
```

**Explanation:** Hindi "मुझे दो दिन से बुखार है" translates correctly with no detected mismatches.

### 3. Unsupported Language

```bash
curl -X POST "http://localhost:8000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{"text": "test", "source_language": "en"}'
```

**Response (HTTP 400):**

```json
{
  "detail": "Unsupported source language code: 'en'"
}
```

### 4. Empty Text

```bash
curl -X POST "http://localhost:8000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{"text": "   ", "source_language": "gu"}'
```

**Response (HTTP 400):**

```json
{
  "detail": "Translation text is empty or whitespace-only"
}
```

### 5. Malformed Request (missing fields)

```bash
curl -X POST "http://localhost:8000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{"text": "મને તાવ છે"}'
```

**Response (HTTP 422 - Validation Error):**

```json
{
  "detail": [
    {
      "loc": ["body", "source_language"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 6. Model Failure (simulated)

When the CT2 model fails to load or inference fails:

```bash
curl -X POST "http://localhost:8000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{"text": "મને તાવ છે", "source_language": "gu"}'
```

**Response (HTTP 502):**

```json
{
  "detail": "Translation service unavailable"
}
```

## API Test Scenarios

| Test Case | Input | Expected |
|---|---|---|
| Successful Gujarati translation | `{"text": "મને બે દિવસથી તાવ છે", "source_language": "gu"}` | 200 + English translation + verification |
| Successful Hindi translation | `{"text": "मुझे दो दिन से बुखार है", "source_language": "hi"}` | 200 + English translation + verification |
| Unsupported language | `{"text": "test", "source_language": "en"}` | 400 + error detail |
| Empty text | `{"text": "   ", "source_language": "gu"}` | 400 + error detail |
| Malformed request (missing source_language) | `{"text": "test"}` | 422 + validation error |
| Model failure | (when CT2 model unavailable) | 502 + "Translation service unavailable" |
| Translation safety warning | Gujarati with duration change | 200 + "needs_review" + duration_mismatch warning |

## Requirements Checklist

- [x] Pydantic request/response models (`TranslateRequest`, `TranslateResponse`)
- [x] Validate empty text → HTTP 400
- [x] Validate source language → HTTP 400 for unsupported codes
- [x] Reject unsupported languages → HTTP 400
- [x] Do not expose stack traces to users → Generic error messages only
- [x] Return appropriate HTTP errors (400, 422, 502)
- [x] Reuse already-loaded IndicTrans2 CT2 model (loaded at import time in `translator.py`)
- [x] Do not load model per request → Model is module-level singleton
- [x] Do not permanently store translation data → No file I/O, in-memory only
- [x] Do not log patient text → No patient data logged (only length metadata)
- [x] Keep endpoint modular → Route calls `translator.py` and `translation_safety.py`
- [x] Route calls `translator.py`, not containing model logic itself → Model logic in `backend/ai/translation/translator.py`
- [x] Route calls translation safety checker → `verify_translation()` from `translation_safety.py`
- [x] Do not introduce IndicTransToolkit → Using official CTranslate2 directly
- [x] Do not introduce Hugging Face inference → Using CTranslate2 only
- [x] Do not introduce WSL2-specific code → Platform-independent code

## Module Integration Path

```
POST /api/translate
    ↓ (Pydantic model validation)
    └── validate text not empty
    └── validate source language supported
    │
    ├── translate() from translator.py
    │   ├── Model loaded once at import time (not per request)
    │   ├── Maps VaaniDoc code → FLORES-200 code (language_map.py)
    │   ├── Preprocesses with language tags
    │   ├── CTranslate2 inference (ctranslate2.Translator)
    │   ├── Postprocesses output (detokenize, strip ▁ markers)
    │   └── Returns English translation
    │
    └── verify_translation() from translation_safety.py
        ├── Checks: duration, negation, body location, dosage, numbers, units
        ├── Symptoms, severity expressions
        ├── Returns {"status": "consistent"|"needs_review", "warnings": [...]}
        ├── Original patient statement always preserved in result["original"]
        └── Does NOT claim medical correctness or guaranteed accuracy
```

## What the Verification Checker Detects

**Duration mismatches:** "3 days" vs "2 days", "two days" vs "3 days"
**Negation inversion:** "no fever" vs "have fever" 
**Body location changes:** "chest" vs "stomach"
**Dosage changes:** "500 mg" vs "100 mg"
**Unit changes:** "mg" vs "ml"
**Number changes:** standalone numbers that differ
**Symptom loss:** known symptom word absent from translation
**Severity changes:** mild vs severe, etc.

**What it does NOT guarantee:**
- Machine translation is correct
- Medical correctness
- Complete clinical information preservation
- Detection of all possible mismatches (only a reliably detectable subset)

The verification result status is:
- `"consistent"` — No detectable clinically important mismatches
- `"needs_review"` — One or more potentially important mismatches detected

The original patient statement is always available in the verification result under the `"original"` key (accessible to callers who need it).