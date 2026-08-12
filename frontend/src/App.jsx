import { useEffect, useRef, useState } from "react";
import { transcribeAudio } from "./api";
import { mediaBlobToWav } from "./audio";
import { SUPPORTED_LANGUAGES, assertSupportedLanguages } from "./languages";

assertSupportedLanguages();

export default function App() {
  const [language, setLanguage] = useState("gu");
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState("");

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);

  useEffect(() => {
    return () => {
      stopTracks();
    };
  }, []);

  const stopTracks = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  };

  const startRecording = async () => {
    setError("");
    setTranscript("");

    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Microphone is not supported in this browser.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);

      streamRef.current = stream;
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        setError("Recording failed.");
        setIsRecording(false);
        stopTracks();
      };

      recorder.onstop = async () => {
        setIsRecording(false);
        stopTracks();

        if (chunksRef.current.length === 0) {
          setError("No audio was recorded.");
          return;
        }

        setIsProcessing(true);

        try {
          const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
          const wavBlob = await mediaBlobToWav(blob);
          const result = await transcribeAudio(wavBlob, language);
          setTranscript(result.transcript || "");
        } catch (err) {
          setError(err.message || "Transcription failed.");
        } finally {
          setIsProcessing(false);
          chunksRef.current = [];
        }
      };

      recorder.start();
      setIsRecording(true);
    } catch (err) {
      setError(err.message || "Microphone access failed.");
      stopTracks();
    }
  };

  const stopRecording = () => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
  };

  return (
    <main className="app-shell">
      <section className="panel">
        <h1>Patient Voice Input</h1>
        <p className="subtitle">Record speech and view the transcript.</p>

        <label className="field">
          <span>Language</span>
          <select value={language} onChange={(event) => setLanguage(event.target.value)} disabled={isRecording || isProcessing}>
            {SUPPORTED_LANGUAGES.map((item) => (
              <option key={item.code} value={item.code}>
                {item.label}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          className={isRecording ? "recording" : ""}
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isProcessing}
        >
          {isRecording ? "Stop Recording" : "Start Recording"}
        </button>

        {isProcessing ? <p className="status">Processing...</p> : null}
        {error ? <p className="error">{error}</p> : null}

        <div className="result">
          <h2>Transcript</h2>
          <p>{transcript || "Your transcript will appear here."}</p>
        </div>
      </section>
    </main>
  );
}
