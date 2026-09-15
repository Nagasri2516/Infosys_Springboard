"""
Check-in Service
Handles QR/manual check-in: validates the ID, prevents duplicates,
records to check_ins table and updates registrations.checked_in.
"""

import uuid
from datetime import datetime
from backend.models import get_db, row_to_dict


def process_checkin(registration_id: str, method: str = "manual") -> dict:
    """
    Attempt to check in an attendee.

    Returns a dict with keys:
      success (bool), message (str), attendee (dict|None)
    """
    rid = registration_id.strip().upper()

    with get_db() as conn:
        reg = row_to_dict(
            conn.execute("SELECT * FROM registrations WHERE id=?", (rid,)).fetchone()
        )

        if not reg:
            return {"success": False, "message": f"Registration ID '{rid}' not found.", "attendee": None}

        if reg["checked_in"]:
            return {
                "success":  False,
                "message":  f"{reg['full_name']} is already checked in.",
                "attendee": reg,
                "already_checked_in": True
            }

        now = datetime.utcnow().isoformat()
        checkin_id = str(uuid.uuid4())

        # Record in check_ins table
        conn.execute("""
            INSERT INTO check_ins (id, registration_id, check_in_time, check_in_method)
            VALUES (?, ?, ?, ?)
        """, (checkin_id, rid, now, method))

        # Update registration row
        conn.execute("""
            UPDATE registrations
            SET checked_in=1, check_in_time=?, status='confirmed', updated_at=?
            WHERE id=?
        """, (now, now, rid))

        reg["checked_in"]    = 1
        reg["check_in_time"] = now
        reg["status"]        = "confirmed"

    return {"success": True, "message": "Check-in successful!", "attendee": reg}


def get_checkin_history(limit: int = 20) -> list:
    """Return the most recent check-in records joined with attendee details."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT c.id as checkin_id, c.check_in_time, c.check_in_method,
                   r.id as registration_id, r.full_name, r.email, r.role_category
            FROM check_ins c
            JOIN registrations r ON r.id = c.registration_id
            ORDER BY c.check_in_time DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]
