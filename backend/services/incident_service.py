"""
Incident Agent & Incident Management Service
Handles incident lifecycle, AI analysis classification, team assignment, timeline history, and escalation workflows.
"""

import uuid
from datetime import datetime
from backend.models import get_db
from backend.services.ai_agent_service import classify_incident

def create_incident(data):
    """
    Creates an incident from Participant Portal or Organizer Portal.
    Participant urgency is recorded as input data, but AI independently evaluates actual category, severity, priority, team, and action.
    """
    incident_uuid = str(uuid.uuid4())
    # Generate readable incident number e.g. INC-1042
    with get_db() as conn:
        row_cnt = conn.execute("SELECT COUNT(*) as cnt FROM incidents").fetchone()["cnt"]
        inc_number = f"INC-{1000 + row_cnt + 1}"
    
    title = data.get("title", data.get("incident_type", "Operational Incident"))
    desc = data.get("description", "")
    location = data.get("location", "Venue")
    reporter = data.get("reported_by", data.get("reporter_id", "Participant"))
    source = data.get("source", "Participant" if "reporter_id" in data or "urgency" in data else "Organizer")
    
    # Run AI analysis engine
    ai_res = classify_incident(title, desc)
    category = ai_res.get("category", "Technical")
    severity = ai_res.get("severity", "Medium")
    priority = ai_res.get("priority", "Medium")
    assigned_team = ai_res.get("assigned_team", "General Support")
    recommended_action = ai_res.get("recommended_action", "Follow standard venue operation protocol.")
    
    now = datetime.utcnow().isoformat()
    status = "REPORTED"
    
    with get_db() as conn:
        conn.execute("""
            INSERT INTO incidents (
                id, incident_number, event_id, title, description, category, severity, priority,
                location, affected_area, source, reporter_id, reported_by, assigned_team,
                status, recommended_action, escalated, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident_uuid, inc_number, data.get("event_id", "EVT-1001"), title, desc, category,
            severity, priority, location, location, source, reporter, reporter, assigned_team,
            status, recommended_action, 0, now, now
        ))
        
        # Initial timeline entry
        conn.execute("""
            INSERT INTO incident_timeline (id, incident_id, status, action, description, performed_by, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), incident_uuid, "REPORTED", "Incident Logged",
            f"Incident reported by {reporter} via {source}. AI evaluated priority: {priority}.",
            reporter, now
        ))
        
        # Timeline entry for AI analysis
        conn.execute("""
            INSERT INTO incident_timeline (id, incident_id, status, action, description, performed_by, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), incident_uuid, "ANALYZING", "AI Classification Completed",
            f"AI assigned category '{category}', severity '{severity}', team '{assigned_team}'. Action: {recommended_action}",
            "AI Agent Engine", now
        ))

        # If Critical or High priority, trigger an Operational Alert
        if priority in ["Critical", "High"]:
            alert_sev = "Critical" if priority == "Critical" else "High-Priority"
            conn.execute("""
                INSERT INTO operational_alerts (
                    id, event_id, title, message, alert_type, severity, priority, module,
                    entity_id, status, recommended_action, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"ALT-{uuid.uuid4().hex[:6].upper()}", data.get("event_id", "EVT-1001"),
                f"Incident Alert: {title}", f"{priority} priority incident logged at {location}: {desc}",
                "Incident", alert_sev, priority, "Incident Agent", incident_uuid, "Active",
                recommended_action, now
            ))

    return get_incident_details(incident_uuid)

def get_incidents(category=None, priority=None, status=None, reporter_id=None):
    with get_db() as conn:
        query = "SELECT * FROM incidents WHERE 1=1"
        params = []
        if category and category != "All":
            query += " AND category = ?"
            params.append(category)
        if priority and priority != "All":
            query += " AND priority = ?"
            params.append(priority)
        if status and status != "All":
            query += " AND status = ?"
            params.append(status)
        if reporter_id:
            query += " AND (reporter_id = ? OR reported_by = ?)"
            params.append(reporter_id)
            params.append(reporter_id)
        query += " ORDER BY created_at DESC"

        incidents = conn.execute(query, params).fetchall()
        return [dict(i) for i in incidents]

