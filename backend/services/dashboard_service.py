"""
Dashboard Service
Returns consolidated organizer dashboard data:
activity log and outbox email index.
"""

import os
import json
from backend.models  import get_db, rows_to_list
from backend.config  import OUTBOX_DIR


def get_activity_log(limit: int = 20) -> list:
    """Return the most recent registrations and check-ins as an activity feed."""
    with get_db() as conn:
        reg_rows = conn.execute("""
            SELECT 'registration' as type, id, full_name, source, role_category, created_at as time
            FROM registrations
            ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()

        checkin_rows = conn.execute("""
            SELECT 'checkin' as type, r.id, r.full_name, c.check_in_method as source,
                   r.role_category, c.check_in_time as time
            FROM check_ins c JOIN registrations r ON r.id=c.registration_id
            ORDER BY c.check_in_time DESC LIMIT ?
        """, (limit,)).fetchall()

    events = [dict(r) for r in reg_rows] + [dict(r) for r in checkin_rows]
    events.sort(key=lambda x: x.get("time", ""), reverse=True)
    return events[:limit]


def get_outbox_emails() -> list:
    """Return metadata for all emails in the outbox directory."""
    emails = []
    if not os.path.isdir(OUTBOX_DIR):
        return emails

    for fname in sorted(os.listdir(OUTBOX_DIR), reverse=True):
        if fname.endswith(".json"):
            fpath = os.path.join(OUTBOX_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                emails.append(meta)
            except Exception:
                pass

    return emails
