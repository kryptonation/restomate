# app/modules/roles/repository.py

from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.modules.roles.models import Role, Permission
from app.modules.roles.exceptions import (
    RoleNotFoundException, PermissionNotFoundException
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class RoleRepository:
    """Repository for Role operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        stmt = select(Role).where(Role.id == role_id).options(
            selectinload(Role.permissions)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        stmt = select(Role).where(Role.name == name).options(
            selectinload(Role.permissions)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> List[Role]:
        """Get all roles with pagination."""
        stmt = select(Role).options(selectinload(Role.permissions))

        if is_active is not None:
            stmt = stmt.where(Role.is_active == is_active)

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create(self, role: Role) -> Role:
        """Create a new role."""
        self.db.add(role)
        await self.db.flush()
        await self.db.refresh(role)
        logger.info("role_created", role_id=role.id, role_name=role.name)
        return role
    
    async def update(self, role: Role) -> Role:
        """Update role."""
        await self.db.flush()
        await self.db.refresh(role)
        logger.info("role_updated", role_id=role.id, role_name=role.name)
        return role
    
    async def delete(self, role: Role) -> None:
        """Delete role."""
        await self.db.delete(role)
        await self.db.flush()
        logger.info("role_deleted", role_id=role.id, role_name=role.name)

    async def add_permissions(self, role: Role, permission_ids: List[int]) -> Role:
        """Add permissions to role."""
        stmt = select(Permission).where(Permission.id.in_(permission_ids))
        result = await self.db.execute(stmt)
        permissions = list(result.scalars().all())

        for permission in permissions:
            if permission not in role.permissions:
                role.permissions.append(permission)


        await self.db.flush()
        await self.db.refresh(role)
        logger.info("permissions_added_to_role", role_id=role.id, count=len(permissions))
        return role
    
    async def remove_permissions(self, role: Role, permission_ids: List[int]) -> Role:
        """Remove permissions from role."""
        role.permissions = [p for p in role.permissions if p.id not in permission_ids]
        await self.db.flush()
        await self.db.refresh(role)
        logger.info("permissions_removed_from_role", role_id=role.id, count=len(permission_ids))
        return role
    

class PermissionRepository:
    """Repository for Permission operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, permission_id: int) -> Optional[Permission]:
        """Get permission by ID."""
        stmt = select(Permission).where(Permission.id == permission_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Permission]:
        """Get permission by name."""
        stmt = select(Permission).where(Permission.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Permission]:
        """Get all permissions with pagination."""
        stmt = select(Permission).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_resource(self, resource: str) -> List[Permission]:
        """Get permissions by resource."""
        stmt = select(Permission).where(Permission.resource == resource)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create(self, permission: Permission) -> Permission:
        """Create a new permission."""
        self.db.add(permission)
        await self.db.flush()
        await self.db.refresh(permission)
        logger.info("permission_created", permission_id=permission.id, name=permission.name)
        return permission
    
    async def bulk_create(self, permissions: List[Permission]) -> List[Permission]:
        """Create multiple permissions."""
        self.db.add_all(permissions)
        await self.db.flush()
        logger.info("permissions_bulk_created", count=len(permissions))
        return permissions
    
