import React from "react";
import { useApp } from "../context/AppContext";
import { SUPPORTED_LANGUAGES } from "../services/languages";
import { useNavigate, Navigate } from "react-router-dom";
import { Copy, Play, Pencil, RotateCcw, ArrowRight } from "lucide-react";

export default function Transcript() {
  const { transcript, language, fetchTranslation, startRecording } = useApp();
  const navigate = useNavigate();

  if (!transcript) {
    return <Navigate to="/intake" />;
  }

  const langLabel = SUPPORTED_LANGUAGES.find((l) => l.code === language)?.label || language;

  const handleConfirm = () => {
    fetchTranslation();
  };

  const handleReRecord = () => {
    navigate("/intake");
  };

  return (
    <div className="w-full max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="heading-page">Transcript</h1>
      </div>

      <div className="card w-full mb-8 lg:px-12 py-10 pt-8 rounded-xl shadow-sm border border-[var(--color-border)] relative overflow-hidden animate-slide-up">
        
        {/* Decorative Top Line */}
        <div className="absolute top-0 left-0 w-full h-1 bg-[var(--color-navy)]"></div>

        {/* Horizontal Stepper */}
        <div className="stepper-container">
          <div className="stepper-line"></div>
          <div className="stepper-progress" style={{ width: '20%' }}></div>
          <div className="step-item completed"><div className="step-circle">01</div><span className="step-label">Voice Input</span></div>
          <div className="step-item active"><div className="step-circle">02</div><span className="step-label">Transcript</span></div>
          <div className="step-item"><div className="step-circle">03</div><span className="step-label">Translation</span></div>
          <div className="step-item"><div className="step-circle">04</div><span className="step-label">Summary</span></div>
          <div className="step-item"><div className="step-circle">05</div><span className="step-label">Review</span></div>
          <div className="step-item"><div className="step-circle">06</div><span className="step-label">Report</span></div>
        </div>

        <div className="mt-8">
          
          <div className="flex justify-between items-center mb-4">
             <h3 className="text-[13px] font-bold text-[var(--color-navy)] uppercase tracking-wider">Patient Statement (Original)</h3>
             <span className="text-xs font-bold text-[var(--color-text-muted)] bg-[var(--color-bg-app)] px-3 py-1 rounded-md">{langLabel}</span>
          </div>

          {/* Transcript Box */}
          <div className="border border-[var(--color-border)] rounded-xl p-8 mb-6 bg-[var(--color-bg-app)] shadow-inner">
             <p className="text-xl md:text-2xl text-[var(--color-navy)] leading-relaxed font-semibold whitespace-pre-wrap">
               {transcript}
             </p>
          </div>

          {/* Minimal Audio Player Placeholder */}
          <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-6 mb-8">
             <div className="flex items-center gap-4 flex-1">
                <button className="bg-[var(--color-white)] border border-[var(--color-border)] rounded-full w-10 h-10 flex items-center justify-center cursor-pointer shadow-sm hover:border-[var(--color-navy)] transition-colors">
                   <Play size={18} className="text-[var(--color-navy)] ml-1" />
                </button>
                <div className="h-1.5 flex-1 max-w-[200px] bg-gray-200 rounded-full relative">
                   <div className="absolute top-0 left-0 h-1.5 bg-[var(--color-navy)] rounded-full w-[35%]"></div>
                </div>
                <span className="text-xs font-bold text-[var(--color-text-muted)] tracking-wider">00:00 / 00:12</span>
             </div>
             <button className="flex items-center gap-2 bg-transparent border-none cursor-pointer text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] hover:text-[var(--color-navy)] transition-colors">
                <Copy size={16} /> Copy
             </button>
          </div>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
             <div className="flex gap-4 w-full sm:w-auto">
               <button className="btn btn-secondary text-xs flex-1 sm:flex-none justify-center">
                 <Pencil size={14} className="text-[var(--color-text-muted)]" /> Edit
               </button>
               <button onClick={handleReRecord} className="btn btn-secondary text-xs flex-1 sm:flex-none justify-center">
                 <RotateCcw size={14} className="text-[var(--color-text-muted)]" /> Re-record
               </button>
             </div>
             <button onClick={handleConfirm} className="btn btn-primary text-sm px-8 shadow-sm w-full sm:w-auto justify-center">
               Confirm & Continue <ArrowRight size={16} className="ml-1" />
             </button>
          </div>

        </div>
      </div>
    </div>
  );
}
