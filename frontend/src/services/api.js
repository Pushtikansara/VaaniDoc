/**
 * VaaniDoc Frontend API Client Service
 * Connects frontend UI to backend FastAPI endpoints.
 */

export async function transcribeAudio(audioBlob, language) {
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.wav");
  formData.append("language", language);

  const response = await fetch("/api/speech/transcribe", {
    method: "POST",
    body: formData,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Transcription failed");
  }
  return data;
}

export async function submitVoiceIntake(audioBlob, language) {
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.wav");
  formData.append("language", language);

  const response = await fetch("/api/intake", {
    method: "POST",
    body: formData,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Voice intake processing failed");
  }
  return data;
}

export async function submitTextIntake(text, language = "gu") {
  const response = await fetch("/api/intake/text", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      text: text.trim(),
      language: language.trim().toLowerCase(),
    }),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Text intake processing failed");
  }
  return data;
}

export async function translateText(text, sourceLanguage) {
  const response = await fetch("/api/translate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      text: text.trim(),
      source_language: sourceLanguage.trim().toLowerCase(),
    }),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Translation failed");
  }
  return data;
}

export async function getReportData(sessionId) {
  const response = await fetch(`/api/report/${encodeURIComponent(sessionId)}/data`);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Failed to retrieve clinical report");
  }
  return data;
}

export async function updateReportData(sessionId, updates) {
  const response = await fetch(`/api/report/${encodeURIComponent(sessionId)}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(updates),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Failed to update clinical report");
  }
  return data;
}

export async function downloadReportPdf(sessionId) {
  const response = await fetch(`/api/report/${encodeURIComponent(sessionId)}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to download PDF report");
  }

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = `vaanidoc_report_${sessionId.slice(0, 8)}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

export async function endSession(sessionId) {
  const response = await fetch(`/api/session/end?session_id=${encodeURIComponent(sessionId)}`, {
    method: "POST",
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Failed to end session");
  }
  return data;
}
