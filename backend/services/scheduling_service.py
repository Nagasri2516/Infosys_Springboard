from backend.models import get_db, init_db, generate_id


def check_speaker_conflict(speaker_id, session_date, start_time, end_time):
    if not speaker_id or not session_date or not start_time or not end_time:
        return None
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM speaker_assignments sa JOIN sessions s ON s.id=sa.session_id WHERE sa.speaker_id=? AND s.session_date=?",
            (speaker_id, session_date),
        ).fetchall()
    for row in rows:
        assigned_start = row["start_time"]
        assigned_end = row["end_time"]
        if assigned_start and assigned_end and start_time < assigned_end and end_time > assigned_start:
            return {
                "speaker_id": speaker_id,
                "message": "Speaker is already assigned to another session during this time.",
            }
    return None


def create_session(event_id, session_name, topic, session_type, session_date, start_time, end_time, venue_id, expected_attendees):
    if not session_date or not start_time or not end_time or not venue_id or not session_name:
        return None
    init_db()
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM sessions WHERE event_id=? AND session_name=? AND session_date=? AND start_time=? AND end_time=? AND venue_id=?",
            (event_id, session_name, session_date, start_time, end_time, venue_id),
        ).fetchone()
        if existing:
            return {"id": existing["id"], "session_name": session_name, "event_id": event_id, "status": "existing"}
        session_id = generate_id("SES")
        conn.execute(
            """
            INSERT INTO sessions (id, event_id, session_name, topic, session_type, session_date, start_time, end_time, venue_id, expected_attendees, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (session_id, event_id, session_name, topic, session_type, session_date, start_time, end_time, venue_id, expected_attendees),
        )
    return {"id": session_id, "session_name": session_name, "event_id": event_id, "status": "created"}


def assign_speaker_to_session(session_id, speaker_id, organizer_id, status="Pending"):
    if not session_id or not speaker_id:
        return None, "A session and speaker are required for assignment."
    init_db()
    with get_db() as conn:
        session = conn.execute("SELECT session_date, start_time, end_time FROM sessions WHERE id=?", (session_id,)).fetchone()
        if not session:
            return None, "Session not found."
        existing = conn.execute("SELECT * FROM speaker_assignments WHERE session_id=? AND speaker_id=?", (session_id, speaker_id)).fetchone()
        if existing:
            return None, "Speaker already assigned to this session."
        conflict = check_speaker_conflict(speaker_id, session["session_date"], session["start_time"], session["end_time"])
        if conflict:
            return None, conflict["message"]
        assignment_id = generate_id("ASS")
        conn.execute(
            "INSERT INTO speaker_assignments (id, session_id, speaker_id, organizer_id, status, assigned_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (assignment_id, session_id, speaker_id, organizer_id, status),
        )
    return {"id": assignment_id, "session_id": session_id, "speaker_id": speaker_id, "status": status}, "Assignment created."
