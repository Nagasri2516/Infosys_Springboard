"""
Analytics Service
Aggregates registration data for Chart.js chart payloads and summary cards.
"""

from backend.models import get_db


def get_summary() -> dict:
    """Return KPI counts for the organizer dashboard."""
    with get_db() as conn:
        total      = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
        checked_in = conn.execute("SELECT COUNT(*) FROM registrations WHERE checked_in=1").fetchone()[0]
        pending    = total - checked_in
        rate       = round((checked_in / total * 100), 1) if total else 0

    return {
        "total_registrations": total,
        "checked_in":          checked_in,
        "pending":             pending,
        "attendance_rate":     rate,
    }


def get_breakdown() -> dict:
    """Return per-category and per-source counts for Chart.js."""
    with get_db() as conn:
        # Role breakdown
        role_rows = conn.execute("""
            SELECT role_category, COUNT(*) as cnt
            FROM registrations
            GROUP BY role_category
        """).fetchall()

        # Source breakdown
        source_rows = conn.execute("""
            SELECT source, COUNT(*) as cnt
            FROM registrations
            GROUP BY source
        """).fetchall()

        # Daily registrations (last 14 days)
        trend_rows = conn.execute("""
            SELECT DATE(created_at) as day, COUNT(*) as cnt
            FROM registrations
            GROUP BY day
            ORDER BY day DESC
            LIMIT 14
        """).fetchall()

    roles   = {r["role_category"]: r["cnt"] for r in role_rows}
    sources = {r["source"]: r["cnt"] for r in source_rows}
    trend   = [{"day": r["day"], "count": r["cnt"]} for r in reversed(trend_rows)]

    # Ensure all expected keys exist (fill with 0 if no data)
    for role in ("Student", "Professional", "Mentor", "Organizer"):
        roles.setdefault(role, 0)
    for src in ("Web Form", "Google Forms", "Mobile App", "API"):
        sources.setdefault(src, 0)

    return {"roles": roles, "sources": sources, "trend": trend}


