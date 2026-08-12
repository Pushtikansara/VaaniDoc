export async function transcribeAudio(audioBlob, language) {
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.wav");
  formData.append("language", language);

  const response = await fetch("/api/speech/transcribe", {
    method: "POST",
    body: formData
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Transcription failed");
  }

  return data;
}
