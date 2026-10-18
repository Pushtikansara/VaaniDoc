import { useState } from "react";
import { updateReportData, downloadReportPdf, endSession } from "../services/api";

export default function DoctorReview({
  sessionId,
  reportData,
  onReportUpdated,
  onSessionEnd,
  onRetranslate,
}) {
  const [report, setReport] = useState(reportData);
  const [isEditing, setIsEditing] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showWarnings, setShowWarnings] = useState(false);
  const [actionMessage, setActionMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const findings = report?.clinical_findings || {};
  const vitals = report?.vital_signs || {};
  const urgencyInfo = report?.urgency || { level: "ROUTINE", reason: "", target_response: "Standard Outpatient Queue" };
  const verification = report?.translation_verification || { status: "consistent", warnings: [] };
  const hasWarnings = verification.warnings && verification.warnings.length > 0;
  const isFinalized = report?.status === "FINALIZED";

  // Edit form state
  const [editForm, setEditForm] = useState({
    chief_complaint: findings.chief_complaint || "",
    symptoms: (findings.symptoms || []).join(", "),
    negated_findings: (findings.negated_findings || []).join(", "),
    duration: findings.duration || "",
    severity: findings.severity || "",
    body_location: findings.body_location || "",
    possible_category: findings.possible_category || "",
    urgency: urgencyInfo.level || "ROUTINE",
    doctor_notes: report?.doctor_notes || "",
    // Patient info
    patient_name: report?.patient_info?.name || "Walk-in Patient",
    patient_age: report?.patient_info?.age || "Adult",
    patient_gender: report?.patient_info?.gender || "Not Specified",
    patient_contact: report?.patient_info?.contact || "Rural Center",
    // Vitals
    bp_systolic: vitals.bp_systolic || "",
    bp_diastolic: vitals.bp_diastolic || "",
    pulse_bpm: vitals.pulse_bpm || "",
    temperature_f: vitals.temperature_f || "",
    spo2_percent: vitals.spo2_percent || "",
    respiratory_rate: vitals.respiratory_rate || "",
    blood_glucose: vitals.blood_glucose || "",
    // Doctor info
    doctor_name: report?.attending_doctor?.doctor_name || "Attending Medical Officer",
    doctor_license: report?.attending_doctor?.license_number || "REG-MCI-VALIDATED",
    // Care plan
    care_follow_up: report?.care_plan?.follow_up || "Review in OPD after 3 days.",
    care_precautions: report?.care_plan?.return_precautions || "Seek emergency care immediately if breathing difficulty, chest pain, or high fever persists.",
  });

  // Prescriptions state
  const [prescriptions, setPrescriptions] = useState(report?.prescriptions || []);
  const [newMed, setNewMed] = useState({ name: "", dosage: "", frequency: "TDS", duration: "3 days", instructions: "After food" });

  // Diagnostic orders state
  const [diagnosticOrders, setDiagnosticOrders] = useState(report?.diagnostic_orders || []);
  const [newTest, setNewTest] = useState({ test_name: "", urgency: "Routine" });

  // Urgency styling map
  const urgencyColors = {
    EMERGENCY: { bg: "#fee2e2", text: "#991b1b", border: "#f87171", badge: "🔴 EMERGENCY (Level 1)" },
    HIGH: { bg: "#fef3c7", text: "#92400e", border: "#f59e0b", badge: "🟠 HIGH URGENCY (Level 2)" },
    MODERATE: { bg: "#dbeafe", text: "#1e40af", border: "#60a5fa", badge: "🔵 MODERATE (Level 3)" },
    ROUTINE: { bg: "#dcfce7", text: "#166534", border: "#4ade80", badge: "🟢 ROUTINE (Level 4)" },
  };

  const currentUrgencyStyle = urgencyColors[urgencyInfo.level] || urgencyColors.ROUTINE;

  const handleStartEdit = () => {
    setEditForm({
      chief_complaint: findings.chief_complaint || "",
      symptoms: (findings.symptoms || []).join(", "),
      negated_findings: (findings.negated_findings || []).join(", "),
      duration: findings.duration || "",
      severity: findings.severity || "",
      body_location: findings.body_location || "",
      possible_category: findings.possible_category || "",
      urgency: urgencyInfo.level || "ROUTINE",
      doctor_notes: report.doctor_notes || "",
      patient_name: report?.patient_info?.name || "Walk-in Patient",
      patient_age: report?.patient_info?.age || "Adult",
      patient_gender: report?.patient_info?.gender || "Not Specified",
      patient_contact: report?.patient_info?.contact || "Rural Center",
      bp_systolic: vitals.bp_systolic || "",
      bp_diastolic: vitals.bp_diastolic || "",
      pulse_bpm: vitals.pulse_bpm || "",
      temperature_f: vitals.temperature_f || "",
      spo2_percent: vitals.spo2_percent || "",
      respiratory_rate: vitals.respiratory_rate || "",
      blood_glucose: vitals.blood_glucose || "",
      doctor_name: report?.attending_doctor?.doctor_name || "Attending Medical Officer",
      doctor_license: report?.attending_doctor?.license_number || "REG-MCI-VALIDATED",
      care_follow_up: report?.care_plan?.follow_up || "Review in OPD after 3 days.",
      care_precautions: report?.care_plan?.return_precautions || "Seek emergency care immediately if breathing difficulty, chest pain, or high fever persists.",
    });
    setPrescriptions(report?.prescriptions || []);
    setDiagnosticOrders(report?.diagnostic_orders || []);
    setIsEditing(true);
    setActionMessage("");
    setErrorMessage("");
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setActionMessage("");
    setErrorMessage("");
  };

  const handleAddMedication = () => {
    if (!newMed.name.trim()) return;
    setPrescriptions([...prescriptions, { ...newMed, name: newMed.name.trim() }]);
    setNewMed({ name: "", dosage: "", frequency: "TDS", duration: "3 days", instructions: "After food" });
  };

  const handleRemoveMedication = (index) => {
    setPrescriptions(prescriptions.filter((_, i) => i !== index));
  };

  const handleAddDiagnosticTest = (testName) => {
    const nameToAdd = testName || newTest.test_name;
    if (!nameToAdd.trim()) return;
    if (diagnosticOrders.some((d) => d.test_name?.toLowerCase() === nameToAdd.trim().toLowerCase())) return;
    setDiagnosticOrders([...diagnosticOrders, { test_name: nameToAdd.trim(), urgency: newTest.urgency || "Routine" }]);
    setNewTest({ test_name: "", urgency: "Routine" });
  };

  const handleRemoveDiagnosticTest = (index) => {
    setDiagnosticOrders(diagnosticOrders.filter((_, i) => i !== index));
  };

  const handleSaveChanges = async (finalizing = false) => {
    setIsSaving(true);
    setErrorMessage("");
    setActionMessage("");

    const parsedSymptoms = editForm.symptoms
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    const parsedNegatives = editForm.negated_findings
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    const payload = {
      chief_complaint: editForm.chief_complaint.trim(),
      symptoms: parsedSymptoms,
      negated_findings: parsedNegatives,
      duration: editForm.duration.trim(),
      severity: editForm.severity.trim(),
      body_location: editForm.body_location.trim(),
      possible_category: editForm.possible_category.trim(),
      urgency: editForm.urgency,
      doctor_notes: editForm.doctor_notes.trim(),
      patient_info: {
        ...(report?.patient_info || {}),
        name: editForm.patient_name.trim(),
        age: editForm.patient_age.trim(),
        gender: editForm.patient_gender.trim(),
        contact: editForm.patient_contact.trim(),
      },
      vital_signs: {
        bp_systolic: editForm.bp_systolic,
        bp_diastolic: editForm.bp_diastolic,
        pulse_bpm: editForm.pulse_bpm,
        temperature_f: editForm.temperature_f,
        spo2_percent: editForm.spo2_percent,
        respiratory_rate: editForm.respiratory_rate,
        blood_glucose: editForm.blood_glucose,
      },
      prescriptions: prescriptions,
      diagnostic_orders: diagnosticOrders,
      attending_doctor: {
        doctor_name: editForm.doctor_name.trim(),
        license_number: editForm.doctor_license.trim(),
      },
      care_plan: {
        assessment: editForm.doctor_notes.trim(),
        follow_up: editForm.care_follow_up.trim(),
        return_precautions: editForm.care_precautions.trim(),
      },
      status: finalizing ? "FINALIZED" : "CLINICIAN_REVIEWED",
    };

    try {
      const updated = await updateReportData(sessionId, payload);
      setReport(updated);
      setIsEditing(false);
      setActionMessage(finalizing ? "✅ Clinical report finalized and digitally signed." : "✅ Clinical report updated successfully.");
      if (onReportUpdated) {
        onReportUpdated(updated);
      }
    } catch (err) {
      setErrorMessage(err.message || "Failed to update clinical report.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadPdf = async () => {
    setIsDownloading(true);
    setActionMessage("");
    setErrorMessage("");
    try {
      await downloadReportPdf(sessionId);
      setActionMessage("✅ PDF clinical report downloaded successfully.");
    } catch (err) {
      setErrorMessage(err.message || "PDF download failed.");
    } finally {
      setIsDownloading(false);
    }
  };

  const handleEndSession = async () => {
    if (!window.confirm("End this patient intake session? All in-memory patient data will be securely purged.")) {
      return;
    }
    try {
      await endSession(sessionId);
      if (onSessionEnd) {
        onSessionEnd();
      }
    } catch (err) {
      setErrorMessage(err.message || "Failed to end session.");
    }
  };

  return (
    <div className="doctor-review-dashboard" style={{ marginTop: "1rem" }}>
      {/* Action Messages */}
      {actionMessage && (
        <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", color: "#166534", padding: "10px 14px", borderRadius: "8px", marginBottom: "12px", fontSize: "0.9rem" }}>
          {actionMessage}
        </div>
      )}
      {errorMessage && (
        <div style={{ background: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b", padding: "10px 14px", borderRadius: "8px", marginBottom: "12px", fontSize: "0.9rem" }}>
          ⚠️ {errorMessage}
        </div>
      )}

      {/* Header Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", borderBottom: "2px solid #e2e8f0", paddingBottom: "12px", marginBottom: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <h2 style={{ margin: 0, fontSize: "1.3rem", color: "#0f172a" }}>Doctor Review &amp; Intake Report</h2>
            <span style={{ fontSize: "0.75rem", background: isFinalized ? "#dcfce7" : "#e0f2fe", color: isFinalized ? "#166534" : "#0369a1", padding: "3px 8px", borderRadius: "12px", fontWeight: "600" }}>
              {isFinalized ? "🔒 FINALIZED & SIGNED" : "📝 DRAFT REVIEW"}
            </span>
          </div>
          <p style={{ margin: "4px 0 0 0", fontSize: "0.85rem", color: "#64748b" }}>
            Report ID: <strong>{report?.report_id || "N/A"}</strong> &bull; Generated: {report?.generated_at}
          </p>
        </div>

        {/* Action Controls */}
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {!isEditing ? (
            <>
              <button
                type="button"
                onClick={handleStartEdit}
                style={{ background: "#0284c7", color: "white", padding: "8px 14px", borderRadius: "6px", border: "none", cursor: "pointer", fontWeight: "600", fontSize: "0.85rem" }}
              >
                ✏️ Edit Clinical Findings &amp; Vitals
              </button>
              <button
                type="button"
                onClick={handleDownloadPdf}
                disabled={isDownloading}
                style={{ background: "#10b981", color: "white", padding: "8px 14px", borderRadius: "6px", border: "none", cursor: "pointer", fontWeight: "600", fontSize: "0.85rem" }}
              >
                {isDownloading ? "⏳ Generating PDF..." : "📥 Download PDF Report"}
              </button>
              {!isFinalized && (
                <button
                  type="button"
                  onClick={() => handleSaveChanges(true)}
                  disabled={isSaving}
                  style={{ background: "#6366f1", color: "white", padding: "8px 14px", borderRadius: "6px", border: "none", cursor: "pointer", fontWeight: "600", fontSize: "0.85rem" }}
                >
                  ✍️ Sign &amp; Finalize
                </button>
              )}
              <button
                type="button"
                onClick={handleEndSession}
                style={{ background: "#f1f5f9", color: "#475569", padding: "8px 12px", borderRadius: "6px", border: "1px solid #cbd5e1", cursor: "pointer", fontSize: "0.85rem" }}
              >
                🗑️ End Session
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() => handleSaveChanges(false)}
                disabled={isSaving}
                style={{ background: "#10b981", color: "white", padding: "8px 16px", borderRadius: "6px", border: "none", cursor: "pointer", fontWeight: "600", fontSize: "0.85rem" }}
              >
                {isSaving ? "Saving..." : "💾 Save Changes"}
              </button>
              <button
                type="button"
                onClick={() => handleSaveChanges(true)}
                disabled={isSaving}
                style={{ background: "#6366f1", color: "white", padding: "8px 16px", borderRadius: "6px", border: "none", cursor: "pointer", fontWeight: "600", fontSize: "0.85rem" }}
              >
                ✍️ Save &amp; Finalize
              </button>
              <button
                type="button"
                onClick={handleCancelEdit}
                disabled={isSaving}
                style={{ background: "#f1f5f9", color: "#475569", padding: "8px 14px", borderRadius: "6px", border: "1px solid #cbd5e1", cursor: "pointer", fontSize: "0.85rem" }}
              >
                Cancel
              </button>
            </>
          )}
        </div>
      </div>

      {/* -------------------------------------------------------------------
          TOP BANNER: Patient Demographics & Triage Priority
      ------------------------------------------------------------------- */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: "16px", marginBottom: "16px" }}>
        {/* Patient Demographics */}
        <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "14px" }}>
          <h3 style={{ margin: "0 0 10px 0", fontSize: "0.95rem", color: "#334155", fontWeight: "700" }}>
            👤 Patient Demographics &amp; Encounter Details
          </h3>
          {!isEditing ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px", fontSize: "0.85rem" }}>
              <div><span style={{ color: "#64748b" }}>Patient Name:</span> <strong>{report?.patient_info?.name || "Walk-in Patient"}</strong></div>
              <div><span style={{ color: "#64748b" }}>Age / Gender:</span> <strong>{report?.patient_info?.age || "Adult"} / {report?.patient_info?.gender || "Not Specified"}</strong></div>
              <div><span style={{ color: "#64748b" }}>UHID:</span> <strong>{report?.patient_info?.patient_id || "N/A"}</strong></div>
              <div><span style={{ color: "#64748b" }}>Language:</span> <strong>{report?.language_name} ({report?.language_code})</strong></div>
              <div><span style={{ color: "#64748b" }}>Contact:</span> <strong>{report?.patient_info?.contact || "Rural Center"}</strong></div>
              <div><span style={{ color: "#64748b" }}>Attending Clinician:</span> <strong>{report?.attending_doctor?.doctor_name}</strong></div>
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px", fontSize: "0.85rem" }}>
              <div>
                <label style={{ display: "block", color: "#64748b", marginBottom: "2px" }}>Patient Name</label>
                <input
                  type="text"
                  value={editForm.patient_name}
                  onChange={(e) => setEditForm({ ...editForm, patient_name: e.target.value })}
                  style={{ width: "100%", padding: "4px 8px", border: "1px solid #cbd5e1", borderRadius: "4px" }}
                />
              </div>
              <div>
                <label style={{ display: "block", color: "#64748b", marginBottom: "2px" }}>Age</label>
                <input
                  type="text"
                  value={editForm.patient_age}
                  onChange={(e) => setEditForm({ ...editForm, patient_age: e.target.value })}
                  style={{ width: "100%", padding: "4px 8px", border: "1px solid #cbd5e1", borderRadius: "4px" }}
                />
              </div>
              <div>
                <label style={{ display: "block", color: "#64748b", marginBottom: "2px" }}>Gender</label>
                <select
                  value={editForm.patient_gender}
                  onChange={(e) => setEditForm({ ...editForm, patient_gender: e.target.value })}
                  style={{ width: "100%", padding: "4px 8px", border: "1px solid #cbd5e1", borderRadius: "4px" }}
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                  <option value="Not Specified">Not Specified</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", color: "#64748b", marginBottom: "2px" }}>Doctor Name</label>
                <input
                  type="text"
                  value={editForm.doctor_name}
                  onChange={(e) => setEditForm({ ...editForm, doctor_name: e.target.value })}
                  style={{ width: "100%", padding: "4px 8px", border: "1px solid #cbd5e1", borderRadius: "4px" }}
                />
              </div>
              <div>
                <label style={{ display: "block", color: "#64748b", marginBottom: "2px" }}>Doctor Reg No.</label>
                <input
                  type="text"
                  value={editForm.doctor_license}
                  onChange={(e) => setEditForm({ ...editForm, doctor_license: e.target.value })}
                  style={{ width: "100%", padding: "4px 8px", border: "1px solid #cbd5e1", borderRadius: "4px" }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Triage Priority Banner */}
        <div style={{ background: currentUrgencyStyle.bg, border: `2px solid ${currentUrgencyStyle.border}`, borderRadius: "8px", padding: "14px", display: "flex", flexDirection: "column", justifyContent: "center", textAlign: "center" }}>
          <div style={{ fontSize: "0.75rem", fontWeight: "700", color: currentUrgencyStyle.text, textTransform: "uppercase", letterSpacing: "0.5px" }}>
            TRIAGE PRIORITY
          </div>
          <div style={{ fontSize: "1.25rem", fontWeight: "800", color: currentUrgencyStyle.text, margin: "4px 0" }}>
            {urgencyInfo.level}
          </div>
          <div style={{ fontSize: "0.8rem", color: currentUrgencyStyle.text, fontWeight: "600" }}>
            ⏱️ {urgencyInfo.target_response}
          </div>
          {isEditing && (
            <div style={{ marginTop: "8px" }}>
              <select
                value={editForm.urgency}
                onChange={(e) => setEditForm({ ...editForm, urgency: e.target.value })}
                style={{ padding: "4px 8px", borderRadius: "4px", border: "1px solid #cbd5e1", fontSize: "0.8rem", fontWeight: "600" }}
              >
                <option value="EMERGENCY">EMERGENCY (Level 1)</option>
                <option value="HIGH">HIGH (Level 2)</option>
                <option value="MODERATE">MODERATE (Level 3)</option>
                <option value="ROUTINE">ROUTINE (Level 4)</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Clinical Triage Rationale */}
      <div style={{ background: "#f8fafc", borderLeft: `4px solid ${currentUrgencyStyle.border}`, padding: "8px 12px", marginBottom: "16px", borderRadius: "0 6px 6px 0", fontSize: "0.85rem" }}>
        <strong>Clinical Triage Rationale:</strong> {urgencyInfo.reason}
      </div>

      {/* -------------------------------------------------------------------
          VITAL SIGNS GRID (With Clinical Abnormal Warnings)
      ------------------------------------------------------------------- */}
      <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "14px", marginBottom: "16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
          <h3 style={{ margin: 0, fontSize: "0.95rem", color: "#334155", fontWeight: "700" }}>
            🩺 Clinical Vital Signs
          </h3>
          {report?.vital_alerts && report.vital_alerts.length > 0 && (
            <span style={{ fontSize: "0.8rem", background: "#fef2f2", color: "#991b1b", border: "1px solid #fecaca", padding: "2px 8px", borderRadius: "12px", fontWeight: "700" }}>
              ⚠️ {report.vital_alerts.length} Abnormal Vital Sign(s) Detected
            </span>
          )}
        </div>

        {!isEditing ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: "10px", textAlign: "center" }}>
            <div style={{ background: "#f8fafc", padding: "8px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Blood Pressure</div>
              <div style={{ fontSize: "0.95rem", fontWeight: "700", color: "#0f172a" }}>{vitals.bp_display || "Not recorded"}</div>
            </div>
            <div style={{ background: "#f8fafc", padding: "8px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Pulse / HR</div>
              <div style={{ fontSize: "0.95rem", fontWeight: "700", color: "#0f172a" }}>{vitals.pulse_display || "Not recorded"}</div>
            </div>
            <div style={{ background: "#f8fafc", padding: "8px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Temperature</div>
              <div style={{ fontSize: "0.95rem", fontWeight: "700", color: "#0f172a" }}>{vitals.temp_display || "Not recorded"}</div>
            </div>
            <div style={{ background: "#f8fafc", padding: "8px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Oxygen (SpO2)</div>
              <div style={{ fontSize: "0.95rem", fontWeight: "700", color: "#0f172a" }}>{vitals.spo2_display || "Not recorded"}</div>
            </div>
            <div style={{ background: "#f8fafc", padding: "8px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Resp. Rate</div>
              <div style={{ fontSize: "0.95rem", fontWeight: "700", color: "#0f172a" }}>{vitals.rr_display || "Not recorded"}</div>
            </div>
            <div style={{ background: "#f8fafc", padding: "8px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Blood Glucose</div>
              <div style={{ fontSize: "0.95rem", fontWeight: "700", color: "#0f172a" }}>{vitals.rbs_display || "Not recorded"}</div>
            </div>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: "10px" }}>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>BP Sys/Dia</label>
              <div style={{ display: "flex", gap: "4px" }}>
                <input
                  type="number"
                  placeholder="120"
                  value={editForm.bp_systolic}
                  onChange={(e) => setEditForm({ ...editForm, bp_systolic: e.target.value })}
                  style={{ width: "50%", padding: "4px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
                />
                <input
                  type="number"
                  placeholder="80"
                  value={editForm.bp_diastolic}
                  onChange={(e) => setEditForm({ ...editForm, bp_diastolic: e.target.value })}
                  style={{ width: "50%", padding: "4px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
                />
              </div>
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>Pulse (bpm)</label>
              <input
                type="number"
                placeholder="75"
                value={editForm.pulse_bpm}
                onChange={(e) => setEditForm({ ...editForm, pulse_bpm: e.target.value })}
                style={{ width: "100%", padding: "4px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>Temp (°F)</label>
              <input
                type="number"
                step="0.1"
                placeholder="98.6"
                value={editForm.temperature_f}
                onChange={(e) => setEditForm({ ...editForm, temperature_f: e.target.value })}
                style={{ width: "100%", padding: "4px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>SpO2 (%)</label>
              <input
                type="number"
                placeholder="98"
                value={editForm.spo2_percent}
                onChange={(e) => setEditForm({ ...editForm, spo2_percent: e.target.value })}
                style={{ width: "100%", padding: "4px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>Resp. Rate</label>
              <input
                type="number"
                placeholder="16"
                value={editForm.respiratory_rate}
                onChange={(e) => setEditForm({ ...editForm, respiratory_rate: e.target.value })}
                style={{ width: "100%", padding: "4px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>RBS (mg/dL)</label>
              <input
                type="number"
                placeholder="110"
                value={editForm.blood_glucose}
                onChange={(e) => setEditForm({ ...editForm, blood_glucose: e.target.value })}
                style={{ width: "100%", padding: "4px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
            </div>
          </div>
        )}

        {report?.vital_alerts && report.vital_alerts.length > 0 && (
          <div style={{ marginTop: "10px", background: "#fef2f2", borderLeft: "3px solid #ef4444", padding: "6px 10px", fontSize: "0.85rem", color: "#991b1b" }}>
            <strong>Abnormal Alerts:</strong> {report.vital_alerts.join("; ")}
          </div>
        )}
      </div>

      {/* -------------------------------------------------------------------
          BILINGUAL INTAKE STATEMENTS & TRANSLATION
      ------------------------------------------------------------------- */}
      <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "14px", marginBottom: "16px" }}>
        <h3 style={{ margin: "0 0 10px 0", fontSize: "0.95rem", color: "#334155", fontWeight: "700" }}>
          🗣️ Multilingual Patient Intake &amp; Verified Translation
        </h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: "700", marginBottom: "4px" }}>
              PATIENT REGIONAL STATEMENT ({report?.language_name}):
            </div>
            <p style={{ margin: 0, fontSize: "0.95rem", color: "#0f172a", lineHeight: "1.4" }}>
              {report?.original_transcript || "No transcript recorded"}
            </p>
          </div>
          <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: "700" }}>VERIFIED ENGLISH TRANSLATION:</span>
              <span style={{ fontSize: "0.75rem", background: verification.status === "consistent" ? "#dcfce7" : "#fef3c7", color: verification.status === "consistent" ? "#166534" : "#92400e", padding: "1px 6px", borderRadius: "4px" }}>
                {verification.status}
              </span>
            </div>
            <p style={{ margin: 0, fontSize: "0.95rem", color: "#0f172a", lineHeight: "1.4" }}>
              {report?.english_translation || "Translation unavailable"}
            </p>
            {hasWarnings && (
              <div style={{ marginTop: "6px", fontSize: "0.8rem", color: "#b45309" }}>
                ⚠️ {verification.warnings.join(", ")}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* -------------------------------------------------------------------
          STRUCTURED CLINICAL FINDINGS (AI-DERIVED)
      ------------------------------------------------------------------- */}
      <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "14px", marginBottom: "16px" }}>
        <h3 style={{ margin: "0 0 10px 0", fontSize: "0.95rem", color: "#334155", fontWeight: "700" }}>
          🔬 Extracted Clinical Findings (AI-Derived)
        </h3>
        {!isEditing ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", fontSize: "0.85rem" }}>
            <div>
              <span style={{ color: "#64748b" }}>Chief Complaint:</span>
              <div style={{ fontWeight: "700", color: "#0f172a", marginTop: "2px" }}>{findings.chief_complaint || "None"}</div>
            </div>
            <div>
              <span style={{ color: "#64748b" }}>Active Symptoms:</span>
              <div style={{ fontWeight: "700", color: "#0f172a", marginTop: "2px" }}>
                {findings.symptoms && findings.symptoms.length > 0 ? (
                  findings.symptoms.map((s, idx) => (
                    <span key={idx} style={{ display: "inline-block", background: "#e0f2fe", color: "#0369a1", padding: "2px 6px", borderRadius: "4px", marginRight: "4px", marginBottom: "2px" }}>
                      {s}
                    </span>
                  ))
                ) : (
                  "None detected"
                )}
              </div>
            </div>
            <div>
              <span style={{ color: "#64748b" }}>Pertinent Negatives:</span>
              <div style={{ fontWeight: "700", color: "#0f172a", marginTop: "2px" }}>
                {findings.negated_findings && findings.negated_findings.length > 0 ? (
                  findings.negated_findings.map((s, idx) => (
                    <span key={idx} style={{ display: "inline-block", background: "#f1f5f9", color: "#475569", padding: "2px 6px", borderRadius: "4px", marginRight: "4px", marginBottom: "2px" }}>
                      No {s}
                    </span>
                  ))
                ) : (
                  "None recorded"
                )}
              </div>
            </div>
            <div>
              <span style={{ color: "#64748b" }}>Duration:</span>
              <div style={{ fontWeight: "700", color: "#0f172a", marginTop: "2px" }}>{findings.duration || "Not specified"}</div>
            </div>
            <div>
              <span style={{ color: "#64748b" }}>Severity:</span>
              <div style={{ fontWeight: "700", color: "#0f172a", marginTop: "2px" }}>{findings.severity || "Not specified"}</div>
            </div>
            <div>
              <span style={{ color: "#64748b" }}>Category:</span>
              <div style={{ fontWeight: "700", color: "#0f172a", marginTop: "2px" }}>{findings.possible_category || "Primary Care"}</div>
            </div>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", fontSize: "0.85rem" }}>
            <div>
              <label style={{ display: "block", color: "#64748b", marginBottom: "2px" }}>Chief Complaint</label>
              <input
                type="text"
                value={editForm.chief_complaint}
                onChange={(e) => setEditForm({ ...editForm, chief_complaint: e.target.value })}
                style={{ width: "100%", padding: "6px 8px", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
            </div>
            <div>
              <label style={{ display: "block", color: "#64748b", marginBottom: "2px" }}>Clinical Category</label>
              <input
                type="text"
                value={editForm.possible_category}
                onChange={(e) => setEditForm({ ...editForm, possible_category: e.target.value })}
                style={{ width: "100%", padding: "6px 8px", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
            </div>
            <div>
              <label style={{ display: "block", color: "#64748b", marginBottom: "2px" }}>Active Symptoms (comma separated)</label>
              <input
                type="text"
                value={editForm.symptoms}
                onChange={(e) => setEditForm({ ...editForm, symptoms: e.target.value })}
                style={{ width: "100%", padding: "6px 8px", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
            </div>
            <div>
              <label style={{ display: "block", color: "#64748b", marginBottom: "2px" }}>Pertinent Negatives (comma separated)</label>
              <input
                type="text"
                value={editForm.negated_findings}
                onChange={(e) => setEditForm({ ...editForm, negated_findings: e.target.value })}
                style={{ width: "100%", padding: "6px 8px", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
            </div>
            <div>
              <label style={{ display: "block", color: "#64748b", marginBottom: "2px" }}>Symptom Duration</label>
              <input
                type="text"
                value={editForm.duration}
                onChange={(e) => setEditForm({ ...editForm, duration: e.target.value })}
                style={{ width: "100%", padding: "6px 8px", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
            </div>
            <div>
              <label style={{ display: "block", color: "#64748b", marginBottom: "2px" }}>Severity / Location</label>
              <div style={{ display: "flex", gap: "6px" }}>
                <input
                  type="text"
                  placeholder="Severity"
                  value={editForm.severity}
                  onChange={(e) => setEditForm({ ...editForm, severity: e.target.value })}
                  style={{ width: "50%", padding: "6px 8px", border: "1px solid #cbd5e1", borderRadius: "4px" }}
                />
                <input
                  type="text"
                  placeholder="Body location"
                  value={editForm.body_location}
                  onChange={(e) => setEditForm({ ...editForm, body_location: e.target.value })}
                  style={{ width: "50%", padding: "6px 8px", border: "1px solid #cbd5e1", borderRadius: "4px" }}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* -------------------------------------------------------------------
          DIFFERENTIAL CONSIDERATIONS
      ------------------------------------------------------------------- */}
      {report?.differential_considerations && report.differential_considerations.length > 0 && (
        <div style={{ background: "#f8fafc", border: "1px solid #cbd5e1", borderRadius: "8px", padding: "12px 14px", marginBottom: "16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
            <h4 style={{ margin: 0, fontSize: "0.85rem", color: "#1e293b", fontWeight: "700" }}>
              💡 Algorithmic Differential Considerations (For Clinician Correlation)
            </h4>
            <span style={{ fontSize: "0.75rem", color: "#64748b" }}>AI-assisted guidance &bull; Not diagnosis</span>
          </div>
          <ul style={{ margin: 0, paddingLeft: "20px", fontSize: "0.85rem", color: "#334155" }}>
            {report.differential_considerations.map((diff, idx) => (
              <li key={idx} style={{ marginBottom: "3px" }}>{diff}</li>
            ))}
          </ul>
        </div>
      )}

      {/* -------------------------------------------------------------------
          PRESCRIPTIONS & MEDICATION ORDERS (Rx)
      ------------------------------------------------------------------- */}
      <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "14px", marginBottom: "16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
          <h3 style={{ margin: 0, fontSize: "0.95rem", color: "#334155", fontWeight: "700" }}>
            💊 Prescriptions &amp; Medication Orders (Rx)
          </h3>
          {isEditing && (
            <span style={{ fontSize: "0.8rem", color: "#64748b" }}>Prescribe medications for outpatient management</span>
          )}
        </div>

        {prescriptions.length === 0 ? (
          <p style={{ margin: 0, fontSize: "0.85rem", color: "#64748b", fontStyle: "italic" }}>
            No medications prescribed yet. Click "Edit" to add prescriptions.
          </p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", marginBottom: isEditing ? "10px" : "0" }}>
            <thead>
              <tr style={{ background: "#f1f5f9", textAlign: "left", color: "#475569" }}>
                <th style={{ padding: "6px 8px", borderBottom: "1px solid #cbd5e1" }}>Medicine Name</th>
                <th style={{ padding: "6px 8px", borderBottom: "1px solid #cbd5e1" }}>Dosage</th>
                <th style={{ padding: "6px 8px", borderBottom: "1px solid #cbd5e1" }}>Frequency</th>
                <th style={{ padding: "6px 8px", borderBottom: "1px solid #cbd5e1" }}>Duration</th>
                <th style={{ padding: "6px 8px", borderBottom: "1px solid #cbd5e1" }}>Instructions</th>
                {isEditing && <th style={{ padding: "6px 8px", borderBottom: "1px solid #cbd5e1", width: "40px" }}></th>}
              </tr>
            </thead>
            <tbody>
              {prescriptions.map((med, idx) => (
                <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                  <td style={{ padding: "6px 8px", fontWeight: "600" }}>{med.name}</td>
                  <td style={{ padding: "6px 8px" }}>{med.dosage}</td>
                  <td style={{ padding: "6px 8px" }}>{med.frequency}</td>
                  <td style={{ padding: "6px 8px" }}>{med.duration}</td>
                  <td style={{ padding: "6px 8px", color: "#475569" }}>{med.instructions}</td>
                  {isEditing && (
                    <td style={{ padding: "6px 8px", textAlign: "center" }}>
                      <button
                        type="button"
                        onClick={() => handleRemoveMedication(idx)}
                        style={{ background: "none", border: "none", cursor: "pointer", color: "#ef4444" }}
                      >
                        ❌
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {isEditing && (
          <div style={{ background: "#f8fafc", padding: "10px", borderRadius: "6px", border: "1px dashed #cbd5e1", display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr 2fr auto", gap: "8px", alignItems: "end" }}>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>Drug Name</label>
              <input
                type="text"
                placeholder="e.g. Paracetamol"
                value={newMed.name}
                onChange={(e) => setNewMed({ ...newMed, name: e.target.value })}
                style={{ width: "100%", padding: "4px 8px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>Dosage</label>
              <input
                type="text"
                placeholder="500 mg"
                value={newMed.dosage}
                onChange={(e) => setNewMed({ ...newMed, dosage: e.target.value })}
                style={{ width: "100%", padding: "4px 8px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>Frequency</label>
              <select
                value={newMed.frequency}
                onChange={(e) => setNewMed({ ...newMed, frequency: e.target.value })}
                style={{ width: "100%", padding: "4px 8px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              >
                <option value="TDS (3 times/day)">TDS</option>
                <option value="BD (2 times/day)">BD</option>
                <option value="OD (Once daily)">OD</option>
                <option value="SOS (As needed)">SOS</option>
                <option value="QID (4 times/day)">QID</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>Duration</label>
              <input
                type="text"
                placeholder="3 days"
                value={newMed.duration}
                onChange={(e) => setNewMed({ ...newMed, duration: e.target.value })}
                style={{ width: "100%", padding: "4px 8px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>Instructions</label>
              <input
                type="text"
                placeholder="Post meals with warm water"
                value={newMed.instructions}
                onChange={(e) => setNewMed({ ...newMed, instructions: e.target.value })}
                style={{ width: "100%", padding: "4px 8px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
            </div>
            <button
              type="button"
              onClick={handleAddMedication}
              style={{ background: "#0284c7", color: "white", padding: "6px 12px", borderRadius: "4px", border: "none", cursor: "pointer", fontWeight: "600", fontSize: "0.85rem" }}
            >
              ➕ Add
            </button>
          </div>
        )}
      </div>

      {/* -------------------------------------------------------------------
          DIAGNOSTIC ORDERS (LAB / RADIOLOGY)
      ------------------------------------------------------------------- */}
      <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "14px", marginBottom: "16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
          <h3 style={{ margin: 0, fontSize: "0.95rem", color: "#334155", fontWeight: "700" }}>
            🧪 Diagnostic Investigations Ordered
          </h3>
        </div>

        {diagnosticOrders.length === 0 ? (
          <p style={{ margin: 0, fontSize: "0.85rem", color: "#64748b", fontStyle: "italic" }}>
            No lab or radiological investigations ordered yet.
          </p>
        ) : (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: isEditing ? "10px" : "0" }}>
            {diagnosticOrders.map((test, idx) => (
              <span
                key={idx}
                style={{ background: "#f8fafc", border: "1px solid #cbd5e1", padding: "4px 10px", borderRadius: "6px", fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "6px" }}
              >
                <strong>{test.test_name}</strong>
                <span style={{ fontSize: "0.75rem", color: "#64748b" }}>({test.urgency})</span>
                {isEditing && (
                  <button
                    type="button"
                    onClick={() => handleRemoveDiagnosticTest(idx)}
                    style={{ background: "none", border: "none", cursor: "pointer", color: "#ef4444", padding: 0 }}
                  >
                    ×
                  </button>
                )}
              </span>
            ))}
          </div>
        )}

        {isEditing && (
          <div style={{ marginTop: "10px" }}>
            <div style={{ fontSize: "0.8rem", color: "#64748b", marginBottom: "6px" }}>Quick Add Standard Tests:</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "10px" }}>
              {["ECG 12-Lead", "CBC", "Chest X-Ray (PA)", "Blood Sugar (RBS)", "Urine Routine", "Serum Electrolytes", "Rapid Malaria Antigen", "Dengue NS1 Antigen"].map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => handleAddDiagnosticTest(t)}
                  style={{ background: "#f1f5f9", border: "1px solid #cbd5e1", borderRadius: "4px", padding: "3px 8px", fontSize: "0.8rem", cursor: "pointer" }}
                >
                  + {t}
                </button>
              ))}
            </div>
            <div style={{ display: "flex", gap: "8px", maxWidth: "400px" }}>
              <input
                type="text"
                placeholder="Custom test name..."
                value={newTest.test_name}
                onChange={(e) => setNewTest({ ...newTest, test_name: e.target.value })}
                style={{ flex: 1, padding: "4px 8px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
              <button
                type="button"
                onClick={() => handleAddDiagnosticTest()}
                style={{ background: "#0284c7", color: "white", padding: "4px 10px", borderRadius: "4px", border: "none", cursor: "pointer", fontSize: "0.85rem" }}
              >
                Add Test
              </button>
            </div>
          </div>
        )}
      </div>

      {/* -------------------------------------------------------------------
          ATTENDING CLINICIAN ASSESSMENT & CARE PLAN
      ------------------------------------------------------------------- */}
      <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "14px", marginBottom: "16px" }}>
        <h3 style={{ margin: "0 0 10px 0", fontSize: "0.95rem", color: "#334155", fontWeight: "700" }}>
          👨‍⚕️ Clinician Assessment &amp; Care Plan
        </h3>

        {!isEditing ? (
          <div>
            <div style={{ marginBottom: "10px" }}>
              <span style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: "700" }}>CLINICAL NOTES &amp; IMPRESSION:</span>
              <p style={{ margin: "4px 0 0 0", fontSize: "0.9rem", color: "#0f172a", whiteSpace: "pre-wrap" }}>
                {report?.doctor_notes || "No digital assessment notes recorded."}
              </p>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", fontSize: "0.85rem", marginTop: "10px" }}>
              <div style={{ background: "#fef3c7", padding: "8px 12px", borderRadius: "6px" }}>
                <strong>🚨 Return Precautions (Red Flags):</strong>
                <p style={{ margin: "4px 0 0 0" }}>{report?.care_plan?.return_precautions}</p>
              </div>
              <div style={{ background: "#f0fdf4", padding: "8px 12px", borderRadius: "6px" }}>
                <strong>📅 Follow-up Plan:</strong>
                <p style={{ margin: "4px 0 0 0" }}>{report?.care_plan?.follow_up}</p>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <div>
              <label style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                Doctor Assessment &amp; Clinical Notes
              </label>
              <textarea
                rows={3}
                value={editForm.doctor_notes}
                onChange={(e) => setEditForm({ ...editForm, doctor_notes: e.target.value })}
                placeholder="Enter physical examination findings, provisional clinical impression, or counseling notes..."
                style={{ width: "100%", padding: "8px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
              />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div>
                <label style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Follow-up Schedule
                </label>
                <input
                  type="text"
                  value={editForm.care_follow_up}
                  onChange={(e) => setEditForm({ ...editForm, care_follow_up: e.target.value })}
                  style={{ width: "100%", padding: "6px 8px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: "600", display: "block", marginBottom: "4px" }}>
                  Emergency Return Precautions
                </label>
                <input
                  type="text"
                  value={editForm.care_precautions}
                  onChange={(e) => setEditForm({ ...editForm, care_precautions: e.target.value })}
                  style={{ width: "100%", padding: "6px 8px", fontSize: "0.85rem", border: "1px solid #cbd5e1", borderRadius: "4px" }}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* -------------------------------------------------------------------
          CLINICIAN SIGN-OFF BLOCK & AI DISCLAIMER
      ------------------------------------------------------------------- */}
      <div style={{ borderTop: "1px solid #e2e8f0", paddingTop: "12px", marginTop: "16px", display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.8rem", color: "#64748b" }}>
        <div>
          <span>Attending Clinician: <strong>{report?.attending_doctor?.doctor_name}</strong></span>
          <span style={{ marginLeft: "12px" }}>License: <strong>{report?.attending_doctor?.license_number}</strong></span>
          {report?.attending_doctor?.signed_at && (
            <span style={{ marginLeft: "12px", color: "#166534" }}>Signed: <strong>{report?.attending_doctor?.signed_at}</strong></span>
          )}
        </div>
        <div>
          <button
            type="button"
            onClick={handleDownloadPdf}
            disabled={isDownloading}
            style={{ background: "#0284c7", color: "white", padding: "6px 12px", borderRadius: "4px", border: "none", cursor: "pointer", fontWeight: "600", fontSize: "0.8rem" }}
          >
            📥 Download Verified PDF
          </button>
        </div>
      </div>
      <p style={{ margin: "8px 0 0 0", fontSize: "0.75rem", color: "#94a3b8", textAlign: "center", fontStyle: "italic" }}>
        {report?.disclaimer}
      </p>
    </div>
  );
}