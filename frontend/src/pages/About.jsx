import React from "react";
import { Mic, FileText, Globe, Activity, ClipboardList, Stethoscope, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

export default function About() {
  const steps = [
    {
      icon: <Mic size={24} />,
      title: "Voice Input",
      desc: "Patient speaks naturally in their preferred Indian language while the doctor securely records the session."
    },
    {
      icon: <FileText size={24} />,
      title: "Speech Recognition",
      desc: "IndicConformer instantly transcribes the complex audio into a highly accurate, readable text format."
    },
    {
      icon: <Globe size={24} />,
      title: "Contextual Translation",
      desc: "IndicTrans2 accurately translates the dialect into a standardized English sentence, preserving medical context."
    },
    {
      icon: <Activity size={24} />,
      title: "Clinical Extraction",
      desc: "An AI model parses the translation to map Chief Complaints, Symptoms, Duration, Severity, and Triage Urgency."
    },
    {
      icon: <ClipboardList size={24} />,
      title: "Doctor Report",
      desc: "A standardized, printable EHR-ready document is generated immediately for the physician's final review."
    }
  ];

  return (
    <div className="w-full max-w-5xl mx-auto animate-fade-in relative pb-16">
      
      {/* Background Decor */}
      <div className="absolute top-10 right-0 w-[400px] h-[400px] bg-[var(--color-cream)] rounded-full opacity-40 mix-blend-multiply blur-[80px] pointer-events-none hidden md:block animate-float"></div>

      <div className="text-center max-w-3xl mx-auto mb-16 relative z-10 pt-4">
        <div className="inline-flex items-center justify-center p-4 bg-white rounded-2xl shadow-sm border border-[var(--color-border)] mb-6 animate-float">
          <Stethoscope size={40} className="text-[var(--color-navy)]" />
        </div>
        <h1 className="text-4xl md:text-5xl font-bold text-[var(--color-navy)] mb-6 tracking-tight">
          Pioneering AI in <span className="text-[var(--color-brown)]">Healthcare</span>
        </h1>
        <p className="text-lg text-[var(--color-text-muted)] leading-relaxed font-medium">
          VaaniDoc bridges the language gap in clinics across India, providing doctors with automated, accurate, and completely private AI-driven clinical notes from normal patient conversations.
        </p>
      </div>

      <div className="max-w-4xl mx-auto relative z-10">
        <h2 className="text-xl font-bold text-center text-[var(--color-navy)] mb-12 uppercase tracking-widest text-sm">Automated Pipeline</h2>
        
        <div className="relative">
          {/* Vertical Connecting Line */}
          <div className="hidden md:block absolute top-12 bottom-12 left-12 w-1 bg-gradient-to-b from-transparent via-[var(--color-navy)] to-transparent opacity-20"></div>

          <div className="flex flex-col gap-10">
            {steps.map((step, idx) => (
              <div key={idx} className="flex flex-col md:flex-row items-center gap-8 animate-slide-up" style={{animationDelay: `${idx * 0.1}s`}}>
                <div className="w-24 h-24 rounded-full bg-[var(--color-white)] shadow-md border-2 border-[var(--color-brown)] flex items-center justify-center text-[var(--color-navy)] z-10 shrink-0 transform transition-transform hover:scale-110 relative bg-white">
                  {step.icon}
                  <div className="absolute -right-3 -top-2 w-6 h-6 rounded-full bg-[var(--color-navy)] text-white flex items-center justify-center text-xs font-bold shadow-sm">
                    {idx + 1}
                  </div>
                </div>
                <div className="card w-full shadow-sm hover:shadow-md transition-shadow border-[var(--color-border)] p-6">
                  <h3 className="text-lg font-bold text-[var(--color-navy)] mb-2 uppercase tracking-wider">{step.title}</h3>
                  <p className="text-sm text-[var(--color-text-muted)] font-medium leading-relaxed">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-16 text-center animate-slide-up" style={{animationDelay: '0.6s'}}>
          <Link to="/intake" className="btn btn-primary px-10 py-4 shadow-md text-base group mt-4">
            Experience the Flow <ArrowRight size={18} className="ml-2 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </div>
    </div>
  );
}
