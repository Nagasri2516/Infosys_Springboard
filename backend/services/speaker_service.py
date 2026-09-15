import json
from pathlib import Path
from backend.models import get_db, generate_id, init_db

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "speakers.json"


def _load_seed_speakers():
    if DATA_FILE.exists():
        with DATA_FILE.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    return []


def seed_speakers():
    init_db()
    speakers = _load_seed_speakers()
    if not speakers:
        return []
    with get_db() as conn:
        conn.execute("DELETE FROM speakers")
        conn.execute("DELETE FROM speaker_assignments")
        conn.execute("DELETE FROM speaker_messages")
        for speaker in speakers:
            conn.execute(
                """
                INSERT INTO speakers (
                    id, name, organization, designation, expertise, years_of_experience, biography,
                    languages, availability, previous_engagements, previous_topics, ratings,
                    audience_engagement_score, communication_score, previous_feedback, certifications,
                    achievements, honorarium, preferred_event_types, preferred_audience, delivery_mode,
                    contact_info, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    speaker.get("id", generate_id("SP")), speaker.get("name"), speaker.get("organization"), speaker.get("designation"),
                    ",".join(speaker.get("expertise", [])), speaker.get("years_of_experience"), speaker.get("biography"),
                    ",".join(speaker.get("languages", [])), speaker.get("availability"), speaker.get("previous_engagements"),
                    ",".join(speaker.get("previous_topics", [])), speaker.get("ratings"), speaker.get("audience_engagement_score"),
                    speaker.get("communication_score"), speaker.get("previous_feedback"), ",".join(speaker.get("certifications", [])),
                    ",".join(speaker.get("achievements", [])), speaker.get("honorarium"), ",".join(speaker.get("preferred_event_types", [])),
                    ",".join(speaker.get("preferred_audience", [])), speaker.get("delivery_mode"), speaker.get("contact_info"), speaker.get("status", "Available")
                ),
            )
    return speakers


def list_speakers():
    init_db()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM speakers ORDER BY name").fetchall()
        return [dict(r) for r in rows]


def recommend_speakers(event_topic, event_type, audience_type, required_expertise=None, preferred_language=None,
                        budget=None, delivery_mode=None, date=None):
    init_db()
    required_expertise = required_expertise or []
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM speakers").fetchall()
    speakers = [dict(r) for r in rows]
    if not speakers:
        seed_speakers()
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM speakers").fetchall()
        speakers = [dict(r) for r in rows]

    results = []
    for speaker in speakers:
        if speaker.get("availability") == "Unavailable":
            continue
        expertise = set((speaker.get("expertise") or "").split(","))
        if required_expertise and not set(required_expertise).issubset(expertise):
            continue
        if budget and speaker.get("honorarium", 0) and speaker.get("honorarium", 0) > budget:
            continue
        if preferred_language and preferred_language not in (speaker.get("languages") or ""):
            continue
        score = 60 + (speaker.get("ratings", 0) * 6) + (speaker.get("audience_engagement_score", 0) * 2) + (speaker.get("communication_score", 0) * 2)
        if event_type and event_type in (speaker.get("preferred_event_types") or ""):
            score += 8
        if audience_type and audience_type in (speaker.get("preferred_audience") or ""):
            score += 6
        results.append({**speaker, "match_score": min(99, int(score))})

    results.sort(key=lambda item: item["match_score"], reverse=True)
    return results


def assign_speaker(session_id, speaker_id, organizer_id, status="Pending"):
    init_db()
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM speaker_assignments WHERE session_id=? AND speaker_id=?", (session_id, speaker_id)).fetchone()
        if existing:
            return None, "Speaker already assigned to this session."
        conn.execute(
            """
            INSERT INTO speaker_assignments (id, session_id, speaker_id, organizer_id, status, assigned_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (generate_id("ASS"), session_id, speaker_id, organizer_id, status),
        )
    return {"status": status}, "Assignment created."


def update_assignment_status(assignment_id, status):
    init_db()
    with get_db() as conn:
        conn.execute("UPDATE speaker_assignments SET status=? WHERE id=?", (status, assignment_id))
    return {"id": assignment_id, "status": status}


def send_message(assignment_id, sender, message, message_type="Update"):
    init_db()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO speaker_messages (id, assignment_id, sender, message, message_type, created_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (generate_id("MSG"), assignment_id, sender, message, message_type),
        )
    return {"message": message}


def add_speaker(data):
    """Manually add a speaker to the database."""
    init_db()
    speaker_id = generate_id("SP")

    def to_csv(val):
        if isinstance(val, list):
            return ",".join(val)
        return str(val) if val else ""

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO speakers (
                id, name, organization, designation, expertise, years_of_experience, biography,
                languages, availability, previous_engagements, previous_topics, ratings,
                audience_engagement_score, communication_score, previous_feedback, certifications,
                achievements, honorarium, preferred_event_types, preferred_audience, delivery_mode,
                contact_info, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                speaker_id,
                data.get("name"),
                data.get("organization", ""),
                data.get("designation", ""),
                to_csv(data.get("expertise", [])),
                int(data.get("years_of_experience", 0) or 0),
                data.get("biography", ""),
                to_csv(data.get("languages", [])),
                data.get("availability", "Available"),
                int(data.get("previous_engagements", 0) or 0),
                to_csv(data.get("previous_topics", [])),
                float(data.get("ratings", 3) or 3),
                float(data.get("audience_engagement_score", 3) or 3),
                float(data.get("communication_score", 3) or 3),
                data.get("previous_feedback", ""),
                to_csv(data.get("certifications", [])),
                to_csv(data.get("achievements", [])),
                float(data.get("honorarium", 0) or 0),
                to_csv(data.get("preferred_event_types", [])),
                to_csv(data.get("preferred_audience", [])),
                data.get("delivery_mode", "Offline"),
                data.get("contact_info", ""),
                data.get("status", "Available"),
            ),
        )
    with get_db() as conn:
        row = conn.execute("SELECT * FROM speakers WHERE id=?", (speaker_id,)).fetchone()
    return dict(row) if row else {"id": speaker_id, "name": data.get("name")}
