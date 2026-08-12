from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from ai.speech.asr import LANGUAGE_CODES, transcribe


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = Path("backend") / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/speech/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form(...),
):
    language = language.strip().lower()
    if language not in LANGUAGE_CODES:
        raise HTTPException(status_code=400, detail="Invalid language code")

    if not audio.filename:
        raise HTTPException(status_code=400, detail="Missing audio file")

    suffix = Path(audio.filename).suffix or ".wav"
    temp_path = TEMP_DIR / f"{uuid4().hex}{suffix}"

    try:
        content = await audio.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty audio file")

        temp_path.write_bytes(content)
        transcript = transcribe(temp_path, language)
        return {"language": language, "transcript": transcript}
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc
    finally:
        await audio.close()
        temp_path.unlink(missing_ok=True)
