# app/modules/roles/exceptions.py

from app.core.exceptions import (
    NotFoundException, ValidationException
)


class RoleNotFoundException(NotFoundException):
    """Role not found exception."""

    def __init__(self, role_id: int = None, role_name: str = None):
        identifier = f"ID {role_id}" if role_id else f"name '{role_name}'"
        super().__init__(
            message=f"Role with {identifier} not found.",
            details={"role_id": role_id, "role_name": role_name}
        )


class PermissionNotFoundException(NotFoundException):
    """Permission not found exception."""

    def __init__(self, permission_id: int = None, permission_name: str = None):
        identifier = f"ID {permission_id}" if permission_id else f"name '{permission_name}'"
        super().__init__(
            message=f"Permission with {identifier} not found.",
            details={"permission_id": permission_id, "permission_name": permission_name}
        )


class RoleAlreadyExistsException(ValidationException):
    """Role already exists exception."""

    def __init__(self, role_name: str):
        super().__init__(
            message=f"Role with name '{role_name}' already exists.",
            details={"role_name": role_name}
        )


class SystemRoleProtectionException(ValidationException):
    """System role protection exception."""

    def __init__(self, operation: str):
        super().__init__(
            message=f"Cannot {operation} system role",
            details={"operation": operation}
        )

