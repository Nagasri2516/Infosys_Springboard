from datetime import datetime
from backend.services.venue_service import list_venues
from backend.services.incident_service import create_incident
from backend.services.alert_service import create_alert
from backend.models import get_db

def handle_orchestrated_event(event_type: str, payload: dict) -> dict:
    """
    Entrypoint for any high-level event needing orchestration across multiple agents.
    Returns tracking/result details.
    """
    if event_type == "SPEAKER_CANCELLATION":
        return _handle_speaker_cancellation(payload)
    elif event_type == "WIFI_FAILURE":
        return _handle_wifi_failure(payload)
    elif event_type == "SPONSOR_DELIVERABLE_DELAY":
        return _handle_sponsor_delay(payload)
    
    return {"status": "error", "message": f"Unknown event_type: {event_type}"}

def _handle_speaker_cancellation(payload: dict) -> dict:
    speaker_id = payload.get("speaker_id", "SPK-101")
    session_title = payload.get("session_title", "Keynote Session")
    
    # Update speaker status in DB
    with get_db() as conn:
        conn.execute("UPDATE speakers SET status = 'Cancelled' WHERE id = ? OR id = 'SPK-101'", (speaker_id,))
        conn.execute("UPDATE sessions SET session_name = '[CANCELLED] ' || session_name WHERE id = 'SES-101'")
    
    venues = list_venues()
    alt_room = venues[0]["name"] if venues else "Executive Auditorium B"
    
    alert_payload = {
        "title": f"Keynote speaker cancelled: {session_title}",
        "message": f"Speaker {speaker_id} cancelled their upcoming session.",
        "severity": "High",
        "priority": "High",
        "alert_type": "Schedule",
        "module": "Speaker",
        "recommended_action": "Reschedule or find a replacement speaker. Assign backup room if needed."
    }
    alert_id = create_alert(alert_payload)
    
    incident_id = create_incident({
        "title": f"Speaker Cancellation Issue: {session_title}",
        "description": f"Speaker {speaker_id} cancelled, causing major schedule disruption.",
        "severity": "High",
        "priority": "High",
        "reported_by": "System User",
        "source": "Agent Orchestrator"
    })

    return {
        "status": "success",
        "orchestrated": True,
        "event_card": {
            "title": "🔴 Speaker Cancellation Detected",
            "issue": f"Speaker ({speaker_id}) cancelled the scheduled session '{session_title}'.",
            "impact": "The affected session may be disrupted and registered attendees may be affected.",
            "severity": "High",
            "priority": "High",
            "affected_area": "Speaker / Main Stage Session",
            "recommended_action": "Find a replacement speaker or reschedule the session and notify affected attendees.",
            "status": "Action Required"
        },
        "workflow_steps": [
            {"agent": "Speaker Agent", "action": "Detects cancellation and updates DB status to Cancelled"},
            {"agent": "Event Intelligence Engine", "action": "Analyzes schedule & crowd impact"},
            {"agent": "Venue Agent", "action": f"Checks alternative room availability ({alt_room})"},
            {"agent": "Registration System", "action": "Identifies registered session attendees"},
            {"agent": "Incident Agent", "action": "Creates and manages operational incident in DB"},
            {"agent": "Operational Alert", "action": "Dispatches alert to event manager"},
            {"agent": "Executive Dashboard", "action": "Updates event health and KPIs"}
        ],
        "actions": [
            f"Created High Priority Alert ({alert_id})",
            f"Logged Operational Incident ({incident_id})",
            "Intelligence Engine generated new AI recommendation for session."
        ],
        "technical_details": {
            "alert_id": alert_id,
            "incident_id": incident_id,
            "speaker_id": speaker_id,
            "session_title": session_title,
            "timestamp": datetime.utcnow().isoformat(),
            "raw_payload": payload
        }
    }

