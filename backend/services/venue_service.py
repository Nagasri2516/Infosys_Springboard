import json
import os
from pathlib import Path
from backend.models import get_db, generate_id, init_db

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "venues.json"


def _load_seed_venues():
    if DATA_FILE.exists():
        with DATA_FILE.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    return []


def seed_venues():
    init_db()
    venues = _load_seed_venues()
    if not venues:
        return []
    with get_db() as conn:
        conn.execute("DELETE FROM venues")
        conn.execute("DELETE FROM venue_bookings")
        for venue in venues:
            conn.execute(
                """
                INSERT INTO venues (
                    id, name, location, city, state, country, address, latitude, longitude,
                    capacity, venue_type, event_types_supported, cost, availability_status,
                    facilities, wifi, projector, projector_screen, sound_system, microphones,
                    air_conditioning, parking, stage, seating_arrangement, power_backup,
                    cleanliness_rating, security_rating, cctv, fire_safety, emergency_exits,
                    accessibility, wheelchair_accessibility, lift, drinking_water, washrooms,
                    technical_support, ratings, reviews, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    venue.get("id", generate_id("VEN")),
                    venue.get("name"), venue.get("location"), venue.get("city"), venue.get("state"), venue.get("country"),
                    venue.get("address"), venue.get("latitude"), venue.get("longitude"), venue.get("capacity"), venue.get("venue_type"),
                    ",".join(venue.get("event_types_supported", [])), venue.get("cost"), venue.get("availability_status", "Available"),
                    ",".join(venue.get("facilities", [])), int(venue.get("wifi", 0)), int(venue.get("projector", 0)), int(venue.get("projector_screen", 0)),
                    int(venue.get("sound_system", 0)), int(venue.get("microphones", 0)), int(venue.get("air_conditioning", 0)), int(venue.get("parking", 0)),
                    int(venue.get("stage", 0)), venue.get("seating_arrangement"), int(venue.get("power_backup", 0)), venue.get("cleanliness_rating"),
                    venue.get("security_rating"), int(venue.get("cctv", 0)), int(venue.get("fire_safety", 0)), int(venue.get("emergency_exits", 0)),
                    int(venue.get("accessibility", 0)), int(venue.get("wheelchair_accessibility", 0)), int(venue.get("lift", 0)), int(venue.get("drinking_water", 0)),
                    int(venue.get("washrooms", 0)), int(venue.get("technical_support", 0)), venue.get("ratings"), venue.get("reviews"), venue.get("description")
                ),
            )
    return venues


def list_venues():
    init_db()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM venues ORDER BY name").fetchall()
        return [dict(r) for r in rows]


def recommend_venues(event_type, expected_attendees, max_budget, preferred_city=None, required_facilities=None,
                     power_backup_required=False, cleanliness_preference="Medium", security_required=False,
                     accessibility_required=False, indoor_preference=None, date=None, time=None, allow_relaxed=True):
    init_db()
    required_facilities = required_facilities or []
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM venues").fetchall()
    venues = [dict(r) for r in rows]
    if not venues:
        seed_venues()
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM venues").fetchall()
        venues = [dict(r) for r in rows]
    # First pass: strict filtering (exact matches)
    strict_results = []
    for venue in venues:
        try:
            cap = int(venue.get("capacity") or 0)
        except Exception:
            cap = 0
        if cap < expected_attendees:
            continue
        if max_budget and (venue.get("cost") or 0) > max_budget:
            continue
        if preferred_city and str(venue.get("city", "")).lower() != str(preferred_city).lower():
            continue
        supported = set((venue.get("event_types_supported") or "").split(","))
        support = set([value.strip().lower() for value in supported if value.strip()])
        if event_type and event_type.lower() not in support and support:
            continue
        facilities = set([f.strip().lower() for f in (venue.get("facilities") or "").split(",") if f.strip()])
        if required_facilities and not set([f.lower() for f in required_facilities]).issubset(facilities):
            continue
        if power_backup_required and not venue.get("power_backup"):
            continue
        if security_required and not (venue.get("security_rating") or 0) >= 4:
            continue
        if accessibility_required and not venue.get("wheelchair_accessibility"):
            continue
        if cleanliness_preference == "High" and (venue.get("cleanliness_rating") or 0) < 4:
            continue
        score = 70
        score += min(20, int((venue.get("ratings", 0) or 0) * 2))
        score += 5 if venue.get("power_backup") else 0
        score += 5 if venue.get("wifi") else 0
        score += 5 if venue.get("projector") else 0
        score += 5 if venue.get("accessibility") else 0
        strict_results.append({**venue, "match_score": min(99, score), "relaxed": False})

    if strict_results:
        strict_results.sort(key=lambda item: item["match_score"], reverse=True)
        return strict_results

    # If relaxed fallback not allowed, return empty list to indicate no strict matches
    if not allow_relaxed:
        return []

    # Fallback: relaxed matching — return near-misses with explanations and lower scores
    relaxed_results = []
    for venue in venues:
        reasons = []
        score = 60
        cap = int(venue.get("capacity") or 0)
        # capacity: prefer >= expected, but accept slightly smaller venues with penalty
        if cap < expected_attendees:
            shortfall = expected_attendees - cap
            reasons.append(f"Capacity short by {shortfall}")
            score -= min(30, int((shortfall / max(1, expected_attendees)) * 50))
        else:
            score += 5

        # budget: allow modest overages with penalty
        cost = venue.get("cost") or 0
        if max_budget and cost > max_budget:
            over = cost - max_budget
            reasons.append(f"Over budget by {over}")
            score -= min(25, int((over / max(1, max_budget)) * 50))
        else:
            score += 5

        # city/location: if different city, mark as nearby candidate
        if preferred_city and str(venue.get("city", "")).lower() != str(preferred_city).lower():
            reasons.append(f"Located in {venue.get('city')}")
            score -= 8
        else:
            score += 3

        supported = set((venue.get("event_types_supported") or "").split(","))
        support = set([value.strip().lower() for value in supported if value.strip()])
        if event_type and support and event_type.lower() not in support:
            reasons.append("Does not explicitly list event type")
            score -= 5
        else:
            score += 2

        facilities = set([f.strip().lower() for f in (venue.get("facilities") or "").split(",") if f.strip()])
        missing = []
        for req in required_facilities:
            if req.strip().lower() not in facilities:
                missing.append(req.strip())
        if missing:
            reasons.append("Missing: " + ", ".join(missing))
            score -= min(20, len(missing) * 6)
        else:
            score += 3

        if power_backup_required and not venue.get("power_backup"):
            reasons.append("No power backup")
            score -= 6
        if security_required and not (venue.get("security_rating") or 0) >= 4:
            reasons.append("Lower security rating")
            score -= 4
        if accessibility_required and not venue.get("wheelchair_accessibility"):
            reasons.append("Limited accessibility")
            score -= 4

        # Ratings and amenities boost
        score += min(15, int((venue.get("ratings", 0) or 0) * 2))
        if venue.get("wifi"): score += 3
        if venue.get("projector"): score += 3

        score = max(10, min(98, int(score)))
        relaxed_results.append({**venue, "match_score": score, "relaxed": True, "relax_reasons": reasons})

    # sort relaxed by score
    relaxed_results.sort(key=lambda item: item["match_score"], reverse=True)
    return relaxed_results


def check_availability(venue_id, event_date, start_time, end_time):
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM venue_bookings WHERE venue_id=? AND booking_date=? AND status != 'Cancelled'",
            (venue_id, event_date),
        ).fetchall()
    bookings = [dict(r) for r in rows]
    for booking in bookings:
        current_start = booking.get("start_time")
        current_end = booking.get("end_time")
        if current_start and current_end and not (end_time <= current_start or start_time >= current_end):
            return False, "Venue is already booked for the requested time slot."
    return True, "Venue is available."


def book_venue(event_id, venue_id, organizer_id, event_name, event_date, start_time, end_time, status="Booked"):
    init_db()
    available, message = check_availability(venue_id, event_date, start_time, end_time)
    if not available:
        return None, message
    booking_id = generate_id("BKG")
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO venue_bookings (id, event_id, venue_id, organizer_id, event_name, booking_date, start_time, end_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (booking_id, event_id, venue_id, organizer_id, event_name, event_date, start_time, end_time, status),
        )
        conn.execute("UPDATE events SET selected_venue_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (venue_id, event_id))
    return {"id": booking_id, "event_id": event_id, "venue_id": venue_id, "status": status}, "Booking confirmed."


def add_venue(data):
    """Manually add a venue to the database."""
    init_db()
    venue_id = generate_id("VEN")
    facilities_list = data.get("facilities", [])
    if isinstance(facilities_list, str):
        facilities_list = [f.strip() for f in facilities_list.split(",") if f.strip()]
    event_types_list = data.get("event_types_supported", [])
    if isinstance(event_types_list, str):
        event_types_list = [e.strip() for e in event_types_list.split(",") if e.strip()]

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO venues (
                id, name, location, city, state, country, address, capacity, venue_type,
                event_types_supported, cost, availability_status, facilities, wifi, projector,
                projector_screen, sound_system, microphones, air_conditioning, parking, stage,
                seating_arrangement, power_backup, cleanliness_rating, security_rating, cctv,
                fire_safety, emergency_exits, accessibility, wheelchair_accessibility, lift,
                drinking_water, washrooms, technical_support, ratings, reviews, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                venue_id,
                data.get("name"),
                data.get("location", ""),
                data.get("city", ""),
                data.get("state", ""),
                data.get("country", "India"),
                data.get("address", ""),
                int(data.get("capacity", 0) or 0),
                data.get("venue_type", "Hall"),
                ",".join(event_types_list),
                float(data.get("cost", 0) or 0),
                data.get("availability_status", "Available"),
                ",".join(facilities_list),
                int(bool(data.get("wifi"))),
                int(bool(data.get("projector"))),
                int(bool(data.get("projector_screen"))),
                int(bool(data.get("sound_system"))),
                int(bool(data.get("microphones"))),
                int(bool(data.get("air_conditioning"))),
                int(bool(data.get("parking"))),
                int(bool(data.get("stage"))),
                data.get("seating_arrangement", "Theatre"),
                int(bool(data.get("power_backup"))),
                float(data.get("cleanliness_rating", 3) or 3),
                float(data.get("security_rating", 3) or 3),
                int(bool(data.get("cctv"))),
                int(bool(data.get("fire_safety"))),
                int(bool(data.get("emergency_exits"))),
                int(bool(data.get("accessibility"))),
                int(bool(data.get("wheelchair_accessibility"))),
                int(bool(data.get("lift"))),
                int(bool(data.get("drinking_water"))),
                int(bool(data.get("washrooms"))),
                int(bool(data.get("technical_support"))),
                float(data.get("ratings", 3) or 3),
                int(data.get("reviews", 0) or 0),
                data.get("description", ""),
            ),
        )
    with get_db() as conn:
        row = conn.execute("SELECT * FROM venues WHERE id=?", (venue_id,)).fetchone()
    return dict(row) if row else {"id": venue_id, "name": data.get("name")}
