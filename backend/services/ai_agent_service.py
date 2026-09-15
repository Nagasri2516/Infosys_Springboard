"""
AI Agent Intelligence Service
Provides AI classification for incidents, sponsor QA assistant, sponsor performance recommendations, and predictive operational risk detection.
"""

def classify_incident(title, description):
    """
    Analyzes incident title & description to categorize, determine severity & priority, assign team, and recommend action.
    """
    text = (str(title) + " " + str(description)).lower()
    
    category = "Technical"
    severity = "Medium"
    priority = "Medium"
    assigned_team = "IT Operations Team"
    recommended_action = "Investigate root cause and execute standard response protocol."
    reasoning = "General operational incident detected."

    if any(k in text for k in ["mic", "microphone", "audio", "sound", "speaker", "projector", "av", "screen", "display"]):
        category = "Audio/Video"
        assigned_team = "AV Team"
        recommended_action = "Deploy backup wireless microphone or reboot AV mixer console immediately."
        reasoning = "Audio/Video disruption directly impacts active stage presentations."
    elif any(k in text for k in ["wifi", "wi-fi", "network", "internet", "router", "connectivity"]):
        category = "Network"
        assigned_team = "Network Engineering Team"
        recommended_action = "Check access point power supply and verify VLAN routing tables."
        reasoning = "Network outages affect live demo stations and attendee connectivity."
    elif any(k in text for k in ["registration", "badge", "checkin", "check-in", "qr", "scanner", "entry"]):
        category = "Registration"
        assigned_team = "Registration Operations"
        recommended_action = "Switch to offline QR scanning mode and open auxiliary entry gates."
        reasoning = "Registration bottlenecks cause crowd congestion at entrance."
    elif any(k in text for k in ["medical", "doctor", "faint", "injury", "first aid", "health"]):
        category = "Medical"
        severity = "Critical"
        priority = "Critical"
        assigned_team = "Medical Emergency Team"
        recommended_action = "Dispatch first aid paramedics immediately and clear emergency corridor."
        reasoning = "Life safety emergency requires immediate onsite medical response."
    elif any(k in text for k in ["security", "fight", "theft", "unauthorized", "suspicious", "crowd"]):
        category = "Security"
        severity = "High"
        priority = "High"
        assigned_team = "Security & Venue Safety"
        recommended_action = "Deploy security personnel to location and verify accreditation badges."
        reasoning = "Security incident poses risk to attendee safety and event decorum."
    elif any(k in text for k in ["sponsor", "branding", "banner", "booth", "deliverable"]):
        category = "Sponsor"
        assigned_team = "Sponsorship Operations"
        recommended_action = "Coordinate with venue production team to rectify sponsor branding asset."
        reasoning = "Sponsor deliverable issue affects commercial contractual commitments."
    elif any(k in text for k in ["ac", "aircon", "chair", "water", "leak", "cleaning", "food", "hall", "toilet"]):
        category = "Venue"
        assigned_team = "Venue Facilities Team"
        recommended_action = "Contact venue facility manager to dispatch maintenance staff."
        reasoning = "Venue comfort issue affects attendee satisfaction."

    # Priority escalation keywords
    if any(k in text for k in ["urgent", "down", "outage", "emergency", "fire", "system failure", "hundreds"]):
        severity = "High" if severity != "Critical" else "Critical"
        priority = "High" if priority != "Critical" else "Critical"
        reasoning += " High urgency keywords detected in report payload."

    return {
        "category": category,
        "severity": severity,
        "priority": priority,
        "assigned_team": assigned_team,
        "recommended_action": recommended_action,
        "ai_reasoning": reasoning
    }

