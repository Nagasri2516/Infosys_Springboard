from backend.models import get_db, generate_id, rows_to_list, init_db


def list_events():
    init_db()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM events ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_event(event_id):
    init_db()
    with get_db() as conn:
        event = conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
        if not event:
            return None
        event = dict(event)

        counts = conn.execute(
            "SELECT COUNT(*) as total, SUM(CASE WHEN status='confirmed' THEN 1 ELSE 0 END) as confirmed, "
            "SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END) as cancelled, "
            "SUM(CASE WHEN checked_in=1 THEN 1 ELSE 0 END) as checked_in "
            "FROM registrations WHERE event_id=?",
            (event_id,),
        ).fetchone()
        event_counts = {"registered": counts["total"], "confirmed": counts["confirmed"] or 0, "cancelled": counts["cancelled"] or 0, "checked_in": counts["checked_in"] or 0}

        venue = None
        if event.get("selected_venue_id"):
            venue_row = conn.execute("SELECT * FROM venues WHERE id=?", (event["selected_venue_id"],)).fetchone()
            venue = dict(venue_row) if venue_row else None

        sessions = rows_to_list(conn.execute("SELECT * FROM sessions WHERE event_id=? ORDER BY session_date, start_time", (event_id,)).fetchall())
        assignments = rows_to_list(conn.execute(
            "SELECT sa.id, sa.session_id, sa.speaker_id, sa.status, sa.assigned_at, s.session_name, sp.name as speaker_name, sp.expertise, sp.ratings FROM speaker_assignments sa "
            "LEFT JOIN sessions s ON sa.session_id=s.id LEFT JOIN speakers sp ON sa.speaker_id=sp.id WHERE s.event_id=?",
            (event_id,),
        ).fetchall())
        venue_bookings = rows_to_list(conn.execute("SELECT * FROM venue_bookings WHERE event_id=? ORDER BY booking_date DESC", (event_id,)).fetchall())

    return {
        **event,
        "stats": event_counts,
        "selected_venue": venue,
        "sessions": sessions,
        "speaker_assignments": assignments,
        "venue_bookings": venue_bookings,
    }


def create_event(data):
    init_db()
    event_id = generate_id("EVT")
    with get_db() as conn:
        conn.execute(
            "INSERT INTO events (id, name, description, event_type, start_date, end_date, location, expected_attendees, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (
                event_id,
                data.get("name"),
                data.get("description"),
                data.get("event_type"),
                data.get("start_date"),
                data.get("end_date"),
                data.get("location"),
                int(data.get("expected_attendees", 0) or 0),
                data.get("status", "Draft"),
            ),
        )
    return {"id": event_id, "name": data.get("name"), "status": data.get("status", "Draft")}


def update_event(event_id, data):
    init_db()
    fields = []
    params = []
    for key in ("name", "description", "event_type", "start_date", "end_date", "location", "expected_attendees", "status", "selected_venue_id"):
        if key in data:
            fields.append(f"{key}=?")
            params.append(data[key])
    if not fields:
        return None
    params.append(event_id)
    with get_db() as conn:
        conn.execute(f"UPDATE events SET {', '.join(fields)}, updated_at=CURRENT_TIMESTAMP WHERE id=?", params)
        row = conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    return dict(row) if row else None


def ensure_event_exists(event_id):
    if not event_id:
        return False
    init_db()
    with get_db() as conn:
        row = conn.execute("SELECT id FROM events WHERE id=?", (event_id,)).fetchone()
    return bool(row)