def get_incident_details(incident_id):
    with get_db() as conn:
        inc = conn.execute("SELECT * FROM incidents WHERE id = ? OR incident_number = ?", (incident_id, incident_id)).fetchone()
        if not inc:
            return None
        result = dict(inc)
        timeline = conn.execute("SELECT * FROM incident_timeline WHERE incident_id = ? ORDER BY timestamp ASC", (result["id"],)).fetchall()
        result["timeline"] = [dict(t) for t in timeline]
        return result

def transition_incident_status(incident_id, new_status, updated_by="Organizer"):
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute("UPDATE incidents SET status = ?, updated_at = ? WHERE id = ?", (new_status, now, incident_id))
        
        # Check if marking resolved or closed
        if new_status in ["Resolved", "Closed"]:
            conn.execute("UPDATE incidents SET resolved_at = ? WHERE id = ?", (now, incident_id))
            # Resolve related alerts
            conn.execute("UPDATE operational_alerts SET status = 'Resolved', resolved_at = ? WHERE entity_id = ?", (now, incident_id))
            
        conn.execute("""
            INSERT INTO incident_timeline (id, incident_id, status, action, description, performed_by, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), incident_id, new_status, f"Status updated to {new_status}",
            f"Incident workflow moved to {new_status} state by {updated_by}.", updated_by, now
        ))
    return get_incident_details(incident_id)

def assign_incident_team(incident_id, team, assigned_by="Organizer"):
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute("UPDATE incidents SET assigned_team = ?, status = 'Assigned', updated_at = ? WHERE id = ?", (team, now, incident_id))
        conn.execute("""
            INSERT INTO incident_timeline (id, incident_id, status, action, description, performed_by, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), incident_id, "Assigned", "Team Assigned",
            f"Response team '{team}' assigned by {assigned_by}.", assigned_by, now
        ))
    return get_incident_details(incident_id)

def escalate_incident(incident_id, reason="Escalated by Operations Lead"):
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute("UPDATE incidents SET priority = 'Critical', severity = 'Critical', status = 'Escalated', escalated = 1, updated_at = ? WHERE id = ?", (now, incident_id))
        inc = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
        inc_dict = dict(inc) if inc else {}

        # Log timeline
        conn.execute("""
            INSERT INTO incident_timeline (id, incident_id, status, action, description, performed_by, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), incident_id, "Escalated", "CRITICAL ESCALATION",
            f"Incident escalated to Critical status: {reason}", "Operations Lead", now
        ))

        # Create Critical Operational Alert
        conn.execute("""
            INSERT INTO operational_alerts (
                id, event_id, title, message, alert_type, severity, priority, module,
                entity_id, status, recommended_action, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"ALT-{uuid.uuid4().hex[:6].upper()}", inc_dict.get("event_id", "EVT-1001"),
            f"CRITICAL ESCALATION: {inc_dict.get('title', 'Incident')}",
            f"Critical escalation reported at {inc_dict.get('location', 'Venue')}: {reason}",
            "Escalation", "Critical", "Critical", "Incident Management", incident_id, "Active",
            inc_dict.get("recommended_action", "Dispatch response team immediately."), now
        ))

    return get_incident_details(incident_id)

def resolve_incident(incident_id, resolution_notes="Resolved by operations team."):
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute("UPDATE incidents SET status = 'Resolved', resolved_at = ?, updated_at = ?, resolution_notes = ? WHERE id = ?", (now, now, resolution_notes, incident_id))
        conn.execute("UPDATE operational_alerts SET status = 'Resolved', resolved_at = ? WHERE entity_id = ?", (now, incident_id))
        
        conn.execute("""
            INSERT INTO incident_timeline (id, incident_id, status, action, description, performed_by, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), incident_id, "Resolved", "Incident Resolved",
            f"Incident resolved: {resolution_notes}", "Assigned Team Lead", now
        ))

    return get_incident_details(incident_id)
