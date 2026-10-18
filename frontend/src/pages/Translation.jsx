import React from "react";
import { useApp } from "../context/AppContext";
import { SUPPORTED_LANGUAGES } from "../services/languages";
import { Navigate, Link } from "react-router-dom";
import { ArrowRight, CheckCircle2 } from "lucide-react";

export default function Translation() {
  const { originalText, englishText, language, verificationStatus, isProcessing } = useApp();

  if (!originalText && !isProcessing) {
    return <Navigate to="/intake" />;
  }

  const langLabel = SUPPORTED_LANGUAGES.find((l) => l.code === language)?.label || language;
  const isVerified = verificationStatus === "consistent";

  if (isProcessing) {
    return (
      <div className="w-full flex-1 flex flex-col items-center justify-center py-32 animate-fade-in">
        <div className="spinner border-[4px] mb-6"></div>
        <p className="text-xl font-bold text-[var(--color-navy)] mb-2">Translating to English...</p>
        <p className="text-xs font-bold text-[var(--color-text-muted)] tracking-widest uppercase">Powered by IndicTrans2</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="heading-page">Translation</h1>
      </div>

      <div className="card w-full mb-8 lg:px-12 py-10 pt-8 rounded-xl shadow-sm border border-[var(--color-border)] relative overflow-hidden animate-slide-up">
        <div className="absolute top-0 left-0 w-full h-1 bg-[var(--color-navy)]"></div>

        {/* Stepper */}
        <div className="stepper-container">
          <div className="stepper-line"></div>
          <div className="stepper-progress" style={{ width: '40%' }}></div>
          <div className="step-item completed"><div className="step-circle">01</div><span className="step-label">Voice Input</span></div>
          <div className="step-item completed"><div className="step-circle">02</div><span className="step-label">Transcript</span></div>
          <div className="step-item active"><div className="step-circle">03</div><span className="step-label">Translation</span></div>
          <div className="step-item"><div className="step-circle">04</div><span className="step-label">Summary</span></div>
          <div className="step-item"><div className="step-circle">05</div><span className="step-label">Review</span></div>
          <div className="step-item"><div className="step-circle">06</div><span className="step-label">Report</span></div>
        </div>

        <div className="mt-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative items-stretch mb-8">
             
             {/* Center Arrow Connector */}
             <div className="hidden md:flex absolute top-[45%] left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 w-9 h-9 rounded-full bg-[var(--color-navy)] text-white items-center justify-center shadow-md">
                <ArrowRight size={18} />
             </div>

             {/* Source Side */}
             <div className="border border-[var(--color-border)] rounded-xl p-8 bg-[var(--color-bg-app)] min-h-[260px]">
                <h3 className="text-xs font-bold text-[var(--color-navy)] mb-4 pb-4 border-b border-[var(--color-border)] uppercase tracking-wider flex justify-between">
                   Original ({langLabel})
                </h3>
                <p className="text-base text-[var(--color-text-muted)] font-medium leading-relaxed whitespace-pre-wrap">
                  {originalText}
                </p>
             </div>

             {/* Translation Side */}
             <div className="border border-[var(--color-navy)] shadow-[0_0_0_1px_rgba(10,41,71,0.1)] rounded-xl p-8 bg-white min-h-[260px] relative">
                <h3 className="text-xs font-bold text-[var(--color-navy)] mb-4 pb-4 border-b border-[var(--color-border)] uppercase tracking-wider">
                   English Translation
                </h3>
                <p className="text-lg text-[var(--color-navy)] font-bold leading-relaxed whitespace-pre-wrap">
                  {englishText}
                </p>
             </div>
          </div>

          {/* Status & Actions */}
          <div className="flex flex-col sm:flex-row justify-between items-center bg-[var(--color-bg-app)] p-5 rounded-xl border border-[var(--color-border)] mb-8">
             <div className="flex items-center gap-3">
               <span className="text-xs font-bold text-[var(--color-navy)] uppercase tracking-wider">Status:</span>
               {isVerified ? (
                 <span className="badge badge-low border border-[#A7F3D0] px-3"><CheckCircle2 size={12}/> Verified</span>
               ) : (
                 <span className="badge badge-urg">Requires Review</span>
               )}
             </div>
             <div className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mt-4 sm:mt-0">
                Powered by IndicTrans2
             </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-[var(--color-border)]">
             <Link to="/summary" className="btn btn-primary px-8 shadow-sm">
               Extract Clinical Data <ArrowRight size={16} className="ml-2" />
             </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
