"""
Flask Application – EventCore API
All REST endpoints + static file serving for the frontend.
"""

import os, uuid
from flask       import Flask, request, jsonify, send_from_directory, abort
from flask_cors  import CORS

from backend.config   import SECRET_KEY, DEBUG, DATABASE_PATH
from backend.models   import init_db, get_db, rows_to_list, row_to_dict, generate_id
from backend.services import (
    registration_agent  as reg_svc,
    checkin_service     as ci_svc,
    analytics_service   as an_svc,
    ai_insights_service as ai_svc,
    dashboard_service   as db_svc,
    event_service       as event_svc,
    venue_service       as venue_svc,
    speaker_service     as speaker_svc,
    optimization_service as opt_svc,
    scheduling_service  as sched_svc,
    sponsorship_service as spn_svc,
    incident_service    as inc_svc,
    alert_service       as alt_svc,
    ai_agent_service    as ai_agent_svc,
    agent_orchestrator  as orch_svc,
    event_intelligence_service as eie_svc,
)
from backend.config import OUTBOX_DIR

# ─── App Factory ─────────────────────────────────────────────────────────────

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
STATIC_DIR   = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
app.secret_key = SECRET_KEY
CORS(app)

# Ensure DB tables exist
init_db()
try:
    venue_svc.seed_venues()
    speaker_svc.seed_speakers()
except Exception:
    pass


# ─── Frontend Serving ─────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:filename>")
def frontend_files(filename):
    """Serve JS, CSS and other frontend assets."""
    return send_from_directory(FRONTEND_DIR, filename)

@app.route("/outbox/<path:filename>")
def serve_outbox(filename):
    """Serve HTML email previews directly."""
    return send_from_directory(OUTBOX_DIR, filename)


# ─── Helper ──────────────────────────────────────────────────────────────────

def ok(data=None, **kwargs):
    payload = {"success": True}
    if data is not None:
        payload["data"] = data
    payload.update(kwargs)
    return jsonify(payload)

def err(message, code=400):
    return jsonify({"success": False, "message": message}), code


# ─── Registration Endpoints ───────────────────────────────────────────────────

@app.route("/api/registrations", methods=["POST"])
def create_registration():
    """Submit a new registration (web form / simulation)."""
    data = request.get_json(silent=True) or {}

    # Validation
    errors = reg_svc.validate_payload(data)
    if errors:
        return err("; ".join(errors))

    # Reject duplicate emails before creating a new registration.
    existing = reg_svc.check_duplicate(data["email"])
    if existing:
        return err(
            f"A registration with this email already exists. Existing ID: {existing['id']}",
            409,
        )

    reg, email_result = reg_svc.create_registration(data)

    return ok(
        data        = reg,
        email       = email_result,
        duplicate_warning = False,
        existing_id = None,
    ), 201


@app.route("/api/registrations", methods=["GET"])
def list_registrations():
    """Return filtered/paginated registration list."""
    search = request.args.get("search", "").strip().lower()
    role   = request.args.get("role",   "All")
    source = request.args.get("source", "All")
    status = request.args.get("status", "All")

    query  = "SELECT * FROM registrations WHERE 1=1"
    params = []

    if search:
        query += " AND (LOWER(full_name) LIKE ? OR LOWER(email) LIKE ? OR id LIKE ? OR LOWER(organization) LIKE ?)"
        like = f"%{search}%"
        params += [like, like, like, like]
    if role != "All":
        query += " AND role_category=?"
        params.append(role)
    if source != "All":
        query += " AND source=?"
        params.append(source)
    if status == "Checked In":
        query += " AND checked_in=1"
    elif status == "Pending":
        query += " AND checked_in=0"

    query += " ORDER BY created_at DESC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()

    return ok(rows_to_list(rows))


