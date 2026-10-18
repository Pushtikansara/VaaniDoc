
# 🩺 VaaniDoc — Multilingual AI Health Intake for Rural Clinics

> **Speak in your language. Get a structured clinical intake in English.**

VaaniDoc is a privacy-first, multilingual AI health intake system designed for rural and semi-urban clinics in India.

The system operates on a **three-module pipeline**:

1. **Member 1 - Speech AI**: Automatic Speech Recognition (IndicConformer) transcribes patient speech into Indian-language text
2. **Member 2 - Translation**: IndicTrans2 CT2 translates Indian-language text to English (graceful fallback when model unavailable)
3. **Member 3 - Clinical AI**: Deterministic symptom extraction and urgency classification produces structured clinical data

Patients can **speak or type symptoms in Indian regional languages**, while VaaniDoc automatically converts the input into a structured **English clinical intake form** for doctors.

The system is designed around three core constraints:

* 🌐 **Multilingual:** Supports 22 Indian languages through multilingual pretrained models
* 📶 **Low-bandwidth:** Designed for rural environments with connectivity below 100 KB/s
* 🔐 **Privacy-first:** Patient information exists only for the active consultation session and is deleted afterward

---

## 🎯 Problem

Doctors in rural and semi-urban clinics spend significant consultation time on documentation.

At the same time, patients may face:

* Language barriers
* Low literacy
* Difficulty describing symptoms in English
* Limited access to digital healthcare infrastructure
* Poor internet connectivity

VaaniDoc addresses this by allowing patients to communicate naturally in their preferred Indian language.

---

# 🚀 How VaaniDoc Works

```text
                    PATIENT
                       │
               ┌────────┴────────┐
               │                 │
            🎤 Voice           ⌨️ Text
               │                 │
               ▼                 │
      ┌──────────────────┐       │
      │ IndicConformer   │       │
      │ Multilingual ASR │       │
      └────────┬─────────┘       │
               │                 │
               └────────┬────────┘
                        ▼
               Indian-language Text
                        │
                        ▼
              ┌──────────────────┐
              │    Member 2      │
              │   IndicTrans2    │
              │  Indian → English│
              └────────┬─────────┘
                       ▼
                  English Text
                       │
                       ▼
              ┌──────────────────┐
              │  Member 3        │
              │ Clinical         │
              │ Information      │
              │ Extraction       │
              └────────┬─────────┘
                       ▼
               Structured JSON
                       │
                       ▼
              ┌──────────────────┐
              │ Urgency Rule     │
              │ Engine           │
              └────────┬─────────┘
                       ▼
               English Clinical
                    Intake
                       │
              ┌────────┴────────┐
              ▼                 ▼
       Patient View       Doctor Dashboard
```

**Note:** When the IndicTrans2 model is unavailable, the system uses a graceful fallback translation:
`"[Simulated Translation] Patient states: {transcript}"` while maintaining full pipeline functionality.

---

# ✨ Key Features

### 🌐 Multilingual Input

Patients can enter symptoms using:

* Voice
* Text

The system is designed around multilingual Indic language processing rather than maintaining separate application pipelines for each language.

### 🎤 Multilingual Speech Recognition

**IndicConformer** converts patient speech into text.

```text
Gujarati Speech
   ↓
IndicConformer
   ↓
Gujarati Text
```

The multilingual IndicConformer model supports the 22 scheduled Indian languages.

### 🌍 Translation to English

**IndicTrans2** converts Indian-language text into English.

```text
મને બે દિવસથી તાવ છે

   ↓

I have had fever for two days.
```

**Fallback translation** (when model unavailable):
`"[Simulated Translation] Patient states: {transcript}"`

The system is fully functional with fallback for demonstration/prototyping.

### 🧠 Clinical Information Extraction

The English patient statement is converted into structured clinical information, including `chief_complaint` (first detected symptom).

Example:

```json
{
  "chief_complaint": "Fever",
  "symptoms": [
    "fever",
    "headache"
  ],
  "duration": "2 days",
  "severity": "moderate",
  "body_location": "head"
}
```

### ⚠️ Urgency Classification

A deterministic clinical rule layer evaluates extracted symptoms and assigns an intake urgency level:

```text
🔴 EMERGENCY
🟠 HIGH
🟡 MODERATE
🟢 ROUTINE
```

The system is intended for **clinical intake support and prioritization**, not diagnosis.

### 👨‍⚕️ Doctor Dashboard

The doctor receives the structured intake in English without requiring the patient to communicate in English.

The dashboard displays:

* Chief complaint
* Symptoms
* Duration
* Severity
* Body location
* Associated symptoms
* Urgency
* Original patient statement

### 📄 Clinical Report

The structured JSON is rendered into a standardized English clinical intake form that can be downloaded/printed as PDF.

### 🔐 Privacy-First Design

Patient information is maintained only during the active consultation session.

The system does not permanently retain:

* Audio
* Transcripts
* Translations
* Clinical intake data

When the session ends, temporary patient data is deleted.

### 📶 Low-Bandwidth Design

The application is designed for low-connectivity environments using:

