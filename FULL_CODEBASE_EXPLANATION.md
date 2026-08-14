# VaaniDoc Codebase Explanation

This document explains the current codebase in `E:\VaaniDoc` as it exists on August 12, 2026.

It covers:

- every Python file
- how the frontend talks to the backend
- how the FastAPI API is structured
- how to use the built-in FastAPI documentation
- important runtime behavior and current limitations

---

## 1. Current project structure

```text
VaaniDoc/
├── ai/
│   ├── __init__.py
│   └── speech/
│       ├── __init__.py
│       ├── asr.py
│       ├── audio.py
│       ├── test_asr.py
│       └── audio/
│           └── gujarati_test.wav
├── backend/
│   ├── speech_api.py
│   └── temp/
│       └── .gitkeep
├── frontend/
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       ├── audio.js
│       ├── languages.js
│       ├── main.jsx
│       └── styles.css
└── README.md
```

This is currently a small end-to-end speech transcription app:

1. frontend records patient audio in the browser
2. frontend converts that recording to WAV
3. frontend sends the WAV file and selected language to FastAPI
4. backend saves the uploaded file temporarily
5. backend runs ASR using the AI4Bharat IndicConformer model
6. backend returns the transcript as JSON
7. frontend displays the transcript

At the moment, the app does transcription only. The translation, clinical extraction, urgency, session handling, and PDF/reporting mentioned in the README are not implemented in this codebase yet.

---

## 2. High-level architecture

```text
Browser
  └─ React UI
      ├─ records microphone audio
      ├─ converts recorded blob to WAV
      └─ POST /api/speech/transcribe
              |
              v
        Vite dev proxy
              |
              v
        FastAPI backend
              ├─ validates form data
              ├─ writes temp audio file
              ├─ loads audio into tensor
              ├─ loads ASR model if needed
              ├─ runs transcription
              └─ returns JSON response
```

Key point: during local development, the browser does not call `http://127.0.0.1:8000` directly. It calls `/api/...` on the Vite dev server, and Vite proxies that request to the FastAPI backend.

---

## 3. Python files: full explanation

## 3.1 `ai/__init__.py`

Purpose:

- marks `ai` as a Python package

Current behavior:

- file is empty

Why it matters:

- it allows imports like:

```python
from ai.speech.asr import transcribe
```

Without this package structure, `backend/speech_api.py` would not be able to import the speech modules correctly.

---

## 3.2 `ai/speech/__init__.py`

Purpose:

- marks `ai.speech` as a Python subpackage

Current behavior:

- file is empty

Why it matters:

- it allows nested imports under `ai.speech`

---

## 3.3 `ai/speech/audio.py`

This file is responsible for audio loading and normalization before speech recognition.

### Imports

```python
from pathlib import Path

import soundfile as sf
import torch
import torchaudio
```

What each import is doing:

- `Path`: filesystem-safe path handling
- `soundfile`: reads the audio file from disk
- `torch`: converts audio into a PyTorch tensor
- `torchaudio`: resamples audio to the expected sample rate

### Constant

```python
SAMPLE_RATE = 16000
```

Meaning:

- the ASR pipeline expects 16 kHz mono audio

### Main function: `load_audio(audio_path)`

Purpose:

- read an audio file
- validate that it exists and is not empty
- convert stereo to mono if needed
- resample to 16 kHz if needed
- return a tensor with shape `(channels, samples)`

Flow:

1. convert `audio_path` into a `Path`
2. check file existence and non-zero size
3. read the file with `soundfile`
4. if the audio has multiple channels, average them into one channel
5. convert to a PyTorch tensor
6. if sample rate is not 16 kHz, resample it
7. return the tensor

Important implementation details:

- `sf.read(..., dtype="float32")` loads audio as floating-point samples
- `data.mean(axis=1)` converts multichannel audio to mono
- `unsqueeze(0)` adds a channel dimension

Returned shape:

- mono waveform as `(1, samples)`

Possible failure cases:

- file missing
- file empty
- unreadable/corrupt audio file
- unsupported audio format for the installed backend libraries

Role in system:

- this is the preprocessing layer between uploaded file storage and model inference

---

## 3.4 `ai/speech/asr.py`

This file contains the speech recognition logic.

### Imports

```python
import torch
from transformers import AutoModel
```

Plus:

```python
try:
    from .audio import load_audio
except ImportError:
    from audio import load_audio
```

Why the `try/except` import exists:

