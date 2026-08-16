import React, { createContext, useContext, useState, useRef } from "react";
import { transcribeAudio } from "../services/api";
import { mediaBlobToWav } from "../services/audio";
import { useNavigate } from "react-router-dom";

const AppContext = createContext();

export const useApp = () => useContext(AppContext);

export const AppProvider = ({ children }) => {
  const [language, setLanguage] = useState("gu");
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [originalText, setOriginalText] = useState("");
  const [englishText, setEnglishText] = useState("");
  const [verificationStatus, setVerificationStatus] = useState("consistent");
  const [warnings, setWarnings] = useState([]);
  const [error, setError] = useState("");

  const [clinicalData, setClinicalData] = useState({
    chiefComplaint: "",
    symptoms: [],
    duration: "",
    severity: "",
    bodyLocation: "",
    associatedSymptoms: [],
    urgency: "routine",
  });

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);

  const navigate = useNavigate();

  const stopTracks = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  };

  const resetAll = () => {
    setError("");
    setTranscript("");
    setOriginalText("");
    setEnglishText("");
    setVerificationStatus("consistent");
    setWarnings([]);
    setClinicalData({
      chiefComplaint: "",
      symptoms: [],
      duration: "",
      severity: "",
      bodyLocation: "",
      associatedSymptoms: [],
      urgency: "routine",
    });
  };

  const startRecording = async () => {
    resetAll();

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
          const blob = new Blob(chunksRef.current, {
            type: recorder.mimeType || "audio/webm",
          });
          const wavBlob = await mediaBlobToWav(blob);
          const result = await transcribeAudio(wavBlob, language);
          const transcriptText = result.transcript || "";

          setTranscript(transcriptText);
          setOriginalText(transcriptText);
          setIsProcessing(false);
          // Navigate to Transcript page
          navigate("/transcript");
        } catch (err) {
          setError(err.message || "Transcription failed.");
          setIsProcessing(false);
        }
      };

      recorder.start();
      setIsRecording(true);
    } catch (err) {
      setError(err.message || "Microphone access failed.");
      setIsRecording(false);
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
    setIsProcessing(true);
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

      setEnglishText(data.english_text || "");
      setVerificationStatus(data.verification?.status || "consistent");
      setWarnings(data.verification?.warnings || []);

      // Extract clinical info immediately
      if (data.english_text) {
        try {
          const clinicalResponse = await fetch("/api/clinical/extract", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              text: data.english_text,
            }),
          });

          if (clinicalResponse.ok) {
            const extracted = await clinicalResponse.json();
            setClinicalData({
              chiefComplaint: extracted.chief_complaint || "",
              symptoms: extracted.symptoms || [],
              duration: extracted.duration || "",
              severity: extracted.severity || "",
              bodyLocation: extracted.body_location || "",
              associatedSymptoms: extracted.associated_symptoms || [],
              urgency: extracted.urgency || "routine",
            });
          }
        } catch (clinicalError) {
          console.error("Clinical extraction failed:", clinicalError);
        }
      }
      setIsProcessing(false);
      navigate("/translation");
    } catch (err) {
      setError(err.message || "Translation failed.");
      setIsProcessing(false);
    }
  };

  const value = {
    language,
    setLanguage,
    isRecording,
    isProcessing,
    transcript,
    originalText,
    englishText,
    verificationStatus,
    warnings,
    error,
    setError,
    clinicalData,
    setClinicalData,
    startRecording,
    stopRecording,
    fetchTranslation,
    resetAll
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
