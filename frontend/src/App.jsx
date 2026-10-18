import { useEffect, useRef, useState } from "react";
import { transcribeAudio, submitTextIntake, getReportData, translateText } from "./services/api";
import { mediaBlobToWav } from "./services/audio";
import { SUPPORTED_LANGUAGES, assertSupportedLanguages, getBrowserSpeechLocale, getLanguageLabel } from "./services/languages";
import TranscriptDisplay from "./components/TranscriptDisplay";
import DoctorReview from "./components/DoctorReview";

assertSupportedLanguages();

export default function App() {
  const [activeTab, setActiveTab] = useState("voice"); // "voice" | "text" | "review"
  const [language, setLanguage] = useState("gu");
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState("");
  const [isSpeechRecognitionSupported, setIsSpeechRecognitionSupported] = useState(false);

  // Input states
  const [typedText, setTypedText] = useState("");
  const [transcript, setTranscript] = useState("");
  const [isEditingTranscript, setIsEditingTranscript] = useState(false);
  const [confirmationState, setConfirmationState] = useState("idle"); // "idle" | "translating" | "confirmed" | "edited"

  // Processed session states
  const [sessionId, setSessionId] = useState("");
  const [originalText, setOriginalText] = useState("");
  const [englishText, setEnglishText] = useState("");
  const [verificationStatus, setVerificationStatus] = useState("consistent");
  const [warnings, setWarnings] = useState([]);
  const [reportData, setReportData] = useState(null);

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    setIsSpeechRecognitionSupported(Boolean(SpeechRecognition));
    return () => {
      stopTracks();
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (_) {}
      }
    };
  }, []);

  const stopTracks = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  };

  const resetAllState = () => {
    setSessionId("");
    setTranscript("");
    setTypedText("");
    setOriginalText("");
    setEnglishText("");
    setVerificationStatus("consistent");
    setWarnings([]);
    setReportData(null);
    setConfirmationState("idle");
    setError("");
    setStatusMessage("");
    setActiveTab("voice");
  };

  // -------------------------------------------------------------------------
  // Voice Recording with Native Browser Speech Recognition & Audio Fallback
  // -------------------------------------------------------------------------

  const startRecording = async () => {
    setError("");
    setTranscript("");
    setOriginalText("");
    setEnglishText("");
    setVerificationStatus("consistent");
    setWarnings([]);
    setConfirmationState("idle");
    setIsEditingTranscript(false);

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    // Approach 1: Browser Native Multilingual Speech Recognition (Real Speech, Zero Static Texts)
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        const locale = getBrowserSpeechLocale(language);
        recognition.lang = locale;
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;

        let accumulatedFinal = "";

        recognition.onresult = (event) => {
          let interim = "";
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              accumulatedFinal += event.results[i][0].transcript + " ";
            } else {
              interim += event.results[i][0].transcript;
            }
          }
          const spoken = (accumulatedFinal + interim).trim();
          if (spoken) {
            setTranscript(spoken);
            setOriginalText(spoken);
          }
        };

        recognition.onerror = (event) => {
          console.warn("SpeechRecognition event:", event.error);
          if (event.error === "no-speech") return;
          if (event.error === "not-allowed") {
            setError("Microphone permission was denied. Please allow microphone access in your browser.");
          } else {
            setError(`Speech recognition note: ${event.error}`);
          }
          setIsRecording(false);
          setStatusMessage("");
        };

        recognition.onend = () => {
          setIsRecording(false);
          setStatusMessage("");
        };

        recognitionRef.current = recognition;
        recognition.start();
        setIsRecording(true);
        setStatusMessage(`🎙️ Listening in ${getLanguageLabel(language)} (${locale})... Speak symptoms clearly into your mic.`);
        return;
      } catch (err) {
        console.warn("Native SpeechRecognition start error, trying MediaRecorder fallback:", err);
      }
    }

    // Approach 2: MediaRecorder with Backend ASR Service Fallback
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Microphone audio is not supported in this browser. Please use Regional Text Input.");
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
        setError("Audio recording failed.");
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

        setIsProcessing(true);
        setStatusMessage("Transcribing patient speech via ASR...");

        try {
          const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
          const wavBlob = await mediaBlobToWav(blob);
          const result = await transcribeAudio(wavBlob, language);
          const transcriptText = result.transcript || "";

          setTranscript(transcriptText);
          setOriginalText(transcriptText);
          setConfirmationState("idle");
          setIsProcessing(false);
          setStatusMessage("");
        } catch (err) {
          setError(err.message || "Speech transcription failed.");
          setIsProcessing(false);
          setStatusMessage("");
        }
      };

      recorder.start();
      setIsRecording(true);
      setStatusMessage(`🎙️ Recording audio in ${getLanguageLabel(language)}... Click Stop when finished.`);
    } catch (err) {
      setError(err.message || "Microphone access failed.");
      setIsRecording(false);
      setConfirmationState("idle");
      stopTracks();
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (_) {}
      recognitionRef.current = null;
    }

    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
    setIsRecording(false);
    setStatusMessage("");
  };

  // -------------------------------------------------------------------------
  // Processing Pipeline (Voice Confirmed or Text Submitted)
  // -------------------------------------------------------------------------

  const processIntake = async (inputText) => {
    setIsProcessing(true);
    setError("");
    setStatusMessage("Translating and extracting clinical findings...");
    setConfirmationState("translating");

    try {
      const result = await submitTextIntake(inputText, language);
      setSessionId(result.session_id);
      setOriginalText(result.transcript || inputText);
      setEnglishText(result.english_text || "");
      setVerificationStatus(result.verification?.status || "consistent");
      setWarnings(result.verification?.warnings || []);

      // Fetch structured report data for Doctor Review
      const report = await getReportData(result.session_id);
      setReportData(report);
      setConfirmationState("confirmed");
      setActiveTab("review");
      setIsProcessing(false);
      setStatusMessage("");
    } catch (err) {
      setError(err.message || "Clinical intake processing failed.");
      setIsProcessing(false);
      setStatusMessage("");
      setConfirmationState("idle");
    }
  };

  const handleConfirmTranscript = () => {
    if (!transcript.trim()) {
      setError("Please speak or enter symptoms first.");
      return;
    }
    processIntake(transcript);
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (!typedText.trim()) {
      setError("Please enter patient symptoms before submitting.");
      return;
    }
    processIntake(typedText);
  };

  const handleRetranslate = async () => {
    if (!sessionId || !originalText) return;
    setIsProcessing(true);
    setStatusMessage("Re-translating patient statement...");
    try {
      const transResult = await translateText(originalText, language);
      setEnglishText(transResult.english_text);
      setVerificationStatus(transResult.verification?.status || "consistent");
      setWarnings(transResult.verification?.warnings || []);

      const updatedReport = await getReportData(sessionId);
      setReportData(updatedReport);
      setStatusMessage("");
    } catch (err) {
      setError(err.message || "Re-translation failed.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <main className="app-shell">
      <section className={`panel ${activeTab === "review" ? "panel-wide" : ""}`}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h1>VaaniDoc</h1>
            <p className="subtitle">Multilingual AI Health Intake &amp; Clinical Reporting for Rural Clinics</p>
          </div>
          <span style={{ fontSize: "0.8rem", color: "#64748b", background: "#f1f5f9", padding: "4px 8px", borderRadius: "4px", fontWeight: "600" }}>
            PS-03
          </span>
        </div>

        {/* Tab Navigation */}
        <div className="tab-nav">
          <button
            type="button"
            className={`tab-btn ${activeTab === "voice" ? "active" : ""}`}
            onClick={() => setActiveTab("voice")}
            disabled={isProcessing}
          >
            🎙️ Voice Input {isSpeechRecognitionSupported ? "(Live Speech)" : ""}
          </button>
          <button
            type="button"
            className={`tab-btn ${activeTab === "text" ? "active" : ""}`}
            onClick={() => setActiveTab("text")}
            disabled={isProcessing}
          >
            ✍️ Regional Text Input
          </button>
          {sessionId && (
            <button
              type="button"
              className={`tab-btn ${activeTab === "review" ? "active" : ""}`}
              onClick={() => setActiveTab("review")}
            >
              📋 Doctor Review ({reportData?.urgency?.level || "Active"})
            </button>
          )}
        </div>

        {/* Error and Status Displays */}
        {error && (
          <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "8px", padding: "12px", margin: "12px 0", color: "#991b1b" }}>
            <p style={{ margin: 0, fontWeight: "600", fontSize: "0.9rem" }}>⚠️ {error}</p>
            {(activeTab === "voice" || error.includes("401") || error.includes("HF_TOKEN") || error.includes("ASR") || error.includes("gated")) && (
              <div style={{ marginTop: "8px", fontSize: "0.85rem", color: "#7f1d1d" }}>
                <span>💡 You can immediately test the entire intake, clinical extraction, doctor dashboard, and PDF report using </span>
                <button
                  type="button"
                  onClick={() => { setError(""); setActiveTab("text"); }}
                  style={{ background: "#0284c7", color: "white", padding: "4px 8px", borderRadius: "4px", border: "none", cursor: "pointer", marginLeft: "4px", fontSize: "0.85rem" }}
                >
                  ✍️ Regional Text Input
                </button>
              </div>
            )}
          </div>
        )}
        {isProcessing && <p className="status">⏳ {statusMessage || "Processing intake..."}</p>}

        {/* -----------------------------------------------------------------
            TAB 1: Voice Input
        ----------------------------------------------------------------- */}
        {activeTab === "voice" && (
          <div>
            <label className="field">
              <span>Patient Regional Language</span>
              <select
                value={language}
                onChange={(event) => setLanguage(event.target.value)}
                disabled={isRecording || isProcessing}
              >
                {SUPPORTED_LANGUAGES.map((item) => (
                  <option key={item.code} value={item.code}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>

            <div style={{ display: "flex", gap: "8px", alignItems: "center", margin: "12px 0" }}>
              <button
                type="button"
                className={isRecording ? "recording" : ""}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isProcessing}
                style={{ flex: 1, minHeight: "44px", fontSize: "1rem", fontWeight: "700" }}
              >
                {isRecording ? "⏹️ Stop Recording" : "🎙️ Start Voice Recording"}
              </button>
            </div>

            {isRecording && (
              <div style={{ background: "#fef2f2", border: "1px solid #fecaca", padding: "10px", borderRadius: "6px", marginBottom: "12px", textAlign: "center" }}>
                <span style={{ color: "#dc2626", fontWeight: "700" }}>🔴 Recording Active:</span>{" "}
                <span style={{ color: "#7f1d1d" }}>Speak into your microphone in {getLanguageLabel(language)}. What you speak will appear below in real-time.</span>
              </div>
            )}

            <div style={{ marginTop: "10px", marginBottom: "14px", background: "#f8fafc", padding: "10px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "0.78rem", color: "#64748b", fontWeight: "700", marginBottom: "6px" }}>
                🎙️ Quick Test Presets (Loads spoken text directly for instant testing):
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                <button
                  type="button"
                  onClick={() => { setLanguage("gu"); setTranscript("અને હૃદયમાં દુખાવો થાય છે"); setOriginalText("અને હૃદયમાં દુખાવો થાય છે"); }}
                  style={{ background: "#fee2e2", border: "1px solid #f87171", color: "#991b1b", borderRadius: "4px", padding: "4px 8px", fontSize: "0.78rem", cursor: "pointer", fontWeight: "700" }}
                >
                  🔴 Gujarati Emergency: અને હૃદયમાં દુખાવો થાય છે
                </button>
                <button
                  type="button"
                  onClick={() => { setLanguage("gu"); setTranscript("મને બે દિવસથી ખૂબ તાવ અને માથાનો દુખાવો છે"); setOriginalText("મને બે દિવસથી ખૂબ તાવ અને માથાનો દુખાવો છે"); }}
                  style={{ background: "#fff", border: "1px solid #cbd5e1", borderRadius: "4px", padding: "4px 8px", fontSize: "0.78rem", cursor: "pointer" }}
                >
                  🟢 Gujarati Routine: તાવ અને માથાનો દુખાવો
                </button>
                <button
                  type="button"
                  onClick={() => { setLanguage("hi"); setTranscript("मुझे तीन दिन से सीने में तेज दर्द है और सांस लेने में तकलीफ है"); setOriginalText("मुझे तीन दिन से सीने में तेज दर्द है और सांस लेने में तकलीफ है"); }}
                  style={{ background: "#fee2e2", border: "1px solid #f87171", color: "#991b1b", borderRadius: "4px", padding: "4px 8px", fontSize: "0.78rem", cursor: "pointer", fontWeight: "700" }}
                >
                  🔴 Hindi Emergency: सीने में दर्द
                </button>
              </div>
            </div>

            {/* Recognized Live Speech Box */}
            {transcript && (
              <div className="step-box" style={{ background: "#f8fafc", border: "1px solid #cbd5e1", borderRadius: "8px", padding: "14px", marginTop: "12px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <h3 style={{ fontSize: "0.95rem", fontWeight: "700", color: "#334155", margin: 0 }}>
                    Recognized Speech ({getLanguageLabel(language)}):
                  </h3>
                  <button
                    type="button"
                    onClick={() => setIsEditingTranscript(!isEditingTranscript)}
                    style={{ background: "none", border: "none", color: "#0284c7", cursor: "pointer", fontSize: "0.8rem", textDecoration: "underline" }}
                  >
                    {isEditingTranscript ? "Done Editing" : "✏️ Edit Transcript"}
                  </button>
                </div>

                {isEditingTranscript ? (
                  <textarea
                    rows={3}
                    value={transcript}
                    onChange={(e) => {
                      setTranscript(e.target.value);
                      setOriginalText(e.target.value);
                    }}
                    style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #0284c7", fontSize: "1rem", marginBottom: "10px" }}
                  />
                ) : (
                  <p style={{ fontSize: "1.05rem", color: "#0f172a", marginBottom: "12px", background: "#fff", padding: "10px", borderRadius: "6px", border: "1px solid #cbd5e1", lineHeight: "1.5" }}>
                    {transcript}
                  </p>
                )}

                {confirmationState === "idle" && (
                  <div>
                    <p style={{ fontSize: "0.85rem", color: "#475569", marginBottom: "8px" }}>
                      Click below to translate and generate the clinical intake report:
                    </p>
                    <div style={{ display: "flex", gap: "8px" }}>
                      <button
                        type="button"
                        onClick={handleConfirmTranscript}
                        disabled={isProcessing}
                        style={{ background: "#15803d", color: "#fff", margin: 0, minHeight: "38px", flex: 1, fontWeight: "700" }}
                      >
                        ✓ Confirm &amp; Process Clinical Intake
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setTranscript("");
                          setOriginalText("");
                          setIsEditingTranscript(false);
                        }}
                        disabled={isProcessing}
                        style={{ background: "#f1f5f9", color: "#334155", border: "1px solid #cbd5e1", margin: 0, minHeight: "38px" }}
                      >
                        Clear
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* -----------------------------------------------------------------
            TAB 2: Regional Text Input
        ----------------------------------------------------------------- */}
        {activeTab === "text" && (
          <div>
            <form onSubmit={handleTextSubmit}>
              <label className="field">
                <span>Patient Language</span>
                <select
                  value={language}
                  onChange={(event) => setLanguage(event.target.value)}
                  disabled={isProcessing}
                >
                  {SUPPORTED_LANGUAGES.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span>Patient Symptoms &amp; Clinical Information ({getLanguageLabel(language)})</span>
                <textarea
                  rows={4}
                  placeholder={`Type symptoms here in ${getLanguageLabel(language)} (e.g. મને બે દિવસથી તાવ અને માથાનો દુખાવો છે)...`}
                  value={typedText}
                  onChange={(e) => setTypedText(e.target.value)}
                  disabled={isProcessing}
                  style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #cbd5e1", fontSize: "0.95rem" }}
                />
              </label>

              <button
                type="submit"
                disabled={isProcessing || !typedText.trim()}
                style={{ width: "100%", background: "#0284c7", color: "white", padding: "10px", borderRadius: "6px", fontWeight: "700", border: "none", cursor: "pointer", fontSize: "1rem" }}
              >
                {isProcessing ? "Processing..." : "Process Intake Form"}
              </button>
            </form>

            <div style={{ marginTop: "16px", background: "#f8fafc", padding: "12px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: "700", marginBottom: "6px" }}>
                Sample Regional Prompts for Instant Testing:
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                <button
                  type="button"
                  onClick={() => { setLanguage("gu"); setTypedText("અને હૃદયમાં દુખાવો થાય છે"); }}
                  style={{ background: "#fee2e2", border: "1px solid #f87171", color: "#991b1b", borderRadius: "4px", padding: "4px 8px", fontSize: "0.8rem", cursor: "pointer", fontWeight: "700" }}
                >
                  🔴 Gujarati Emergency: અને હૃદયમાં દુખાવો થાય છે
                </button>
                <button
                  type="button"
                  onClick={() => { setLanguage("gu"); setTypedText("મને બે દિવસથી ખૂબ તાવ અને માથાનો દુખાવો છે"); }}
                  style={{ background: "#fff", border: "1px solid #cbd5e1", borderRadius: "4px", padding: "4px 8px", fontSize: "0.8rem", cursor: "pointer" }}
                >
                  🟢 Gujarati Routine: તાવ અને માથાનો દુખાવો
                </button>
                <button
                  type="button"
                  onClick={() => { setLanguage("hi"); setTypedText("मुझे तीन दिन से सीने में तेज दर्द है और सांस लेने में तकलीफ है"); }}
                  style={{ background: "#fee2e2", border: "1px solid #f87171", color: "#991b1b", borderRadius: "4px", padding: "4px 8px", fontSize: "0.8rem", cursor: "pointer", fontWeight: "700" }}
                >
                  🔴 Hindi Emergency: सीने में दर्द
                </button>
                <button
                  type="button"
                  onClick={() => { setLanguage("mr"); setTypedText("मला दोन दिवसांपासून ताप आणि खोकला आहे"); }}
                  style={{ background: "#fff", border: "1px solid #cbd5e1", borderRadius: "4px", padding: "4px 8px", fontSize: "0.8rem", cursor: "pointer" }}
                >
                  Marathi: ताप आणि खोकला
                </button>
                <button
                  type="button"
                  onClick={() => { setLanguage("ta"); setTypedText("எனக்கு இரண்டு நாட்களாக கடுமையான காய்ச்சல் உள்ளது"); }}
                  style={{ background: "#fff", border: "1px solid #cbd5e1", borderRadius: "4px", padding: "4px 8px", fontSize: "0.8rem", cursor: "pointer" }}
                >
                  Tamil: கடுமையான காய்ச்சல்
                </button>
              </div>
            </div>
          </div>
        )}

        {/* -----------------------------------------------------------------
            TAB 3: Doctor Review & Intake Report Dashboard
        ----------------------------------------------------------------- */}
        {activeTab === "review" && (
          <div>
            {sessionId && reportData ? (
              <DoctorReview
                sessionId={sessionId}
                reportData={reportData}
                onReportUpdated={(updated) => setReportData(updated)}
                onSessionEnd={resetAllState}
                onRetranslate={handleRetranslate}
              />
            ) : (
              <div style={{ textAlign: "center", padding: "2rem", color: "#64748b" }}>
                <p>No active intake report session found.</p>
                <button
                  type="button"
                  onClick={() => setActiveTab("voice")}
                  style={{ background: "#0284c7", color: "white", padding: "8px 16px", borderRadius: "6px", border: "none", cursor: "pointer" }}
                >
                  Start New Intake
                </button>
              </div>
            )}
          </div>
        )}
      </section>
    </main>
import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppProvider } from "./context/AppContext";
import Layout from "./components/Layout";

// Pages
import Landing from "./pages/Landing";
import PatientIntake from "./pages/PatientIntake";
import Transcript from "./pages/Transcript";
import Translation from "./pages/Translation";
import ClinicalSummary from "./pages/ClinicalSummary";
import DoctorDashboard from "./pages/DoctorDashboard";
import DoctorReport from "./pages/DoctorReport";
import Settings from "./pages/Settings";
import About from "./pages/About";

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/intake" element={<PatientIntake />} />
            <Route path="/transcript" element={<Transcript />} />
            <Route path="/translation" element={<Translation />} />
            <Route path="/summary" element={<ClinicalSummary />} />
            <Route path="/dashboard" element={<DoctorDashboard />} />
            <Route path="/report" element={<DoctorReport />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </Layout>
      </AppProvider>
    </BrowserRouter>
  );
}