- when used as part of the package, `.audio` works
- when run more directly in some local contexts, fallback import `audio` may work

This is a convenience pattern, but it also indicates the file is being used both as package code and as a script dependency.

### Model identifier

```python
MODEL_ID = "ai4bharat/indic-conformer-600m-multilingual"
```

Meaning:

- the transcription model is downloaded from Hugging Face
- this is the AI4Bharat multilingual IndicConformer model

### Supported language codes

```python
LANGUAGE_CODES = {
    "as", "bn", "brx", "doi", "gu", "hi", "kn", "ks", "kok", "mai", "ml",
    "mni", "mr", "ne", "or", "pa", "sa", "sat", "sd", "ta", "te", "ur",
}
```

Purpose:

- valid input values for the `language` form field
- backend rejects anything outside this set

### Module-level cache

```python
_model = None
_device = None
```

Purpose:

- avoid reloading the ASR model for every request
- once loaded, the same Python process reuses it

### `_get_device()`

```python
def _get_device():
    return "cuda" if torch.cuda.is_available() else "cpu"
```

Purpose:

- detect whether GPU is available
- use CUDA if possible, otherwise CPU

### `_get_model()`

Purpose:

- lazily load the ASR model only on first use

Flow:

1. detect execution device
2. if `_model` is `None`, call:

```python
AutoModel.from_pretrained(MODEL_ID, trust_remote_code=True)
```

3. move model to CPU or GPU
4. switch model to evaluation mode with `.eval()`
5. cache model and device
6. return them

Important behavior:

- first transcription request will be significantly slower than later ones
- model load may download weights if not already cached locally
- if network access is blocked and the model is not cached, first load can fail

### `transcribe(audio_path, language)`

Purpose:

- main public function in this file
- converts one audio file into a transcript string

Flow:

1. normalize and validate language code
2. load waveform tensor using `load_audio`
3. get cached model and device
4. move waveform tensor to same device as model
5. run inference:

```python
text = model(wav, language, "ctc")
```

6. normalize return value to a string
7. return transcript

Why `"ctc"` is passed:

- it specifies the decoding/inference mode expected by the model implementation

Possible failure cases:

- unsupported language
- model load failure
- audio preprocessing failure
- device memory issues
- incompatible model/runtime environment

Role in system:

- this is the core inference layer

---

## 3.5 `ai/speech/test_asr.py`

This is a local test/utility script for transcription.

### Imports

```python
import sys
from pathlib import Path

from asr import transcribe
```

Purpose:

- run the ASR code from the command line
- default to a bundled Gujarati sample file if no arguments are provided

### `main()`

Behavior:

1. read `audio_path` from first command-line argument
2. if no argument is provided, use:

```python
ai/speech/audio/gujarati_test.wav
```

3. read `language` from second command-line argument, default `"gu"`
4. validate that the sample file exists and is not empty
5. call `transcribe(audio_path, language)`
6. print the result

Typical usage:

```powershell
cd E:\VaaniDoc\ai\speech
..\..\ .venv\Scripts\python.exe test_asr.py
```

or with explicit inputs:

```powershell
python test_asr.py audio\gujarati_test.wav gu
```

Current caveat:

- `from asr import transcribe` assumes execution from inside `ai\speech` or with that directory on the import path
- it is a script-style import, not package-style import

Role in system:

- local developer test tool, not part of the FastAPI request path

---

## 3.6 `backend/speech_api.py`

This is the backend application entrypoint. It defines the FastAPI app and HTTP endpoints.

### Imports

```python
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from ai.speech.asr import LANGUAGE_CODES, transcribe
```

What each part does:

- `Path`: build safe filesystem paths
- `uuid4`: generate unique filenames for uploaded audio
- `FastAPI`: create the web app
- `File`, `Form`, `UploadFile`: declare multipart request inputs
- `HTTPException`: return HTTP errors with proper status codes
- `CORSMiddleware`: allow browser requests across origins if needed
- `LANGUAGE_CODES`, `transcribe`: speech pipeline integration

### App initialization

```python
app = FastAPI()
```

This creates the ASGI application instance.

### CORS configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Meaning:

- all origins are allowed
- all methods and headers are allowed

Practical effect:

- the frontend can call this backend from any origin during development

Security note:

- this is permissive and convenient for local development
- in production it should usually be restricted to known frontend origins

### Temp directory

```python
TEMP_DIR = Path("backend") / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
```

Purpose:

- uploaded files are written temporarily to `backend/temp`

