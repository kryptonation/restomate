# app/modules/seeder/seeders.py

from typing import Dict, Any, Optional

from app.modules.seeder.base import BaseSeeder
from app.modules.roles.models import Role, Permission
from app.modules.users.models import User, SMSTemplate
from app.core.security import get_password_hash
from app.core.logging import get_logger

logger = get_logger(__name__)


class PermissionSeeder(BaseSeeder):
    """Seed initial permissions."""

    async def seed(self) -> Dict[str, Any]:
        """Seed permissions for all modules."""
        stats = {"created": 0, "updated": 0, "deleted": 0}

        # Define all permissions
        permissions_data = [
            # User management
            {'name': 'users:create', 'resource': 'users', 'action': 'create', 'description': 'Create users'},
            {'name': 'users:read', 'resource': 'users', 'action': 'read', 'description': 'View users'},
            {'name': 'users:update', 'resource': 'users', 'action': 'update', 'description': 'Update users'},
            {'name': 'users:delete', 'resource': 'users', 'action': 'delete', 'description': 'Delete users'},
            
            # Role management
            {'name': 'roles:create', 'resource': 'roles', 'action': 'create', 'description': 'Create roles'},
            {'name': 'roles:read', 'resource': 'roles', 'action': 'read', 'description': 'View roles'},
            {'name': 'roles:update', 'resource': 'roles', 'action': 'update', 'description': 'Update roles'},
            {'name': 'roles:delete', 'resource': 'roles', 'action': 'delete', 'description': 'Delete roles'},
            
            # Permission management
            {'name': 'permissions:read', 'resource': 'permissions', 'action': 'read', 'description': 'View permissions'},
            
            # File management
            {'name': 'files:create', 'resource': 'files', 'action': 'create', 'description': 'Upload files'},
            {'name': 'files:read', 'resource': 'files', 'action': 'read', 'description': 'View files'},
            {'name': 'files:update', 'resource': 'files', 'action': 'update', 'description': 'Update files'},
            {'name': 'files:delete', 'resource': 'files', 'action': 'delete', 'description': 'Delete files'},
            
            # Seeder management
            {'name': 'seeders:execute', 'resource': 'seeders', 'action': 'execute', 'description': 'Execute seeders'},
            {'name': 'seeders:read', 'resource': 'seeders', 'action': 'read', 'description': 'View seeder history'},
            
            # Restaurant management (for future)
            {'name': 'restaurants:create', 'resource': 'restaurants', 'action': 'create', 'description': 'Create restaurants'},
            {'name': 'restaurants:read', 'resource': 'restaurants', 'action': 'read', 'description': 'View restaurants'},
            {'name': 'restaurants:update', 'resource': 'restaurants', 'action': 'update', 'description': 'Update restaurants'},
            {'name': 'restaurants:delete', 'resource': 'restaurants', 'action': 'delete', 'description': 'Delete restaurants'},
            
            # Menu management (for future)
            {'name': 'menus:create', 'resource': 'menus', 'action': 'create', 'description': 'Create menus'},
            {'name': 'menus:read', 'resource': 'menus', 'action': 'read', 'description': 'View menus'},
            {'name': 'menus:update', 'resource': 'menus', 'action': 'update', 'description': 'Update menus'},
            {'name': 'menus:delete', 'resource': 'menus', 'action': 'delete', 'description': 'Delete menus'},
        ]

        for perm_data in permissions_data:
            permission, created = await self.get_or_create(
                Permission,
                filters={"name": perm_data["resource"]},
                defaults={
                    "resource": perm_data["resource"],
                    "action": perm_data["action"],
                    "description": perm_data["description"]
                }
            )

            if created:
                stats["created"] += 1
                logger.info("permission_created", name=perm_data["name"])

        await self.db.flush()
        return stats
    
    