* Compressed audio
* Short voice recordings instead of continuous streaming
* Lightweight frontend assets
* PWA caching
* Minimal API payloads

---

# 🧠 AI Architecture

VaaniDoc intentionally uses **pretrained multilingual models instead of training separate models for every Indian language**.

## 1. IndicConformer

**Task:** Speech → Indian-language text

```text
Audio
  ↓
IndicConformer
  ↓
Indian-language transcript
```

## 2. IndicTrans2

**Task:** Indian-language text → English

```text
Indian-language text
        ↓
   IndicTrans2
        ↓
      English
```

A distilled Indic→English model is used to reduce computational requirements.

## 3. Clinical Extraction Layer

**Task:** English narrative → structured clinical information

```text
English patient statement
          ↓
Clinical extraction
          ↓
Structured JSON
```

The extraction stage is constrained to a predefined schema to reduce hallucination and make the output predictable.

## 4. Urgency Rule Engine

The final urgency level is determined using application-level safety rules rather than relying entirely on generative output.

```text
Clinical JSON
     ↓
Safety Rules
     ↓
Urgency
```

---

# 🛠️ Tech Stack

## Frontend

* React
* Vite
* Tailwind CSS
* Progressive Web App (PWA)
* Browser MediaRecorder API

## Backend

* Python
* FastAPI
* WebSockets

## AI / NLP

* AI4Bharat IndicConformer
* AI4Bharat IndicTrans2
* Structured clinical information extraction

## Report

* HTML/CSS clinical template
* Browser PDF printing / PDF generation

## Storage

* Temporary in-memory session storage
* No permanent patient-data storage

---

# 📁 Project Structure

```text
VaaniDoc/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── VoiceRecorder.jsx
│   │   │   ├── LanguageSelector.jsx
│   │   │   ├── ClinicalForm.jsx
│   │   │   └── UrgencyBadge.jsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Patient.jsx
│   │   │   └── Doctor.jsx
│   │   │
│   │   └── App.jsx
│   │
│   └── package.json
│
├── backend/
│   ├── speech_api.py
│   ├── asr.py
│   ├── translation.py
│   ├── extraction.py
│   ├── urgency.py
│   ├── sessions.py
│   └── requirements.txt
│
├── tests/
│   └── clinical_test_cases.json
│
└── README.md
```

---

# ⚙️ Installation

## Prerequisites

* Python 3.10+
* Node.js 18+
* Git
* NVIDIA GPU recommended for local model inference

---

## Backend

```bash
cd backend

python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux/macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn speech_api:app --reload
```

Backend:

```text
http://localhost:8000
```

If you prefer to run from the repository root instead of `backend/`, this also works:

```bash
python -m uvicorn backend.speech_api:app --reload
```

---

# 💻 Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 🔄 Example Input → Output

### Patient Input

```text
Language: Gujarati

મને બે દિવસથી તાવ છે અને માથું દુખે છે.
```

### Speech Recognition

```text
મને બે દિવસથી તાવ છે અને માથું દુખે છે.
```

### English Translation

```text
[Simulated Translation] Patient states: મને બે દિવસથી તાવ છે અને માથું દુખે છે.
```

*Uses fallback translation when IndicTrans2 model is unavailable. System remains fully functional.*

### Clinical Extraction

```json
{
  "chief_complaint": "Fever",
  "symptoms": [
    "fever",
    "headache"
  ],
  "duration": "2 days",
  "severity": null,
  "body_location": "head",
  "associated_symptoms": []
}
```

### Urgency

```text
🟢 ROUTINE
```

### Doctor Output

```text
Chief Complaint:
Fever

Symptoms:
• Fever
• Headache

Duration:
2 days

Severity:
Not specified

Urgency:
ROUTINE

English Translation:
[Simulated Translation] Patient states: મને બે દિવસથી તાવ છે અને માથું દુખે છે.

Verification:
Status: consistent
Warnings: none
```

---

# 🧪 Evaluation

The system is evaluated against **20 multilingual clinical test cases**.

Evaluation includes:

### Symptom Extraction Accuracy

```text
Correctly extracted symptoms
──────────────────────────── × 100
Expected symptoms
```

### Additional Metrics

* Duration extraction accuracy
* Severity extraction accuracy
* Urgency classification accuracy
* Language handling accuracy
* Speech transcription quality
* End-to-end processing time

Test cases cover multiple Indian languages and different symptom scenarios.

---

# 🛠️ Setup and Execution Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Node.js 18+ and npm
- Dependencies installed via `pip install -r backend/requirements.txt` and `cd frontend && npm install`

### 2. Starting the Backend Service
Run from the repository root:
```bash
uvicorn backend.main:app --reload --port 8000
```
API Documentation and Swagger UI will be available at:
`http://127.0.0.1:8000/docs`

