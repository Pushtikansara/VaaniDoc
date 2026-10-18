import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { Search, Filter, ChevronDown } from "lucide-react";

export default function DoctorDashboard() {
  const { clinicalData, originalText, language } = useApp();
  const [searchTerm, setSearchTerm] = useState("");

  const hasData = Boolean(originalText);

  // Stats mirroring the UI
  const stats = {
    total: 12, // From image
    urgent: 3, // From image
    translations: 28, // From image
  };

  const getUrgencyConfig = (urgency) => {
    const level = urgency?.toLowerCase() || "routine";
    if (level.includes("emergency") || level.includes("urgent") || level.includes("high")) {
      return { class: "badge-urg bg-red-100 text-red-700", label: "High" };
    }
    if (level.includes("moderate")) {
      return { class: "badge-mod bg-orange-100 text-orange-700", label: "Moderate" };
    }
    return { class: "badge-low bg-green-100 text-green-700", label: "Low" };
  };

  return (
    <div className="w-full animate-fade-in pb-12">
      
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[var(--color-navy)] flex items-center gap-2">
          Doctor Dashboard
        </h1>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="card shadow-sm p-5 border border-[var(--color-border)]">
          <p className="text-xs font-bold text-[var(--color-navy)] mb-2">Today's Consultations</p>
          <p className="text-3xl font-bold text-[var(--color-navy)]">{hasData ? stats.total + 1 : stats.total}</p>
        </div>
        <div className="card shadow-sm p-5 border border-[var(--color-border)]">
          <p className="text-xs font-bold text-[var(--color-navy)] mb-2">Urgent Cases</p>
          <p className="text-3xl font-bold text-red-600">
            {clinicalData.urgency?.toLowerCase().includes("urgent") ? stats.urgent + 1 : stats.urgent}
          </p>
        </div>
        <div className="card shadow-sm p-5 border border-[var(--color-border)]">
          <p className="text-xs font-bold text-[var(--color-navy)] mb-2">Translations</p>
          <p className="text-3xl font-bold text-[#059669]">{hasData ? stats.translations + 1 : stats.translations}</p>
        </div>
        <div className="card shadow-sm p-5 border border-[var(--color-border)] flex flex-col justify-center">
          <p className="text-[10px] uppercase font-bold text-[var(--color-text-muted)] tracking-widest mb-1">System Status</p>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#059669]"></div>
            <p className="text-sm font-bold text-[#059669]">All Systems<br/>Operational</p>
          </div>
        </div>
      </div>

      {/* Table Section */}
      <div className="card shadow-sm border border-[var(--color-border)] p-0 overflow-hidden bg-white">
        
        {/* Filters */}
        <div className="p-4 border-b border-[var(--color-border)] flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" size={16} />
            <input 
              type="text" 
              placeholder="Search consultations..." 
              className="w-full pl-9 py-2 text-sm bg-[#FAFAF8] border-none rounded-md outline-none text-[var(--color-navy)] font-medium focus:ring-2 focus:ring-[var(--color-border)]"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex gap-4 w-full md:w-auto">
            <button className="flex items-center gap-2 text-xs font-bold text-[var(--color-text-muted)] bg-transparent border-none cursor-pointer">
              All Languages <ChevronDown size={14}/>
            </button>
            <button className="flex items-center gap-2 text-xs font-bold text-[var(--color-text-muted)] bg-transparent border-none cursor-pointer">
              All Status <ChevronDown size={14}/>
            </button>
          </div>
        </div>

        {/* Table itself */}
        <div className="table-container border-none shadow-none rounded-none rounded-b-xl">
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Patient ID</th>
                <th>Language</th>
                <th>Chief Complaint</th>
                <th>Urgency</th>
                <th>Time</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              
              {/* Dynamic Latest Row if available */}
              {hasData && (
                <tr className="cursor-pointer hover:bg-[#F8FAFC]">
                  <td>VD-2024-101</td>
                  <td className="capitalize">{language === 'gu' ? 'Gujarati' : language}</td>
                  <td>{clinicalData.chiefComplaint || "No complaint recorded"}</td>
                  <td>
                    <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${getUrgencyConfig(clinicalData.urgency).class}`}>
                       {getUrgencyConfig(clinicalData.urgency).label}
                    </span>
                  </td>
                  <td>{new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</td>
                  <td>
                    <span className="text-xs font-bold text-[#059669]">Completed</span>
                  </td>
                </tr>
              )}

              {/* Mock Row 1 */}
              <tr className="cursor-pointer hover:bg-[#F8FAFC]">
                <td>VD-2024-100</td>
                <td>Hindi</td>
                <td>Cough and cold</td>
                <td>
                  <span className="px-2 py-1 rounded text-[10px] font-bold uppercase bg-green-100 text-green-700">Low</span>
                </td>
                <td>09:45 AM</td>
                <td>
                  <span className="text-xs font-bold text-[#059669]">Completed</span>
                </td>
              </tr>

              {/* Mock Row 2 */}
              <tr className="cursor-pointer hover:bg-[#F8FAFC]">
                <td>VD-2024-099</td>
                <td>Marathi</td>
                <td>Stomach pain</td>
                <td>
                  <span className="px-2 py-1 rounded text-[10px] font-bold uppercase bg-red-100 text-red-700">High</span>
                </td>
                <td>09:20 AM</td>
                <td>
                  <span className="text-xs font-bold text-orange-600">Pending</span>
                </td>
              </tr>

              {/* Mock Row 3 */}
              <tr className="cursor-pointer hover:bg-[#F8FAFC]">
                <td>VD-2024-098</td>
                <td>Tamil</td>
                <td>Body ache</td>
                <td>
                  <span className="px-2 py-1 rounded text-[10px] font-bold uppercase bg-green-100 text-green-700">Low</span>
                </td>
                <td>08:50 AM</td>
                <td>
                  <span className="text-xs font-bold text-[#059669]">Completed</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
}