Why this matters:

- the backend does not stream directly into the model
- it saves to disk first, then passes the path to the ASR pipeline

### `GET /health`

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

Purpose:

- health/status endpoint
- useful for checking whether the backend is up

Response:

```json
{"status":"ok"}
```

### `POST /api/speech/transcribe`

```python
@app.post("/api/speech/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form(...),
):
```

Purpose:

- receive uploaded audio and language code
- return transcript JSON

Request format:

- `multipart/form-data`
- fields:
  - `audio`: uploaded audio file
  - `language`: one of the supported language codes

Processing flow:

1. normalize `language`
2. validate language against `LANGUAGE_CODES`
3. ensure filename exists
4. generate unique temp filename
5. read uploaded bytes
6. reject empty upload
7. write bytes to temp file
8. call `transcribe(temp_path, language)`
9. return:

```json
{
  "language": "gu",
  "transcript": "..."
}
```

10. close uploaded file handle
11. delete temp file in `finally`

### Error handling

The route maps different failures to HTTP responses:

- invalid language -> `400`
- missing filename -> `400`
- empty upload -> `400`
- missing/empty temp audio file -> `400`
- unsupported language in ASR function -> `400`
- unexpected transcription failure -> `500`

This separation is good because client-side mistakes and server-side failures are not mixed together.

### Important startup detail

This file imports `ai.speech.asr`, so the backend must be started from the repo root, not from inside `backend`.

Correct:

```powershell
cd E:\VaaniDoc
.\.venv\Scripts\python.exe -m uvicorn backend.speech_api:app --reload
```

Incorrect for this repo layout:

```powershell
cd E:\VaaniDoc\backend
uvicorn speech_api:app --reload
```

Why the incorrect command fails:

- Python cannot resolve the top-level `ai` package when the working directory is only `backend`

---

## 4. Frontend files: how they connect to the backend

## 4.1 `frontend/src/main.jsx`

Purpose:

- React entrypoint
- renders the root `App` component into the DOM

This is standard Vite/React bootstrap code.

---

## 4.2 `frontend/src/App.jsx`

This is the main UI and state manager for recording and transcription.

### Main state

- `language`: currently selected language code, default `"gu"`
- `isRecording`: whether recording is active
- `isProcessing`: whether the app is converting/uploading/transcribing
- `transcript`: returned transcript text
- `error`: current error message

### Refs

- `mediaRecorderRef`: active `MediaRecorder`
- `streamRef`: active microphone stream
- `chunksRef`: recorded audio chunks

### Recording flow

`startRecording()`:

1. clear previous error and transcript
2. verify browser supports microphone capture
3. request microphone access with `getUserMedia({ audio: true })`
4. create `MediaRecorder`
5. collect chunks in `ondataavailable`
6. define error handling
7. define `onstop` behavior
8. call `recorder.start()`

`stopRecording()`:

1. stop the `MediaRecorder`
2. `onstop` then executes automatically

### Processing flow in `onstop`

1. stop media tracks
2. ensure at least one audio chunk exists
3. build a browser `Blob`
4. call `mediaBlobToWav(blob)`
5. call `transcribeAudio(wavBlob, language)`
6. display returned transcript

### UI behavior

- language dropdown is disabled while recording/processing
- record button toggles between start and stop
- transcript result is shown in a result box
- processing and error messages are displayed in the page

Role in system:

- this file orchestrates the entire browser-side workflow

---

## 4.3 `frontend/src/audio.js`

This file converts recorded browser audio into a WAV file.

Why it exists:

- browser `MediaRecorder` commonly produces formats like WebM/Opus
- backend ASR path is expecting audio that can be reliably decoded by the Python stack
- WAV is a simple and predictable format for this use case

### `pcmToWav(samples, sampleRate)`

Purpose:

- build a WAV file manually from raw PCM samples

What it writes:

- RIFF header
- WAVE metadata
- PCM format block
- data chunk

Output:

- `Blob` with MIME type `audio/wav`

### `mediaBlobToWav(blob)`

Purpose:

- decode the recorded browser audio blob
- extract audio samples
- encode them back as WAV

Flow:

1. convert blob to array buffer
2. create `AudioContext`
3. decode audio data into `AudioBuffer`
4. use channel 0
5. pass samples to `pcmToWav`
6. close `AudioContext`

Current behavior note:

- only the first audio channel is used
- if the source has multiple channels, this code does not average them in JS; it simply takes channel 0

---

