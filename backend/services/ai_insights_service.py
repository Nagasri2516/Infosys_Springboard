"""
AI Insights Service
Rule-based intelligence engine that provides:
  - Attendance probability forecasting
  - Duplicate registration detection
  - Contextual recommendations for organizers
"""

from backend.models import get_db, rows_to_list


# Attendance probability weights by role and source
ROLE_WEIGHTS   = {"Mentor": 0.90, "Organizer": 0.98, "Student": 0.78, "Professional": 0.72}
SOURCE_WEIGHTS = {"API": 0.05, "Mobile App": 0.03, "Google Forms": -0.08, "Web Form": 0.0}


def get_insights() -> dict:
    """Return a complete insights payload for the frontend."""
    with get_db() as conn:
        regs = rows_to_list(conn.execute("SELECT * FROM registrations").fetchall())

    if not regs:
        return {
            "forecast": {"predicted": 0, "percentage": 0, "total": 0},
            "duplicates": [],
            "recommendations": [],
            "ratio_alert": None,
        }

    # ── Attendance Forecast ────────────────────────────────────────────────────
    predicted_sum = 0.0
    for r in regs:
        if r["checked_in"]:
            predicted_sum += 1.0
        else:
            prob = ROLE_WEIGHTS.get(r["role_category"], 0.70)
            prob += SOURCE_WEIGHTS.get(r["source"], 0.0)
            predicted_sum += min(max(prob, 0.40), 0.99)

    predicted  = round(predicted_sum)
    total      = len(regs)
    percentage = round((predicted / total * 100)) if total else 0

    # ── Duplicate Detection ───────────────────────────────────────────────────
    email_map = {}
    phone_map = {}
    for r in regs:
        key = r["email"].lower().strip()
        email_map.setdefault(key, []).append(r)
        phone_key = "".join(c for c in r["phone"] if c.isdigit())
        if len(phone_key) >= 7:
            phone_map.setdefault(phone_key, []).append(r)

    seen_ids = set()
    duplicates = []
    for match_val, records in {**email_map}.items():
        if len(records) > 1:
            ids_key = ",".join(sorted(r["id"] for r in records))
            if ids_key not in seen_ids:
                seen_ids.add(ids_key)
                duplicates.append({
                    "type":       "Email",
                    "match_value": match_val,
                    "records":    [{"id": r["id"], "full_name": r["full_name"],
                                    "role_category": r["role_category"], "source": r["source"]}
                                   for r in records]
                })
    for match_val, records in phone_map.items():
        if len(records) > 1:
            ids_key = ",".join(sorted(r["id"] for r in records))
            if ids_key not in seen_ids:
                seen_ids.add(ids_key)
                duplicates.append({
                    "type":       "Phone",
                    "match_value": records[0]["phone"],
                    "records":    [{"id": r["id"], "full_name": r["full_name"],
                                    "role_category": r["role_category"], "source": r["source"]}
                                   for r in records]
                })

    # ── Ratio Alert ──────────────────────────────────────────────────────────
    students = [r for r in regs if r["role_category"] == "Student"]
    mentors  = [r for r in regs if r["role_category"] == "Mentor"]
    ratio_alert = None
    if students:
        ratio = len(students) / max(len(mentors), 1)
        if ratio > 6.0:
            ratio_alert = {
                "type":    "danger",
                "ratio":   round(ratio, 1),
                "message": f"High student-to-mentor ratio ({ratio:.1f}:1). "
                           f"Recommend recruiting at least {max(0, int(len(students)/5) - len(mentors))} more Mentors."
            }
        else:
            ratio_alert = {
                "type":    "success",
                "ratio":   round(ratio, 1),
                "message": f"Healthy student-to-mentor ratio ({ratio:.1f}:1)."
            }

    # ── Dynamic Recommendations ──────────────────────────────────────────────
    recommendations = []
    checked_in     = sum(1 for r in regs if r["checked_in"])
    checkin_rate   = checked_in / total if total else 0

    if checkin_rate < 0.40 and total > 8:
        recommendations.append({
            "type":    "info",
            "icon":    "fa-chart-line",
            "title":   "Check-in Tracking Lag",
            "message": f"Current check-in rate is low ({round(checkin_rate*100)}%). "
                       "Send personalized QR code reminders to attendees."
        })

    student_checkins = sum(1 for r in students if r["checked_in"])
    student_rate     = student_checkins / len(students) if students else 1
    if student_rate < 0.50 and len(students) > 4:
        recommendations.append({
            "type":    "warning",
            "icon":    "fa-graduation-cap",
            "title":   f"Low Student Check-ins ({round(student_rate*100)}%)",
            "message": "Students are checking in slower than Professionals. "
                       "Set up a dedicated student fast-track lane."
        })

    source_counts = {}
    for r in regs:
        source_counts[r["source"]] = source_counts.get(r["source"], 0) + 1

    if source_counts.get("Google Forms", 0) > source_counts.get("Web Form", 0) * 2:
        recommendations.append({
            "type":    "info",
            "icon":    "fa-lightbulb",
            "title":   "Google Forms Dominance",
            "message": "Over 60% of entries originate from Google Forms. "
                       "Verify form redirects are capturing all data fields correctly."
        })

    if not recommendations:
        recommendations.append({
            "type":    "success",
            "icon":    "fa-bolt",
            "title":   "All Systems Optimal",
            "message": "Registration sources, check-in rates, and resource ratios are all within healthy ranges."
        })

    return {
        "forecast":        {"predicted": predicted, "percentage": percentage, "total": total},
        "duplicates":      duplicates,
        "recommendations": recommendations,
        "ratio_alert":     ratio_alert,
    }
