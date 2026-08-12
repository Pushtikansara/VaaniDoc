import sys
from pathlib import Path

from asr import transcribe


def main():
    audio_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "audio" / "gujarati_test.wav"
    language = sys.argv[2] if len(sys.argv) > 2 else "gu"

    if not audio_path.exists() or audio_path.stat().st_size == 0:
        raise SystemExit(f"Sample WAV not found or empty: {audio_path}")

    text = transcribe(audio_path, language)
    print(text)


if __name__ == "__main__":
    main()