## 4.4 `frontend/src/api.js`

This file wraps the frontend call to the backend API.

### `transcribeAudio(audioBlob, language)`

Flow:

1. create `FormData`
2. append:
   - `"audio"` -> `audioBlob` as `recording.wav`
   - `"language"` -> selected language code
3. send `POST` request to:

```text
/api/speech/transcribe
```

4. parse JSON response if possible
5. if response is not OK, throw an `Error`
6. return parsed JSON

Why the URL is relative:

- during development, Vite proxy forwards `/api/...` to FastAPI

---

## 4.5 `frontend/src/languages.js`

This file defines the frontend list of selectable languages.

### `SUPPORTED_LANGUAGES`

Contains 22 objects, each with:

- `label`
- `code`

The codes match `LANGUAGE_CODES` in the backend.

### `assertSupportedLanguages()`

Purpose:

- guard against accidental UI config mistakes

Checks:

- exactly 22 languages
- all codes unique

What it does not check:

- it does not verify equality with the backend set at runtime
- if frontend and backend diverge, the frontend may still render options the backend rejects

---

## 4.6 `frontend/vite.config.js`

This file configures the local frontend dev server.

### Plugin

- React plugin for Vite

### Dev server

- port `5173`

### Proxy

```js
proxy: {
  "/api": "http://127.0.0.1:8000",
  "/health": "http://127.0.0.1:8000"
}
```

Meaning:

- requests from the browser to `/api/...` are forwarded to FastAPI on port `8000`
- `/health` is also forwarded

Why this helps:

- avoids hardcoding backend base URLs in frontend code
- reduces local CORS friction during development

---

## 5. End-to-end request flow

This is the exact runtime path when a user records audio and clicks stop.

### Step 1: browser records audio

`App.jsx` uses:

```js
navigator.mediaDevices.getUserMedia({ audio: true })
```

and:

```js
new MediaRecorder(stream)
```

The browser collects audio chunks.

### Step 2: browser converts recording to WAV

When recording stops:

- chunks are combined into a `Blob`
- `mediaBlobToWav()` decodes that blob and rewrites it as WAV

### Step 3: frontend sends multipart request

`api.js` sends:

- audio file
- language code

to:

```text
POST /api/speech/transcribe
```

### Step 4: Vite proxies request

Because of `vite.config.js`:

```text
frontend browser -> http://127.0.0.1:5173/api/speech/transcribe
                   -> proxied to http://127.0.0.1:8000/api/speech/transcribe
```

### Step 5: FastAPI receives upload

`backend/speech_api.py`:

- parses multipart form
- validates `language`
- reads uploaded file bytes

### Step 6: backend writes temp file

The file is saved into:

```text
backend/temp/<random-uuid>.<ext>
```

### Step 7: backend loads and normalizes audio

`ai/speech/audio.py`:

- reads file
- converts to mono if needed
- resamples to 16 kHz if needed
- returns PyTorch tensor

### Step 8: backend runs ASR model

`ai/speech/asr.py`:

- loads model on first request
- moves waveform to CPU/GPU
- runs inference
- returns transcript string

### Step 9: backend returns JSON

Example:

```json
{
  "language": "gu",
  "transcript": "recognized text here"
}
```

### Step 10: frontend renders transcript

`App.jsx` sets:

- `transcript`
- or `error`

and updates the UI.

---

## 6. FastAPI API surface

The current backend exposes two HTTP endpoints.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Basic health check |
| POST | `/api/speech/transcribe` | Upload audio and return transcript |

---

## 7. FastAPI request and response details

## 7.1 `GET /health`

### Request

```http
GET /health
```

### Response

```json
{"status":"ok"}
```

### Use cases

- verify backend startup
- confirm proxy connectivity
- simple uptime check

---

## 7.2 `POST /api/speech/transcribe`

### Request type

`multipart/form-data`

### Fields

- `audio`: file upload
- `language`: text field such as `gu`, `hi`, `ta`

### Example using `curl`

```bash
curl -X POST "http://127.0.0.1:8000/api/speech/transcribe" \
  -F "audio=@sample.wav" \
  -F "language=gu"
```

### Success response

```json
{
  "language": "gu",
  "transcript": "..."
}
```

### Common error responses

Invalid language:

```json
{"detail":"Invalid language code"}
```

Empty file:

```json
{"detail":"Empty audio file"}
```

Unhandled transcription failure:

```json
{"detail":"Transcription failed: ..."}
```

---

