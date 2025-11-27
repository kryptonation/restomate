# app/modules/seeder/exceptions.py

from app.core.exceptions import NotFoundException, BaseAppException


class SeederNotFoundException(NotFoundException):
    """Seeder execution not found."""

    def __init__(self, identifier):
        super().__init__(
            message=f"Seeder execution {identifier} not found.",
            details={"identifier": identifier}
        )


class SeederExecutionException(BaseAppException):
    """Seeder execution failed."""

    def __init__(self, error: str):
        super().__init__(
            message=f"Seeder execution failed: {error}",
            status_code=500,
            details={"error": error}
        )
