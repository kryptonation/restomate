# app/modules/roles/models.py

from typing import List, Optional

from sqlalchemy import String, Boolean, JSON, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel


# Association table for role-permission relationship
role_permissions = Table(
    'role_permissions',
    BaseModel.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
)


class Permission(BaseModel):
    """Permission model for RBAC"""
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary=role_permissions, back_populates="permissions"
    )

    def __repr__(self) -> str:
        return f"<Permission {self.name}: {self.resource}:{self.action}>"
    

class Role(BaseModel):
    """Role model for RBAC."""
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    permissions: Mapped[List[Permission]] = relationship(
        "Permission", secondary=role_permissions, back_populates="roles",
        lazy="selectin"
    )
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="role"
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
    

