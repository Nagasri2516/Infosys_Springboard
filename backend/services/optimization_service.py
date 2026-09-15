def optimize_room_allocation(event_type, total_attendees, sessions, available_rooms=None):
    available_rooms = available_rooms or [
        {"id": "RM-1", "name": "Hall A", "capacity": 500, "facilities": ["Wi-Fi", "Projector", "Stage"]},
        {"id": "RM-2", "name": "Hall B", "capacity": 200, "facilities": ["Wi-Fi", "Projector"]},
        {"id": "RM-3", "name": "Hall C", "capacity": 120, "facilities": ["Wi-Fi"]},
    ]
    allocations = []
    for session in sessions:
        expected = int(session.get("expected_attendees", 0))
        suitable = [room for room in available_rooms if room.get("capacity", 0) >= expected]
        if not suitable:
            allocations.append({**session, "assigned_room": None, "suggestion": "No suitable room matches this session size."})
            continue
        chosen = min(suitable, key=lambda room: room.get("capacity", 0))
        allocations.append({**session, "assigned_room": chosen, "suggestion": f"Assigned {chosen['name']} for {expected} attendees."})
    return allocations


def suggest_room_change(session_attendees, current_room_capacity):
    if session_attendees > current_room_capacity:
        return f"Upgrade to a room with capacity >= {session_attendees}."
    if session_attendees < current_room_capacity - 80:
        return "Downgrade to a smaller room to reduce unused capacity and cost."
    return "Current room size remains appropriate."
