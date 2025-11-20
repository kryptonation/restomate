# Food fleet Modular Application - Architecture & Design Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Design Patterns](#design-patterns)
3. [Module Structure](#module-structure)
4. [Database Design](#database-design)
5. [Security Architecture](#security-architecture)
6. [Communication Layer](#communication-layer)
7. [Logging & Monitoring](#logging--monitoring)
8. [Error Handling](#error-handling)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
│                  (Web, Mobile, Desktop)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTPS/REST
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Middleware  │  │   Routers    │  │ Dependencies │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         ▼                  ▼                  ▼              │
│  ┌──────────────────────────────────────────────────┐      │
│  │              Service Layer                        │      │
│  │  (Business Logic & Orchestration)                 │      │
│  └──────────────────┬───────────────────────────────┘      │
│                     │                                        │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────┐      │
│  │           Repository Layer                        │      │
│  │         (Data Access & ORM)                       │      │
│  └──────────────────┬───────────────────────────────┘      │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬──────────────┐
        ▼            ▼            ▼              ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐
   │PostgreSQL│  │  Redis  │  │ AWS SES │  │ AWS SNS  │
   └─────────┘  └─────────┘  └─────────┘  └──────────┘
```

### Layered Architecture

#### 1. **Presentation Layer** (Routers)
- **Purpose**: Handle HTTP requests/responses
- **Responsibilities**:
  - Request validation (Pydantic schemas)
  - Response serialization
  - Route definitions
  - Dependency injection
- **Example**: `app/modules/users/router.py`

#### 2. **Business Logic Layer** (Services)
- **Purpose**: Implement business rules and orchestration
- **Responsibilities**:
  - Business logic execution
  - Transaction management
  - Cross-cutting concerns
  - Service orchestration
- **Example**: `app/modules/users/services.py`

#### 3. **Data Access Layer** (Repositories)
- **Purpose**: Abstract database operations
- **Responsibilities**:
  - CRUD operations
  - Query building
  - Data mapping
  - Database transactions
- **Example**: `app/modules/users/repository.py`

#### 4. **Domain Layer** (Models)
- **Purpose**: Define data structures
- **Responsibilities**:
  - SQLAlchemy ORM models
  - Relationships
  - Constraints
  - Domain logic
- **Example**: `app/modules/users/models.py`

---

## Design Patterns

### 1. Repository Pattern

**Purpose**: Separate data access logic from business logic.

```python
class UserRepository:
    """Encapsulates all database operations for User entity."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
```

**Benefits**:
- Centralized data access logic
- Easy to mock for testing
- Database-agnostic business logic
- Single source of truth for queries

### 2. Service Layer Pattern

**Purpose**: Encapsulate business logic and orchestrate operations.

```python
class UserService:
    """Orchestrates user-related business operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_service = RoleService(db)
    
    async def create_user(self, email: str, password: str, ...) -> User:
        # Business logic: validation, password hashing, etc.
        # Orchestration: coordinate multiple repositories
        # Transaction management
        pass
```

**Benefits**:
- Clear separation of concerns
- Reusable business logic
- Transaction boundaries
- Easy to test

### 3. Dependency Injection

**Purpose**: Inject dependencies through FastAPI's dependency system.

```python
def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """DI factory for UserService."""
    return UserService(db)

@router.post("/users")
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    return await service.create_user(...)
```

**Benefits**:
- Loose coupling
- Easy testing with mocks
- Clear dependencies
- Automatic resource management

### 4. Factory Pattern

**Purpose**: Create complex objects.

```python
# Service Factory
def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)

# Email Service Singleton
email_service = EmailService()  # Created once, reused

# OTP Service Factory
otp_service = OTPService()
```

### 5. Strategy Pattern

**Purpose**: Encapsulate algorithms (email templates, SMS strategies).

```python
# Email templates as strategies
await email_service.send_templated_email(
    to_emails=[user.email],
    subject="Welcome",
    template_path="users/templates/welcome_email.html",
    context={"username": user.username}
)
```

### 6. Decorator Pattern

**Purpose**: Add functionality without modifying code.

```python
# Permission decorator
async def require_permission(resource: str, action: str):
    """Decorator to check permissions."""
    def decorator(user = Depends(get_current_user)):
        # Check permission logic
        pass
    return decorator

@router.delete("/users/{user_id}")
async def delete_user(
    user = Depends(require_permission("users", "delete"))
):
    pass
```

---

## Module Structure

### Standard Module Layout

```
modules/
└── {module_name}/
    ├── __init__.py          # Module exports
    ├── models.py            # SQLAlchemy models
    ├── schemas.py           # Pydantic schemas (DTOs)
    ├── repository.py        # Data access layer
    ├── services.py          # Business logic layer
    ├── router.py            # API endpoints
    ├── exceptions.py        # Custom exceptions
    ├── utils.py             # Helper functions
    ├── tasks.py             # Async tasks (Celery)
    ├── tests.py             # Unit tests
    └── templates/           # Email/SMS templates
```

### File Responsibilities

#### **models.py**
- SQLAlchemy ORM models
- Database table definitions
- Relationships
- Enums
- Model-level validation

```python
class User(BaseModel):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    
    # Relationships
    role: Mapped[Optional["Role"]] = relationship("Role")
```

#### **schemas.py**
- Pydantic models (DTOs)
- Request validation
- Response serialization
- Data transfer objects

```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    
class UserResponse(BaseModel):
    id: int
    email: str
    model_config = ConfigDict(from_attributes=True)
```

#### **repository.py**
- Database queries
- CRUD operations
- Complex queries
- No business logic

```python
class UserRepository:
    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
```

#### **services.py**
- Business logic
- Orchestration
- Transaction management
- External service calls

```python
class UserService:
    async def register_user(self, data: UserCreate) -> User:
        # Validation
        # Password hashing
        # User creation
        # Send welcome email
        # Return user
        pass
```

#### **router.py**
- API endpoints
- Route definitions
- Request/response handling
- Dependency injection

```python
@router.post("/users", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    return await service.create_user(data)
```

#### **exceptions.py**
- Custom exceptions
- Domain-specific errors
- Error messages

```python
class UserNotFoundException(NotFoundException):
    def __init__(self, user_id: int):
        super().__init__(
            message=f"User {user_id} not found",
            details={"user_id": user_id}
        )
```

---

## Database Design

### SQLAlchemy 2.x Approach

#### **Async Engine Configuration**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@host/db",
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

#### **Declarative Base with Mapped Types**

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    # Type-safe columns with Mapped
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Optional columns
    phone: Mapped[Optional[str]] = mapped_column(String(20))
```

#### **Relationships**

```python
# One-to-Many
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

# Many-to-Many
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', ForeignKey('permissions.id'), primary_key=True)
)

class Role(Base):
    __tablename__ = "roles"
    
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )
```

#### **Async Query Patterns**

```python
# Select
async def get_user(db: AsyncSession, user_id: int):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# Join with eager loading
stmt = (
    select(User)
    .options(selectinload(User.role))
    .where(User.id == user_id)
)

# Filter and pagination
stmt = (
    select(User)
    .where(User.is_active == True)
    .offset(skip)
    .limit(limit)
)

# Insert
user = User(email="test@example.com")
db.add(user)
await db.flush()  # Get ID without committing
await db.refresh(user)

# Update
stmt = select(User).where(User.id == user_id)
result = await db.execute(stmt)
user = result.scalar_one()
user.email = "new@example.com"
await db.flush()

# Delete
await db.delete(user)
await db.flush()
```

---

## Security Architecture

### 1. Authentication Flow

```
User Login Request
    ↓
Validate Credentials
    ↓
Check Account Status (active, locked, etc.)
    ↓
Check 2FA (if enabled)
    ↓
Generate JWT Access Token (30 min)
    ↓
Generate JWT Refresh Token (7 days)
    ↓
Store Refresh Token in Database
    ↓
Return Tokens to Client
```

### 2. JWT Token Structure

**Access Token**:
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "type": "access",
  "exp": 1234567890
}
```

**Refresh Token**:
```json
{
  "sub": "user_id",
  "type": "refresh",
  "exp": 1234567890
}
```

### 3. Password Security

- **Hashing**: bcrypt via passlib
- **Validation**: 
  - Minimum 8 characters
  - Uppercase, lowercase, digit, special char
  - Not in common passwords list
- **Reset Flow**: Time-limited tokens (15 min)
- **History**: Prevent password reuse

### 4. Two-Factor Authentication

```
Setup 2FA
    ↓
Generate TOTP Secret
    ↓
Create QR Code
    ↓
Generate Backup Codes (10)
    ↓
Store Secret (not enabled yet)
    ↓
User Scans QR Code
    ↓
Verify TOTP Code
    ↓
Enable 2FA
    ↓
Return Backup Codes
```

**Technology**: PyOTP (TOTP - Time-based One-Time Password)
**Window**: 30 seconds
**Backup Codes**: 10 single-use codes

### 5. RBAC Implementation

```
User → Role → Permissions → Resources:Actions

Example:
User "john_doe" 
  → Role "Editor"
    → Permissions ["articles:create", "articles:edit", "articles:read"]
```

**Permission Check**:
```python
async def require_permission(resource: str, action: str):
    # Get user's role
    # Check if role has permission for resource:action
    # Allow or deny access
```

---

## Communication Layer

### Email Service (AWS SES)

**Architecture**:
```python
EmailService (Singleton)
    ├── boto3 SES client
    ├── Jinja2 template engine
    └── Methods:
        ├── send_email()
        ├── send_templated_email()
        └── render_template()
```

**Usage Pattern**:
```python
await email_service.send_templated_email(
    to_emails=["user@example.com"],
    subject="Welcome",
    template_path="users/templates/welcome_email.html",
    context={"username": "john_doe"},
    attachments=[{"filename": "doc.pdf", "content": pdf_bytes}]
)
```

**Features**:
- HTML and plain text support
- Template rendering with Jinja2
- Attachments support
- CC and BCC
- Reply-to headers

### SMS Service (AWS SNS)

**Architecture**:
```python
SMSService (Singleton)
    ├── boto3 SNS client
    ├── Database template lookup
    └── Methods:
        ├── send_sms()
        └── send_templated_sms()
```

**Template Storage**:
```sql
CREATE TABLE sms_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    content TEXT,
    is_active BOOLEAN
);

-- Example template
INSERT INTO sms_templates (name, content) VALUES
('2fa_code', 'Your verification code is: {{code}}');
```

**Usage**:
```python
await sms_service.send_templated_sms(
    db=db,
    phone_number="+1234567890",
    template_name="2fa_code",
    variables={"code": "123456"}
)
```

---

## Logging & Monitoring

### Structured Logging with Structlog

**Configuration**:
```python
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()  # Production
        # structlog.dev.ConsoleRenderer()  # Development
    ]
)
```

**Log Output (Production)**:
```json
{
  "event": "user_login",
  "level": "info",
  "timestamp": "2025-01-15T10:30:00.123456Z",
  "user_id": 123,
  "email": "user@example.com",
  "request_id": "abc-123-def-456",
  "logger": "app.modules.users.services"
}
```

**Usage Patterns**:
```python
logger.info("user_created", user_id=user.id, email=user.email)
logger.warning("failed_login_attempt", email=email, attempts=attempts)
logger.error("database_error", error=str(e), query=query)
```

### Request Tracking

**Request ID Middleware**:
- Generates UUID for each request
- Adds to context variables
- Returns in response headers
- Included in all logs

**Benefits**:
- Trace requests across services
- Debug specific requests
- Correlate logs

---

## Error Handling

### Exception Hierarchy

```
BaseAppException (500)
    ├── DatabaseException (500)
    ├── NotFoundException (404)
    │   ├── UserNotFoundException
    │   ├── RoleNotFoundException
    │   └── PermissionNotFoundException
    ├── UnauthorizedException (401)
    │   ├── InvalidCredentialsException
    │   ├── AccountLockedException
    │   ├── Invalid2FACodeException
    │   └── InvalidTokenException
    ├── ForbiddenException (403)
    │   └── InsufficientPermissionsException
    └── ValidationException (422)
        ├── WeakPasswordException
        ├── PasswordReusedException
        └── UserAlreadyExistsException
```

### Global Exception Handlers

```python
@app.exception_handler(BaseAppException)
async def app_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details}
    )
```

### Usage in Services

```python
# Raise custom exception
if not user:
    raise UserNotFoundException(user_id=user_id)

# Exception with details
raise ValidationException(
    message="Invalid data",
    details={"field": "email", "error": "already exists"}
)
```

This architecture provides a solid foundation for building scalable, maintainable FastAPI applications with clear separation of concerns and industry-standard patterns.