# app/utils/otp.py

from io import BytesIO
from typing import Tuple

import pyotp
import qrcode

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OTPService:
    """Service for handling OTP/2FA operations."""

    @staticmethod
    def generate_secret() -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_provisioning_uri(secret: str, user_email: str) -> str:
        """Generate provisioning URI for QR code."""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=user_email,
            issuer_name=settings.two_fa_issuer
        )
    
    @staticmethod
    def generate_qr_code(provisioning_uri: str) -> bytes:
        """Generate QR code image."""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    
    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """Verify the TOTP token."""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> list[str]:
        """Generate backup codes for 2FA"""
        import secrets
        return [secrets.token_hex(4).upper() for _ in range(count)]
    

otp_service = OTPService()