class RoleSeeder(BaseSeeder):
    """Seed initial roles with permissions."""

    async def seed(self) -> Dict[str, Any]:
        """Seed system roles."""
        stats = {"created": 0, "updated": 0, "deleted": 0}

        # Get all permissions
        from sqlalchemy import select
        stmt = select(Permission)
        result = await self.db.execute(stmt)
        all_permissions = list(result.scalars().all())

        # Create permission lookup
        perm_lookup = {p.name: p for p in all_permissions}

        # Define roles with their permissions
        roles_data = [
            {
                'name': 'superadmin',
                'description': 'Super Administrator with full system access',
                'is_system': True,
                'permissions': [p.name for p in all_permissions]  # All permissions
            },
            {
                'name': 'admin',
                'description': 'Administrator with limited system access',
                'is_system': True,
                'permissions': [
                    'users:read', 'users:create', 'users:update',
                    'roles:read',
                    'files:create', 'files:read', 'files:update', 'files:delete',
                    'restaurants:create', 'restaurants:read', 'restaurants:update', 'restaurants:delete',
                    'menus:create', 'menus:read', 'menus:update', 'menus:delete',
                ]
            },
            {
                'name': 'restaurant_owner',
                'description': 'Restaurant owner with restaurant management access',
                'is_system': False,
                'permissions': [
                    'restaurants:read', 'restaurants:update',
                    'menus:create', 'menus:read', 'menus:update', 'menus:delete',
                    'files:create', 'files:read', 'files:update',
                ]
            },
            {
                'name': 'restaurant_manager',
                'description': 'Restaurant manager with operational access',
                'is_system': False,
                'permissions': [
                    'restaurants:read',
                    'menus:read', 'menus:update',
                    'files:create', 'files:read',
                ]
            },
            {
                'name': 'customer',
                'description': 'Customer with basic access',
                'is_system': False,
                'permissions': [
                    'restaurants:read',
                    'menus:read',
                ]
            },
        ]

        for role_data in roles_data:
            role, created = await self.get_or_create(
                Role,
                filters={"name": role_data["name"]},
                defaults={
                    "description": role_data["description"],
                    "is_system": role_data["is_system"]
                }
            )

            if created or not role.permissions:
                # Add permissions
                role.permissions = [
                    perm_lookup[perm_name]
                    for perm_name in role_data["permissions"]
                    if perm_name in perm_lookup
                ]
                stats["created"] += 1 if created else 0
                stats["updated"] += 0 if created else 1
                logger.info("role_created", name=role_data["name"], permissions=len(role.permissions))

        await self.db.flush()
        return stats
    

class SuperAdminSeeder(BaseSeeder):
    """Seed initial superadmin user."""

    async def seed(self) -> Dict[str, Any]:
        """Seed superadmin user."""
        stats = {"created": 0, "updated": 0, "deleted": 0}

        # Get superadmin role
        from sqlalchemy import select
        stmt = select(Role).where(Role.name == "superadmin")
        result = await self.db.execute(stmt)
        superadmin_role = result.scalar_one_or_none()

        if not superadmin_role:
            logger.error("superadmin_role_not_found")
            raise ValueError("superadmin role not found. Run RoleSeeder first.")
        
        # Create superadmin user
        user, created = await self.get_or_create(
            User,
            filters={"email": "admin@foodfleet.com"},
            defaults={
                "username": "superadmin",
                "password_hash": get_password_hash("SuperAdmin@123"),
                "first_name": "Super",
                "last_name": "Admin",
                "is_active": True,
                "is_verified": True,
                "is_superuser": True,
                "role_id": superadmin_role.id
            }
        )

        if created:
            stats["created"] += 1
            logger.info("superadmin_created", email="admin@foodfleet.com")

        await self.db.flush()
        return stats
    

class SMSTemplateSeeder(BaseSeeder):
    """Seed SMS templates."""

    async def seed(self) -> Dict[str, Any]:
        """Seed SMS templates."""
        stats = {"created": 0, "updated": 0, "deleted": 0}

        templates_data = [
            {
                'name': '2fa_code',
                'content': 'Your Food Fleet verification code is: {{code}}. Valid for 5 minutes.',
                'description': '2FA verification code'
            },
            {
                'name': 'password_reset',
                'content': 'Your Food Fleet password reset code is: {{code}}. Valid for 15 minutes.',
                'description': 'Password reset code'
            },
            {
                'name': 'order_confirmation',
                'content': 'Your order #{{order_id}} has been confirmed. Estimated delivery: {{delivery_time}}.',
                'description': 'Order confirmation notification'
            },
            {
                'name': 'order_delivered',
                'content': 'Your order #{{order_id}} has been delivered. Enjoy your meal!',
                'description': 'Order delivery notification'
            },
        ]

        for template_data in templates_data:
            template, created = await self.get_or_create(
                SMSTemplate,
                filters={"name": template_data["name"]},
                defaults={
                    "content": template_data["content"],
                    "description": template_data["description"]
                }
            )

            if created:
                stats["created"] += 1
                logger.info("sms_template_created", name=template_data["name"])

        await self.db.flush()
        return stats
    

class MasterSeeder:
    """Master seeder to run all seeders in order."""

    def __init__(self, db):
        self.db = db
        self.seeders = [
            PermissionSeeder,
            RoleSeeder,
            SuperAdminSeeder,
            SMSTemplateSeeder
        ]

    async def run_all(self, seeder_type=None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Run all seeders in sequence."""
        from app.modules.seeder.models import SeederType

        seeder_type = seeder_type or SeederType.INITIAL

        results = {}
        total_stats = {"created": 0, "updated": 0, "deleted": 0}

        for seeder_class in self.seeders:
            seeder = seeder_class(self.db)
            execution = await seeder.execute(
                seeder_type=seeder_type, user_id=user_id
            )

            results[seeder.name] = {
                "status": execution.status.value,
                "created": execution.records_created,
                "updated": execution.records_updated,
                "deleted": execution.records_deleted
            }

            total_stats["created"] += execution.records_created
            total_stats["updated"] += execution.records_updated
            total_stats["deleted"] += execution.records_deleted

        return {
            "seeders": results,
            "total": total_stats
        }
