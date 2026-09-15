"""
Operational Alerts Service
Handles real-time operational notifications, severity filtering, acknowledgement/resolution workflows, and AI predictive risk scans.
"""

import uuid
from datetime import datetime
from backend.models import get_db
from backend.services.ai_agent_service import scan_operational_risks

def get_alerts(severity=None, status=None):
    with get_db() as conn:
        query = "SELECT * FROM operational_alerts WHERE 1=1"
        params = []
        if severity and severity != "All":
            query += " AND severity = ?"
            params.append(severity)
        if status and status != "All":
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY timestamp DESC"

        alerts = conn.execute(query, params).fetchall()
        return [dict(a) for a in alerts]

def create_alert(data):
    alert_id = f"ALT-{uuid.uuid4().hex[:6].upper()}"
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO operational_alerts (
                id, event_id, title, message, alert_type, severity, priority, module,
                entity_id, status, recommended_action, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert_id,
            data.get("event_id", "EVT-1001"),
            data.get("title", "Operational Alert"),
            data.get("message", ""),
            data.get("alert_type", "Operational"),
            data.get("severity", "Medium"),
            data.get("priority", "Medium"),
            data.get("module", "System"),
            data.get("entity_id", None),
            "Active",
            data.get("recommended_action", "Acknowledge and inspect affected area."),
            now
        ))
    return alert_id

def acknowledge_alert(alert_id):
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute("UPDATE operational_alerts SET status = 'Acknowledged', acknowledged_at = ? WHERE id = ?", (now, alert_id))
    return True

def resolve_alert(alert_id):
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute("UPDATE operational_alerts SET status = 'Resolved', resolved_at = ? WHERE id = ?", (now, alert_id))
    return True

def generate_predictive_risk_alerts():
    risks = scan_operational_risks()
    created_count = 0
    with get_db() as conn:
        for r in risks:
            # Check if alert already exists to prevent duplicate
            existing = conn.execute("SELECT id FROM operational_alerts WHERE title = ? AND status != 'Resolved'", (r["title"],)).fetchone()
            if not existing:
                conn.execute("""
                    INSERT INTO operational_alerts (
                        id, event_id, title, message, alert_type, severity, priority, module,
                        status, recommended_action, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"ALT-{uuid.uuid4().hex[:6].upper()}", "EVT-1001", r["title"], r["message"],
                    r["alert_type"], r["severity"], r["priority"], r["module"],
                    "Active", r["recommended_action"], datetime.utcnow().isoformat()
                ))
                created_count += 1
    return created_count
