import React from "react";
import { useApp } from "../context/AppContext";
import { Navigate, Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";

export default function ClinicalSummary() {
  const { clinicalData, originalText, isProcessing } = useApp();

  if (!originalText && !isProcessing) {
    return <Navigate to="/intake" />;
  }

  const getUrgencyBadge = (urgency) => {
    const level = urgency?.toLowerCase() || "routine";
    if (level.includes("emergency") || level.includes("urgent") || level.includes("high")) {
      return <span className="badge badge-urg px-2.5 py-1">HIGH</span>;
    }
    if (level.includes("moderate")) {
      return <span className="badge badge-mod bg-orange-100 text-orange-700 px-2.5 py-1 rounded">MODERATE+</span>;
    }
    return <span className="badge badge-low bg-green-100 text-green-700 px-2.5 py-1 rounded">LOW</span>;
  };

  return (
    <div className="w-full max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="heading-page">Clinical Summary</h1>
      </div>

      <div className="card w-full mb-8 lg:px-12 py-10 pt-8 rounded-xl shadow-sm border border-[var(--color-border)] relative overflow-hidden animate-slide-up">
        <div className="absolute top-0 left-0 w-full h-1 bg-[var(--color-navy)]"></div>

        {/* Stepper */}
        <div className="stepper-container">
          <div className="stepper-line"></div>
          <div className="stepper-progress" style={{ width: '60%' }}></div>
          <div className="step-item completed"><div className="step-circle">01</div><span className="step-label">Voice Input</span></div>
          <div className="step-item completed"><div className="step-circle">02</div><span className="step-label">Transcript</span></div>
          <div className="step-item completed"><div className="step-circle">03</div><span className="step-label">Translation</span></div>
          <div className="step-item active"><div className="step-circle">04</div><span className="step-label">Summary</span></div>
          <div className="step-item"><div className="step-circle">05</div><span className="step-label">Review</span></div>
          <div className="step-item"><div className="step-circle">06</div><span className="step-label">Report</span></div>
        </div>

        <div className="mt-12">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-16 gap-y-10">
             
             {/* Left Column */}
             <div className="flex flex-col gap-10">
                <div>
                  <h3 className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-3">Chief Complaint</h3>
                  <p className="text-xl font-bold text-[var(--color-navy)] leading-tight">{clinicalData.chiefComplaint || "Not specified"}</p>
                </div>
                
                <div>
                  <h3 className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-3">Symptoms</h3>
                  {clinicalData.symptoms?.length > 0 ? (
                    <ul className="list-disc pl-5 space-y-2.5 text-sm font-semibold text-[var(--color-navy)]">
                      {clinicalData.symptoms.map((s, i) => <li key={i}>{s}</li>)}
                    </ul>
                  ) : <span className="text-sm font-medium text-[var(--color-text-muted)] italic">None detected</span>}
                </div>
             </div>

             {/* Right Column */}
             <div className="flex flex-col gap-8">
                <div className="grid grid-cols-2 gap-8">
                  <div>
                    <h3 className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">Duration</h3>
                    <p className="text-sm font-bold text-[var(--color-navy)]">{clinicalData.duration || "Not specified"}</p>
                  </div>

                  <div>
                    <h3 className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">Severity</h3>
                    <p className="text-sm font-bold text-[var(--color-navy)]">{clinicalData.severity || "Not specified"}</p>
                  </div>
                </div>

                <div>
                  <h3 className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-2">Urgency</h3>
                  {getUrgencyBadge(clinicalData.urgency)}
                </div>

                <div className="border-t border-[var(--color-border)] pt-8 mt-2">
                  <h3 className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-3">Associated Symptoms</h3>
                  <div className="flex flex-wrap gap-2">
                    {clinicalData.associatedSymptoms?.length > 0 ? 
                      clinicalData.associatedSymptoms.map((s,i) => <span key={i} className="px-3 py-1.5 bg-[var(--color-bg-app)] border border-[var(--color-border)] rounded-md text-xs font-semibold text-[var(--color-navy)]">{s}</span>) 
                      : <span className="text-sm font-medium text-[var(--color-text-muted)] italic">None specified</span>}
                  </div>
                </div>
             </div>
          </div>

          <div className="flex justify-end mt-12 border-t border-[var(--color-border)] pt-6">
             <Link to="/report" className="btn btn-primary px-8 shadow-sm">
               Continue to Review <ArrowRight size={16} className="ml-2" />
             </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