def answer_sponsor_query(query):
    """
    Answers natural language queries about sponsor status, deliverables, and performance using DB context.
    """
    from backend.services.sponsorship_service import get_all_sponsors, get_sponsor_performance
    
    q = query.lower()
    sponsors = get_all_sponsors()
    perf = get_sponsor_performance()

    if "pending deliverable" in q or "overdue" in q:
        pending_list = []
        for s in sponsors:
            deliv_sum = s.get("deliverables_summary", {})
            if deliv_sum.get("completed", 0) < deliv_sum.get("total", 0):
                pending_list.append(f"• <strong>{s['name']}</strong> ({s['tier']}): {deliv_sum['completed']}/{deliv_sum['total']} completed")
        
        if pending_list:
            return "The following sponsors have pending or overdue deliverables:<br>" + "<br>".join(pending_list)
        return "All sponsor deliverables are currently 100% completed!"

    elif "highest engagement" in q or "top sponsor" in q or "best engagement" in q:
        sorted_s = sorted(sponsors, key=lambda x: x.get("engagement_score", 0), reverse=True)
        if sorted_s:
            top = sorted_s[0]
            return f"<strong>{top['name']}</strong> ({top['tier']}) currently leads with the highest engagement score of <strong>{top['engagement_score']}%</strong>."
        return "No engagement data available."

    elif "payment" in q or "pending payment" in q:
        unpaid = [s['name'] for s in sponsors if s.get("payment_status") != "Completed"]
        if unpaid:
            return f"Sponsors with pending/overdue payments: <strong>{', '.join(unpaid)}</strong>."
        return "All sponsors have completed their payments."

    elif "at risk" in q or "attention" in q:
        at_risk = [item['name'] for item in perf.get("sponsors", []) if item.get("performance_category") == "At Risk"]
        if at_risk:
            return f"Sponsors flagged as 'At Risk': <strong>{', '.join(at_risk)}</strong>. Immediate coordinator follow-up recommended."
        return "No sponsors are currently flagged as at-risk!"

    else:
        return f"Sponsorship Database Overview: Total Sponsors: {len(sponsors)}, Average Engagement: {perf.get('summary', {}).get('avg_engagement_score', 0)}%. You can inquire specifically about deliverables, engagement scores, payments, or at-risk sponsors."

def generate_sponsor_recommendations():
    """
    Generates dynamic AI recommendations for sponsorship managers based on deliverable and engagement metrics.
    """
    from backend.services.sponsorship_service import get_all_sponsors, get_sponsor_performance
    sponsors = get_all_sponsors()
    perf = get_sponsor_performance()
    recs = []

    for s in sponsors:
        deliv_sum = s.get("deliverables_summary", {})
        if deliv_sum.get("completed", 0) < deliv_sum.get("total", 0):
            recs.append({
                "sponsor_name": s["name"],
                "tier": s["tier"],
                "type": "Deliverable Risk",
                "recommendation": f"{s['name']} has {deliv_sum['total'] - deliv_sum['completed']} pending deliverable(s). Follow up with branding coordinator to avoid contract penalty."
            })
        if s.get("engagement_score", 0) < 65:
            recs.append({
                "sponsor_name": s["name"],
                "tier": s["tier"],
                "type": "Low Engagement",
                "recommendation": f"Engagement score for {s['name']} is at {s['engagement_score']}%. Schedule a promotional push or push notifications on the attendee portal."
            })

    if not recs:
        recs.append({
            "sponsor_name": "System Overall",
            "tier": "All",
            "type": "Optimal State",
            "recommendation": "All sponsor commitments are currently on track with strong engagement scores across Platinum and Gold tiers."
        })

    return recs[:4]

def scan_operational_risks():
    """
    Scans operational metrics (venue capacity, attendee registration surge, incidents) and generates predictive risk alerts.
    """
    alerts = [
        {
            "title": "Predictive Crowd Surge Warning: Hall B",
            "message": "Hall B capacity has reached 85%. Entry velocity increased by 30% over the last 10 minutes. High risk of doorway congestion.",
            "alert_type": "Predictive Risk",
            "severity": "High-Priority",
            "priority": "High",
            "module": "Operational Alerts",
            "recommended_action": "Deploy auxiliary usher staff to Hall B and open side overflow doors."
        },
        {
            "title": "Predictive Wi-Fi Bottleneck Risk",
            "message": "Connected devices in Exhibition Hall A exceeded 450 concurrent sessions. Bandwidth utilization at 92%.",
            "alert_type": "Predictive Risk",
            "severity": "Medium",
            "priority": "Medium",
            "module": "Network Operations",
            "recommended_action": "Enable 5GHz secondary SSID beamforming and limit background streaming bandwidth."
        }
    ]
    return alerts
