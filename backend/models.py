"""
Database Models & SQLite Helper
Provides a thin wrapper around sqlite3 and defines all table schemas.
"""

import sqlite3
import uuid
from contextlib import contextmanager
from backend.config import DATABASE_PATH


# ─── Connection Helper ────────────────────────────────────────────────────────

@contextmanager
def get_db():
    """Context manager that yields a dict-row connection and auto-commits."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row          # rows act like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─── Schema DDL ───────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT CHECK(role IN ('organizer','participant')) DEFAULT 'participant',
    full_name     TEXT NOT NULL,
    phone         TEXT,
    organization  TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    event_type TEXT,
    start_date TEXT,
    end_date TEXT,
    location TEXT,
    expected_attendees INTEGER DEFAULT 0,
    status TEXT DEFAULT 'Draft',
    selected_venue_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS registrations (
    id               TEXT PRIMARY KEY,
    event_id         TEXT,
    full_name        TEXT NOT NULL,
    email            TEXT NOT NULL,
    phone            TEXT NOT NULL,
    role_category    TEXT CHECK(role_category IN ('Student','Professional','Mentor','Organizer')) DEFAULT 'Professional',
    organization     TEXT DEFAULT '',
    state            TEXT DEFAULT '',
    country          TEXT DEFAULT '',
    area_of_interest TEXT DEFAULT '',
    qr_code_path     TEXT DEFAULT '',
    status           TEXT CHECK(status IN ('pending','confirmed','cancelled')) DEFAULT 'pending',
    source           TEXT DEFAULT 'Web Form',
    checked_in       INTEGER DEFAULT 0,
    check_in_time    TIMESTAMP,
    verified_at      TIMESTAMP,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS check_ins (
    id               TEXT PRIMARY KEY,
    registration_id  TEXT REFERENCES registrations(id) ON DELETE CASCADE,
    check_in_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    check_in_method  TEXT CHECK(check_in_method IN ('QR','manual')) DEFAULT 'manual'
);

CREATE TABLE IF NOT EXISTS venues (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    address TEXT,
    latitude REAL,
    longitude REAL,
    capacity INTEGER,
    venue_type TEXT,
    event_types_supported TEXT,
    cost REAL,
    availability_status TEXT DEFAULT 'Available',
    facilities TEXT,
    wifi INTEGER DEFAULT 0,
    projector INTEGER DEFAULT 0,
    projector_screen INTEGER DEFAULT 0,
    sound_system INTEGER DEFAULT 0,
    microphones INTEGER DEFAULT 0,
    air_conditioning INTEGER DEFAULT 0,
    parking INTEGER DEFAULT 0,
    stage INTEGER DEFAULT 0,
    seating_arrangement TEXT,
    power_backup INTEGER DEFAULT 0,
    cleanliness_rating REAL,
    security_rating REAL,
    cctv INTEGER DEFAULT 0,
    fire_safety INTEGER DEFAULT 0,
    emergency_exits INTEGER DEFAULT 0,
    accessibility INTEGER DEFAULT 0,
    wheelchair_accessibility INTEGER DEFAULT 0,
    lift INTEGER DEFAULT 0,
    drinking_water INTEGER DEFAULT 0,
    washrooms INTEGER DEFAULT 0,
    technical_support INTEGER DEFAULT 0,
    ratings REAL,
    reviews INTEGER,
    description TEXT
);

CREATE TABLE IF NOT EXISTS venue_bookings (
    id TEXT PRIMARY KEY,
    event_id TEXT REFERENCES events(id),
    venue_id TEXT REFERENCES venues(id),
    organizer_id TEXT,
    event_name TEXT,
    booking_date TEXT,
    start_time TEXT,
    end_time TEXT,
    status TEXT DEFAULT 'Booked'
);

CREATE TABLE IF NOT EXISTS speakers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    organization TEXT,
    designation TEXT,
    expertise TEXT,
    years_of_experience INTEGER,
    biography TEXT,
    languages TEXT,
    availability TEXT DEFAULT 'Available',
    previous_engagements INTEGER,
    previous_topics TEXT,
    ratings REAL,
    audience_engagement_score REAL,
    communication_score REAL,
    previous_feedback TEXT,
    certifications TEXT,
    achievements TEXT,
    honorarium REAL,
    preferred_event_types TEXT,
    preferred_audience TEXT,
    delivery_mode TEXT,
    contact_info TEXT,
    status TEXT DEFAULT 'Available'
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    event_id TEXT REFERENCES events(id),
    session_name TEXT,
    topic TEXT,
    session_type TEXT,
    session_date TEXT,
    start_time TEXT,
    end_time TEXT,
    venue_id TEXT,
    expected_attendees INTEGER,
    required_expertise TEXT,
    room_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS speaker_assignments (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    speaker_id TEXT REFERENCES speakers(id),
    organizer_id TEXT,
    status TEXT CHECK(status IN ('Pending','Accepted','Declined')) DEFAULT 'Pending',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS speaker_messages (
    id TEXT PRIMARY KEY,
    assignment_id TEXT,
    sender TEXT,
    message TEXT,
    message_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS session_attendance (
    id TEXT PRIMARY KEY,
    event_id TEXT REFERENCES events(id),
    session_id TEXT REFERENCES sessions(id),
    registration_id TEXT REFERENCES registrations(id),
    check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT REFERENCES events(id),
    name TEXT,
    reg_id TEXT,
    session_id TEXT REFERENCES sessions(id),
    rating INTEGER,
    comment TEXT,
    submitted_at TEXT
);

CREATE TABLE IF NOT EXISTS sponsors (
    id                    TEXT PRIMARY KEY,
    event_id              TEXT DEFAULT 'EVT-1001',
    name                  TEXT NOT NULL,
    tier                  TEXT CHECK(tier IN ('Platinum','Gold','Silver','Bronze','Custom')) DEFAULT 'Gold',
    contact_person        TEXT,
    contact_email         TEXT,
    phone                 TEXT,
    contract_status       TEXT DEFAULT 'Signed',
    contract_value        REAL DEFAULT 0.0,
    payment_status        TEXT DEFAULT 'Pending',
    total_amount          REAL DEFAULT 0.0,
    paid_amount           REAL DEFAULT 0.0,
    engagement_score      INTEGER DEFAULT 75,
    overall_performance   TEXT DEFAULT 'Good',
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sponsorship_deliverables (
    id                    TEXT PRIMARY KEY,
    sponsor_id            TEXT REFERENCES sponsors(id) ON DELETE CASCADE,
    deliverable_name      TEXT NOT NULL,
    description           TEXT,
    due_date              TEXT,
    status                TEXT CHECK(status IN ('Pending','In Progress','Completed','Overdue')) DEFAULT 'Pending',
    completion_percentage INTEGER DEFAULT 0,
    completed_at          TIMESTAMP,
    notes                 TEXT
);

CREATE TABLE IF NOT EXISTS sponsor_engagements (
    id                    TEXT PRIMARY KEY,
    sponsor_id            TEXT REFERENCES sponsors(id) ON DELETE CASCADE,
    booth_visits          INTEGER DEFAULT 0,
    attendee_interactions INTEGER DEFAULT 0,
    session_participation INTEGER DEFAULT 0,
    social_engagement     INTEGER DEFAULT 0,
    leads                 INTEGER DEFAULT 0,
    engagement_score      INTEGER DEFAULT 75,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS incidents (
    id                    TEXT PRIMARY KEY,
    incident_number       TEXT UNIQUE,
    event_id              TEXT DEFAULT 'EVT-1001',
    title                 TEXT NOT NULL,
    description           TEXT,
    category              TEXT DEFAULT 'General',
    severity              TEXT CHECK(severity IN ('Low','Medium','High','Critical')) DEFAULT 'Medium',
    priority              TEXT CHECK(priority IN ('Low','Medium','High','Critical')) DEFAULT 'Medium',
    location              TEXT,
    affected_area         TEXT,
    source                TEXT DEFAULT 'Participant Portal',
    reporter_id           TEXT,
    reported_by           TEXT,
    assigned_team         TEXT DEFAULT 'General Support',
    status                TEXT DEFAULT 'REPORTED',
    recommended_action    TEXT,
    escalated             INTEGER DEFAULT 0,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at           TIMESTAMP,
    closed_at             TIMESTAMP
);

CREATE TABLE IF NOT EXISTS incident_timeline (
    id                    TEXT PRIMARY KEY,
    incident_id           TEXT REFERENCES incidents(id) ON DELETE CASCADE,
    status                TEXT NOT NULL,
    action                TEXT NOT NULL,
    description           TEXT,
    performed_by          TEXT DEFAULT 'System',
    timestamp             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operational_alerts (
    id                    TEXT PRIMARY KEY,
    event_id              TEXT DEFAULT 'EVT-1001',
    title                 TEXT NOT NULL,
    message               TEXT,
    alert_type            TEXT DEFAULT 'Operational',
    severity              TEXT CHECK(severity IN ('Info','Low','Medium','High','High-Priority','Critical')) DEFAULT 'Medium',
    priority              TEXT DEFAULT 'Medium',
    module                TEXT DEFAULT 'System',
    entity_id             TEXT,
    status                TEXT DEFAULT 'Active',
    recommended_action    TEXT,
    timestamp             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at       TIMESTAMP,
    resolved_at           TIMESTAMP
);
"""