def get_session_analytics() -> dict:
    """Return session-level analytics computed from sessions, session_attendance, speakers, and venues."""
    with get_db() as conn:
        # Pull sessions with venue capacity
        srows = conn.execute("SELECT s.*, v.capacity as venue_capacity, v.name as venue_name FROM sessions s LEFT JOIN venues v ON s.venue_id=v.id ORDER BY s.session_date, s.start_time").fetchall()
        sessions = [dict(r) for r in srows]

        # Precompute attendance counts per session
        attend_rows = conn.execute("SELECT session_id, COUNT(*) as cnt FROM session_attendance GROUP BY session_id").fetchall()
        attendance_map = {r['session_id']: r['cnt'] for r in attend_rows}

        # Total registrations for participation rate baseline
        total_regs = conn.execute("SELECT COUNT(*) as cnt FROM registrations").fetchone()[0]

        session_metrics = []
        for s in sessions:
            sid = s.get('id')
            checked_in = int(attendance_map.get(sid, 0))
            expected = int(s.get('expected_attendees') or 0)
            capacity = int(s.get('venue_capacity') or 0)
            attendance_rate = round((checked_in / expected * 100), 1) if expected else None
            participation_rate = round((checked_in / total_regs * 100), 1) if total_regs else None

            # Speaker assignment (may not exist)
            spar = conn.execute("SELECT sa.speaker_id, sp.name, sp.ratings, sp.audience_engagement_score FROM speaker_assignments sa LEFT JOIN speakers sp ON sa.speaker_id=sp.id WHERE sa.session_id=? LIMIT 1", (sid,)).fetchone()
            speaker = dict(spar) if spar else None

            # Venue utilization for this session
            occupancy_pct = None
            if capacity and capacity > 0:
                occupancy_pct = round((checked_in / capacity * 100), 1)

            # session feedback: avg rating for this session
            frow = conn.execute("SELECT AVG(rating) as avg_rating, COUNT(*) as cnt FROM feedback WHERE session_id=?", (sid,)).fetchone()
            session_feedback_avg = round(frow['avg_rating'], 1) if frow and frow['avg_rating'] is not None else None

            session_metrics.append({
                "id": sid,
                "session_name": s.get('session_name'),
                "topic": s.get('topic'),
                "session_date": s.get('session_date'),
                "start_time": s.get('start_time'),
                "end_time": s.get('end_time'),
                "venue_id": s.get('venue_id'),
                "venue_name": s.get('venue_name'),
                "expected_attendees": expected,
                "capacity": capacity,
                "checked_in": checked_in,
                "attendance_rate": attendance_rate,
                "participation_rate": participation_rate,
                "occupancy_pct": occupancy_pct,
                "speaker": speaker,
                "feedback_avg": session_feedback_avg,
            })

        # Popularity lists
        sorted_by_att = sorted(session_metrics, key=lambda x: x['checked_in'], reverse=True)
        most_popular = sorted_by_att[:5]
        least_popular = [s for s in sorted_by_att if s['checked_in'] > 0][-5:]

        # Peak attendance hours (from session_attendance.check_in_time)
        ph = conn.execute("SELECT STRFTIME('%H', check_in_time) as hour, COUNT(*) as cnt FROM session_attendance GROUP BY hour ORDER BY cnt DESC LIMIT 6").fetchall()
        peak_hours = [{"hour": r['hour'], "count": r['cnt']} for r in ph]

        # Speaker summaries: average rating from speaker table + avg attendance for assigned sessions and feedback
        sp_rows = conn.execute("SELECT id, name, ratings, audience_engagement_score FROM speakers").fetchall()
        speakers = []
        for sp in sp_rows:
            spd = dict(sp)
            # sessions assigned to this speaker
            srows_sp = conn.execute("SELECT s.id FROM speaker_assignments sa JOIN sessions s ON sa.session_id=s.id WHERE sa.speaker_id=?", (spd['id'],)).fetchall()
            session_ids = [r['id'] for r in srows_sp]
            if session_ids:
                q = f"SELECT session_id, COUNT(*) as cnt FROM session_attendance WHERE session_id IN ({','.join(['?']*len(session_ids))}) GROUP BY session_id"
                ar = conn.execute(q, session_ids).fetchall()
                counts = [r['cnt'] for r in ar]
                avg_att = round(sum(counts)/len(counts), 1) if counts else 0
            else:
                avg_att = 0
            # compute average feedback across the speaker's sessions
            fb_avg = None
            if session_ids:
                qfb = f"SELECT AVG(rating) as avg_rating FROM feedback WHERE session_id IN ({','.join(['?']*len(session_ids))})"
                fb_row = conn.execute(qfb, session_ids).fetchone()
                if fb_row and fb_row['avg_rating'] is not None:
                    fb_avg = round(fb_row['avg_rating'],1)

            speakers.append({
                "id": spd['id'],
                "name": spd['name'],
                "rating": spd.get('ratings'),
                "audience_engagement_score": spd.get('audience_engagement_score'),
                "avg_attendance": avg_att,
                "feedback_avg": fb_avg,
            })

        # Venue utilization summary
        vrows = conn.execute("SELECT id, name, capacity FROM venues").fetchall()
        venues = []
        for v in vrows:
            vid = v['id']
            # sessions held in venue
            s_in_v = conn.execute("SELECT id FROM sessions WHERE venue_id=?", (vid,)).fetchall()
            sids = [r['id'] for r in s_in_v]
            total_expected = 0
            total_actual = 0
            if sids:
                q2 = f"SELECT SUM(expected_attendees) as se FROM sessions WHERE venue_id=?"
                se = conn.execute(q2, (vid,)).fetchone()['se'] or 0
                total_expected = int(se)
                q3 = f"SELECT COUNT(*) as cnt FROM session_attendance sa JOIN sessions s ON sa.session_id=s.id WHERE s.venue_id=?"
                total_actual = conn.execute(q3, (vid,)).fetchone()['cnt'] or 0
            utilization = None
            if (v['capacity'] or 0) and total_actual:
                # percent of capacity across sessions (approx)
                utilization = round((total_actual / ((v['capacity'] or 0) * max(1, len(sids))) * 100), 1) if sids else None
            venues.append({
                "id": vid,
                "name": v['name'],
                "capacity": v['capacity'],
                "total_expected": total_expected,
                "total_actual": total_actual,
                "utilization_pct": utilization,
            })

        # AI-generated insights based on real measurements
        insights = []
        if most_popular:
            top = most_popular[0]
            insights.append(f"Top session: {top['session_name']} with {top['checked_in']} checked-in attendees.")
        # highest attendance rate
        rated = [s for s in session_metrics if s['attendance_rate'] is not None]
        if rated:
            best_rate = max(rated, key=lambda x: x['attendance_rate'])
            insights.append(f"Highest attendance rate: {best_rate['session_name']} at {best_rate['attendance_rate']}%.")
        # best utilized room
        utilized = [v for v in venues if v['utilization_pct'] is not None]
        if utilized:
            best_room = max(utilized, key=lambda x: x['utilization_pct'])
            insights.append(f"Highest room utilization: {best_room['name']} at {best_room['utilization_pct']}%.")
        # peak hour
        if peak_hours:
            ph0 = peak_hours[0]
            insights.append(f"Peak attendance hour: {ph0['hour']}:00 with {ph0['count']} check-ins.")

        return {
            "sessions": session_metrics,
            "most_popular": most_popular,
            "least_popular": least_popular,
            "peak_hours": peak_hours,
            "speakers": speakers,
            "venues": venues,
            "ai_insights": insights,
        }
