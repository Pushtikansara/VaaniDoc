from pathlib import Path

import soundfile as sf
import torch
import torchaudio


SAMPLE_RATE = 16000


def load_audio(audio_path):
    """Load audio as mono 16 kHz tensor shaped (channels, samples)."""
    path = Path(audio_path)
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(f"Audio file not found or empty: {path}")

    data, sample_rate = sf.read(str(path), dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)

    wav = torch.from_numpy(data).unsqueeze(0)
    if sample_rate != SAMPLE_RATE:
        wav = torchaudio.transforms.Resample(sample_rate, SAMPLE_RATE)(wav)

    return wav
