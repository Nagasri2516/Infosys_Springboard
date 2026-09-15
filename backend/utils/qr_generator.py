"""
QR Code Generator Utility
Generates a QR-code PNG for a given registration_id,
saves it under backend/static/qrcodes/ and returns the web-accessible URL.
"""

import os
import qrcode
from qrcode.image.pure import PyPNGImage
from backend.config import QR_CODE_DIR


def generate_qr(registration_id: str) -> str:
    """
    Generate a QR code PNG for `registration_id`.

    Returns:
        The relative URL path  e.g. "/static/qrcodes/REG-123456.png"
    """
    filename  = f"{registration_id}.png"
    file_path = os.path.join(QR_CODE_DIR, filename)

    if not os.path.exists(file_path):
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(registration_id)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#0f172a", back_color="#f8fafc")
        img.save(file_path)

    return f"/static/qrcodes/{filename}"
