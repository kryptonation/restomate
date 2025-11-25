# app/modules/files/exceptions.py

from app.core.exceptions import (
    ValidationException, NotFoundException, BaseAppException
)


class FileValidationException(ValidationException):
    """File validation exception."""

    def __init__(self, message: str):
        super().__init__(message=message, details={})


class FileSizeExceededException(ValidationException):
    """File size exceeded exception."""

    def __init__(self, size: int, max_size: int):
        super().__init__(
            message=f"File size {size} bytes exceeds maximum allowed size of {max_size} bytes.",
            details={"size": size, "max_size": max_size}
        )


class InvalidFileTypeException(ValidationException):
    """Invalid file type exception."""

    def __init__(self, file_type: str, allowed_types: list):
        super().__init__(
            message=f"File type '{file_type}' is not allowed.",
            details={"file_type": file_type, "allowed_types": allowed_types}
        )


class FileNotFoundException(NotFoundException):
    """File not found exception."""

    def __init__(self, file_id: int = None, s3_key: str = None):
        super().__init__(
            message=f"File with ID {file_id} not found.",
            details={"file_id": file_id, "s3_key": s3_key}
        )


class S3OperationException(BaseAppException):
    """S3 operation exception."""

    def __init__(self, operation: str, error: str):
        super().__init__(
            message=f"S3 {operation} operation failed: {error}",
            status_code=500,
            details={"operation": operation, "error": error}
        )


class VirusScanException(ValidationException):
    """Virus scan exception."""

    def __init__(self, filename: str):
        super().__init__(
            message=f"File '{filename}' failed virus scan.",
            details={"filename": filename}
        )