### 3. Starting the Frontend UI
Run from the `frontend/` directory:
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173` in any modern web browser or mobile browser.

### 4. Running Automated Tests
Run the deterministic 26-test suite (covering 20 clinical symptom extraction cases + backend lifecycle):
```bash
python -m pytest tests/ -v
```

### 5. Building Frontend for Production
```bash
cd frontend
npm run build
```

---

# 📡 Integrated API Routes

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service and module readiness health check |
| `POST` | `/api/intake` | Full voice intake pipeline (Audio + Language → ASR → Translation → Extraction → Urgency) |
| `POST` | `/api/intake/text` | Full text intake pipeline for typed Indian language symptoms |
| `POST` | `/api/speech/transcribe` | Standalone ASR speech-to-text |
| `POST` | `/api/translate` | Standalone IndicTrans2 translation with safety verification |
| `POST` | `/api/clinical/extract` | Extraction of active symptoms and explicit negative findings |
| `POST` | `/api/clinical/analyze` | Full clinical extraction with urgency triage classification |
| `GET` | `/api/report/{session_id}/data` | Structured clinical report JSON for Doctor Dashboard preview |
| `PUT` | `/api/report/{session_id}` | Doctor updates to clinical findings, triage tier, and clinical notes |
| `GET` | `/api/report/{session_id}` | Streams a formatted ReportLab PDF clinical intake report |
| `POST` | `/api/session/end` | Immediately purges patient session data from memory |

---

# 📋 Clinical Reporting & Doctor Dashboard Workflow

1. **Intake Ingestion**: Patient speaks or types symptoms in an Indian regional language (e.g., Gujarati, Hindi, Marathi, etc.) or English.
2. **Translation & Safety Verification**: The statement is translated into English while checking for negation inversions, duration mismatches, or dosage alterations.
3. **Clinical Extraction**: Deterministic extraction isolates confirmed active symptoms, explicit negative findings (denied symptoms), symptom duration, severity, and anatomical body location.
4. **Urgency Triage**: Evaluates clinical findings across 4 tiers (`EMERGENCY`, `HIGH`, `MODERATE`, `ROUTINE`) with an inspectable clinical rationale.
5. **Doctor Review & Edit**: Attending clinician reviews the intake summary on the Doctor Dashboard, edits findings if necessary, and enters clinical examination notes and treatment orders.
6. **PDF Export**: Clinician generates a signed, formatted clinical intake PDF report.
7. **Privacy Cleanup**: On consultation conclusion, the session is cleared from memory with zero persistent patient data retained.

---


# 🔒 Privacy Model

VaaniDoc follows a session-based privacy architecture.

```text
Patient
   ↓
Temporary Session
   ↓
AI Processing
   ↓
Doctor Dashboard
   ↓
Consultation Ends
   ↓
🗑️ Session Data Deleted
```

No permanent patient database is required for the MVP.

---

# 📶 Low-Bandwidth Strategy

The system is optimized for rural connectivity constraints.

### Instead of:

```text
Continuous audio streaming
```

VaaniDoc uses:

```text
Short recording
      ↓
Compressed audio
      ↓
Single upload
      ↓
Processing
```

The frontend is also designed as a PWA so core application resources can be cached locally.

---

# ⚠️ Medical Safety Disclaimer

VaaniDoc is a **clinical intake and documentation assistance system**.

It does **not** provide a medical diagnosis or replace a qualified healthcare professional.

Urgency classification is intended to assist clinical prioritization and should always be reviewed by the attending healthcare professional.

---

# 🔧 System Status

**Current Status**: Fully functional with fallback translation

- **Backend API**: All endpoints operational
- **Speech AI (ASR)**: 22 Indian languages supported
- **Translation (Member 2)**: Functional with simulated fallback when IndicTrans2 CT2 model is unavailable
- **Clinical AI (Member 3)**: Symptom extraction, urgency classification working correctly
- **Frontend UI**: Professional design, all interactions working
- **PDF Reports**: Generatable from session data
- **Privacy**: Audio deleted immediately, memory-only sessions

**To enable live translation**: Download AI4Bharat IndicTrans2 CT2 model (~1.5GB) and set `VAANI_TRANSLATION_MODEL_PATH`. Until then, the system is fully operational for demonstration and prototyping.

---

# 🌍 Social Impact

VaaniDoc aims to reduce communication and documentation barriers between patients and healthcare workers.

### Before VaaniDoc

```text
Patient
   ↓
Language barrier
   ↓
Difficulty describing symptoms
   ↓
Manual documentation
   ↓
Doctor spends more time on paperwork
```

### With VaaniDoc

```text
Patient speaks naturally
        ↓
Multilingual AI
        ↓
Structured English intake
        ↓
Doctor
        ↓
More time for patient care
```

---

# 🚀 Future Scope

* More regional language coverage
* Better medical terminology normalization
* Fully offline ASR for supported devices
* Integration with existing clinic systems
* FHIR-compatible clinical records
* Multilingual voice responses
* Additional clinical specialties
* Larger multilingual evaluation datasets

---

# 👥 Team

**Project:** VaaniDoc
**Track:** Social Impact & Inclusion
**Problem:** Multilingual AI Health Intake System for Rural Clinics
**Domain:** AI + Healthcare + NLP

---

## ❤️ VaaniDoc

**Breaking the language barrier between patients and healthcare.**

> **Speak your language. Let the doctor understand.**
