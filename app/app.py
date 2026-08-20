import os
import smtplib
import sys
import textwrap
from datetime import datetime
from email.message import EmailMessage
from io import BytesIO
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from src.database import create_report, get_reports, initialise_database, update_status

st.set_page_config(page_title="JalRakshak AI", page_icon="💧", layout="wide")
MODEL_PATH = BASE_DIR / "models" / "outbreak_model.pkl"
FEATURES_PATH = BASE_DIR / "models" / "features.pkl"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
ISSUES = ["Suspected Water Contamination", "Dirty / Unsafe Drinking Water", "Flooding", "Multiple Illness Cases", "Dead Animals Near Water", "Other"]
STATUSES = ["New", "Under Review", "Monitoring", "Resolved", "✅ Solved", "Emergency"]


def load_env_file():
    env_file = BASE_DIR / ".env"
    if not env_file.exists(): return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


load_env_file()


@st.cache_resource
def load_model():
    try: return joblib.load(MODEL_PATH), joblib.load(FEATURES_PATH)
    except Exception: return None, None


def create_pdf(report_id, name, location, issue, description):
    """Create a polished, printable citizen-report acknowledgement."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Soft water-inspired page background and decorative header.
    pdf.setFillColorRGB(0.96, 0.985, 0.99)
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setFillColorRGB(0.025, 0.20, 0.29)
    pdf.rect(0, height - 142, width, 142, fill=1, stroke=0)
    pdf.setFillColorRGB(0.02, 0.52, 0.64)
    pdf.circle(width - 30, height - 32, 68, fill=1, stroke=0)
    pdf.setFillColorRGB(0.07, 0.34, 0.45)
    pdf.circle(width - 5, height - 116, 52, fill=1, stroke=0)

    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 26)
    pdf.drawString(45, height - 61, "JalRakshak AI")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(45, height - 84, "Citizen Water Safety Report Acknowledgement")
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(45, height - 110, "WATER SAFETY INTELLIGENCE PLATFORM")

    # Reference card.
    y = height - 175
    pdf.setFillColorRGB(1, 1, 1)
    pdf.roundRect(45, y - 46, width - 90, 52, 9, fill=1, stroke=0)
    pdf.setStrokeColorRGB(0.73, 0.87, 0.90)
    pdf.roundRect(45, y - 46, width - 90, 52, 9, fill=0, stroke=1)
    pdf.setFillColorRGB(0.25, 0.38, 0.43)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(58, y - 14, "REFERENCE NUMBER")
    pdf.setFillColorRGB(0.02, 0.20, 0.29)
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(58, y - 33, report_id)
    pdf.setFillColorRGB(0.86, 0.94, 0.88)
    pdf.roundRect(width - 167, y - 34, 107, 24, 8, fill=1, stroke=0)
    pdf.setFillColorRGB(0.08, 0.38, 0.18)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(width - 113, y - 25, "STATUS: NEW")

    y -= 78
    pdf.setFillColorRGB(0.02, 0.20, 0.29)
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(45, y, "Report details")
    y -= 12
    pdf.setStrokeColorRGB(0.05, 0.55, 0.66)
    pdf.setLineWidth(1.5)
    pdf.line(45, y, width - 45, y)
    y -= 18

    fields = [("REPORTER", name), ("LOCATION", location), ("ISSUE TYPE", issue),
              ("DESCRIPTION", description or "Not provided"),
              ("SUBMITTED ON", datetime.now().strftime("%d %B %Y, %I:%M %p"))]
    for label, value in fields:
        lines = textwrap.wrap(str(value).replace("\n", " "), width=65) or ["Not provided"]
        card_height = max(34, 19 + len(lines) * 14)
        pdf.setFillColorRGB(1, 1, 1)
        pdf.roundRect(45, y - card_height, width - 90, card_height, 6, fill=1, stroke=0)
        pdf.setFillColorRGB(0.91, 0.97, 0.98)
        pdf.roundRect(45, y - card_height, 112, card_height, 6, fill=1, stroke=0)
        pdf.setFillColorRGB(0.03, 0.29, 0.38)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(57, y - 17, label)
        pdf.setFillColorRGB(0.05, 0.12, 0.15)
        pdf.setFont("Helvetica", 10)
        for index, line in enumerate(lines):
            pdf.drawString(171, y - 17 - index * 14, line)
        y -= card_height + 10

    pdf.setFillColorRGB(1.0, 0.97, 0.88)
    pdf.roundRect(45, y - 55, width - 90, 55, 7, fill=1, stroke=0)
    pdf.setFillColorRGB(0.35, 0.25, 0.04)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(58, y - 19, "What happens next?")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(58, y - 35, "The authority team can review this report from the JalRakshak dashboard.")

    pdf.setStrokeColorRGB(0.75, 0.84, 0.87)
    pdf.setLineWidth(0.6)
    pdf.line(45, 55, width - 45, 55)
    pdf.setFillColorRGB(0.34, 0.43, 0.47)
    pdf.setFont("Helvetica", 8)
    pdf.drawCentredString(width / 2, 38, "JalRakshak AI | Keep your reference number for follow-up")
    pdf.save()
    return buffer.getvalue()

def save_photo(upload, report_id):
    if upload is None: return None
    ext = Path(upload.name).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png"} or upload.size > 5 * 1024 * 1024: raise ValueError("Use a PNG/JPG photo smaller than 5 MB.")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True); path = UPLOAD_DIR / f"{report_id}{ext}"; path.write_bytes(upload.getvalue())
    return str(path.relative_to(BASE_DIR))


def notify_authority(report_id, location, issue, source):
    """Send a professional HTML alert email for every submitted report."""
    required = ["SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "ALERT_RECIPIENT"]
    if not all(os.getenv(item) for item in required):
        return "Saved to Authority Alert Queue. Email is not configured yet."

    urgent_issues = {"Suspected Water Contamination", "Multiple Illness Cases", "Flooding"}
    severity = "HIGH PRIORITY" if issue in urgent_issues else "NEW REPORT"
    badge_color = "#B42318" if issue in urgent_issues else "#0F766E"
    submitted_at = datetime.now().strftime("%d %B %Y, %I:%M %p")
    message = EmailMessage()
    message["From"] = f"JalRakshak AI Alerts <{os.environ['SMTP_USERNAME']}>"
    message["To"] = os.environ["ALERT_RECIPIENT"]
    message["Subject"] = f"[{severity}] JalRakshak report — {issue}"
    message.set_content(
        f"New JalRakshak report received\n\n"
        f"Reference: {report_id}\nLocation: {location}\nIssue: {issue}\n"
        f"Priority: {severity}\nSubmitted: {submitted_at}\n\n"
        "Open the JalRakshak Authority Dashboard to review and update the report status."
    )
    message.add_alternative(f"""
    <!DOCTYPE html><html><body style="margin:0;background:#f1f5f9;font-family:Arial,sans-serif;color:#16303a;">
      <div style="max-width:640px;margin:24px auto;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #d9e5e8;">
        <div style="padding:30px 34px;background:linear-gradient(135deg,#063b4c,#0b6374);color:#ffffff;">
          <div style="font-size:25px;font-weight:700;">JalRakshak AI</div>
          <div style="font-size:14px;margin-top:7px;color:#d8f3f7;">Water Safety Intelligence Alert</div>
        </div>
        <div style="padding:28px 34px;">
          <span style="display:inline-block;background:{badge_color};color:#ffffff;padding:7px 12px;border-radius:20px;font-size:12px;font-weight:700;letter-spacing:.4px;">{severity}</span>
          <h2 style="margin:20px 0 8px;font-size:21px;color:#0b3340;">A new citizen report needs review</h2>
          <p style="margin:0 0 22px;color:#5c6f77;line-height:1.5;">A water-safety complaint was submitted and is now visible in the Authority Alert Queue.</p>
          <table role="presentation" style="width:100%;border-collapse:separate;border-spacing:0;border:1px solid #d9e5e8;border-radius:10px;overflow:hidden;">
            <tr><td style="padding:12px;background:#eef9fa;width:38%;font-size:12px;font-weight:700;color:#25606d;">REFERENCE ID</td><td style="padding:12px;font-weight:700;color:#0b3340;">{report_id}</td></tr>
            <tr><td style="padding:12px;background:#f8fcfc;font-size:12px;font-weight:700;color:#25606d;">LOCATION</td><td style="padding:12px;">{location}</td></tr>
            <tr><td style="padding:12px;background:#eef9fa;font-size:12px;font-weight:700;color:#25606d;">ISSUE</td><td style="padding:12px;">{issue}</td></tr>
            <tr><td style="padding:12px;background:#f8fcfc;font-size:12px;font-weight:700;color:#25606d;">SOURCE</td><td style="padding:12px;">{source}</td></tr>
            <tr><td style="padding:12px;background:#eef9fa;font-size:12px;font-weight:700;color:#25606d;">SUBMITTED</td><td style="padding:12px;">{submitted_at}</td></tr>
          </table>
          <div style="margin-top:22px;padding:15px 17px;border-left:4px solid {badge_color};background:#f8fafc;color:#334e58;line-height:1.5;">
            <strong>Recommended next step:</strong> Open the JalRakshak Authority Dashboard, review the report and update its status.
          </div>
        </div>
        <div style="padding:17px 34px;background:#f8fafc;border-top:1px solid #d9e5e8;font-size:11px;color:#71858d;">This is an automated JalRakshak AI notification. Please do not reply to this email.</div>
      </div>
    </body></html>
    """, subtype="html")
    try:
        with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.getenv("SMTP_PORT", "587"))) as server:
            server.starttls()
            server.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
            server.send_message(message)
        return "Professional authority email alert sent successfully."
    except (OSError, smtplib.SMTPException) as error:
        return f"Saved to Alert Queue. Email failed: {error}"

initialise_database(); model, features = load_model()
st.markdown("""<style>.stApp{background:radial-gradient(circle at 8% 5%,rgba(34,211,238,.18),transparent 28%),radial-gradient(circle at 95% 15%,rgba(20,184,166,.14),transparent 25%),linear-gradient(135deg,#061824,#0b3040 55%,#07212c)}.block-container{max-width:1250px;padding-top:2.2rem}.hero{font-size:48px;font-weight:800;color:#fff;letter-spacing:-1px}.sub{color:#c7e9f7;font-size:18px;margin-top:4px}.stForm{background:rgba(255,255,255,.06);border:1px solid rgba(125,211,252,.22);border-radius:16px;padding:20px}.stMetric{background:rgba(255,255,255,.06);border-radius:12px;padding:10px}</style><div class="hero">💧 JalRakshak AI</div><div class="sub">Water Safety Intelligence Platform</div>""", unsafe_allow_html=True)
st.divider(); portal = st.radio("Choose your service", ["👤 Citizen Report", "🏛️ Authority Dashboard"], horizontal=True)

if portal == "👤 Citizen Report":
    st.header("Report a Water-Related Issue")
    with st.form("citizen_report", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: name = st.text_input("Your Name *"); location = st.text_input("Location / Area *")
        with c2: issue = st.selectbox("Issue Type *", ISSUES); contact = st.text_input("Contact Number (optional)")
        description = st.text_area("Describe the Issue", max_chars=1000); photo = st.file_uploader("Attach photo (PNG/JPG, max 5 MB)", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("🚨 Submit Report")
    if submitted:
        if not name.strip() or not location.strip(): st.error("Name and location are required.")
        else:
            report_id = create_report(name, location, issue, contact, description, None, None, None)
            try:
                save_photo(photo, report_id)
                st.success(f"Report submitted. Tracking ID: {report_id}")
                st.info(notify_authority(report_id, location, issue, "Citizen"))
                st.download_button("📄 Download PDF receipt", create_pdf(report_id, name, location, issue, description), "JalRakshak_Report.pdf", "application/pdf")
            except ValueError as error: st.error(str(error))
else:
    st.header("🏛️ Authority Control Room")
    reports = pd.DataFrame(get_reports())
    if reports.empty: reports = pd.DataFrame(columns=["report_id", "name", "location", "issue", "status", "created_at"])
    reports["created_at"] = pd.to_datetime(reports["created_at"], errors="coerce")
    new_alerts = reports[reports["status"] == "New"]
    st.subheader("🔔 New Alert Queue")
    if new_alerts.empty: st.success("No new reports waiting for review.")
    else: st.warning(f"{len(new_alerts)} new report(s) need authority review."); st.dataframe(new_alerts[["report_id", "location", "issue", "created_at"]], use_container_width=True, hide_index=True)
    st.divider()
    locations = sorted(reports["location"].dropna().unique().tolist())
    chosen_locations = st.multiselect("Location", locations, default=locations)
    filtered = reports[reports["location"].isin(chosen_locations)]
    m1, m2 = st.columns(2); m1.metric("All reports", len(filtered)); m2.metric("New", int((filtered["status"] == "New").sum()))
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download reports CSV", filtered.to_csv(index=False).encode(), "jalrakshak_reports.csv", "text/csv")
    if not filtered.empty:
        st.subheader("Report distribution"); st.bar_chart(filtered["issue"].value_counts())
        report_id = st.selectbox("Update report", filtered["report_id"].tolist()); status = st.selectbox("New status", STATUSES)
        if st.button("Save status"): update_status(report_id, status); st.success("Status saved. Refresh to view updated queue.")
    st.divider(); st.header("🤖 AI Risk Prediction")
    if model is None: st.warning("Model unavailable. Run src/train_model.py first.")
    else:
        keys = ["rainfall", "temperature", "humidity", "water_ph", "turbidity", "contamination_level", "diarrhea_cases", "population_density", "flood_risk"]
        defaults = [100.0, 30.0, 70.0, 7.0, 40.0, 50.0, 50.0, 1000.0, 40.0]; values = {}; cols = st.columns(3)
        for index, key in enumerate(keys):
            with cols[index % 3]: values[key] = st.number_input(key.replace("_", " ").title(), min_value=0.0, value=defaults[index])
        if st.button("Predict risk"):
            data = pd.DataFrame([values]).reindex(columns=features); prediction = model.predict(data)[0]; confidence = model.predict_proba(data)[0][list(model.classes_).index(prediction)] * 100
            getattr(st, {"High":"error", "Medium":"warning"}.get(prediction, "success"))(f"{prediction.upper()} RISK — Confidence: {confidence:.1f}%")

st.divider(); st.caption("JalRakshak AI | Citizen reports notify the Authority Alert Queue immediately.")






