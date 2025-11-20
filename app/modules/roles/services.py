# app/modules/roles/services.py

from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.roles.models import Role
from app.modules.roles.repository import RoleRepository, PermissionRepository
from app.modules.roles.exceptions import (
    RoleNotFoundException,
    PermissionNotFoundException,
    RoleAlreadyExistsException,
    SystemRoleProtectionException
)
from app.modules.roles.schemas import RoleCreate, RoleUpdate
from app.core.logging import get_logger

logger = get_logger(__name__)


class RoleService:
    """Service for role management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.role_repo = RoleRepository(db)
        self.permission_repo = PermissionRepository(db)

    async def get_role(self, role_id: int) -> Role:
        """Get role by ID."""
        role = await self.role_repo.get_by_id(role_id=role_id)
        if not role:
            raise RoleNotFoundException(role_id=role_id)
        return role
    
    async def get_role_by_name(self, name: str) -> Role:
        """Get role by name."""
        role = await self.role_repo.get_by_name(name=name)
        if not role:
            raise RoleNotFoundException(role_name=name)
        return role
    
    async def list_roles(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> List[Role]:
        """List all roles"""
        return await self.role_repo.get_all(skip=skip, limit=limit, is_active=is_active)
    
    async def create_role(self, role_data: RoleCreate) -> Role:
        """Create a new role."""
        # Check if role already exists
        existing_role = await self.role_repo.get_by_name(name=role_data.name)
        if existing_role:
            raise RoleAlreadyExistsException(role_name=role_data.name)
        
        # Create role
        role = Role(
            name=role_data.name,
            description=role_data.description,
            is_active=role_data.is_active,
            is_system=False
        )

        # Add permissions if provided
        if role_data.permission_ids:
            for perm_id in role_data.permission_ids:
                permission = await self.permission_repo.get_by_id(permission_id=perm_id)
                if not permission:
                    raise PermissionNotFoundException(permission_id=perm_id)
                role.permissions.append(permission)

        role = await self.role_repo.create(role)
        logger.info("role_service_created", role_id=role.id, role_name=role.name)
        return role
    
    async def update_role(self, role_id: int, role_data: RoleUpdate) -> Role:
        """Update role."""
        role = await self.get_role(role_id=role_id)

        if role.is_system:
            raise SystemRoleProtectionException("update")
        
        # Update fields
        if role_data.name is not None:
            # Check if new name conflicts
            if role_data.name != role.name:
                existing_role = await self.role_repo.get_by_name(name=role_data.name)
                if existing_role:
                    raise RoleAlreadyExistsException(role_name=role_data.name)
            role.name = role_data.name
        
        if role_data.description is not None:
            role.description = role_data.description

        if role_data.is_active is not None:
            role.is_active = role_data.is_active

        role = await self.role_repo.update(role)
        logger.info("role_service_updated", role_id=role.id, role_name=role.name)
        return role
    
    async def delete_role(self, role_id: int) -> None:
        """Delete Role."""
        role = await self.get_role(role_id=role_id)

        if role.is_system:
            raise SystemRoleProtectionException("delete")
        
        await self.role_repo.delete(role)
        logger.info("role_service_deleted", role_id=role_id)

    async def add_permissions_to_role(self, role_id: int, permission_ids: List[int]) -> Role:
        """Add permissions to a role."""
        role = await self.get_role(role_id=role_id)

        # Verify all permissions exist
        for perm_id in permission_ids:
            permission = await self.permission_repo.get_by_id(permission_id=perm_id)
            if not permission:
                raise PermissionNotFoundException(permission_id=perm_id)
            
        role = await self.role_repo.add_permissions(role, permission_ids)
        logger.info("role_permissions_added", role_id=role.id, permission_ids=permission_ids)
        return role
    
    async def remove_permissions_from_role(self, role_id: int, permission_ids: List[int]) -> Role:
        """Remove permissions from role"""
        role = await self.get_role(role_id=role_id)
        role = await self.role_repo.remove_permissions(role, permission_ids)
        logger.info("role_permissions_removed", role_id=role_id, count=len(permission_ids))
        return role
    
    async def check_permissions(self, role_id: int, resource: str, action: str) -> bool:
        """Check if role has specific permission."""
        role = await self.get_role(role_id=role_id)

        for permission in role.permissions:
            if permission.resource == resource and permission.action == action:
                return True
            
        return False
    


        
        
