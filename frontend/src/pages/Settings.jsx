import React from "react";
import { Settings as SettingsIcon, Monitor, Globe, Mic, Shield, Server, CheckCircle2 } from "lucide-react";
import { useApp } from "../context/AppContext";

export default function Settings() {
  const { language } = useApp();

  return (
    <div className="w-full animate-fade-in max-w-5xl mx-auto pb-12">
      <div className="mb-10">
        <h1 className="heading-page mb-2 flex items-center gap-3">
          Settings
        </h1>
        <p className="text-sm font-medium text-[var(--color-text-muted)]">Manage your VaaniDoc application preferences</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-10 items-start">
        {/* Settings Sidebar Nav */}
        <div className="flex flex-col gap-2 relative md:sticky top-24">
           <button className="nav-link nav-link-active">
              <span className="nav-icon"><Monitor size={18} /></span> Appearance
           </button>
           <button className="nav-link">
              <span className="nav-icon"><Globe size={18} /></span> Language
           </button>
           <button className="nav-link">
              <span className="nav-icon"><Mic size={18} /></span> Audio & Devices
           </button>
           <button className="nav-link">
              <span className="nav-icon"><Shield size={18} /></span> Privacy
           </button>
           <button className="nav-link">
              <span className="nav-icon"><Server size={18} /></span> System Status
           </button>
        </div>

        {/* Settings Content Area */}
        <div className="md:col-span-3 flex flex-col gap-10">
           
           {/* Section 1 */}
           <section className="card border-[var(--color-border)] shadow-sm animate-slide-up p-8">
              <h2 className="text-lg font-bold text-[var(--color-navy)] flex items-center gap-2 mb-6 pb-4 border-b border-[var(--color-border)]">
                <Monitor size={20} className="text-[var(--color-brown)]" /> Appearance
              </h2>
              <div className="flex flex-col gap-6">
                 <div>
                   <label className="text-xs uppercase tracking-widest text-[var(--color-text-muted)] mb-4">Theme Preference</label>
                   <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                     <div className="border-2 border-[var(--color-navy)] bg-white p-6 rounded-xl cursor-pointer text-center shadow-sm relative overflow-hidden transition-transform transform hover:-translate-y-1">
                        <div className="w-full h-20 bg-[var(--color-bg-app)] rounded-md mb-4 flex flex-col gap-3 p-3 border border-[var(--color-border)]">
                           <div className="h-3 w-full bg-white rounded-sm"></div>
                           <div className="h-3 w-3/4 bg-white rounded-sm"></div>
                        </div>
                        <span className="text-sm font-bold text-[var(--color-navy)]">Light Mode</span>
                        <div className="absolute top-3 right-3 text-[var(--color-navy)]"><CheckCircle2 size={18}/></div>
                     </div>
                     <div className="border border-[var(--color-border)] bg-[#1E293B] p-6 rounded-xl cursor-not-allowed opacity-60 text-center">
                        <div className="w-full h-20 bg-[#0F172A] rounded-md mb-4 flex flex-col gap-3 p-3 border border-[#334155]">
                           <div className="h-3 w-full bg-[#1E293B] rounded-sm"></div>
                           <div className="h-3 w-3/4 bg-[#1E293B] rounded-sm"></div>
                        </div>
                        <span className="text-sm font-bold text-white">Dark Mode (Soon)</span>
                     </div>
                   </div>
                 </div>
              </div>
           </section>

           {/* Section 2 */}
           <section className="card border-[var(--color-border)] shadow-sm animate-slide-up stagger-1 p-8">
              <h2 className="text-lg font-bold text-[var(--color-navy)] flex items-center gap-2 mb-6 pb-4 border-b border-[var(--color-border)]">
                <Globe size={20} className="text-[var(--color-brown)]" /> Default Language Configuration
              </h2>
              <div>
                 <p className="text-sm text-[var(--color-text-muted)] mb-6 font-medium leading-relaxed">The selected language automatically applies to the speech recognition pipeline and dictionary initialization for Indic Trans2 translation.</p>
                 <div className="form-group mb-0 max-w-sm">
                    <label className="text-xs uppercase tracking-widest text-[var(--color-text-muted)] mb-3">Session Default</label>
                    <select className="font-semibold text-sm appearance-none bg-[var(--color-bg-app)]" value={language} disabled>
                      <option value={language}>{language.toUpperCase()} (Based on Session)</option>
                    </select>
                 </div>
              </div>
           </section>

           {/* Section 3 */}
           <section className="card border-[var(--color-border)] shadow-sm animate-slide-up stagger-2 p-8">
              <h2 className="text-lg font-bold text-[var(--color-navy)] flex items-center gap-2 mb-6 pb-4 border-b border-[var(--color-border)]">
                <Server size={20} className="text-[var(--color-brown)]" /> AI System Connectivity
              </h2>
              <div className="flex flex-col gap-4">
                 <div className="flex justify-between items-center p-5 bg-[var(--color-bg-app)] rounded-xl border border-[var(--color-border)]">
                    <div>
                       <p className="text-sm font-bold text-[var(--color-navy)] mb-1">IndicConformer Inference Engine</p>
                       <p className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider">WebSocket/REST ASR Context</p>
                    </div>
                    <span className="badge badge-low px-3 py-1">Operational</span>
                 </div>
                 <div className="flex justify-between items-center p-5 bg-[var(--color-bg-app)] rounded-xl border border-[var(--color-border)]">
                    <div>
                       <p className="text-sm font-bold text-[var(--color-navy)] mb-1">IndicTrans2 Pipeline</p>
                       <p className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Model deployed on backend</p>
                    </div>
                    <span className="badge badge-low px-3 py-1">Operational</span>
                 </div>
                 <div className="flex justify-between items-center p-5 bg-[var(--color-bg-app)] rounded-xl border border-[var(--color-border)]">
                    <div>
                       <p className="text-sm font-bold text-[var(--color-navy)] mb-1">Clinical Extraction Model</p>
                       <p className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Zero-shot clinical parse</p>
                    </div>
                    <span className="badge badge-low px-3 py-1">Operational</span>
                 </div>
              </div>
           </section>

        </div>
      </div>
    </div>
  );
}
