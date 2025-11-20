# app/modules/roles/router.py

from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.roles.services import RoleService
from app.modules.roles.schemas import (
    RoleCreate, RoleUpdate, RoleResponse,
    RolePermissionUpdate,
)

router = APIRouter(prefix="/roles", tags=["roles"])

def get_role_service(db: AsyncSession = Depends(get_db)) -> RoleService:
    """Dependency to get role service."""
    return RoleService(db)


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    service: RoleService = Depends(get_role_service)
):
    """Create a new role."""
    return await service.create_role(role_data=role_data)

@router.get("/", response_model=List[RoleResponse])
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    service: RoleService = Depends(get_role_service)
):
    """List all roles."""
    return await service.list_roles(skip=skip, limit=limit, is_active=is_active)

@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    service: RoleService = Depends(get_role_service)
):
    """Get a role by ID."""
    return await service.get_role(role_id=role_id)

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    service: RoleService = Depends(get_role_service)
):
    """Update a role by ID."""
    return await service.update_role(role_id=role_id, role_data=role_data)

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    service: RoleService = Depends(get_role_service)
):
    """Delete role."""
    await service.delete_role(role_id=role_id)

@router.put("/{role_id}/permissions", response_model=RoleResponse)
async def add_permissions(
    role_id: int,
    permissions: RolePermissionUpdate,
    service: RoleService = Depends(get_role_service)
):
    """Add permissions to a role."""
    return await service.add_permissions_to_role(role_id=role_id, permission_ids=permissions.permission_ids)

@router.delete("/{role_id}/permissions", response_model=RoleResponse)
async def remove_permissions(
    role_id: int,
    permissions: RolePermissionUpdate,
    service: RoleService = Depends(get_role_service)
):
    """Remove permissions from a role."""
    return await service.remove_permissions_from_role(role_id=role_id, permission_ids=permissions.permission_ids)

