# Database Seeder System - Complete Guide

## Overview

A production-ready database seeding system with:
- ✅ Automated seeding for all modules
- ✅ S3-based backup and restore
- ✅ RBAC-protected API endpoints
- ✅ CLI interface for development
- ✅ Execution tracking and history
- ✅ Support for reset and rollback
- ✅ Comprehensive error handling

## Features

### 1. Multi-Seeder Architecture
- **PermissionsSeeder**: Seeds all system permissions
- **RolesSeeder**: Creates roles with assigned permissions
- **SuperAdminSeeder**: Creates initial superadmin user
- **SMSTemplatesSeeder**: Seeds SMS notification templates
- **MasterSeeder**: Orchestrates all seeders in correct order

### 2. Backup & Restore
- Automatic S3 backups before seeding
- Compressed JSON format (gzip)
- Point-in-time restore capability
- Metadata tracking for all backups

### 3. Execution Tracking
- Complete audit trail of all seeder runs
- Status tracking (pending, running, completed, failed)
- Statistics (records created/updated/deleted)
- Error logging with tracebacks

### 4. RBAC Protection
- All seeder endpoints require authentication
- Permission-based access control
- Only superadmin/admin can execute seeders

## Installation

### 1. Create Module Structure

```bash
mkdir -p app/modules/seeder
touch app/modules/seeder/__init__.py
```

### 2. Add Files

Place all seeder module files in `app/modules/seeder/`:
- `models.py` - Database models
- `base.py` - Base seeder classes
- `seeders.py` - Seeder implementations
- `repository.py` - Data access layer
- `services.py` - Business logic
- `schemas.py` - Pydantic schemas
- `router.py` - API endpoints
- `exceptions.py` - Custom exceptions

### 3. Run Migration

```bash
# Import seeder models in alembic/env.py
from app.modules.seeder.models import *

# Create and apply migration
alembic revision --autogenerate -m "Add seeder module"
alembic upgrade head
```

### 4. Configure Environment

Add to `.env`:

```bash
# Existing S3 configuration is sufficient
# No additional configuration needed
```

## Usage

### CLI Usage (Development)

#### 1. Make CLI Script Executable

```bash
chmod +x scripts/seed.py
```

#### 2. Run Seeders

```bash
# Run all seeders (with automatic backup)
python scripts/seed.py

# Reset database and reseed
python scripts/seed.py --reset

# Restore from latest backup
python scripts/seed.py --restore

# Restore from specific backup
python scripts/seed.py --restore --key "database-backups/20250115_120000_execution_123.json.gz"
```

### API Usage (Production)

#### 1. Login as Superadmin

```bash
# Login (use credentials from SuperAdminSeeder)
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@foodfleet.com",
    "password": "SuperAdmin@123"
  }'

# Save access_token from response
TOKEN="your-access-token"
```

#### 2. Execute Seeders

```bash
curl -X POST "http://localhost:8000/api/v1/seeders/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "create_backup": true
  }'
```

**Response:**
```json
{
  "success": true,
  "backup_created": true,
  "backup_s3_key": "database-backups/20250115_120000_execution_5.json.gz",
  "results": {
    "seeders": {
      "PermissionsSeeder": {
        "status": "completed",
        "created": 24,
        "updated": 0,
        "deleted": 0
      },
      "RolesSeeder": {
        "status": "completed",
        "created": 5,
        "updated": 0,
        "deleted": 0
      },
      "SuperAdminSeeder": {
        "status": "completed",
        "created": 1,
        "updated": 0,
        "deleted": 0
      },
      "SMSTemplatesSeeder": {
        "status": "completed",
        "created": 4,
        "updated": 0,
        "deleted": 0
      }
    },
    "total": {
      "created": 34,
      "updated": 0,
      "deleted": 0
    }
  }
}
```

#### 3. Reset Database

```bash
curl -X POST "http://localhost:8000/api/v1/seeders/reset" \
  -H "Authorization: Bearer $TOKEN"
```

#### 4. Restore from Backup

```bash
# Restore from latest backup
curl -X POST "http://localhost:8000/api/v1/seeders/restore" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# Restore from specific backup
curl -X POST "http://localhost:8000/api/v1/seeders/restore" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_key": "database-backups/20250115_120000_execution_5.json.gz"
  }'

# Restore from execution ID
curl -X POST "http://localhost:8000/api/v1/seeders/restore" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": 5
  }'
```

#### 5. View Execution History

```bash
curl -X GET "http://localhost:8000/api/v1/seeders/?skip=0&limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

#### 6. Get Specific Execution

```bash
curl -X GET "http://localhost:8000/api/v1/seeders/5" \
  -H "Authorization: Bearer $TOKEN"
