# app/modules/users/exceptions.py

from fastapi import status

from app.core.exceptions import (
    BaseAppException, NotFoundException, UnauthorizedException,
    ValidationException, ForbiddenException
)


class UserNotFoundException(NotFoundException):
    """User not found exception."""

    def __init__(self, user_id: int = None, email: str = None, username: str = None):
        if user_id:
            identifier = f"ID {user_id}"
        elif email:
            identifier = f"email '{email}'"
        else:
            identifier = f"username '{username}'"

        super().__init__(
            message=f"User with {identifier} not found.",
            details={"user_id": user_id, "email": email, "username": username}
        )


class UserAlreadyExistsException(ValidationException):
    """User already exists exception."""

    def __init__(self, field: str, value: str):
        super().__init__(
            message=f"User with {field} '{value}' already exists.",
            details={"field": field, "value": value}
        )


class InvalidCredentialsException(UnauthorizedException):
    """Invalid credentials exception."""

    def __init__(self):
        super().__init__(
            message="Invalid email or password",
            details={}
        )


class AccountLockedException(UnauthorizedException):
    """Account locked exception."""

    def __init__(self, locked_until: str):
        super().__init__(
            message=f"Account is locked until {locked_until}",
            details={"locked_until": locked_until}
        )


class AccountInactiveException(UnauthorizedException):
    """Account inactive exception."""

    def __init__(self):
        super().__init__(
            message="Account is inactive or suspended",
            details={}
        )


class EmailNotVerifiedException(UnauthorizedException):
    """Email not verified exception."""

    def __init__(self):
        super().__init__(
            message="Email address is not verified",
            details={}
        )


class TwoFactorRequiredException(UnauthorizedException):
    """2FA required exception."""

    def __init__(self):
        super().__init__(
            message="Two-factor authentication code required",
            details={"requires_2fa": True}
        )


class Invalid2FACodeException(UnauthorizedException):
    """Invalid 2FA code exception."""

    def __init__(self):
        super().__init__(
            message="Invalid two-factor authentication code",
            details={}
        )


class TwoFactorAlreadyEnabledException(ValidationException):
    """2FA already enabled exception."""

    def __init__(self):
        super().__init__(
            message="Two-factor authentication is already enabled",
            details={}
        )


class TwoFactorNotEnabledException(ValidationException):
    """2FA not enabled exception."""

    def __init__(self):
        super().__init__(
            message="Two-factor authentication is not enabled",
            details={}
        )


class InvalidTokenException(UnauthorizedException):
    """Invalid token exception."""

    def __init__(self, token_type: str = "token"):
        super().__init__(
            message=f"Invalid or expired {token_type}",
            details={"token_type": token_type}
        )


class WeakPasswordException(ValidationException):
    """Weak password exception."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            details={}
        )


class PasswordReusedException(ValidationException):
    """Password reused exception."""

    def __init__(self):
        super().__init__(
            message="Cannot reuse recent passwords",
            details={}
        )


class InsufficientPermissionsException(ForbiddenException):
    """Insufficient permissions exception."""

    def __init__(self, resource: str, action: str):
        super().__init__(
            message=f"Insufficient permissions: {action} required on {resource}",
            details={"resource": resource, "action": action}
        )