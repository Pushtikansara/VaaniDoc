import { useEffect, useRef, useState } from "react";
import { transcribeAudio } from "./api";
import { mediaBlobToWav } from "./audio";
import { SUPPORTED_LANGUAGES, assertSupportedLanguages } from "./languages";
import TranscriptDisplay from "./TranscriptDisplay";
import DoctorReview from "./DoctorReview";

assertSupportedLanguages();

export default function App() {
  const [language, setLanguage] = useState("gu");
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [confirmationState, setConfirmationState] = useState<"idle" | "confirmed" | "edited" | "re_record">("idle");
  const [showEnglish, setShowEnglish] = useState(false);
  const [error, setError] = useState("");

  const [originalText, setOriginalText] = useState("");
  const [englishText, setEnglishText] = useState("");
  const [verificationStatus, setVerificationStatus] = useState<"consistent" | "needs_review">("consistent");
  const [warnings, setWarnings] = useState<Array<{ type: string; message: string }>>([]);

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
    setOriginalText("");
    setEnglishText("");
    setVerificationStatus("consistent");
    setWarnings([]);
    setConfirmationState("idle");
    setShowEnglish(false);

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
        setConfirmationState("idle");
        stopTracks();
      };

      recorder.onstop = async () => {
        setIsRecording(false);
        stopTracks();

        if (chunksRef.current.length === 0) {
          setError("No audio was recorded.");
          return;
        }

        // Step 1: Speech recognized - show the Indian-language transcript
        setIsProcessing(true);

        try {
          const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
          const wavBlob = await mediaBlobToWav(blob);
          const result = await transcribeAudio(wavBlob, language);
          const transcriptText = result.transcript || "";

          setTranscript(transcriptText);
          setOriginalText(transcriptText);
          // Immediately call backend to translate and check safety
          setConfirmationState("translating");
        } catch (err) {
          setError(err.message || "Transcription failed.");
          setIsProcessing(false);
          setConfirmationState("idle");
        }
      };

      recorder.start();
      setIsRecording(true);
    } catch (err) {
      setError(err.message || "Microphone access failed.");
      setIsRecording(false);
      setConfirmationState("idle");
      stopTracks();
    }
  };

  const stopRecording = () => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
  };

  const fetchTranslation = async () => {
    // Call the backend /api/translate endpoint
    try {
      const response = await fetch("/api/translate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: transcript,
          source_language: language,
        }),
      });

      if (!response.ok) {
        throw new Error(response.statusText || "Translation failed");
      }

      const data = await response.json();

      // Update state with translation and verification results
      setEnglishText(data.english_text || "");
      setVerificationStatus(data.verification.status || "consistent");
      setWarnings(data.verification.warnings || []);

      // Show English translation for doctor
      setShowEnglish(true);
      setConfirmationState("confirmed");
      setIsProcessing(false);
    } catch (err) {
      setError(err.message || "Translation failed.");
      setIsProcessing(false);
      setConfirmationState("idle");
    }
  };

  const confirmPatientStatement = () => {
    // Patient has confirmed their statement in their own language
    // Move to translation phase
    setConfirmationState("translating");
    // Fetch translation from backend
    fetchTranslation();
  };

  const editReEnter = () => {
    // Patient wants to edit or re-enter the statement
    setConfirmationState("edited");
    setTranscript("");
    setOriginalText("");
    setEnglishText("");
    setVerificationStatus("consistent");
    setWarnings([]);
    setShowEnglish(false);
    setIsProcessing(false);
  };

  const reRecord = () => {
    // Patient wants to re-record
    setConfirmationState("re_record");
    setTranscript("");
    setOriginalText("");
    setEnglishText("");
    setVerificationStatus("consistent");
    setWarnings([]);
    setShowEnglish(false);
    setIsProcessing(false);
    // Stop and restart recording
    stopRecording();
    setIsRecording(false);
    // Reset state for re-recording
    setTranscript("");
    setConfirmationState("idle");
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
            ))
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

        {/* Transcript display section */}
        {transcript && (
          <TranscriptDisplay
            originalText={originalText}
            englishText={englishText}
            verificationStatus={verificationStatus}
            warnings={warnings}
            onReview={() => {
              // Doctor can review in EHR system
              window.open(`/ehr-review?patient=${language}&text=${encodeURIComponent(transcript)}`, "_blank");
            }}
            onCopy={() => {
              // Copy the transcript to clipboard
              navigator.clipboard.writeText(`${originalText}\n${englishText}`);
              alert("Copied to clipboard");
            }}
          />
        )}

        {confirmationState === "idle" && transcript ? (
          <div>
            <p className="step">Step 1: Speech recognized</p>
            <p className="step">Step 2: Language detected</p>
            <p className="step">Step 3: Patient statement confirmed</p>
            <p>{transcript}</p>
            <div>
              <button onClick={confirmPatientStatement} className="btn">
                Confirm
              </button>
              <button onClick={editReEnter} className="btn">
                Edit/re-enter
              </button>
              <button onClick={reRecord} className="btn">
                Re-record
              </button>
            <DoctorReview
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
  </div>
          </div>
        ) : null}

        {confirmationState === "translating" ? (
          <div>
            <p className="step">Translating to English</p>
            <p className="step">Checking translation</p>
            <p>Please wait while the translation is processed...</p>
          </div>
        ) : null}

        {confirmationState === "confirmed" ? (
          <div>
            <p className="step">✓ Translation ready</p>
            <p>English translation is available for the doctor's reference.</p>
            <p className="text-sm text-gray-600">
              The original statement is always preserved above.
            </p>
          </div>
        ) : null}
      </section>
    </main>
  );
}