def get_table_columns(conn, table_name):
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


def ensure_schema_updates(conn):
    existing = get_table_columns(conn, 'registrations')
    if 'event_id' not in existing:
        conn.execute('ALTER TABLE registrations ADD COLUMN event_id TEXT')

    existing = get_table_columns(conn, 'sessions')
    if 'required_expertise' not in existing:
        conn.execute('ALTER TABLE sessions ADD COLUMN required_expertise TEXT')
    if 'room_id' not in existing:
        conn.execute('ALTER TABLE sessions ADD COLUMN room_id TEXT')

    existing = get_table_columns(conn, 'session_attendance')
    if 'event_id' not in existing:
        conn.execute('ALTER TABLE session_attendance ADD COLUMN event_id TEXT')

    existing = get_table_columns(conn, 'venue_bookings')
    if 'event_id' not in existing:
        conn.execute('ALTER TABLE venue_bookings ADD COLUMN event_id TEXT')

    existing = get_table_columns(conn, 'sponsor_engagements')
    if 'leads' not in existing:
        conn.execute('ALTER TABLE sponsor_engagements ADD COLUMN leads INTEGER DEFAULT 0')

    # ensure feedback table exists in older databases
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'").fetchall()
    if not rows:
        conn.execute('''
            CREATE TABLE feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT REFERENCES events(id),
                name TEXT,
                reg_id TEXT,
                session_id TEXT REFERENCES sessions(id),
                rating INTEGER,
                comment TEXT,
                submitted_at TEXT
            )
        ''')


def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.executescript(SCHEMA_SQL)
        ensure_schema_updates(conn)


def generate_id(prefix="REG"):
    """Generate a unique Registration ID like REG-839201."""
    import random
    return f"{prefix}-{random.randint(100000, 999999)}"


def row_to_dict(row):
    """Convert a sqlite3.Row to a plain dict."""
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    """Convert a list of sqlite3.Row objects to plain dicts."""
    return [dict(r) for r in rows]
