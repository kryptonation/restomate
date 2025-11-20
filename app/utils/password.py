# app/utils/password.py

import re
from typing import Tuple


class PasswordValidator:
    """Validate password strength"""

    @staticmethod
    def validate_strength(password: str) -> Tuple[bool, str]:
        """
        Validate password strength.

        Returns:
            Tuple of (is_valid, message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if len(password) > 128:
            return False, "Password must not exceed 128 characters."
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is strong."
    
    @staticmethod
    def check_common_passwords(password: str) -> bool:
        """Check if password is in common passwords list."""
        # TODO: In production, use a more comprehensive list
        common_passwords = {
            "password", "123456", "123456789", "qwerty", "abc123",
            "monkey", "letmein", "dragon", "111111", "baseball"
        }
        return password.lower() in common_passwords
    

password_validator = PasswordValidator()