```

## Default Credentials

After seeding, login with:

```
Email: admin@foodfleet.com
Password: SuperAdmin@123
```

**IMPORTANT:** Change this password immediately in production!

## Seeded Data

### Permissions (24 total)

**User Management:**
- users:create, users:read, users:update, users:delete

**Role Management:**
- roles:create, roles:read, roles:update, roles:delete

**Permission Management:**
- permissions:read

**File Management:**
- files:create, files:read, files:update, files:delete

**Seeder Management:**
- seeders:execute, seeders:read

**Restaurant Management (Future):**
- restaurants:create, restaurants:read, restaurants:update, restaurants:delete

**Menu Management (Future):**
- menus:create, menus:read, menus:update, menus:delete

### Roles (5 total)

1. **superadmin** (System Role)
   - All permissions
   - Cannot be modified or deleted

2. **admin** (System Role)
   - User management (read, create, update)
   - Role viewing
   - File management
   - Restaurant management
   - Menu management

3. **restaurant_owner**
   - Restaurant management (read, update)
   - Full menu management
   - File management (create, read, update)

4. **restaurant_manager**
   - Restaurant viewing
   - Menu management (read, update)
   - File management (create, read)

5. **customer**
   - Restaurant viewing
   - Menu viewing

### Users

1. **Super Administrator**
   - Email: admin@foodfleet.com
   - Username: superadmin
   - Role: superadmin
   - Status: Active, Verified

### SMS Templates (4 total)

1. **2fa_code** - Two-factor authentication
2. **password_reset** - Password reset notification
3. **order_confirmation** - Order confirmation (future)
4. **order_delivered** - Delivery notification (future)

## Creating Custom Seeders

### Step 1: Create Seeder Class

```python
# app/modules/seeder/seeders.py

from app.modules.seeder.base import BaseSeeder

class RestaurantsSeeder(BaseSeeder):
    """Seed initial restaurants."""
    
    async def seed(self) -> Dict[str, Any]:
        """Seed restaurants."""
        stats = {'created': 0, 'updated': 0, 'deleted': 0}
        
        restaurants_data = [
            {
                'name': 'Pizza Palace',
                'description': 'Best pizza in town',
                'address': '123 Main St'
            },
            # Add more restaurants...
        ]
        
        for restaurant_data in restaurants_data:
            restaurant, created = await self.get_or_create(
                Restaurant,
                filters={'name': restaurant_data['name']},
                defaults={
                    'description': restaurant_data['description'],
                    'address': restaurant_data['address']
                }
            )
            
            if created:
                stats['created'] += 1
        
        await self.db.flush()
        return stats
```

### Step 2: Add to MasterSeeder

```python
# app/modules/seeder/seeders.py

class MasterSeeder:
    def __init__(self, db):
        self.db = db
        self.seeders = [
            PermissionsSeeder,
            RolesSeeder,
            SuperAdminSeeder,
            SMSTemplatesSeeder,
            RestaurantsSeeder,  # Add your seeder here
        ]
```

### Step 3: Run Migration

```bash
# Import new models in alembic/env.py
from app.modules.restaurants.models import Restaurant

# Create migration
alembic revision --autogenerate -m "Add restaurants"
alembic upgrade head
```

### Step 4: Execute

```bash
python scripts/seed.py
```

## Backup Format

Backups are stored as compressed JSON files in S3:

**S3 Key Format:**
```
database-backups/{timestamp}_execution_{id}.json.gz
```

**Example:**
```
database-backups/20250115_120000_execution_5.json.gz
```

**Backup Structure:**
```json
{
  "users": [
    {
      "id": 1,
      "email": "admin@foodfleet.com",
      "username": "superadmin",
      ...
    }
  ],
  "roles": [...],
  "permissions": [...],
  ...
}
```

## S3 Configuration

Backups use existing S3 configuration from `app/config.py`:

```python
# Required settings
S3_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

Backups are stored in the `database-backups/` folder within your S3 bucket.

## RBAC Implementation

### Protected Endpoints

All seeder endpoints require authentication and specific permissions:

| Endpoint | Permission Required |
|----------|-------------------|
| POST /seeders/execute | seeders:execute |
| POST /seeders/reset | seeders:execute |
| POST /seeders/restore | seeders:execute |
| GET /seeders/ | seeders:read |
| GET /seeders/{id} | seeders:read |

### Updated Module Protections

**Users Module:**
- List users: users:read
- Get user: users:read
- Delete user: users:delete

**Roles Module:**
- Create role: roles:create
- List roles: roles:read
- Get role: roles:read
- Update role: roles:update
- Delete role: roles:delete
- Add/Remove permissions: roles:update

