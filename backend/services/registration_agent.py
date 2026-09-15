"""
Registration Agent Service
Handles: form validation, duplicate detection, ID generation,
         QR code creation, DB insertion, and email dispatch.
"""

import uuid
from datetime import datetime
from backend.models       import get_db, generate_id, row_to_dict
from backend.utils.qr_generator  import generate_qr
from backend.utils.email_sender  import send_registration_email


VALID_ROLES   = {"Student", "Professional", "Mentor", "Organizer"}
VALID_SOURCES = {"Web Form", "Google Forms", "Mobile App", "API"}


def validate_payload(data: dict) -> list[str]:
    """Return a list of validation error messages (empty = valid)."""
    errors = []
    if not data.get("full_name", "").strip():
        errors.append("full_name is required.")
    email = data.get("email", "").strip()
    if not email or "@" not in email:
        errors.append("A valid email is required.")
    if not data.get("phone", "").strip():
        errors.append("phone is required.")
    if data.get("role_category") not in VALID_ROLES:
        errors.append(f"role_category must be one of {VALID_ROLES}.")
    return errors


def check_duplicate(email: str) -> dict | None:
    """Return an existing registration row if this email is already registered."""
    if not email:
        return None
    normalized_email = email.strip().lower()
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM registrations WHERE LOWER(email)=LOWER(?)", (normalized_email,)
        ).fetchone()
    return row_to_dict(row)


def create_registration(data: dict) -> tuple[dict, dict]:
    """
    Create a new registration record.

    Returns:
        (registration_dict, email_result_dict)
    """
    reg_id = generate_id("REG")

    # Generate QR code PNG
    qr_path = generate_qr(reg_id)

    now = datetime.utcnow().isoformat()

    reg = {
        "id":               reg_id,
        "full_name":        data["full_name"].strip(),
        "email":            data["email"].strip().lower(),
        "phone":            data["phone"].strip(),
        "role_category":    data.get("role_category", "Professional"),
        "organization":     data.get("organization", "").strip(),
        "state":            data.get("state", "").strip(),
        "country":          data.get("country", "").strip(),
        "area_of_interest": data.get("area_of_interest", "").strip(),
        "qr_code_path":     qr_path,
        "status":           "pending",
        "source":           data.get("source", "Web Form"),
        "checked_in":       0,
        "check_in_time":    None,
        "created_at":       now,
        "updated_at":       now,
    }

    with get_db() as conn:
        conn.execute("""
            INSERT INTO registrations
              (id, full_name, email, phone, role_category, organization,
               state, country, area_of_interest, qr_code_path,
               status, source, checked_in, check_in_time, created_at, updated_at)
            VALUES
              (:id, :full_name, :email, :phone, :role_category, :organization,
               :state, :country, :area_of_interest, :qr_code_path,
               :status, :source, :checked_in, :check_in_time, :created_at, :updated_at)
        """, reg)

    # Send confirmation email (or save to outbox)
    email_result = send_registration_email(reg)

    return reg, email_result
