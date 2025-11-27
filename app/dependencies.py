# app/dependencies.py

from typing import Annotated

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.users.services import UserService
from app.modules.users.models import User
from app.core.security import decode_token
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get current authenticated user."""
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header.split(" ")[1]
    token_data = decode_token(token)

    if not token_data or token_data.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_service = UserService(db)
    user_id = int(token_data.get("sub"))
    user = await user_service.get_user(user_id)

    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_permission(resource: str, action: str):
    """
    Dependency factory to require specific permission.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(
            current_user: ActiveUser,
            _: None = Depends(require_permission("resource", "action"))
        ):
            ...
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Check if user has required permission."""
        from app.modules.roles.services import RoleService

        # Superusers bypass all permission checks
        if current_user.is_superuser:
            return current_user
        
        # Check if user has a role
        if not current_user.role_id:
            logger.warning(
                "permission_denied_no_role",
                user_id=current_user.id,
                resource=resource,
                action=action
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No role assigned"
            )
        
        # Check permission
        role_service = RoleService(db)
        has_permission = await role_service.check_permissions(
            current_user.role_id,
            resource,
            action
        )

        if not has_permission:
            logger.warning(
                "permission_denied",
                user_id=current_user.id,
                resource=resource,
                action=action
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions to {action} {resource}"
            )
        
        return current_user
    
    return permission_checker


# Type aliases for common dependencies
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]

    