**Files Module:**
- Upload file: files:create
- List files: files:read
- Get file: files:read
- Get presigned URL: files:read
- Get metadata: files:read
- Download: files:read
- Delete: files:delete
- Update metadata: files:update
- Copy: files:create

## Error Handling

### Seeder Failures

If a seeder fails:
1. Database transaction is rolled back
2. Error is logged with full traceback
3. Execution record is updated with error details
4. HTTP 500 error is returned

### Backup Failures

If backup creation fails:
1. Error is logged
2. Seeding continues without backup
3. Warning is returned in response

### Restore Failures

If restore fails:
1. Database transaction is rolled back
2. Original data remains intact
3. Error is logged with details
4. HTTP 500 error is returned

## Monitoring

### View Seeder History

```bash
curl -X GET "http://localhost:8000/api/v1/seeders/" \
  -H "Authorization: Bearer $TOKEN"
```

### Check Execution Status

```bash
curl -X GET "http://localhost:8000/api/v1/seeders/5" \
  -H "Authorization: Bearer $TOKEN"
```

### CloudWatch Integration

All seeder operations are logged to CloudWatch (if configured):

**Log Events:**
- `seeder_started`
- `seeder_completed`
- `seeder_failed`
- `backup_started`
- `backup_completed`
- `backup_failed`
- `restore_started`
- `restore_completed`
- `restore_failed`

## Best Practices

### 1. Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/new-module

# 2. Create models and migrations
alembic revision --autogenerate -m "Add new module"
alembic upgrade head

# 3. Create seeder
# Add seeder class to seeders.py

# 4. Test seeder
python scripts/seed.py --reset

# 5. Verify data
psql -U user -d foodfleet -c "SELECT * FROM your_table"
```

### 2. Production Deployment

```bash
# 1. Backup current database
curl -X POST "$API_URL/api/v1/seeders/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"create_backup": true}'

# 2. Apply migrations
alembic upgrade head

# 3. Run seeders
curl -X POST "$API_URL/api/v1/seeders/execute" \
  -H "Authorization: Bearer $TOKEN"

# 4. Verify seeding
curl -X GET "$API_URL/api/v1/seeders/?limit=1" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Disaster Recovery

```bash
# 1. Identify backup to restore
curl -X GET "$API_URL/api/v1/seeders/" \
  -H "Authorization: Bearer $TOKEN"

# 2. Restore from backup
curl -X POST "$API_URL/api/v1/seeders/restore" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"execution_id": 123}'

# 3. Verify restoration
curl -X GET "$API_URL/health" \
  -H "Authorization: Bearer $TOKEN"
```

## Troubleshooting

### Issue: Seeder fails with "Permission denied"

**Solution:** Ensure you're logged in with superadmin or admin role:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -d '{"email": "admin@foodfleet.com", "password": "SuperAdmin@123"}'
```

### Issue: S3 upload fails

**Solution:** Check S3 configuration and IAM permissions:

```bash
# Verify S3 bucket exists
aws s3 ls s3://your-bucket-name/database-backups/

# Test S3 write permissions
aws s3 cp test.txt s3://your-bucket-name/database-backups/test.txt
```

### Issue: "Role not found" during seeding

**Solution:** Ensure seeders run in correct order. RolesSeeder must run before SuperAdminSeeder.

### Issue: Duplicate key errors

**Solution:** Seeders use `get_or_create` pattern to handle duplicates. If errors persist, reset database:

```bash
python scripts/seed.py --reset
```

## Security Considerations

### 1. Change Default Password

```bash
curl -X POST "http://localhost:8000/api/v1/auth/password/change" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "current_password": "SuperAdmin@123",
    "new_password": "NewSecurePassword123!"
  }'
```

### 2. Restrict Seeder Access

Only superadmin and admin roles have seeder permissions. Never grant these to regular users.

### 3. Secure S3 Backups

- Enable S3 bucket encryption
- Enable versioning
- Configure lifecycle policies
- Restrict IAM permissions

### 4. Audit Logging

All seeder executions are logged with:
- User ID
- Timestamp
- Actions performed
- Results

## Next Steps

1. ✅ Run initial seeding
2. ✅ Change default superadmin password
3. ✅ Verify RBAC permissions
4. ⬜ Create restaurant module seeders
5. ⬜ Create menu module seeders
6. ⬜ Set up automated backups
7. ⬜ Configure CloudWatch alarms
8. ⬜ Implement CI/CD seeding pipeline

## Support

For issues or questions:
- Check execution logs: `GET /api/v1/seeders/`
- Review CloudWatch logs
- Check S3 backups: `aws s3 ls s3://bucket/database-backups/`