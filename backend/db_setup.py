"""
Database Setup & Mock Data Seeder
Run this script once (or via /api/debug/reset) to initialise tables
and populate 15 realistic attendee records with QR codes and outbox emails.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.models              import init_db, get_db, generate_id
from backend.utils.qr_generator  import generate_qr
from backend.utils.email_sender  import send_registration_email
from datetime import datetime, timedelta
import random

MOCK_REGISTRATIONS = [
    {"full_name": "Alex Rivera",      "email": "alex.rivera@edu.org",        "phone": "415-555-0192", "role_category": "Student",       "organization": "Stanford University",   "source": "Web Form",     "checked_in": 1, "days_ago": 3},
    {"full_name": "Dr. Sarah Jenkins","email": "sjenkins@techcorp.com",       "phone": "212-555-0143", "role_category": "Mentor",        "organization": "Quantum Technologies",  "source": "Google Forms", "checked_in": 1, "days_ago": 3},
    {"full_name": "Marcus Chen",      "email": "marcus.chen@innovate.io",     "phone": "650-555-0188", "role_category": "Professional",  "organization": "Innovate Labs",         "source": "Mobile App",   "checked_in": 0, "days_ago": 2},
    {"full_name": "Emily Watson",     "email": "emily.watson@mit.edu",        "phone": "617-555-0129", "role_category": "Student",       "organization": "MIT Research",          "source": "API",          "checked_in": 1, "days_ago": 2},
    {"full_name": "David Kim",        "email": "d.kim@ventures.com",          "phone": "310-555-0176", "role_category": "Professional",  "organization": "Apex Ventures",         "source": "Web Form",     "checked_in": 0, "days_ago": 2},
    {"full_name": "Sophia Martinez",  "email": "sophia.m@designs.com",        "phone": "512-555-0155", "role_category": "Mentor",        "organization": "Prism Design Studio",   "source": "Google Forms", "checked_in": 0, "days_ago": 1},
    # Intentional duplicates for AI detection
    {"full_name": "Alice Johnson",    "email": "alice.j@domain.com",          "phone": "312-555-0144", "role_category": "Student",       "organization": "City College",          "source": "Web Form",     "checked_in": 1, "days_ago": 1},
    {"full_name": "Alice Johnson",    "email": "alice.j@domain.com",          "phone": "312-555-0144", "role_category": "Student",       "organization": "City College Inc",      "source": "Google Forms", "checked_in": 0, "days_ago": 1},
    {"full_name": "Robert Smith",     "email": "rsmith@freelance.org",        "phone": "800-555-0100", "role_category": "Professional",  "organization": "Freelance",             "source": "Mobile App",   "checked_in": 0, "days_ago": 1},
    {"full_name": "Robert Smith",     "email": "rsmith@freelance.org",        "phone": "800-555-0100", "role_category": "Professional",  "organization": "Freelance Developers",  "source": "API",          "checked_in": 0, "days_ago": 1},
    {"full_name": "Elena Rostova",    "email": "e.rostova@academy.ru",        "phone": "702-555-0167", "role_category": "Student",       "organization": "State University",      "source": "Web Form",     "checked_in": 1, "days_ago": 1},
    {"full_name": "Tyler Durden",     "email": "soap@project.org",            "phone": "206-555-0150", "role_category": "Professional",  "organization": "Paper Street Soap Co", "source": "API",          "checked_in": 0, "days_ago": 0},
    {"full_name": "Jane Doe",         "email": "jane.doe@standard.com",       "phone": "917-555-0111", "role_category": "Organizer",     "organization": "Standard Agency",       "source": "Mobile App",   "checked_in": 1, "days_ago": 3},
    {"full_name": "Prof. Alan Turing","email": "turing@bletchley.edu",        "phone": "508-555-0199", "role_category": "Mentor",        "organization": "King's College",        "source": "Web Form",     "checked_in": 1, "days_ago": 3},
    {"full_name": "Dr. Grace Hopper", "email": "hopper@navy.mil",             "phone": "703-555-0133", "role_category": "Mentor",        "organization": "US Navy",               "source": "API",          "checked_in": 1, "days_ago": 3},
]


def seed(send_emails: bool = True):
    """Initialise DB and insert mock records."""
    init_db()

    with get_db() as conn:
        conn.execute("DELETE FROM check_ins")
        conn.execute("DELETE FROM registrations")

    print("[OK] Tables cleared")

    for m in MOCK_REGISTRATIONS:
        reg_id  = generate_id("REG")
        qr_path = generate_qr(reg_id)
        days_ago = m.pop("days_ago", 0)
        checked_in = m.pop("checked_in", 0)
        now      = (datetime.utcnow() - timedelta(days=days_ago)).isoformat()
        checkin_time = now if checked_in else None

        reg = {
            "id":               reg_id,
            "full_name":        m["full_name"],
            "email":            m["email"].lower(),
            "phone":            m["phone"],
            "role_category":    m["role_category"],
            "organization":     m.get("organization", ""),
            "state":            "",
            "country":          "",
            "area_of_interest": "",
            "qr_code_path":     qr_path,
            "status":           "confirmed" if checked_in else "pending",
            "source":           m.get("source", "Web Form"),
            "checked_in":       checked_in,
            "check_in_time":    checkin_time,
            "created_at":       now,
            "updated_at":       now,
        }

        with get_db() as conn:
            conn.execute("""
                INSERT INTO registrations
                  (id, full_name, email, phone, role_category, organization,
                   state, country, area_of_interest, qr_code_path,
                   status, source, checked_in, check_in_time, created_at, updated_at)
                VALUES
                  (:id, :full_name, :email, :phone, :role_category, :organization,
                   :state, :country, :area_of_interest, :qr_code_path,
                   :status, :source, :checked_in, :check_in_time, :created_at, :updated_at)
            """, reg)

        if checked_in:
            with get_db() as conn:
                import uuid
                conn.execute("""
                    INSERT INTO check_ins (id, registration_id, check_in_time, check_in_method)
                    VALUES (?, ?, ?, 'manual')
                """, (str(uuid.uuid4()), reg_id, checkin_time))

        if send_emails:
            send_registration_email(reg)

        print(f"  [OK] {reg['full_name']} -> {reg_id}")

    print(f"\n[DONE] Seeded {len(MOCK_REGISTRATIONS)} registrations into database.")

    # Seed M3 Data
    seed_m3_data()


def seed_m3_data():
    """Seeds Milestone 3 & Milestone 4 mock data for events, venues, speakers, sessions, sponsors, incidents, and alerts."""
    import uuid
    from datetime import datetime
    now = datetime.utcnow().isoformat()

    with get_db() as conn:
        conn.execute("DELETE FROM incident_timeline")
        conn.execute("DELETE FROM incidents")
        conn.execute("DELETE FROM operational_alerts")
        conn.execute("DELETE FROM sponsorship_deliverables")
        conn.execute("DELETE FROM sponsor_engagements")
        conn.execute("DELETE FROM sponsors")
        conn.execute("DELETE FROM speaker_messages")
        conn.execute("DELETE FROM speaker_assignments")
        conn.execute("DELETE FROM session_attendance")
        conn.execute("DELETE FROM feedback")
        conn.execute("DELETE FROM sessions")
        conn.execute("DELETE FROM venue_bookings")
        conn.execute("DELETE FROM speakers")
        conn.execute("DELETE FROM venues")
        conn.execute("DELETE FROM events")

        # 0. Demo Event
        conn.execute("""
            INSERT INTO events (id, name, description, event_type, start_date, end_date, location, expected_attendees, status, created_at)
            VALUES ('EVT-1001', 'AI & Tech Executive Summit 2026', 'Annual flagship conference on AI Agent Orchestration and Event Intelligence.', 'Conference', '2026-09-01', '2026-09-03', 'Convention Center - Main Campus', 100, 'Active', ?)
        """, (now,))

        # 0.1 Venues
        venues_data = [
            ("VEN-101", "Main Exhibition Hall A", "Floor 1", "Convention Center", 100, "Main Hall", 5000.0, "Available"),
            ("VEN-102", "Executive Auditorium B", "Floor 2", "Convention Center", 50, "Auditorium", 3000.0, "Available"),
            ("VEN-103", "Workshop Suite C", "Floor 3", "Convention Center", 30, "Workshop Room", 1500.0, "Available")
        ]
        for vid, vname, loc, addr, cap, vtype, cost, avail in venues_data:
            conn.execute("""
                INSERT INTO venues (id, name, location, address, capacity, venue_type, cost, availability_status, wifi, projector, sound_system)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 1)
            """, (vid, vname, loc, addr, cap, vtype, cost, avail))

        # 0.2 Speakers
        speakers_data = [
            ("SPK-101", "Dr. Aris Thorne", "AI Research Institute", "Director of Research", "Agentic Systems", 12, "Keynote speaker on autonomous multi-agent orchestration.", "Confirmed"),
            ("SPK-102", "Elena Rostova", "Quantum Analytics Labs", "VP of Engineering", "Predictive Analytics", 9, "Expert in real-time operational risk modeling.", "Confirmed"),
            ("SPK-103", "Marcus Vance", "CyberPulse Security", "Chief Security Officer", "Event Infrastructure", 15, "Specialist in high-concurrency event Wi-Fi and IoT security.", "Confirmed")
        ]
        for sid, sname, org, desig, exp, yrs, bio, st in speakers_data:
            conn.execute("""
                INSERT INTO speakers (id, name, organization, designation, expertise, years_of_experience, biography, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sid, sname, org, desig, exp, yrs, bio, st))

        # 0.3 Sessions
        sessions_data = [
            ("SES-101", "EVT-1001", "Keynote: Agentic Workflows in Enterprise", "Agent Orchestration", "Keynote", "2026-09-01", "09:00 AM", "10:30 AM", "VEN-101", 85),
            ("SES-102", "EVT-1001", "Deep-Dive: Predictive Event Intelligence", "Data Analytics", "Technical Session", "2026-09-01", "11:00 AM", "12:30 PM", "VEN-102", 45),
            ("SES-103", "EVT-1001", "Workshop: Real-Time Network Security", "Security Ops", "Hands-on Workshop", "2026-09-01", "02:00 PM", "04:00 PM", "VEN-103", 25)
        ]
        for ses_id, eid, sname, topic, stype, sdate, stime, etime, vid, exp_att in sessions_data:
            conn.execute("""
                INSERT INTO sessions (id, event_id, session_name, topic, session_type, session_date, start_time, end_time, venue_id, expected_attendees)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ses_id, eid, sname, topic, stype, sdate, stime, etime, vid, exp_att))

        # 1. Sponsors
        sponsors_data = [
            {
                "id": "SPN-PLAT01", "name": "TechGlobal Cloud Solutions", "tier": "Platinum",
                "contact_person": "Sarah Jenkins", "contact_email": "s.jenkins@techglobal.com",
                "phone": "+1 (555) 234-5678", "contract_status": "Signed", "contract_value": 25000.0,
                "payment_status": "Completed", "total_amount": 25000.0, "paid_amount": 25000.0,
                "engagement_score": 92, "overall_performance": "Excellent"
            },
            {
                "id": "SPN-GOLD01", "name": "InnoSoft AI Corp", "tier": "Gold",
                "contact_person": "David Chen", "contact_email": "d.chen@innosoft.ai",
                "phone": "+1 (555) 345-6789", "contract_status": "Signed", "contract_value": 15000.0,
                "payment_status": "Partial", "total_amount": 15000.0, "paid_amount": 7500.0,
                "engagement_score": 78, "overall_performance": "Good"
            },
            {
                "id": "SPN-SILV01", "name": "CyberPulse Security", "tier": "Silver",
                "contact_person": "Marcus Vance", "contact_email": "m.vance@cyberpulse.io",
                "phone": "+1 (555) 456-7890", "contract_status": "Pending Review", "contract_value": 7500.0,
                "payment_status": "Pending", "total_amount": 7500.0, "paid_amount": 0.0,
                "engagement_score": 58, "overall_performance": "Needs Attention"
            }
        ]

        for s in sponsors_data:
            conn.execute("""
                INSERT INTO sponsors (
                    id, event_id, name, tier, contact_person, contact_email, phone,
                    contract_status, contract_value, payment_status, total_amount, paid_amount,
                    engagement_score, overall_performance, created_at
                ) VALUES (?, 'EVT-1001', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                s["id"], s["name"], s["tier"], s["contact_person"], s["contact_email"], s["phone"],
                s["contract_status"], s["contract_value"], s["payment_status"], s["total_amount"],
                s["paid_amount"], s["engagement_score"], s["overall_performance"], now
            ))

        # Deliverables
        delivs = [
            ("SPN-PLAT01", "Main-Stage Branding", "Logo placement on central stage screens", "Completed", 100),
            ("SPN-PLAT01", "Promotional Keynote Slot", "30-min keynote speaking slot", "Completed", 100),
            ("SPN-PLAT01", "Exhibition Booth #101", "Prime booth location at main hall entrance", "Completed", 100),
            ("SPN-PLAT01", "Social Media Spotlight", "Dedicated posts across official channels", "Completed", 100),
            ("SPN-GOLD01", "Keynote Stage Logo", "Logo on sponsor slide", "Completed", 100),
            ("SPN-GOLD01", "Exhibition Booth #202", "Standard booth in hall A", "Completed", 100),
            ("SPN-GOLD01", "Social Media Mention", "Combined post with Gold sponsors", "Completed", 70),
            ("SPN-SILV01", "Website Logo Display", "Logo on official event site", "Completed", 100),
            ("SPN-SILV01", "Brochure Insert", "Promotional flyer in attendee bag", "In Progress", 40)
        ]
        for sp_id, d_name, d_desc, d_status, d_pct in delivs:
            conn.execute("""
                INSERT INTO sponsorship_deliverables (id, sponsor_id, deliverable_name, description, status, completion_percentage)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f"DEL-{uuid.uuid4().hex[:6].upper()}", sp_id, d_name, d_desc, d_status, d_pct))

        # Engagements
        conn.execute("INSERT INTO sponsor_engagements (id, sponsor_id, booth_visits, attendee_interactions, session_participation, social_engagement, leads, engagement_score) VALUES (?, 'SPN-PLAT01', 340, 850, 4, 1200, 450, 92)", (f"ENG-{uuid.uuid4().hex[:6].upper()}",))
        conn.execute("INSERT INTO sponsor_engagements (id, sponsor_id, booth_visits, attendee_interactions, session_participation, social_engagement, leads, engagement_score) VALUES (?, 'SPN-GOLD01', 180, 420, 2, 650, 280, 76)", (f"ENG-{uuid.uuid4().hex[:6].upper()}",))
        conn.execute("INSERT INTO sponsor_engagements (id, sponsor_id, booth_visits, attendee_interactions, session_participation, social_engagement, leads, engagement_score) VALUES (?, 'SPN-SILV01', 65, 140, 1, 210, 120, 48)", (f"ENG-{uuid.uuid4().hex[:6].upper()}",))

        # 2. Incidents & Timeline
        incidents_data = [
            {
                "id": "INC-1001", "number": "INC-1001", "title": "Main Stage Wireless Mic Audio Dropouts",
                "description": "Intermittent audio loss during Keynote Session in Main Auditorium.",
                "category": "Audio/Video", "severity": "High", "priority": "High",
                "location": "Main Auditorium Stage", "source": "Participant Portal",
                "reporter": "Alex Rivera", "assigned_team": "AV Team", "status": "In Progress",
                "recommended_action": "Switch to backup UHF channel 48 and inspect receiver gain."
            },
            {
                "id": "INC-1002", "number": "INC-1002", "title": "Exhibition Hall Wi-Fi Bandwidth Degradation",
                "description": "High latency and connection timeout reported by booth exhibitors in Hall B.",
                "category": "Network", "severity": "Medium", "priority": "Medium",
                "location": "Exhibition Hall B", "source": "Organizer Portal",
                "reporter": "Ops Coordinator", "assigned_team": "Network Engineering Team", "status": "Assigned",
                "recommended_action": "Enable 5GHz secondary SSID beamforming and throttle guest P2P traffic."
            },
            {
                "id": "INC-1003", "number": "INC-1003", "title": "Registration Desk QR Scanner Malfunction",
                "description": "Scanner #3 at Gate 2 failing to recognize dark-mode mobile screens.",
                "category": "Registration", "severity": "Low", "priority": "Low",
                "location": "Gate 2 Entrance", "source": "Participant Portal",
                "reporter": "Attendee", "assigned_team": "Registration Operations", "status": "Resolved",
                "recommended_action": "Increase ambient scanner LED illumination level."
            }
        ]

        for i in incidents_data:
            conn.execute("""
                INSERT INTO incidents (
                    id, incident_number, event_id, title, description, category, severity, priority,
                    location, affected_area, source, reporter_id, reported_by, assigned_team,
                    status, recommended_action, escalated, created_at, updated_at
                ) VALUES (?, ?, 'EVT-1001', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """, (
                i["id"], i["number"], i["title"], i["description"], i["category"], i["severity"],
                i["priority"], i["location"], i["location"], i["source"], i["reporter"], i["reporter"],
                i["assigned_team"], i["status"], i["recommended_action"], now, now
            ))

            # Timeline
            conn.execute("""
                INSERT INTO incident_timeline (id, incident_id, status, action, description, performed_by, timestamp)
                VALUES (?, ?, 'REPORTED', 'Incident Logged', ?, ?, ?)
            """, (str(uuid.uuid4()), i["id"], f"Reported via {i['source']}.", i["reporter"], now))
            conn.execute("""
                INSERT INTO incident_timeline (id, incident_id, status, action, description, performed_by, timestamp)
                VALUES (?, ?, ?, 'Status Update', ?, 'AI Incident Engine', ?)
            """, (str(uuid.uuid4()), i["id"], i["status"], f"Assigned to {i['assigned_team']}.", now))

        # 3. Operational Alerts
        alerts_data = [
            {
                "id": "ALT-001", "title": "CRITICAL: Main Stage Audio Dropout",
                "message": "High priority incident logged at Main Auditorium Stage: Mic channel dropout during keynote.",
                "type": "Incident", "severity": "Critical", "priority": "Critical", "module": "Incident Agent",
                "entity": "INC-1001", "status": "Active", "action": "Dispatch AV lead to auditorium console immediately."
            },
            {
                "id": "ALT-002", "title": "Predictive Risk: Hall B Capacity Growth",
                "message": "Hall B entry velocity increased by 30%. High risk of doorway bottleneck during lunch break.",
                "type": "Predictive Risk", "severity": "High-Priority", "priority": "High", "module": "Operational Risk Engine",
                "entity": None, "status": "Active", "action": "Deploy auxiliary ushers to Hall B entrance."
            },
            {
                "id": "ALT-003", "title": "Sponsor Deliverable Overdue Warning",
                "message": "CyberPulse Security brochure insert deliverable is past due date.",
                "type": "Sponsorship", "severity": "Medium", "priority": "Medium", "module": "Sponsorship Agent",
                "entity": "SPN-SILV01", "status": "Acknowledged", "action": "Contact sponsor coordinator."
            }
        ]

        for a in alerts_data:
            conn.execute("""
                INSERT INTO operational_alerts (
                    id, event_id, title, message, alert_type, severity, priority, module,
                    entity_id, status, recommended_action, timestamp
                ) VALUES (?, 'EVT-1001', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                a["id"], a["title"], a["message"], a["type"], a["severity"], a["priority"],
                a["module"], a["entity"], a["status"], a["action"], now
            ))

    print("[DONE] Seeded Milestone 3 & Milestone 4 data (Events, Venues, Speakers, Sessions, Sponsors, Deliverables, Incidents, Alerts).")



if __name__ == "__main__":
    seed()

