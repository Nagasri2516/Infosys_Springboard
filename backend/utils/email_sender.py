"""
Email Sender Utility
Dual-mode email dispatcher:
  1. Real SMTP delivery when SMTP_USER + SMTP_PASSWORD are configured.
  2. HTML-file fallback – writes a styled receipt to backend/outbox/
     so you can preview it instantly in the browser Dashboard.
"""

import os
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text       import MIMEText
from email.mime.image      import MIMEImage
from datetime              import datetime

from backend.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USE_TLS, SMTP_USER, SMTP_PASSWORD,
    SENDER_NAME, SENDER_EMAIL, OUTBOX_DIR,
    EVENT_NAME, EVENT_DATE, EVENT_VENUE
)


# ─── HTML Template ────────────────────────────────────────────────────────────

def _build_html(reg: dict) -> str:
    """Render a stylish HTML email receipt for the registration."""
    qr_url = f"http://localhost:5000{reg.get('qr_code_path','')}"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Registration Confirmed – {EVENT_NAME}</title>
  <style>
    body {{ margin:0; padding:0; background:#0f172a; font-family:'Segoe UI',sans-serif; color:#f8fafc; }}
    .wrapper {{ max-width:600px; margin:40px auto; background:rgba(30,41,59,0.95);
                border-radius:20px; overflow:hidden;
                border:1px solid rgba(99,102,241,0.25);
                box-shadow:0 20px 60px rgba(0,0,0,0.5); }}
    .header {{ background:linear-gradient(135deg,#6366f1,#a855f7); padding:36px 32px; text-align:center; }}
    .header h1 {{ margin:0; font-size:1.6rem; font-weight:800; letter-spacing:-0.5px; }}
    .header p  {{ margin:8px 0 0; font-size:0.9rem; opacity:0.85; }}
    .badge {{ display:inline-block; margin-top:16px; background:rgba(255,255,255,0.15);
              border:1px solid rgba(255,255,255,0.3); border-radius:30px;
              padding:6px 20px; font-size:0.85rem; font-weight:600; letter-spacing:1px; }}
    .body   {{ padding:32px; }}
    .greeting {{ font-size:1.1rem; margin-bottom:20px; }}
    .ticket  {{ background:rgba(15,23,42,0.6); border:1px dashed rgba(255,255,255,0.12);
                border-radius:14px; padding:20px 24px; margin:20px 0; }}
    .row     {{ display:flex; justify-content:space-between; align-items:center;
                padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.05);
                font-size:0.9rem; }}
    .row:last-child {{ border-bottom:none; }}
    .lbl     {{ color:#94a3b8; }}
    .val     {{ font-weight:600; font-family:monospace; }}
    .qr-wrap {{ text-align:center; margin:24px 0; }}
    .qr-wrap img {{ background:#f8fafc; padding:12px; border-radius:12px;
                    width:160px; height:160px; }}
    .footer  {{ text-align:center; padding:20px 32px 32px; font-size:0.8rem; color:#64748b; }}
    .btn     {{ display:inline-block; margin:16px auto; background:linear-gradient(135deg,#6366f1,#a855f7);
                color:#fff; padding:12px 32px; border-radius:10px; text-decoration:none;
                font-weight:700; font-size:0.95rem; }}
  </style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>🎉 Registration Confirmed!</h1>
    <p>{EVENT_NAME}</p>
    <span class="badge">✓ You're Registered</span>
  </div>
  <div class="body">
    <p class="greeting">Hello <strong>{reg.get('full_name','Attendee')}</strong>,</p>
    <p style="color:#94a3b8;font-size:0.9rem;line-height:1.6;">
      Your registration for <strong>{EVENT_NAME}</strong> has been successfully received and confirmed.
      Please bring this QR code on event day for seamless check-in.
    </p>

    <div class="ticket">
      <div class="row"><span class="lbl">Registration ID</span><span class="val">{reg.get('id','—')}</span></div>
      <div class="row"><span class="lbl">Full Name</span><span class="val">{reg.get('full_name','—')}</span></div>
      <div class="row"><span class="lbl">Email</span><span class="val">{reg.get('email','—')}</span></div>
      <div class="row"><span class="lbl">Role</span><span class="val">{reg.get('role_category','—')}</span></div>
      <div class="row"><span class="lbl">Organization</span><span class="val">{reg.get('organization','N/A')}</span></div>
      <div class="row"><span class="lbl">Source</span><span class="val">{reg.get('source','—')}</span></div>
      <div class="row"><span class="lbl">Event Date</span><span class="val">{EVENT_DATE}</span></div>
      <div class="row"><span class="lbl">Venue</span><span class="val">{EVENT_VENUE}</span></div>
    </div>

    <div class="qr-wrap">
      <p style="color:#94a3b8;font-size:0.85rem;margin-bottom:12px;">Your Personal Check-in QR Code</p>
      <img src="{qr_url}" alt="QR Code for {reg.get('id','')}" />
      <p style="font-family:monospace;font-size:0.8rem;color:#64748b;margin-top:8px;">{reg.get('id','')}</p>
    </div>

    <p style="color:#94a3b8;font-size:0.85rem;line-height:1.6;margin-top:16px;">
      If you have any questions, please contact the organizers.
    </p>
  </div>
  <div class="footer">
    <p>© 2026 {EVENT_NAME} · Powered by EventCore</p>
    <p>This is an automated message. Please do not reply directly.</p>
  </div>
</div>
</body>
</html>"""


# ─── Outbox Fallback ─────────────────────────────────────────────────────────

def _save_to_outbox(reg: dict, html: str) -> dict:
    """Write the email HTML to outbox/ and return a metadata dict."""
    reg_id    = reg.get("id", "UNKNOWN")
    filename  = f"email_{reg_id}.html"
    filepath  = os.path.join(OUTBOX_DIR, filename)
    meta_file = filepath.replace(".html", ".json")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    meta = {
        "id":         reg_id,
        "to":         reg.get("email", ""),
        "name":       reg.get("full_name", ""),
        "subject":    f"Registration Confirmed – {reg_id} | {EVENT_NAME}",
        "html_file":  filename,
        "sent_at":    datetime.utcnow().isoformat() + "Z",
        "delivered":  False,
        "mode":       "outbox"
    }
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return meta


# ─── SMTP Delivery ────────────────────────────────────────────────────────────

def _send_smtp(to_email: str, subject: str, html: str) -> bool:
    """Attempt real SMTP delivery. Returns True on success."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            if SMTP_USE_TLS:
                server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[EmailSender] SMTP failed: {e}")
        return False


# ─── Public API ───────────────────────────────────────────────────────────────

def send_registration_email(reg: dict) -> dict:
    """
    Send (or simulate) a registration confirmation email.

    Returns a result dict with keys:
      delivered (bool), mode ('smtp'|'outbox'), html_file (str|None)
    """
    html    = _build_html(reg)
    subject = f"Registration Confirmed – {reg.get('id','')} | {EVENT_NAME}"

    # Try real SMTP if credentials are configured
    if SMTP_USER and SMTP_PASSWORD:
        ok = _send_smtp(reg.get("email", ""), subject, html)
        if ok:
            return {"delivered": True, "mode": "smtp", "html_file": None}

    # Fall back to outbox
    meta = _save_to_outbox(reg, html)
    print(f"[EmailSender] Saved to outbox -> {meta['html_file']}")
    return meta
