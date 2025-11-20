# app/core/exceptions.py

from typing import Any, Optional

from fastapi import status


class BaseAppException(Exception):
    """Base exception for all application exceptions."""

    def __init__(
        self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    
class DatabaseException(BaseAppException):
    """Database operation exception."""

    def __init__(
        self, message: str = "Database operation failed",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class NotFoundException(BaseAppException):
    """Resource not found exception."""

    def __init__(
        self, message: str = "Resource not found",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class UnauthorizedException(BaseAppException):
    """Unauthorized access exception."""

    def __init__(
        self, message: str = "Unauthorized access",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class ForbiddenException(BaseAppException):
    """Forbidden access exception."""

    def __init__(
        self, message: str = "Forbidden access",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ValidationException(BaseAppException):
    """Data validation exception."""

    def __init__(
        self, message: str = "Data validation error",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            details=details
        )