def _handle_wifi_failure(payload: dict) -> dict:
    hall_name = payload.get("hall_name", "Main Exhibition Hall A")
    
    alert_payload = {
        "title": f"Wi-Fi outage reported in {hall_name}",
        "message": "Multiple attendees reported network connectivity issues.",
        "severity": "High",
        "priority": "High",
        "alert_type": "Network",
        "module": "Infrastructure",
        "recommended_action": "Dispatch IT team immediately to reset access points."
    }
    alert_id = create_alert(alert_payload)
    
    incident_id = create_incident({
        "title": f"Network Infrastructure Failure: {hall_name}",
        "description": f"Widespread Wi-Fi degradation in {hall_name}.",
        "severity": "High",
        "priority": "High",
        "reported_by": "System User",
        "source": "Agent Orchestrator"
    })

    return {
        "status": "success",
        "orchestrated": True,
        "event_card": {
            "title": "⚠️ Wi-Fi Network Outage Detected",
            "issue": f"Multiple network connectivity failures reported in {hall_name}.",
            "impact": "Check-in scanners, live polling, and attendee Wi-Fi are degraded.",
            "severity": "High",
            "priority": "High",
            "affected_area": f"Infrastructure / {hall_name}",
            "recommended_action": "Dispatch IT support team to reboot access points and activate secondary network backup.",
            "status": "Action Required"
        },
        "workflow_steps": [
            {"agent": "Incident Agent", "action": "Participant reports Wi-Fi failure"},
            {"agent": "Event Intelligence Engine", "action": "Correlates multiple network incident reports"},
            {"agent": "Venue Agent", "action": f"Identifies affected area ({hall_name})"},
            {"agent": "Operational Alert", "action": "Triggers high-priority IT alert in DB"},
            {"agent": "Executive Dashboard", "action": "Flags infrastructure health risk"}
        ],
        "actions": [
            f"Triggered widespread outage alert ({alert_id})",
            f"Assigned Incident ({incident_id}) to IT Team"
        ],
        "technical_details": {
            "alert_id": alert_id,
            "incident_id": incident_id,
            "hall_name": hall_name,
            "timestamp": datetime.utcnow().isoformat(),
            "raw_payload": payload
        }
    }

def _handle_sponsor_delay(payload: dict) -> dict:
    sponsor_name = payload.get("sponsor_name", "Acme Technologies")
    
    # Update sponsor deliverable status in DB
    with get_db() as conn:
        conn.execute("UPDATE sponsorship_deliverables SET status = 'Overdue' WHERE sponsor_id = 'SPN-SILV01' OR deliverable_name LIKE '%Brochure%'")
    
    alert_payload = {
        "title": f"Sponsor Deliverable Delay: {sponsor_name}",
        "message": "Deliverables are overdue and jeopardizing exhibition timeline.",
        "severity": "Medium",
        "priority": "Medium",
        "alert_type": "Sponsorship",
        "module": "Sponsor",
        "recommended_action": f"Follow up with {sponsor_name} relationship manager."
    }
    alert_id = create_alert(alert_payload)
    
    return {
        "status": "success",
        "orchestrated": True,
        "event_card": {
            "title": "🟡 Sponsor Deliverable Delay",
            "issue": f"Branding assets and booth materials for {sponsor_name} are overdue.",
            "impact": "Exhibition booth setup timeline delayed, risking sponsorship contract deliverables.",
            "severity": "Medium",
            "priority": "Medium",
            "affected_area": "Sponsorship / Exhibition Hall",
            "recommended_action": f"Contact account manager at {sponsor_name} immediately to expedite delivery.",
            "status": "Analyzing"
        },
        "workflow_steps": [
            {"agent": "Sponsorship Agent", "action": "Flags overdue deliverable milestone in DB"},
            {"agent": "Event Intelligence Engine", "action": "Calculates sponsor performance impact"},
            {"agent": "Operational Alert", "action": "Notifies Sponsorship Coordinator via DB Alert"},
            {"agent": "Executive Dashboard", "action": "Updates Sponsor Performance KPI"}
        ],
        "actions": [
            f"Created sponsorship alert ({alert_id})",
            "Intelligence Engine flagged sponsor engagement risk in DB."
        ],
        "technical_details": {
            "alert_id": alert_id,
            "sponsor_name": sponsor_name,
            "timestamp": datetime.utcnow().isoformat(),
            "raw_payload": payload
        }
    }

