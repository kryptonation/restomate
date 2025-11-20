# app/modules/roles/schemas.py

from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class PermissionBase(BaseModel):
    """Base schema for permissions."""
    name: str = Field(..., max_legth=100)
    resource: str = Field(..., max_length=100)
    action: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=255)


class PermissionCreate(PermissionBase):
    """Schema for creating a new permission."""
    pass


class PermissionResponse(PermissionBase):
    """Schema for permission response."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    """Base schema for roles."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    is_active: bool = True


class RoleCreate(RoleBase):
    """Schema for creating a new role."""
    permission_ids: List[int] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    """Schema for updating an existing role."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class RoleResponse(RoleBase):
    """Schema for role response."""
    id: int
    is_system: bool
    permissions: List[PermissionResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RolePermissionUpdate(BaseModel):
    """Schema for updating role permissions."""
    permission_ids: List[int]

