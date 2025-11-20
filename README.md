# Food Fleet Super admin backend

A production-ready Food fleet application with Django-like modular architecture, featuring comprehensive user management, RBAC, 2FA, and AWS integrations.

## Features

### Core Features
- **Modular Architecture**: Django-style app structure with clear separation of concerns
- **SQLAlchemy 2.x**: Modern async database operations
- **Structured Logging**: Centralized logging with structlog
- **Dependency Injection**: Clean service layer with FastAPI dependencies

### Authentication & Security
- **JWT Authentication**: Access and refresh tokens
- **Two-Factor Authentication (2FA)**: TOTP-based with QR code generation
- **Backup Codes**: Emergency access codes for 2FA
- **Password Management**: 
  - Strong password validation
  - Password reset via email
  - Password change with verification
- **Account Security**:
  - Account lockout after failed login attempts
  - Session management
  - Logout from all devices

### Authorization
- **Role-Based Access Control (RBAC)**:
  - Dynamic roles and permissions
  - Resource-action based permissions
  - System role protection
- **Fine-grained Permissions**: Control access at resource and action level

### Communication
- **Email (AWS SES)**:
  - Template-based emails with Jinja2
  - Attachments support
  - HTML and plain text emails
- **SMS (AWS SNS)**:
  - Template-based SMS from database
  - Transactional SMS support

### Additional Features
- **Email Verification**: Verify user email addresses
- **Audit Logging**: Track all user actions
- **User Management**: Full CRUD operations
- **Request ID Tracking**: Trace requests across the system

## Project Structure

```
fastapi_project/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── database.py             # Database setup
│   ├── dependencies.py         # Global dependencies
│   │
│   ├── core/                   # Core utilities
│   │   ├── logging.py          # Structured logging setup
│   │   ├── security.py         # Security utilities
│   │   ├── exceptions.py       # Base exceptions
│   │   ├── middleware.py       # Custom middleware
│   │   └── base_models.py      # Base SQLAlchemy models
│   │
│   ├── utils/                  # Utility modules
│   │   ├── email.py            # AWS SES email service
│   │   ├── sms.py              # AWS SNS SMS service
│   │   ├── otp.py              # OTP/2FA utilities
│   │   └── password.py         # Password validation
│   │
│   └── modules/                # Application modules
│       ├── users/              # User management module
│       │   ├── models.py
│       │   ├── repository.py
│       │   ├── services.py
│       │   ├── router.py
│       │   ├── schemas.py
│       │   ├── exceptions.py
│       │   └── templates/      # Email templates
│       │
│       └── roles/              # Role & permission module
│           ├── models.py
│           ├── repository.py
│           ├── services.py
│           ├── router.py
│           ├── schemas.py
│           └── exceptions.py
│
├── tests/                      # Test files
├── alembic/                    # Database migrations
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis
- AWS Account (for SES and SNS)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd fastapi_project
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize database:
```bash
# Create PostgreSQL database
createdb your_database_name

# Run migrations
alembic upgrade head
```

6. Create initial roles and permissions (optional):
```bash
python scripts/init_permissions.py
```

## Running the Application

### Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### With Gunicorn
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Authentication Flow

### Registration
```bash
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Login
```bash
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

### Login with 2FA
```bash
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "totp_code": "123456"
}
```

### Setup 2FA
```bash
# 1. Setup (generates QR code)
POST /api/v1/auth/2fa/setup
Authorization: Bearer <access_token>

# 2. Enable (verify with TOTP code)
POST /api/v1/auth/2fa/enable
{
  "totp_code": "123456"
}
```

## RBAC Usage

### Create Role
```bash
POST /api/v1/roles/
{
  "name": "editor",
  "description": "Content editor role",
  "permission_ids": [1, 2, 3]
}
```

### Check Permission
```python
from app.dependencies import require_permission

@router.post("/articles")
async def create_article(
    user = Depends(require_permission("articles", "create"))
):
    # Only users with 'create' permission on 'articles' can access
    pass
```

## Email Templates

Email templates are located in `app/modules/users/templates/`. Available templates:
- `welcome_email.html` - Welcome new users
- `reset_password.html` - Password reset
- `verify_email.html` - Email verification
- `2fa_enabled.html` - 2FA enabled notification
- `password_changed.html` - Password change notification

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific module
pytest tests/modules/test_users.py
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Adding New Modules

1. Create module directory in `app/modules/`
2. Add required files (models, repository, services, router, etc.)
3. Register router in `app/main.py`

Example:
```python
# app/main.py
from app.modules.your_module.router import router as your_router
app.include_router(your_router, prefix=settings.API_V1_PREFIX)
```

## Security Best Practices

- Change `SECRET_KEY` in production
- Use strong passwords (enforced by validator)
- Enable 2FA for sensitive accounts
- Rotate JWT tokens regularly
- Use HTTPS in production
- Keep dependencies updated
- Review audit logs regularly

## Monitoring & Logging

All logs are structured JSON (in production) for easy parsing:
```json
{
  "event": "user_login",
  "user_id": 123,
  "email": "user@example.com",
  "timestamp": "2025-01-15T10:30:00Z",
  "request_id": "uuid-here"
}
```

## Deployment

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
Ensure all environment variables are set in your deployment environment.

## License

MIT License

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📞 Support

For issues and questions, please open an issue on GitHub.