## 8. FastAPI built-in documentation

Because this app uses FastAPI, it automatically provides API docs.

Assuming backend is running on port `8000`:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI schema JSON: `http://127.0.0.1:8000/openapi.json`

### 8.1 What `/docs` gives you

`/docs` is the interactive Swagger UI.

You can:

- inspect all routes
- see expected parameters
- see request/response shapes
- test endpoints directly from the browser

For this project, `/docs` is the easiest way to manually test `POST /api/speech/transcribe`.

### 8.2 What `/redoc` gives you

`/redoc` shows the same API schema in a cleaner documentation layout.

Use it when:

- you want readable API docs
- you are explaining the API to another developer

### 8.3 What `/openapi.json` gives you

This is the machine-readable OpenAPI schema generated by FastAPI.

Use it when:

- generating client SDKs
- importing the API into API tools
- programmatically inspecting the backend contract

### 8.4 How FastAPI generates these docs here

FastAPI reads:

- route decorators like `@app.get(...)`, `@app.post(...)`
- parameter declarations like `File(...)` and `Form(...)`
- function signatures

From that it builds the OpenAPI schema automatically.

In this codebase, no custom response models are defined yet, so the docs are functional but fairly minimal.

---

## 9. How to run the full stack

## 9.1 Backend

Start from repo root:

```powershell
cd E:\VaaniDoc
.\.venv\Scripts\python.exe -m uvicorn backend.speech_api:app --reload
```

Backend URLs:

- API root host: `http://127.0.0.1:8000`
- health: `http://127.0.0.1:8000/health`
- docs: `http://127.0.0.1:8000/docs`

## 9.2 Frontend

```powershell
cd E:\VaaniDoc\frontend
npm run dev
```

Frontend URL:

- `http://127.0.0.1:5173`

## 9.3 Development interaction

Open the frontend in the browser, record speech, and the frontend will call the backend through the Vite proxy automatically.

---

## 10. Important codebase limitations and technical notes

## 10.1 README is ahead of the implementation

The README describes a larger product than what is currently implemented.

Currently implemented:

- browser recording
- WAV conversion
- upload API
- speech transcription

Not currently implemented in code:

- translation to English
- clinical information extraction
- urgency classification
- doctor dashboard
- session management
- structured intake JSON
- report/PDF generation

## 10.2 First request may be slow

Reason:

- ASR model is loaded lazily on the first transcription request

## 10.3 Model download may fail in restricted environments

Reason:

- `AutoModel.from_pretrained(...)` may need internet access if model weights are not already cached

## 10.4 Backend temp file strategy is simple but valid

Good:

- easy to understand
- safe cleanup in `finally`

Tradeoff:

- uses disk IO for every request
- not an in-memory streaming design

## 10.5 Frontend/backend language lists are duplicated

Current state:

- frontend has `SUPPORTED_LANGUAGES`
- backend has `LANGUAGE_CODES`

Risk:

- they can drift out of sync over time

Better future design:

- backend exposes supported languages
- frontend fetches the list dynamically

## 10.6 Current API contract has no typed response models

FastAPI supports Pydantic response models, but this code does not use them yet.

That means:

- docs still work
- schema is less explicit than it could be
- validation/documentation could be improved

## 10.7 CORS is fully open

This is fine for local development.

For deployment, it should be restricted to approved frontend origins.

---

## 11. Suggested next improvements

If you want this repo to be easier to maintain, these are the next practical improvements:

1. fix the README backend startup command so it matches the actual repo layout
2. add `pydantic` request/response models for clearer FastAPI docs
3. add a `/api/languages` endpoint so the frontend does not hardcode the language list
4. make `test_asr.py` use package-safe imports
5. add structured logging around upload, inference time, and errors
6. separate model-loading concerns from API code for cleaner backend architecture
7. implement the missing translation/clinical extraction pipeline if the README scope is intentional

---

## 12. Summary

The current codebase is a working speech-transcription prototype built from:

- React frontend for microphone capture
- Vite proxy for local dev integration
- FastAPI backend for upload handling
- PyTorch/Transformers ASR inference using AI4Bharat IndicConformer

The critical path is:

```text
Record audio -> convert to WAV -> upload to FastAPI -> save temp file ->
load audio tensor -> run ASR model -> return transcript JSON -> render UI
```

If you want this document extended, the next useful additions would be:

- sequence diagrams
- per-function explanation tables
- deployment guide
- dependency explanation
- error troubleshooting section
