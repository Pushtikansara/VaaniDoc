import React from "react";
import { Link, Navigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { SUPPORTED_LANGUAGES } from "../services/languages";
import { Printer, Download, Share2 } from "lucide-react";

export default function DoctorReport() {
  const { clinicalData, originalText, englishText, language } = useApp();

  if (!originalText) {
    return <Navigate to="/intake" />;
  }

  const langLabel = SUPPORTED_LANGUAGES.find((l) => l.code === language)?.label || language;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="w-full max-w-5xl mx-auto animate-fade-in pb-16">
      
      <div className="mb-6 flex justify-between items-center print:hidden">
        <h1 className="heading-page">Clinical Report</h1>
        <div className="text-sm font-bold text-[var(--color-navy)] flex flex-col items-end">
           <span className="text-xl">06</span>
           <span className="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">Report</span>
        </div>
      </div>

      <div className="card shadow-md border border-[var(--color-border)] p-8 md:p-12 print:border-none print:shadow-none print:p-0 page-break-inside-avoid animate-slide-up relative overflow-hidden">
        
        <div className="absolute top-0 left-0 w-full h-1 bg-[var(--color-navy)] print:hidden"></div>

        {/* Top Info Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-8 border-b border-[var(--color-border)] mb-8 mt-2">
           <div>
             <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] flex items-center gap-2 mb-2">
               Patient / Session ID
             </span>
             <p className="text-sm font-bold text-[var(--color-navy)]">VD-2024-{Math.floor(Math.random() * 1000)}</p>
           </div>
           <div>
             <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-2 block">Language</span>
             <p className="text-sm font-bold text-[var(--color-navy)]">{langLabel}</p>
           </div>
           <div className="md:text-right">
             <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-2 block">Date & Time</span>
             <p className="text-sm font-bold text-[var(--color-navy)]">{new Date().toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</p>
           </div>
        </div>

        {/* Transcripts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-10 pb-10 border-b border-[var(--color-border)]">
           <div className="bg-[var(--color-bg-app)] p-6 rounded-xl border border-[var(--color-border)]">
              <h4 className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)] mb-4">Patient Statement (Original)</h4>
              <p className="text-sm text-[var(--color-text-main)] leading-relaxed font-medium whitespace-pre-wrap">
                {originalText}
              </p>
           </div>
           <div className="bg-white p-6 rounded-xl border border-[var(--color-border)] shadow-sm">
              <h4 className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-navy)] mb-4">English Translation</h4>
              <p className="text-sm text-[var(--color-navy)] leading-relaxed font-semibold whitespace-pre-wrap">
                {englishText}
              </p>
           </div>
        </div>

        {/* Clinical Info */}
        <div className="mb-4">
           <h4 className="text-[11px] font-bold text-[var(--color-text-muted)] mb-8 uppercase tracking-widest flex items-center gap-2">
             Clinical Information
           </h4>
           
           <div className="grid grid-cols-2 md:grid-cols-5 gap-y-10 gap-x-6">
              <div className="col-span-2 md:col-span-1">
                 <p className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Chief Complaint</p>
                 <p className="text-sm font-bold text-[var(--color-navy)] leading-tight">{clinicalData.chiefComplaint || "None"}</p>
              </div>
              <div className="col-span-2 md:col-span-2">
                 <p className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Symptoms</p>
                 <p className="text-sm font-semibold text-[var(--color-navy)] leading-tight">
                    {clinicalData.symptoms?.length > 0 ? clinicalData.symptoms.join(", ") : "None detected"}
                    {clinicalData.associatedSymptoms?.length > 0 ? `, ${clinicalData.associatedSymptoms.join(", ")}` : ""}
                 </p>
              </div>
              <div>
                 <p className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Duration</p>
                 <p className="text-sm font-semibold text-[var(--color-navy)]">{clinicalData.duration || "-"}</p>
              </div>
              <div>
                 <p className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Severity</p>
                 <p className="text-sm font-semibold text-[var(--color-navy)]">{clinicalData.severity || "-"}</p>
              </div>
           </div>

           <div className="mt-8 pt-8 border-t border-[var(--color-border)] flex justify-between items-center">
              <div>
                 <p className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Urgency Assessment</p>
                 {clinicalData.urgency?.toLowerCase().includes("urgent") || clinicalData.urgency?.toLowerCase().includes("high") ? (
                    <span className="badge badge-urg px-4 py-1.5 shadow-sm">HIGH</span>
                 ) : clinicalData.urgency?.toLowerCase().includes("moderate") ? (
                    <span className="badge badge-mod bg-orange-100 text-orange-700 px-4 py-1.5 rounded shadow-sm">MODERATE</span>
                 ) : (
                    <span className="badge badge-low bg-green-100 text-green-700 px-4 py-1.5 rounded shadow-sm">ROUTINE</span>
                 )}
              </div>
              <div className="text-right">
                <p className="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-light)]">Electronically Generated</p>
                <p className="text-xs font-bold text-[var(--color-navy)] mt-1">VaaniDoc System</p>
              </div>
           </div>
        </div>
      </div>

      <div className="mt-8 flex justify-center gap-6 print:hidden">
         <button onClick={handlePrint} className="flex items-center gap-2 text-sm font-bold text-[var(--color-navy)] hover:text-[var(--color-brown)] transition-colors bg-transparent border-none cursor-pointer">
            <Printer size={18} /> Print Report
         </button>
         <button className="flex items-center gap-2 text-sm font-bold bg-[var(--color-brown)] text-white px-8 py-3 rounded-lg hover:bg-[#714D32] transition-colors border-none cursor-pointer shadow-md transform hover:-translate-y-0.5">
            <Download size={18} /> Download PDF
         </button>
         <button className="flex items-center gap-2 text-sm font-bold text-[var(--color-navy)] hover:text-[var(--color-brown)] transition-colors bg-transparent border-none cursor-pointer">
            <Share2 size={18} /> Share
         </button>
      </div>

    </div>
  );
}