@app.route("/api/registrations/<reg_id>", methods=["GET"])
def get_registration(reg_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM registrations WHERE id=?", (reg_id.upper(),)).fetchone()
    if not row:
        return err("Registration not found.", 404)
    return ok(row_to_dict(row))


@app.route("/api/registrations/<reg_id>/status", methods=["PUT"])
def update_status(reg_id):
    data   = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ("pending", "confirmed", "cancelled"):
        return err("Invalid status value.")
    with get_db() as conn:
        conn.execute("UPDATE registrations SET status=? WHERE id=?", (status, reg_id.upper()))
    return ok(message=f"Status updated to {status}.")


@app.route("/api/registrations/<reg_id>", methods=["DELETE"])
def delete_registration(reg_id):
    with get_db() as conn:
        row = conn.execute("SELECT id, full_name FROM registrations WHERE id=?", (reg_id.upper(),)).fetchone()
        if not row:
            return err("Registration not found.", 404)
        conn.execute("DELETE FROM registrations WHERE id=?", (reg_id.upper(),))
    return ok(message=f"Deleted registration {reg_id}.")


# ─── Check-in Endpoints ───────────────────────────────────────────────────────

@app.route("/api/checkins", methods=["POST"])
def checkin():
    data   = request.get_json(silent=True) or {}
    reg_id = data.get("registration_id", "").strip().upper()
    method = data.get("method", "manual")  # 'QR' or 'manual'

    if not reg_id:
        return err("registration_id is required.")

    result = ci_svc.process_checkin(reg_id, method)
    code   = 200 if result["success"] else 400
    return jsonify(result), code


@app.route("/api/checkins/history", methods=["GET"])
def checkin_history():
    limit = int(request.args.get("limit", 20))
    return ok(ci_svc.get_checkin_history(limit))


# ─── Analytics Endpoints ──────────────────────────────────────────────────────

@app.route("/api/analytics/summary", methods=["GET"])
def analytics_summary():
    return ok(an_svc.get_summary())

@app.route("/api/analytics/breakdown", methods=["GET"])
def analytics_breakdown():
    return ok(an_svc.get_breakdown())


@app.route("/api/analytics/sessions", methods=["GET"])
def sessions_analytics():
    """Return session-level analytics for the organizer portal."""
    return ok(an_svc.get_session_analytics())


# ─── AI Insights Endpoint ─────────────────────────────────────────────────────

@app.route("/api/insights", methods=["GET"])
def insights():
    return ok(ai_svc.get_insights())


# ─── Dashboard Endpoints ──────────────────────────────────────────────────────

@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    summary  = an_svc.get_summary()
    activity = db_svc.get_activity_log(20)
    return ok({"summary": summary, "activity": activity})

@app.route("/api/events", methods=["POST"])
def create_event():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return err("Event name is required.")
    event = event_svc.create_event(data)
    return ok(event), 201

@app.route("/api/events", methods=["GET"])
def list_events():
    return ok(event_svc.list_events())

@app.route("/api/events/<event_id>", methods=["GET"])
def get_event(event_id):
    event = event_svc.get_event(event_id)
    if not event:
        return err("Event not found.", 404)
    return ok(event)

@app.route("/api/events/<event_id>", methods=["PUT"])
def update_event(event_id):
    data = request.get_json(silent=True) or {}
    event = event_svc.update_event(event_id, data)
    if not event:
        return err("No valid event fields provided or event not found.")
    return ok(event)

@app.route("/api/outbox", methods=["GET"])
def outbox():
    """Return metadata list of all outbox emails."""
    return ok(db_svc.get_outbox_emails())


# ─── Venue Endpoints ────────────────────────────────────────────────────────

@app.route("/api/venues", methods=["GET"])
def list_venues():
    return ok(venue_svc.list_venues())


@app.route("/api/venues", methods=["POST"])
def create_venue():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return err("Venue name is required.")
    if not data.get("capacity"):
        return err("Capacity is required.")
    venue = venue_svc.add_venue(data)
    return ok(venue), 201


@app.route("/api/venues/recommend", methods=["POST"])
def recommend_venues():
    data = request.get_json(silent=True) or {}
    results = venue_svc.recommend_venues(
        event_type=data.get("event_type", "Seminar"),
        expected_attendees=int(data.get("expected_attendees", 0) or 0),
        max_budget=int(data.get("max_budget", 0) or 0),
        preferred_city=data.get("preferred_city"),
        required_facilities=data.get("required_facilities", []),
        power_backup_required=bool(data.get("power_backup_required")),
        cleanliness_preference=data.get("cleanliness_preference", "Medium"),
        security_required=bool(data.get("security_required")),
        accessibility_required=bool(data.get("accessibility_required")),
        indoor_preference=data.get("indoor_preference"),
        date=data.get("event_date"),
        time=data.get("start_time"),
        allow_relaxed=bool(data.get("include_near_matches", True)),
    )
    if not results:
        return err("No suitable venue matched the provided requirements. Try adjusting budget, location, or facilities.")
    return ok(results)


@app.route("/api/venues/book", methods=["POST"])
def book_venue():
    data = request.get_json(silent=True) or {}
    if not data.get("event_id"):
        return err("event_id is required for venue booking.")
    booking, message = venue_svc.book_venue(
        event_id=data.get("event_id"),
        venue_id=data.get("venue_id"),
        organizer_id=data.get("organizer_id", "ORG-1"),
        event_name=data.get("event_name", "Event"),
        event_date=data.get("event_date"),
        start_time=data.get("start_time"),
        end_time=data.get("end_time"),
    )
    if not booking:
        return err(message)
    return ok({"booking": booking, "message": message})


# ─── Speaker Endpoints ─────────────────────────────────────────────────────

@app.route("/api/speakers", methods=["GET"])
def list_speakers():
    return ok(speaker_svc.list_speakers())


@app.route("/api/speakers", methods=["POST"])
def create_speaker():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return err("Speaker name is required.")
    speaker = speaker_svc.add_speaker(data)
    return ok(speaker), 201


@app.route("/api/speakers/recommend", methods=["POST"])
def recommend_speakers():
    data = request.get_json(silent=True) or {}
    results = speaker_svc.recommend_speakers(
        event_topic=data.get("event_topic", ""),
        event_type=data.get("event_type", "Seminar"),
        audience_type=data.get("audience_type", "Students"),
        required_expertise=data.get("required_expertise", []),
        preferred_language=data.get("preferred_language"),
        budget=data.get("budget"),
        delivery_mode=data.get("delivery_mode"),
        date=data.get("session_date"),
    )
    if not results:
        return err("No suitable speaker matched the provided requirements.")
    return ok(results)


@app.route("/api/speakers/assign", methods=["POST"])
def assign_speaker():
    data = request.get_json(silent=True) or {}
    result, message = speaker_svc.assign_speaker(
        session_id=data.get("session_id", "SES-1"),
        speaker_id=data.get("speaker_id"),
        organizer_id=data.get("organizer_id", "ORG-1"),
        status=data.get("status", "Pending"),
    )
    if not result:
        return err(message)
    return ok({"assignment": result, "message": message})


@app.route("/api/speakers/messages", methods=["POST"])
def create_message():
    data = request.get_json(silent=True) or {}
    result = speaker_svc.send_message(
        assignment_id=data.get("assignment_id"),
        sender=data.get("sender", "organizer"),
        message=data.get("message", ""),
        message_type=data.get("message_type", "Update"),
    )
    return ok(result)


# ─── Optimization / Scheduling Endpoints ─────────────────────────────────

@app.route("/api/optimization/rooms", methods=["POST"])
def optimize_rooms():
    data = request.get_json(silent=True) or {}
    allocations = opt_svc.optimize_room_allocation(
        event_type=data.get("event_type", "Conference"),
        total_attendees=int(data.get("total_attendees", 0) or 0),
        sessions=data.get("sessions", []),
        available_rooms=data.get("available_rooms"),
    )
    return ok(allocations)


@app.route("/api/sessions", methods=["POST"])
def create_session():
    data = request.get_json(silent=True) or {}
    if not data.get("session_name") or not data.get("session_date") or not data.get("start_time") or not data.get("end_time") or not data.get("venue_id"):
        return err("session_name, session_date, start_time, end_time, and venue_id are required.")

    session = sched_svc.create_session(
        event_id=data.get("event_id", "EVT-1"),
        session_name=data.get("session_name"),
        topic=data.get("topic"),
        session_type=data.get("session_type", "Seminar"),
        session_date=data.get("session_date"),
        start_time=data.get("start_time"),
        end_time=data.get("end_time"),
        venue_id=data.get("venue_id"),
        expected_attendees=data.get("expected_attendees"),
    )
    if not session:
        return err("Unable to create session. It may already exist or required data is missing.")
    return ok(session)


@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    event_id = request.args.get("event_id")
    with get_db() as conn:
        if event_id:
            rows = conn.execute("SELECT * FROM sessions WHERE event_id=? ORDER BY session_date, start_time", (event_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM sessions ORDER BY session_date, start_time").fetchall()
    return ok(rows_to_list(rows))


# ─── Feedback Endpoints ───────────────────────────────────────────────────────

@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    """Submit participant feedback (name, reg_id, rating, comment)."""
    data    = request.get_json(silent=True) or {}
    name    = data.get("name", "").strip()
    reg_id  = data.get("reg_id", "").strip().upper()
    rating  = data.get("rating", 0)
    comment = data.get("comment", "").strip()

    session_id = data.get("session_id")
    if not name:
        return err("name is required.")
    if not reg_id:
        return err("reg_id is required.")
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return err("rating must be an integer between 1 and 5.")

    from datetime import datetime
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, reg_id TEXT, session_id TEXT, rating INTEGER,
                comment TEXT, submitted_at TEXT
            )
        """)
        # if session_id provided, ensure session exists
        if session_id:
            s = conn.execute("SELECT id FROM sessions WHERE id=?", (session_id,)).fetchone()
            if not s:
                return err("Invalid session_id. Session not found.")
        conn.execute(
            "INSERT INTO feedback (name, reg_id, session_id, rating, comment, submitted_at) VALUES (?,?,?,?,?,?)",
            (name, reg_id, session_id, rating, comment, now)
        )
    return ok(message="Feedback submitted successfully."), 201


@app.route("/api/feedback", methods=["GET"])
def list_feedback():
    """Return all feedback entries (organizer use)."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, reg_id TEXT, rating INTEGER,
                comment TEXT, submitted_at TEXT
            )
        """)
        rows = conn.execute("SELECT * FROM feedback ORDER BY submitted_at DESC").fetchall()
    return ok(rows_to_list(rows))


# ─── Milestone 3: Sponsorship, Incident & Alert API Endpoints ────────────────

@app.route("/api/sponsors", methods=["GET"])
def list_sponsors():
    tier = request.args.get("tier")
    status = request.args.get("status")
    search = request.args.get("search")
    data = spn_svc.get_all_sponsors(tier_filter=tier, status_filter=status, search=search)
    return ok(data)

@app.route("/api/sponsors/<sponsor_id>", methods=["GET"])
def get_sponsor(sponsor_id):
    data = spn_svc.get_sponsor_details(sponsor_id)
    if not data:
        return err("Sponsor not found", 404)
    return ok(data)

@app.route("/api/sponsors", methods=["POST"])
def create_sponsor_route():
    body = request.get_json() or {}
    if not body.get("name"):
        return err("Sponsor name is required", 400)
    spn = spn_svc.create_sponsor(body)
    return ok(spn), 201

@app.route("/api/sponsors/prospects", methods=["GET"])
def get_sponsor_prospects_route():
    domain = request.args.get("domain")
    data = spn_svc.get_prospects(domain=domain)
    return ok(data)

@app.route("/api/sponsors/prospects/<prospect_id>/approach", methods=["POST"])
def approach_sponsor_prospect_route(prospect_id):
    body = request.get_json() or {}
    res = spn_svc.approach_prospect(prospect_id, body)
    if not res:
        return err("Prospect not found", 404)
    return ok(res)


@app.route("/api/sponsors/query-ai", methods=["POST"])
def query_sponsor_ai():
    body = request.get_json() or {}
    query = body.get("query", "")
    ans = ai_agent_svc.answer_sponsor_query(query)
    return ok({"query": query, "answer": ans})

@app.route("/api/sponsors/recommendations", methods=["GET"])
def sponsor_recommendations():
    recs = ai_agent_svc.generate_sponsor_recommendations()
    return ok({"recommendations": recs})

@app.route("/api/sponsorship-deliverables", methods=["GET"])
def list_deliverables_route():
    with get_db() as conn:
        delivs = conn.execute("""
            SELECT d.*, s.name as sponsor_name
            FROM sponsorship_deliverables d
            LEFT JOIN sponsors s ON d.sponsor_id = s.id
            ORDER BY d.deliverable_name ASC
        """).fetchall()
        return ok([dict(d) for d in delivs])

@app.route("/api/sponsorship-deliverables/<deliverable_id>", methods=["PUT"])
@app.route("/api/deliverables/<deliverable_id>", methods=["PUT"])
def update_deliverable_route(deliverable_id):
    body = request.get_json() or {}
    status = body.get("status", "Completed")
    spn_svc.update_deliverable(deliverable_id, status)
    return ok(message=f"Deliverable status updated to {status}")

@app.route("/api/sponsor-performance", methods=["GET"])
def sponsor_performance_route():
    res = spn_svc.get_sponsor_performance()
    return ok(res)

@app.route("/api/sponsor-performance/<sponsor_id>", methods=["GET"])
def sponsor_performance_detail_route(sponsor_id):
    res = spn_svc.get_sponsor_performance_detail(sponsor_id)
    if not res:
        return err("Sponsor not found", 404)
    return ok(res)

@app.route("/api/sponsor-performance/<sponsor_id>/update", methods=["POST"])
def sponsor_performance_update_route(sponsor_id):
    body = request.get_json() or {}
    leads = body.get("leads")
    eng_score = body.get("engagement_score")
    res = spn_svc.update_sponsor_metrics(sponsor_id, leads=leads, engagement_score=eng_score)
    return ok(res)

@app.route("/api/incidents", methods=["POST"])
def report_incident_route():
    body = request.get_json() or {}
    if not body.get("title") and not body.get("description") and not body.get("incident_type"):
        return err("Incident title or description is required", 400)
    inc = inc_svc.create_incident(body)
    return ok(inc), 201

@app.route("/api/incidents", methods=["GET"])
def list_incidents_route():
    cat = request.args.get("category")
    pri = request.args.get("priority")
    status = request.args.get("status")
    reporter = request.args.get("reporter_id")
    data = inc_svc.get_incidents(category=cat, priority=pri, status=status, reporter_id=reporter)
    return ok(data)

@app.route("/api/my-incidents", methods=["GET"])
def list_my_incidents_route():
    reporter = request.args.get("reporter_id", "Participant")
    data = inc_svc.get_incidents(reporter_id=reporter)
    return ok(data)

@app.route("/api/incidents/<incident_id>", methods=["GET"])
def get_incident_route(incident_id):
    inc = inc_svc.get_incident_details(incident_id)
    if not inc:
        return err("Incident not found", 404)
    return ok(inc)

@app.route("/api/incidents/classify-ai", methods=["POST"])
def classify_incident_ai_route():
    body = request.get_json() or {}
    title = body.get("title", "")
    desc = body.get("description", "")
    classification = ai_agent_svc.classify_incident(title, desc)
    return ok({"classification": classification})

@app.route("/api/incidents/<incident_id>/transition", methods=["POST"])
def transition_incident_route(incident_id):
    body = request.get_json() or {}
    new_status = body.get("status", "In Progress")
    updated_by = body.get("updated_by", "Organizer")
    res = inc_svc.transition_incident_status(incident_id, new_status, updated_by)
    return ok(res)

@app.route("/api/incidents/<incident_id>/assign", methods=["POST"])
def assign_incident_route(incident_id):
    body = request.get_json() or {}
    team = body.get("team", "IT Operations Team")
    assigned_by = body.get("assigned_by", "Organizer")
    res = inc_svc.assign_incident_team(incident_id, team, assigned_by)
    return ok(res)

@app.route("/api/incidents/<incident_id>/escalate", methods=["POST"])
def escalate_incident_route(incident_id):
    body = request.get_json() or {}
    reason = body.get("reason", "Critical venue escalation")
    res = inc_svc.escalate_incident(incident_id, reason)
    return ok(res)

@app.route("/api/incidents/<incident_id>/resolve", methods=["POST"])
def resolve_incident_route(incident_id):
    body = request.get_json() or {}
    notes = body.get("resolution_notes", "Resolved by venue operations coordinator.")
    res = inc_svc.resolve_incident(incident_id, notes)
    return ok(res)

@app.route("/api/alerts", methods=["GET"])
def list_alerts_route():
    sev = request.args.get("severity")
    status = request.args.get("status")
    data = alt_svc.get_alerts(severity=sev, status=status)
    return ok(data)

@app.route("/api/alerts/<alert_id>/acknowledge", methods=["POST"])
def acknowledge_alert_route(alert_id):
    alt_svc.acknowledge_alert(alert_id)
    return ok(message="Alert acknowledged")

@app.route("/api/alerts/<alert_id>/resolve", methods=["POST"])
def resolve_alert_route(alert_id):
    alt_svc.resolve_alert(alert_id)
    return ok(message="Alert resolved")

@app.route("/api/alerts/predict-risks", methods=["POST"])
def predict_risks_route():
    count = alt_svc.generate_predictive_risk_alerts()
    return ok({"alerts_generated": count, "message": f"{count} predictive operational risk alert(s) generated."})

@app.route("/api/dashboard/m3-summary", methods=["GET"])
def m3_dashboard_summary():
    sponsors = spn_svc.get_all_sponsors()
    incidents = inc_svc.get_incidents()
    alerts = alt_svc.get_alerts()

    pending_delivs = sum(s["deliverables_summary"]["total"] - s["deliverables_summary"]["completed"] for s in sponsors)
    active_incidents = sum(1 for i in incidents if i["status"] not in ["Resolved", "Closed"])
    critical_incidents = sum(1 for i in incidents if i["priority"] == "Critical" and i["status"] not in ["Resolved", "Closed"])
    high_incidents = sum(1 for i in incidents if i["priority"] == "High" and i["status"] not in ["Resolved", "Closed"])
    resolved_incidents = sum(1 for i in incidents if i["status"] == "Resolved")

    unresolved_alerts = sum(1 for a in alerts if a["status"] != "Resolved")
    critical_alerts = sum(1 for a in alerts if a["severity"] == "Critical" and a["status"] != "Resolved")

    return ok({
        "sponsorship": {
            "total_sponsors": len(sponsors),
            "pending_deliverables": pending_delivs
        },
        "incidents": {
            "total_incidents": len(incidents),
            "active_incidents": active_incidents,
            "critical_incidents": critical_incidents,
            "high_incidents": high_incidents,
            "resolved_incidents": resolved_incidents
        },
        "alerts": {
            "total_alerts": len(alerts),
            "unresolved_alerts": unresolved_alerts,
            "critical_alerts": critical_alerts
        }
    })


# ─── Milestone 4: Orchestration & Event Intelligence ──────────────────────────

@app.route("/api/orchestrator/trigger", methods=["POST"])
@app.route("/api/orchestrate", methods=["POST"])
def trigger_orchestrator():
    data = request.get_json(silent=True) or {}
    event_type = data.get("event_type")
    payload = data.get("payload", {})
    if not event_type:
        return err("event_type is required", 400)
    result = orch_svc.handle_orchestrated_event(event_type, payload)
    if result.get("status") == "error":
        return err(result.get("message", "Unknown error"), 400)
    return ok(result)

@app.route("/api/executive-dashboard", methods=["GET"])
def executive_dashboard_route():
    kpis = eie_svc.get_event_kpis()
    health = eie_svc.get_event_health_score(kpis)
    return ok({
        "kpis": kpis,
        "health": health
    })

@app.route("/api/event-intelligence", methods=["GET"])
def event_intelligence_route():
    insights = eie_svc.get_executive_insights()
    return ok(insights)

# ─── Milestone 4: End-to-End Testing & Deployment Endpoints ────────────────

@app.route("/api/test-runner", methods=["GET", "POST"])
def test_runner_route():
    """Run automated End-to-End backend test suite and return results."""
    tests = []
    
    # Test 1: DB Connection & Query Execution
    try:
        with get_db() as conn:
            reg_count = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
            inc_count = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        tests.append({
            "name": "Database Telemetry Integrity",
            "module": "End-to-End Testing",
            "status": "PASS",
            "details": f"Successfully connected to SQLite. Registrations: {reg_count}, Incidents: {inc_count}"
        })
    except Exception as e:
        tests.append({
            "name": "Database Telemetry Integrity",
            "module": "End-to-End Testing",
            "status": "FAIL",
            "details": str(e)
        })

    # Test 2: Event Health Score Formula Validation
    try:
        health = eie_svc.get_event_health_score({"critical_incidents": 1, "open_incidents": 2, "recent_alerts": 3})
        # Score = 100 - (15*1) - (5*2) - (3*3) = 100 - 15 - 10 - 9 = 66 -> WARNING
        if health["score"] == 66 and health["status"] == "WARNING":
            tests.append({
                "name": "Health Scoring Formula Verification",
                "module": "Event Intelligence Engine",
                "status": "PASS",
                "details": f"Penalty formula verified. Score: {health['score']}, Status: {health['status']}"
            })
        else:
            tests.append({
                "name": "Health Scoring Formula Verification",
                "module": "Event Intelligence Engine",
                "status": "FAIL",
                "details": f"Unexpected score: {health['score']}, status: {health['status']}"
            })
    except Exception as e:
        tests.append({
            "name": "Health Scoring Formula Verification",
            "module": "Event Intelligence Engine",
            "status": "FAIL",
            "details": str(e)
        })

    # Test 3: Agent Orchestration Workflow Execution
    try:
        orch_res = orch_svc.handle_orchestrated_event("SPEAKER_CANCELLATION", {"speaker_id": "SPK-3"})
        if orch_res.get("status") == "success" and "workflow_steps" in orch_res:
            tests.append({
                "name": "Multi-Agent Orchestration Sequence",
                "module": "Agent Orchestration",
                "status": "PASS",
                "details": f"Executed {len(orch_res['workflow_steps'])} agent steps for SPEAKER_CANCELLATION"
            })
        else:
            tests.append({
                "name": "Multi-Agent Orchestration Sequence",
                "module": "Agent Orchestration",
                "status": "FAIL",
                "details": "Workflow execution failed or invalid response payload"
            })
    except Exception as e:
        tests.append({
            "name": "Multi-Agent Orchestration Sequence",
            "module": "Agent Orchestration",
            "status": "FAIL",
            "details": str(e)
        })

    # Test 4: Payload Validation Error Handling
    try:
        err_res = reg_svc.validate_payload({})
        if err_res:
            tests.append({
                "name": "Payload Validation & Error Handling",
                "module": "Production Deployment",
                "status": "PASS",
                "details": f"Gracefully rejected empty payload with {len(err_res)} validation errors"
            })
        else:
            tests.append({
                "name": "Payload Validation & Error Handling",
                "module": "Production Deployment",
                "status": "FAIL",
                "details": "Failed to flag invalid payload"
            })
    except Exception as e:
        tests.append({
            "name": "Payload Validation & Error Handling",
            "module": "Production Deployment",
            "status": "FAIL",
            "details": str(e)
        })

    # Test 5: Executive Dashboard API Integration
    try:
        kpis = eie_svc.get_event_kpis()
        if "registrations" in kpis and "checked_in" in kpis:
            tests.append({
                "name": "Executive Dashboard KPI Aggregation",
                "module": "Executive Dashboards",
                "status": "PASS",
                "details": f"Aggregated {kpis['registrations']} registrations, {kpis['attendance_rate']}% attendance rate"
            })
        else:
            tests.append({
                "name": "Executive Dashboard KPI Aggregation",
                "module": "Executive Dashboards",
                "status": "FAIL",
                "details": "Missing required KPI fields"
            })
    except Exception as e:
        tests.append({
            "name": "Executive Dashboard KPI Aggregation",
            "module": "Executive Dashboards",
            "status": "FAIL",
            "details": str(e)
        })

    passed_count = sum(1 for t in tests if t["status"] == "PASS")
    total_count = len(tests)
    
    return ok({
        "summary": {
            "total": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "success_rate": f"{int((passed_count / total_count) * 100)}%"
        },
        "tests": tests
    })


@app.route("/api/deployment-status", methods=["GET"])
def deployment_status_route():
    """Return runtime system deployment configuration and environment health."""
    import sys
    
    outbox_count = 0
    if os.path.exists(OUTBOX_DIR):
        outbox_count = len([f for f in os.listdir(OUTBOX_DIR) if f.endswith(".html")])
        
    db_exists = os.path.exists(DATABASE_PATH)
    
    table_stats = {}
    if db_exists:
        try:
            with get_db() as conn:
                for table in ["registrations", "venues", "speakers", "sponsors", "incidents", "operational_alerts"]:
                    try:
                        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                        table_stats[table] = count
                    except Exception:
                        table_stats[table] = 0
        except Exception:
            pass

    return ok({
        "environment": "Production / Enterprise Local Host",
        "server": {
            "python_version": sys.version.split()[0],
            "framework": "Flask 3.x",
            "host": "0.0.0.0",
            "port": 5000,
            "status": "ONLINE",
            "cors_enabled": True
        },
        "database": {
            "engine": "SQLite 3",
            "path": DATABASE_PATH,
            "exists": db_exists,
            "tables": table_stats
        },
        "services": {
            "event_intelligence_engine": "ACTIVE",
            "agent_orchestrator": "ACTIVE",
            "executive_dashboard": "ACTIVE",
            "email_outbox_fallback": f"ACTIVE ({outbox_count} rendered emails)",
            "ai_insights_rules": "ACTIVE (Offline Deterministic)"
        }
    })

# ─── Debug / Reset Endpoint ───────────────────────────────────────────────────

@app.route("/api/debug/reset", methods=["POST"])
def debug_reset():
    """Re-seed the database with mock records."""
    from backend.db_setup import seed
    seed(send_emails=True)
    return ok(message="Database reset and re-seeded with mock registrations & Milestone 3 data.")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


