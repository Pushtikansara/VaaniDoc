import React, { useState, useEffect } from "react";
import { useApp } from "../context/AppContext";
import { SUPPORTED_LANGUAGES } from "../services/languages";
import { Mic, Square, Loader2, Globe, Pause, RotateCcw } from "lucide-react";

export default function PatientIntake() {
  const { language, setLanguage, isRecording, isProcessing, startRecording, stopRecording, error } = useApp();
  const [recordingTime, setRecordingTime] = useState(0);

  useEffect(() => {
    let interval;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } else {
      setRecordingTime(0);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div className="w-full max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="heading-page">New Consultation</h1>
      </div>

      <div className="card w-full mb-8 lg:px-12 py-10 pt-8 rounded-xl shadow-sm border border-[var(--color-border)] relative overflow-hidden">
        
        {/* Decorative Top Line */}
        <div className="absolute top-0 left-0 w-full h-1 bg-[var(--color-navy)]"></div>

        {/* Stepper */}
        <div className="stepper-container">
          <div className="stepper-line"></div>
          <div className="stepper-progress" style={{ width: '0%' }}></div>
          <div className="step-item active">
             <div className="step-circle">01</div>
             <span className="step-label">Voice Input</span>
          </div>
          <div className="step-item">
             <div className="step-circle">02</div>
             <span className="step-label">Transcript</span>
          </div>
          <div className="step-item">
             <div className="step-circle">03</div>
             <span className="step-label">Translation</span>
          </div>
          <div className="step-item">
             <div className="step-circle">04</div>
             <span className="step-label">Summary</span>
          </div>
          <div className="step-item">
             <div className="step-circle">05</div>
             <span className="step-label">Review</span>
          </div>
          <div className="step-item">
             <div className="step-circle">06</div>
             <span className="step-label">Report</span>
          </div>
        </div>

        <div className="max-w-2xl mx-auto text-center mt-12">
          <h2 className="text-2xl font-bold text-[var(--color-navy)] mb-2 tracking-tight">Patient Voice Input</h2>
          <p className="text-sm font-medium text-[var(--color-text-muted)] mb-8">Speak naturally in the patient's preferred language.</p>

          <div className="inline-block relative mb-16">
            <Globe size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] pointer-events-none"/>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              disabled={isRecording || isProcessing}
              className="appearance-none bg-white border border-[var(--color-border)] text-sm font-bold text-[var(--color-navy)] rounded-full py-2.5 pl-12 pr-10 shadow-sm cursor-pointer outline-none hover:border-[var(--color-brown)] focus:ring-[var(--color-navy)]"
            >
              {SUPPORTED_LANGUAGES.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.label}
                </option>
              ))}
            </select>
            <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
              <svg className="w-4 h-4 text-[var(--color-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
            </div>
          </div>

          <div className={`transition-all duration-300 ease-in-out ${isProcessing ? 'opacity-0 h-0 overflow-hidden' : 'opacity-100'}`}>
            {/* Microphone Recording Layout */}
            <div className={`mic-wrapper ${isRecording ? 'is-recording' : ''}`}>
               <div className="mic-ring mic-ring-1"></div>
               <div className="mic-ring mic-ring-2"></div>
               <button
                  className="mic-btn-large"
                  onClick={isRecording ? null : startRecording}
                  disabled={isRecording}
               >
                 <Mic size={36} />
               </button>
            </div>
            
            <div className="mt-8 mb-8 min-h-[32px]">
               {isRecording ? (
                 <div className="flex flex-col items-center">
                    <span className="text-lg font-bold text-[var(--color-navy)] tracking-wider mb-2">{formatTime(recordingTime)}</span>
                    <span className="text-[10px] font-bold text-red-600 uppercase tracking-[0.2em] flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-red-600 animate-pulse"></span> Recording Audio...
                    </span>
                 </div>
               ) : (
                 <p className="text-xs font-bold uppercase tracking-[0.1em] text-[var(--color-text-light)]">System Ready</p>
               )}
            </div>

            {error && (
               <div className="mb-6 text-xs font-semibold text-red-700 bg-red-50 p-3 rounded-lg border border-red-200 inline-block shadow-sm">
                 {error}
               </div>
            )}

            <div className="flex justify-center items-center gap-4 border-t border-[var(--color-border)] pt-8">
               <button className="btn btn-secondary text-xs" disabled={!isRecording}>
                  <Pause size={14} /> Pause
               </button>
               <button className={`btn shadow-md text-sm px-8 ${isRecording ? 'bg-red-600 text-white hover:bg-red-700 border-red-600' : 'btn-primary'}`} 
                       onClick={isRecording ? stopRecording : startRecording}>
                  {isRecording ? <><Square size={16} fill="currentColor" /> Stop Recording</> : "Start Session"}
               </button>
               <button className="btn btn-secondary text-xs" disabled={isRecording}>
                  <RotateCcw size={14} /> Record Again
               </button>
            </div>
          </div>

          {isProcessing && (
            <div className="flex flex-col items-center justify-center py-12 animate-fade-in">
              <div className="spinner mb-6 border-[4px]"></div>
              <p className="text-sm font-bold text-[var(--color-navy)] uppercase tracking-[0.1em]">Processing Audio Stream</p>
              <p className="text-xs font-semibold text-[var(--color-text-muted)] mt-2">Transcribing with IndicConformer ASR Engine</p>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
