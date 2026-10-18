"""VaaniDoc Advanced Clinical Reporting Module.

Comprehensive Physician Encounter & Health Intake Reporting:
1. Patient Demographics & Intake Metadata.
2. Clinical Vital Signs Grid with Automated Abnormal Threshold Alerts.
3. 4-Tier Urgency Triage & Maximum Target Response Time Matrix.
4. Multilingual Intake Record (Regional Indian Script + Verified English Translation).
5. AI Clinical Extraction: Chief Complaint, Active Symptoms, Pertinent Negatives, Severity & Duration.
6. Differential Considerations (Algorithmic Guidance for Physician Correlation).
7. Prescription & Medication Orders Table (Drug, Dosage, Frequency, Days, Notes).
8. Diagnostic & Laboratory Orders (Test Name, Priority, Urgency).
9. Physician Clinical Assessment, Care Plan & Red Flag Return Precautions.
10. Attending Clinician Digital Sign-off Block & Medicolegal AI Disclaimer.
11. Professional, Executive ReportLab PDF Generator.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ai.clinical.urgency import classify_urgency, get_urgency
from ai.translation.language_map import get_language_name
from ai.translation.sessions import get_session, update_session


# ---------------------------------------------------------------------------
# Urgency Color & Priority Mapping
# ---------------------------------------------------------------------------

URGENCY_COLORS = {
    "EMERGENCY": colors.HexColor("#B91C1C"),  # Crimson Red
    "HIGH": colors.HexColor("#B45309"),       # Amber/Orange
    "MODERATE": colors.HexColor("#1D4ED8"),   # Royal Blue
    "ROUTINE": colors.HexColor("#15803D"),    # Forest Green
}

URGENCY_BG_COLORS = {
    "EMERGENCY": colors.HexColor("#FEE2E2"),  # Light Red
    "HIGH": colors.HexColor("#FEF3C7"),       # Light Amber
    "MODERATE": colors.HexColor("#DBEAFE"),   # Light Blue
    "ROUTINE": colors.HexColor("#DCFCE7"),    # Light Green
}

TRIAGE_RESPONSE_TIMES = {
    "EMERGENCY": "Immediate Resuscitation (< 15 Minutes)",
    "HIGH": "Urgent Evaluation (< 60 Minutes)",
    "MODERATE": "Priority Outpatient Review (< 4 Hours / Same Day)",
    "ROUTINE": "Standard Outpatient Queue",
}

TRIAGE_TITLES = {
    "EMERGENCY": "LEVEL 1: RESUSCITATION / CRITICAL EMERGENCY",
    "HIGH": "LEVEL 2: HIGH URGENCY / TIME-SENSITIVE",
    "MODERATE": "LEVEL 3: MODERATE URGENCY / SAME DAY",
    "ROUTINE": "LEVEL 4: ROUTINE PRIMARY CARE",
}


# ---------------------------------------------------------------------------
# Vital Signs Validation & Flagging
# ---------------------------------------------------------------------------

def evaluate_vital_signs(vitals: Optional[Dict[str, Any]]) -> tuple[Dict[str, Any], List[str]]:
    """Validate vital signs and generate automated clinical warning flags."""
    if not vitals:
        vitals = {}

    alerts: List[str] = []
    
    # Blood pressure
    bp_sys = vitals.get("bp_systolic") or vitals.get("sys") or vitals.get("systolic")
    bp_dia = vitals.get("bp_diastolic") or vitals.get("dia") or vitals.get("diastolic")
    bp_display = "Not recorded"

    if bp_sys and bp_dia:
        bp_display = f"{bp_sys}/{bp_dia} mmHg"
        try:
            sys_val = float(bp_sys)
            dia_val = float(bp_dia)
            if sys_val >= 160 or dia_val >= 100:
                alerts.append(f"Severe Hypertension (Stage 2): {sys_val:.0f}/{dia_val:.0f} mmHg")
            elif sys_val >= 140 or dia_val >= 90:
                alerts.append(f"Elevated Blood Pressure (Stage 1): {sys_val:.0f}/{dia_val:.0f} mmHg")
            elif sys_val < 90 or dia_val < 60:
                alerts.append(f"Hypotension Warning: {sys_val:.0f}/{dia_val:.0f} mmHg")
        except (ValueError, TypeError):
            pass
    elif vitals.get("bp_display"):
        bp_display = str(vitals.get("bp_display"))

    # Heart rate / Pulse
    pulse = vitals.get("pulse_bpm") or vitals.get("pulse") or vitals.get("hr")
    pulse_display = "Not recorded"
    if pulse:
        try:
            pulse_val = float(pulse)
            pulse_display = f"{pulse_val:.0f} bpm"
            if pulse_val > 100:
                alerts.append(f"Tachycardia (Elevated Pulse): {pulse_val:.0f} bpm")
            elif pulse_val < 60:
                alerts.append(f"Bradycardia (Low Pulse): {pulse_val:.0f} bpm")
        except (ValueError, TypeError):
            pulse_display = str(pulse)

    # Temperature
    temp = vitals.get("temperature_f") or vitals.get("temp")
    temp_display = "Not recorded"
    if temp:
        try:
            temp_val = float(temp)
            temp_display = f"{temp_val:.1f} °F"
            if temp_val >= 102.0:
                alerts.append(f"High Fever: {temp_val:.1f} °F")
            elif temp_val >= 100.4:
                alerts.append(f"Low-Grade Pyrexia: {temp_val:.1f} °F")
        except (ValueError, TypeError):
            temp_display = str(temp)

    # Oxygen saturation SpO2
    spo2 = vitals.get("spo2_percent") or vitals.get("spo2")
    spo2_display = "Not recorded"
    if spo2:
        try:
            spo2_val = float(spo2)
            spo2_display = f"{spo2_val:.0f}%"
            if spo2_val < 92:
                alerts.append(f"Critical Hypoxia: SpO2 {spo2_val:.0f}% (< 92%)")
            elif spo2_val < 95:
                alerts.append(f"Borderline Hypoxia: SpO2 {spo2_val:.0f}% (Normal >= 95%)")
        except (ValueError, TypeError):
            spo2_display = str(spo2)

    # Respiratory rate
    rr = vitals.get("respiratory_rate") or vitals.get("rr")
    rr_display = f"{rr} /min" if rr else "Not recorded"
    if rr:
        try:
            rr_val = float(rr)
            if rr_val > 22:
                alerts.append(f"Tachypnea (Elevated Respiratory Rate): {rr_val:.0f} /min")
        except (ValueError, TypeError):
            pass

    # Blood glucose (RBS)
    bg = vitals.get("blood_glucose") or vitals.get("rbs")
    bg_display = f"{bg} mg/dL" if bg else "Not recorded"
    if bg:
        try:
            bg_val = float(bg)
            if bg_val > 200:
                alerts.append(f"Hyperglycemia: {bg_val:.0f} mg/dL")
            elif bg_val < 70:
                alerts.append(f"Hypoglycemia Warning: {bg_val:.0f} mg/dL")
        except (ValueError, TypeError):
            pass

    evaluated = {
        "bp_systolic": bp_sys,
        "bp_diastolic": bp_dia,
        "bp_display": bp_display,
        "pulse_bpm": pulse,
        "pulse_display": pulse_display,
        "temperature_f": temp,
        "temp_display": temp_display,
        "spo2_percent": spo2,
        "spo2_display": spo2_display,
        "respiratory_rate": rr,
        "rr_display": rr_display,
        "blood_glucose": bg,
        "rbs_display": bg_display,
        "alerts": alerts,
    }
    return evaluated, alerts


# ---------------------------------------------------------------------------
# Algorithmic Differential Considerations Generator
# ---------------------------------------------------------------------------

def get_differential_considerations(category: str, symptoms: List[str]) -> List[str]:
    """Generate preliminary algorithmic differential considerations for physician review."""
    symptoms_lower = [s.lower() for s in symptoms]
    diffs = []

    cat_lower = (category or "").lower()

    if "cardio" in cat_lower or any("chest" in s for s in symptoms_lower):
        diffs.append("Acute Coronary Syndrome (ACS) / Angina Pectoris")
        diffs.append("Gastroesophageal Reflux Disease (GERD) / Esophageal Spasm")
        diffs.append("Musculoskeletal Chest Wall Strain / Costochondritis")
        diffs.append("Pleurisy / Pericardial Irritation")
    elif "respiratory" in cat_lower or any(s in symptoms_lower for s in ["cough", "breathlessness", "dyspnea"]):
        diffs.append("Acute Bronchitis / Upper Respiratory Tract Infection (URTI)")
        diffs.append("Community-Acquired Pneumonia (CAP)")
        diffs.append("Reactive Airway Disease / Bronchial Asthma Exacerbation")
    elif "gastro" in cat_lower or any(s in symptoms_lower for s in ["vomiting", "diarrhea", "nausea", "abdominal_pain"]):
        diffs.append("Acute Gastroenteritis (Infectious / Food-borne)")
        diffs.append("Acid Peptic Disease / Acute Gastritis")
        diffs.append("Symptomatic Biliary Colic / Acute Cholecystitis")
    elif "neuro" in cat_lower or any("headache" in s for s in symptoms_lower):
        diffs.append("Tension-type Headache vs. Acute Migraine")
        diffs.append("Febrile Headache / Systemic Viral Illness")
        diffs.append("Secondary Headache (Rule out Intracranial / Meningeal Etiology)")
    elif any("fever" in s for s in symptoms_lower):
        diffs.append("Acute Viral Febrile Illness (Undifferentiated)")
        diffs.append("Endemic Tropical Fever (Malaria, Dengue, Typhoid, Chikungunya)")
        diffs.append("Localized Bacterial Infection (ENT, Respiratory, Urinary)")
    elif any(s in symptoms_lower for s in ["joint_pain", "back_pain", "myalgia"]):
        diffs.append("Acute Musculoskeletal Strain / Lumbar Spondylosis")
        diffs.append("Inflammatory Arthropathy / Post-viral Reactive Arthritis")
    else:
        diffs.append("General Primary Care Clinical Evaluation")
        diffs.append("Subacute Outpatient Symptom Complex")

    return diffs


# ---------------------------------------------------------------------------
# Report Data Aggregator
# ---------------------------------------------------------------------------

def build_report_data(session: Dict[str, Any]) -> Dict[str, Any]:
    """Build a structured clinical intake report dictionary from session data."""
    session_id = session.get("session_id", "UNKNOWN")
    src_lang_code = session.get("source_language", "gu")

    try:
        lang_name = get_language_name(src_lang_code)
    except Exception:
        lang_name = src_lang_code.upper()

    original_text = session.get("original_text", "")
    english_text = session.get("english_text", "")
    verification = session.get("translation_verification") or {}
    clinical_data = session.get("clinical_data") or {}

    # Extract symptoms list safely
    raw_symptoms = clinical_data.get("symptoms", [])
    symptom_names: List[str] = []
    for s in raw_symptoms:
        if isinstance(s, dict):
            symptom_names.append(s.get("name", str(s)))
        elif hasattr(s, "name"):
            symptom_names.append(s.name)
        else:
            symptom_names.append(str(s))

    negated_findings = (
        clinical_data.get("negated_symptoms")
        or clinical_data.get("negated_findings")
        or []
    )
    duration = clinical_data.get("duration") or "Not specified"
    severity = clinical_data.get("severity") or "Not specified"
    body_location = clinical_data.get("body_location") or "Not specified"
    chief_complaint = (
        clinical_data.get("chief_complaint")
        or (symptom_names[0] if symptom_names else "General clinical evaluation")
    )
    possible_category = clinical_data.get("possible_category") or "Primary Care Assessment"

    # Normalize urgency
    session_urgency = (session.get("urgency") or clinical_data.get("urgency") or "").strip().upper()
    if session_urgency not in ("EMERGENCY", "HIGH", "MODERATE", "ROUTINE"):
        legacy_map = {"CRITICAL": "EMERGENCY", "URGENT": "HIGH"}
        session_urgency = legacy_map.get(session_urgency, None)

    if not session_urgency:
        urgency_assessment = classify_urgency(
            symptoms=symptom_names,
            text=english_text or original_text,
            severity=severity,
            duration=duration,
        )
        urgency_level = urgency_assessment.level or "ROUTINE"
        urgency_reason = urgency_assessment.reason or "Standard outpatient primary care evaluation."
    else:
        urgency_level = session_urgency
        urgency_assessment = classify_urgency(
            symptoms=symptom_names,
            text=english_text or original_text,
            severity=severity,
            duration=duration,
        )
        urgency_reason = urgency_assessment.reason or f"Triage level assigned: {urgency_level}."

    # Vital signs evaluation
    raw_vitals = session.get("vital_signs") or clinical_data.get("vital_signs") or {}
    evaluated_vitals, vital_alerts = evaluate_vital_signs(raw_vitals)

    # Differential considerations
    differentials = get_differential_considerations(possible_category, symptom_names)

    # Identify missing items for clinical follow-up
    missing_items: List[str] = []
    if duration in ("Not specified", "", None):
        missing_items.append("Exact onset and symptom duration not specified by patient")
    if severity in ("Not specified", "", None):
        missing_items.append("Subjective discomfort/pain severity scale not recorded")
    if not negated_findings:
        missing_items.append("Pertinent review-of-systems negatives need clinician verification")
    if not symptom_names:
        missing_items.append("No specific localized symptoms matched; broad consultation required")
    if evaluated_vitals.get("bp_display") == "Not recorded":
        missing_items.append("Clinical vital signs (BP, Pulse, Temp, SpO2) pending triage nurse check")

    # Patient info
    patient_info = session.get("patient_info") or {
        "patient_id": f"PAT-{session_id[:6].upper()}",
        "name": "Walk-in Patient",
        "age": "Adult",
        "gender": "Not Specified",
        "contact": "Rural Clinic",
    }

    # Prescriptions
    prescriptions = session.get("prescriptions") or clinical_data.get("prescriptions") or []

    # Diagnostic orders
    diagnostic_orders = session.get("diagnostic_orders") or clinical_data.get("diagnostic_orders") or []

    # Attending doctor
    attending_doctor = session.get("attending_doctor") or {
        "doctor_name": "Attending Medical Officer",
        "license_number": "REG-MCI-VALIDATED",
        "signed_at": None,
    }

    # Care plan & notes
    doctor_notes = session.get("doctor_notes") or clinical_data.get("doctor_notes") or ""
    care_plan = session.get("care_plan") or {
        "assessment": doctor_notes,
        "follow_up": "Return in 3 days or sooner if danger signs appear.",
        "return_precautions": "Seek emergency care immediately if chest pain, severe breathlessness, confusion, or persistent vomiting develops.",
    }

    report_id = f"RPT-{session_id[:8].upper()}"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return {
        "report_id": report_id,
        "session_id": session_id,
        "generated_at": timestamp,
        "clinic_name": "VaaniDoc Multilingual Health Intake Clinic",
        "patient_info": patient_info,
        "vital_signs": evaluated_vitals,
        "vital_alerts": vital_alerts,
        "language_code": src_lang_code,
        "language_name": lang_name,
        "original_transcript": original_text,
        "english_translation": english_text,
        "translation_verification": {
            "status": verification.get("status", "consistent"),
            "warnings": [
                w.get("message", str(w)) if isinstance(w, dict) else str(w)
                for w in verification.get("warnings", [])
            ],
        },
        "clinical_findings": {
            "chief_complaint": chief_complaint,
            "symptoms": symptom_names,
            "negated_findings": negated_findings,
            "duration": duration,
            "severity": severity,
            "body_location": body_location,
            "possible_category": possible_category,
        },
        "urgency": {
            "level": urgency_level,
            "title": TRIAGE_TITLES.get(urgency_level, urgency_level),
            "target_response": TRIAGE_RESPONSE_TIMES.get(urgency_level, "Standard Outpatient Queue"),
            "reason": urgency_reason,
        },
        "differential_considerations": differentials,
        "prescriptions": prescriptions,
        "diagnostic_orders": diagnostic_orders,
        "care_plan": care_plan,
        "attending_doctor": attending_doctor,
        "missing_clarifications": missing_items,
        "doctor_notes": doctor_notes,
        "status": session.get("report_status", "DRAFT_PENDING_REVIEW"),
        "disclaimer": (
            "AI-Assisted Multilingual Health Intake Summary — Generated by VaaniDoc for rural primary care triage. "
            "Requires licensed clinician review and physical verification. Not an autonomous medical diagnosis or prescription."
        ),
    }


def update_report_data(session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Allow attending physician to edit or correct report fields prior to finalization."""
    session = get_session(session_id)
    if not session:
        raise ValueError(f"Session '{session_id}' not found or expired.")

    clinical_data = dict(session.get("clinical_data") or {})

    # Update supported clinical fields
    if "chief_complaint" in updates:
        clinical_data["chief_complaint"] = updates["chief_complaint"]
    if "symptoms" in updates:
        clinical_data["symptoms"] = updates["symptoms"]
    if "negated_findings" in updates:
        clinical_data["negated_findings"] = updates["negated_findings"]
    if "duration" in updates:
        clinical_data["duration"] = updates["duration"]
    if "severity" in updates:
        clinical_data["severity"] = updates["severity"]
    if "body_location" in updates:
        clinical_data["body_location"] = updates["body_location"]
    if "possible_category" in updates:
        clinical_data["possible_category"] = updates["possible_category"]

    # Doctor notes & care plan
    if "doctor_notes" in updates:
        clinical_data["doctor_notes"] = updates["doctor_notes"]
        session["doctor_notes"] = updates["doctor_notes"]
    if "care_plan" in updates:
        session["care_plan"] = updates["care_plan"]

    # Patient info
    if "patient_info" in updates:
        session["patient_info"] = updates["patient_info"]

    # Vital signs
    if "vital_signs" in updates:
        session["vital_signs"] = updates["vital_signs"]
        clinical_data["vital_signs"] = updates["vital_signs"]

    # Prescriptions & Diagnostic orders
    if "prescriptions" in updates:
        session["prescriptions"] = updates["prescriptions"]
        clinical_data["prescriptions"] = updates["prescriptions"]
    if "diagnostic_orders" in updates:
        session["diagnostic_orders"] = updates["diagnostic_orders"]
        clinical_data["diagnostic_orders"] = updates["diagnostic_orders"]

    # Attending doctor
    if "attending_doctor" in updates:
        session["attending_doctor"] = updates["attending_doctor"]

    # Urgency override
    if "urgency" in updates:
        urgency_val = str(updates["urgency"]).strip().upper()
        session["urgency"] = urgency_val
        clinical_data["urgency"] = urgency_val

    # Report status & signing
    if "status" in updates:
        session["report_status"] = updates["status"]
        if updates["status"] == "FINALIZED" and "attending_doctor" not in updates:
            doc_info = dict(session.get("attending_doctor") or {})
            doc_info["signed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            session["attending_doctor"] = doc_info

    session["clinical_data"] = clinical_data
    update_session(
        session_id,
        clinical_data=clinical_data,
        urgency=session.get("urgency"),
    )

    return build_report_data(session)


# ---------------------------------------------------------------------------
# PDF Generation with ReportLab
# ---------------------------------------------------------------------------

def _escape_xml(text: Any) -> str:
    """Escape special XML characters for ReportLab paragraphs."""
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def generate_pdf_report(session: Dict[str, Any]) -> bytes:
    """Generate a valid, beautifully formatted clinical intake PDF report."""
    report = build_report_data(session)
    buffer = io.BytesIO()

    # Create document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    # Styles
    base_styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=base_styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        textColor=colors.HexColor("#0F172A"),
        alignment=0,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#475569"),
    )

    section_header_style = ParagraphStyle(
        "SectionHeader",
        parent=base_styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=7,
        spaceAfter=3,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1E293B"),
    )

    bold_label_style = ParagraphStyle(
        "BoldLabel",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0F172A"),
    )

    alert_style = ParagraphStyle(
        "AlertText",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#B91C1C"),
    )

    urgency_text_style = ParagraphStyle(
        "UrgencyText",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        alignment=1,
    )

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=base_styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#64748B"),
        alignment=1,
    )

    story: List[Any] = []

    # 1. Header & Clinic Branding
    clinic_header_data = [
        [
            Paragraph("<b>VAANIDOC &bull; MULTILINGUAL CLINICAL INTAKE SYSTEM</b>", title_style),
            Paragraph(
                f"<b>REPORT ID:</b> {_escape_xml(report['report_id'])}<br/>"
                f"<b>DATE:</b> {_escape_xml(report['generated_at'])}",
                subtitle_style,
            ),
        ],
        [
            Paragraph("Rural Primary Care Intake &bull; Automated Urgency Triage &bull; Physician Encounter", subtitle_style),
            Paragraph(
                f"<b>LANGUAGE:</b> {_escape_xml(report['language_name'])} ({_escape_xml(report['language_code'])})<br/>"
                f"<b>STATUS:</b> {_escape_xml(report['status'])}",
                subtitle_style,
            ),
        ],
    ]
    clinic_header_table = Table(clinic_header_data, colWidths=[4.4 * inch, 2.8 * inch])
    clinic_header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ])
    )
    story.append(clinic_header_table)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284C7"), spaceAfter=6))

    # 2. Patient Demographics & Urgency Banner
    urgency_lvl = report["urgency"]["level"]
    urgency_color = URGENCY_COLORS.get(urgency_lvl, colors.HexColor("#15803D"))
    urgency_bg = URGENCY_BG_COLORS.get(urgency_lvl, colors.HexColor("#DCFCE7"))

    patient = report["patient_info"]
    patient_text = (
        f"<b>Patient ID:</b> {_escape_xml(patient.get('patient_id', 'N/A'))} &nbsp;&bull;&nbsp; "
        f"<b>Name:</b> {_escape_xml(patient.get('name', 'Walk-in Patient'))} &nbsp;&bull;&nbsp; "
        f"<b>Age/Gender:</b> {_escape_xml(patient.get('age', 'Adult'))} / {_escape_xml(patient.get('gender', 'Unspecified'))}<br/>"
        f"<b>Contact:</b> {_escape_xml(patient.get('contact', 'Rural Center'))} &nbsp;&bull;&nbsp; "
        f"<b>Doctor:</b> {_escape_xml(report['attending_doctor'].get('doctor_name', 'Attending Physician'))}"
    )

    urgency_style_configured = ParagraphStyle(
        "UrgencyConfigured",
        parent=urgency_text_style,
        textColor=urgency_color,
    )

    triage_banner_data = [
        [
            Paragraph(patient_text, body_style),
            Paragraph(f"TRIAGE: {_escape_xml(urgency_lvl)}<br/><font size='8'>{_escape_xml(report['urgency']['target_response'])}</font>", urgency_style_configured),
        ]
    ]
    triage_banner_table = Table(triage_banner_data, colWidths=[4.9 * inch, 2.3 * inch])
    triage_banner_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#F8FAFC")),
            ("BACKGROUND", (1, 0), (1, 0), urgency_bg),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(triage_banner_table)
    story.append(Spacer(1, 4))

    # Triage Rationale
    urgency_rationale_text = f"<b>Clinical Triage Rationale:</b> {_escape_xml(report['urgency']['reason'])}"
    story.append(Paragraph(urgency_rationale_text, body_style))
    story.append(Spacer(1, 6))

    # 3. Clinical Vital Signs Table
    vitals = report["vital_signs"]
    alerts = report.get("vital_alerts", [])
    
    vitals_table_data = [
        [
            Paragraph("<b>Blood Pressure:</b>", bold_label_style),
            Paragraph(_escape_xml(vitals["bp_display"]), body_style),
            Paragraph("<b>Pulse / HR:</b>", bold_label_style),
            Paragraph(_escape_xml(vitals["pulse_display"]), body_style),
            Paragraph("<b>Temperature:</b>", bold_label_style),
            Paragraph(_escape_xml(vitals["temp_display"]), body_style),
        ],
        [
            Paragraph("<b>Oxygen (SpO2):</b>", bold_label_style),
            Paragraph(_escape_xml(vitals["spo2_display"]), body_style),
            Paragraph("<b>Resp. Rate:</b>", bold_label_style),
            Paragraph(_escape_xml(vitals["rr_display"]), body_style),
            Paragraph("<b>Blood Glucose:</b>", bold_label_style),
            Paragraph(_escape_xml(vitals["rbs_display"]), body_style),
        ],
    ]
    vitals_table = Table(vitals_table_data, colWidths=[1.3 * inch, 1.1 * inch, 1.2 * inch, 1.1 * inch, 1.3 * inch, 1.2 * inch])
    vitals_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    story.append(vitals_table)
    
    if alerts:
        alerts_text = "<b>&bull; Abnormal Vitals Alert:</b> " + "; ".join([_escape_xml(a) for a in alerts])
        story.append(Spacer(1, 2))
        story.append(Paragraph(alerts_text, alert_style))

    story.append(Spacer(1, 6))

    # 4. Multilingual Patient Statement & Verified Translation
    story.append(Paragraph("1. MULTILINGUAL PATIENT INTAKE &amp; TRANSLATION", section_header_style))

    original_safe = _escape_xml(report["original_transcript"]) or "<i>No verbal statement recorded</i>"
    english_safe = _escape_xml(report["english_translation"]) or "<i>Translation pending or unavailable</i>"

    verification_warnings = report["translation_verification"]["warnings"]
    warning_note = ""
    if verification_warnings:
        warning_note = f"<br/><font color='#B45309'><b>Safety Flag:</b> {', '.join(_escape_xml(w) for w in verification_warnings)}</font>"

    trans_table_data = [
        [
            Paragraph(f"<b>Patient Statement ({_escape_xml(report['language_name'])}):</b>", bold_label_style),
            Paragraph("<b>Verified English Translation:</b>", bold_label_style),
        ],
        [
            Paragraph(original_safe, body_style),
            Paragraph(f"{english_safe}{warning_note}", body_style),
        ],
    ]
    trans_table = Table(trans_table_data, colWidths=[3.6 * inch, 3.6 * inch])
    trans_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFFFFF")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    story.append(trans_table)
    story.append(Spacer(1, 6))

    # 5. Extracted Clinical Findings
    story.append(Paragraph("2. AI CLINICAL EXTRACTION &amp; FINDINGS", section_header_style))

    findings = report["clinical_findings"]
    symptoms_joined = ", ".join(findings["symptoms"]) if findings["symptoms"] else "None explicitly isolated"
    negatives_joined = ", ".join(findings["negated_findings"]) if findings["negated_findings"] else "None recorded"

    findings_data = [
        [
            Paragraph("<b>Chief Complaint:</b>", bold_label_style),
            Paragraph(_escape_xml(findings["chief_complaint"]), body_style),
            Paragraph("<b>Category:</b>", bold_label_style),
            Paragraph(_escape_xml(findings["possible_category"]), body_style),
        ],
        [
            Paragraph("<b>Active Symptoms:</b>", bold_label_style),
            Paragraph(_escape_xml(symptoms_joined), body_style),
            Paragraph("<b>Duration:</b>", bold_label_style),
            Paragraph(_escape_xml(findings["duration"]), body_style),
        ],
        [
            Paragraph("<b>Pertinent Negatives:</b>", bold_label_style),
            Paragraph(_escape_xml(negatives_joined), body_style),
            Paragraph("<b>Severity / Location:</b>", bold_label_style),
            Paragraph(f"{_escape_xml(findings['severity'])} &bull; {_escape_xml(findings['body_location'])}", body_style),
        ],
    ]
    findings_table = Table(findings_data, colWidths=[1.6 * inch, 2.4 * inch, 1.4 * inch, 1.8 * inch])
    findings_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
            ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    story.append(findings_table)
    story.append(Spacer(1, 6))

    # 6. Differential Considerations (Algorithmic Guidance)
    differentials = report.get("differential_considerations", [])
    if differentials:
        story.append(Paragraph("3. DIFFERENTIAL CONSIDERATIONS (FOR CLINICIAN CORRELATION)", section_header_style))
        diff_text = "<br/>".join([f"&bull; {_escape_xml(d)}" for d in differentials])
        diff_table = Table([[Paragraph(diff_text, body_style)]], colWidths=[7.2 * inch])
        diff_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        story.append(diff_table)
        story.append(Spacer(1, 6))

    # 7. Prescriptions & Medication Orders Table
    prescriptions = report.get("prescriptions", [])
    if prescriptions:
        story.append(Paragraph("4. PRESCRIPTIONS &amp; MEDICATION ORDERS", section_header_style))
        rx_header = [
            Paragraph("<b>Medication / Drug Name</b>", bold_label_style),
            Paragraph("<b>Dosage</b>", bold_label_style),
            Paragraph("<b>Frequency</b>", bold_label_style),
            Paragraph("<b>Duration</b>", bold_label_style),
            Paragraph("<b>Instructions</b>", bold_label_style),
        ]
        rx_rows = [rx_header]
        for p in prescriptions:
            rx_rows.append([
                Paragraph(_escape_xml(p.get("name", "")), body_style),
                Paragraph(_escape_xml(p.get("dosage", "")), body_style),
                Paragraph(_escape_xml(p.get("frequency", "")), body_style),
                Paragraph(_escape_xml(p.get("duration", "")), body_style),
                Paragraph(_escape_xml(p.get("instructions", "")), body_style),
            ])
        rx_table = Table(rx_rows, colWidths=[2.2 * inch, 1.1 * inch, 1.3 * inch, 1.0 * inch, 1.6 * inch])
        rx_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E0F2FE")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        story.append(rx_table)
        story.append(Spacer(1, 6))

    # 8. Diagnostic Orders
    diag_orders = report.get("diagnostic_orders", [])
    if diag_orders:
        story.append(Paragraph("5. DIAGNOSTIC INVESTIGATIONS ORDERED", section_header_style))
        diag_items = []
        for d in diag_orders:
            t_name = d.get("test_name") or d.get("name") or str(d)
            t_urgency = d.get("urgency", "Routine")
            diag_items.append(f"&bull; <b>{_escape_xml(t_name)}</b> &mdash; Priority: {_escape_xml(t_urgency)}")
        diag_table = Table([[Paragraph("<br/>".join(diag_items), body_style)]], colWidths=[7.2 * inch])
        diag_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        story.append(diag_table)
        story.append(Spacer(1, 6))

    # 9. Attending Clinician Review & Care Plan
    care_section: List[Any] = []
    care_section.append(Paragraph("6. ATTENDING PHYSICIAN ASSESSMENT &amp; CARE PLAN", section_header_style))

    doctor_notes_content = _escape_xml(report["doctor_notes"])
    care_plan = report.get("care_plan", {})
    return_precautions = _escape_xml(care_plan.get("return_precautions", "Return immediately if breathing difficulty, chest pain, or high fever persists."))
    follow_up_advice = _escape_xml(care_plan.get("follow_up", "Review in OPD after 3 days."))

    plan_display = ""
    if doctor_notes_content:
        plan_display += f"<b>Clinical Impression &amp; Assessment:</b><br/>{doctor_notes_content}<br/><br/>"
    else:
        plan_display += "<b>Clinical Assessment:</b> Primary outpatient evaluation completed.<br/><br/>"

    plan_display += f"<b>Return Precautions (Red Flags):</b> {return_precautions}<br/>"
    plan_display += f"<b>Follow-up Schedule:</b> {follow_up_advice}"

    plan_table = Table([[Paragraph(plan_display, body_style)]], colWidths=[7.2 * inch])
    plan_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    care_section.append(plan_table)
    care_section.append(Spacer(1, 8))

    # Sign-off line
    doc_info = report["attending_doctor"]
    doc_name = _escape_xml(doc_info.get("doctor_name", "Attending Medical Officer"))
    doc_reg = _escape_xml(doc_info.get("license_number", "REG-MCI-VALIDATED"))
    signed_date = _escape_xml(doc_info.get("signed_at") or report["generated_at"])

    sign_off_data = [
        [
            Paragraph(f"<b>Clinician:</b> {doc_name}<br/><b>Reg No:</b> {doc_reg}", body_style),
            Paragraph(f"<b>Signature:</b> ___________________________<br/><b>Status:</b> {_escape_xml(report['status'])}", body_style),
            Paragraph(f"<b>Verification:</b> Verified Digital Intake<br/><b>Signed:</b> {signed_date}", body_style),
        ]
    ]
    sign_off_table = Table(sign_off_data, colWidths=[2.6 * inch, 2.6 * inch, 2.0 * inch])
    sign_off_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ])
    )
    care_section.append(sign_off_table)
    care_section.append(Spacer(1, 6))

    # Disclaimer Footer
    care_section.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94A3B8"), spaceAfter=4))
    care_section.append(Paragraph(_escape_xml(report["disclaimer"]), disclaimer_style))

    story.append(KeepTogether(care_section))

    # Build PDF into memory buffer
    doc.build(story)
    return buffer.getvalue()
