# Food fleet Modular Application - Integration & Implementation Guide

## Table of Contents
1. [Installation & Setup](#installation--setup)
2. [Database Configuration](#database-configuration)
3. [AWS Services Setup](#aws-services-setup)
4. [Creating New Modules](#creating-new-modules)
5. [Authentication Integration](#authentication-integration)
6. [RBAC Integration](#rbac-integration)
7. [Email & SMS Integration](#email--sms-integration)
8. [Testing Guide](#testing-guide)
9. [Deployment Guide](#deployment-guide)
10. [Common Integration Patterns](#common-integration-patterns)

---

## Installation & Setup

### 1. Prerequisites

**Required Software**:
```bash
Python 3.11+
PostgreSQL 14+
Redis 6+
Git
```

**Optional**:
```bash
Docker & Docker Compose
AWS CLI (for AWS services)
```

### 2. Project Setup

#### Step 1: Clone and Create Virtual Environment

```bash
# Clone repository
git clone <your-repo-url>
cd fastapi_project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

#### Step 2: Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install specific groups
pip install fastapi uvicorn sqlalchemy alembic
pip install boto3  # For AWS services
pip install pytest pytest-asyncio  # For testing
```

#### Step 3: Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Minimum Required Configuration**:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mydb

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production

# AWS (if using SES/SNS)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
SES_SENDER_EMAIL=noreply@yourdomain.com
```

### 3. Generate Secret Key

```python
# Run this Python code to generate a secure secret key
import secrets
print(secrets.token_urlsafe(32))
```

---

## Database Configuration

### 1. PostgreSQL Setup

#### Install PostgreSQL

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS (Homebrew)**:
```bash
brew install postgresql
brew services start postgresql
```

**Windows**: Download from [postgresql.org](https://www.postgresql.org/download/windows/)

#### Create Database

```bash
# Login to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE fastapi_db;
CREATE USER fastapi_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE fastapi_db TO fastapi_user;

# Exit
\q
```

#### Update .env

```bash
DATABASE_URL=postgresql+asyncpg://fastapi_user:secure_password@localhost:5432/fastapi_db
```

### 2. Database Migration Setup

#### Initialize Alembic

```bash
# Initialize alembic (already done in project)
alembic init alembic
```

#### Configure Alembic

**Edit `alembic.ini`**:
```ini
# Remove hardcoded sqlalchemy.url
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

**Edit `alembic/env.py`**:
```python
from app.config import settings
from app.database import Base
from app.modules.users.models import *  # Import all models
from app.modules.roles.models import *

# Set target metadata
target_metadata = Base.metadata

# Set database URL from config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

#### Create Initial Migration

```bash
# Create migration
alembic revision --autogenerate -m "Initial migration"

# Review the migration file in alembic/versions/

# Apply migration
alembic upgrade head
```

### 3. Redis Setup

#### Install Redis

**Ubuntu/Debian**:
```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**macOS**:
```bash
brew install redis
brew services start redis
```

**Docker**:
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

#### Test Redis Connection

```bash
redis-cli ping
# Should return: PONG
```

---

## AWS Services Setup

### 1. AWS Account Configuration

#### Install AWS CLI

```bash
# Install
pip install awscli

# Configure
aws configure
# Enter your Access Key ID
# Enter your Secret Access Key
# Enter default region (e.g., us-east-1)
# Enter default output format (json)
```

### 2. Amazon SES Setup

#### Step 1: Verify Email Address

**Via AWS Console**:
1. Go to Amazon SES Console
2. Navigate to "Verified identities"
3. Click "Create identity"
4. Choose "Email address"
5. Enter your sender email
6. Click verification link in email

**Via AWS CLI**:
```bash
aws ses verify-email-identity --email-address noreply@yourdomain.com
```

#### Step 2: Move Out of Sandbox (Production)

For production, request production access:
1. Go to SES Console
2. Click "Account dashboard"
3. Click "Request production access"
4. Fill out the form

#### Step 3: Configure in .env

```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
SES_SENDER_EMAIL=noreply@yourdomain.com
SES_SENDER_NAME=Your App Name
```

#### Step 4: Test Email Sending

```python
# Create test script: test_email.py
import asyncio
from app.utils.email import email_service

async def test_email():
    result = await email_service.send_email(
        to_emails=["recipient@example.com"],
        subject="Test Email",
        body_html="<h1>Test Email</h1>",
        body_text="Test Email"
    )
    print(f"Email sent: {result}")

asyncio.run(test_email())
```

```bash
python test_email.py
```

### 3. Amazon SNS Setup

#### Step 1: Enable SMS in SNS

```bash
# Set SMS preferences
aws sns set-sms-attributes \
    --attributes DefaultSMSType=Transactional
```

#### Step 2: Configure in .env

```bash
SNS_SMS_TYPE=Transactional
```

#### Step 3: Create SMS Templates

```python
# Run this script to create initial SMS templates
from app.database import AsyncSessionLocal
from app.modules.users.models import SMSTemplate

async def create_templates():
    async with AsyncSessionLocal() as db:
        templates = [
            SMSTemplate(
                name="2fa_code",
                content="Your verification code is: {{code}}",
                description="2FA verification code"
            ),
            SMSTemplate(
                name="password_reset",
                content="Your password reset code is: {{code}}. Valid for 15 minutes.",
                description="Password reset code"
            )
        ]
        db.add_all(templates)
        await db.commit()

import asyncio
asyncio.run(create_templates())
```

#### Step 4: Test SMS Sending

```python
# test_sms.py
import asyncio
from app.utils.sms import sms_service

async def test_sms():
    result = await sms_service.send_sms(
        phone_number="+1234567890",
        message="Test SMS from FastAPI"
    )
    print(f"SMS sent: {result}")

asyncio.run(test_sms())
```

---

## Creating New Modules

### Step-by-Step Guide to Create a New Module

#### Example: Creating a "Products" Module

### Step 1: Create Module Directory Structure

```bash
mkdir -p app/modules/products
cd app/modules/products

# Create files
touch __init__.py models.py schemas.py repository.py
touch services.py router.py exceptions.py utils.py tests.py
```

### Step 2: Define Models

**`app/modules/products/models.py`**:
```python
from sqlalchemy import String, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from app.core.base_models import BaseModel

class Category(BaseModel):
    """Product category model."""
    __tablename__ = "categories"
    
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    products: Mapped[list["Product"]] = relationship(
        "Product", 
        back_populates="category"
    )

class Product(BaseModel):
    """Product model."""
    __tablename__ = "products"
    
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    stock: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE")
    )
    
    category: Mapped["Category"] = relationship(
        "Category", 
        back_populates="products"
    )
```

### Step 3: Define Schemas

**`app/modules/products/schemas.py`**:
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ProductBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    category_id: int

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = None

class ProductResponse(ProductBase):
    id: int
    is_active: bool
    category: CategoryResponse
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

### Step 4: Create Repository

**`app/modules/products/repository.py`**:
```python
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.modules.products.models import Product, Category
from app.core.logging import get_logger

logger = get_logger(__name__)

class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, product_id: int) -> Optional[Product]:
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.category))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        category_id: Optional[int] = None
    ) -> List[Product]:
        stmt = select(Product).options(selectinload(Product.category))
        
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create(self, product: Product) -> Product:
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        logger.info("product_created", product_id=product.id)
        return product
    
    async def update(self, product: Product) -> Product:
        await self.db.flush()
        await self.db.refresh(product)
        logger.info("product_updated", product_id=product.id)
        return product
    
    async def delete(self, product: Product) -> None:
        await self.db.delete(product)
        await self.db.flush()
        logger.info("product_deleted", product_id=product.id)
```

### Step 5: Create Service

**`app/modules/products/services.py`**:
```python
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.products.models import Product
from app.modules.products.repository import ProductRepository
from app.modules.products.schemas import ProductCreate, ProductUpdate
from app.modules.products.exceptions import ProductNotFoundException
from app.core.logging import get_logger

logger = get_logger(__name__)

class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProductRepository(db)
    
    async def get_product(self, product_id: int) -> Product:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise ProductNotFoundException(product_id)
        return product
    
    async def list_products(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[int] = None
    ) -> List[Product]:
        return await self.repo.get_all(skip, limit, category_id)
    
    async def create_product(self, data: ProductCreate) -> Product:
        product = Product(
            name=data.name,
            description=data.description,
            price=data.price,
            stock=data.stock,
            category_id=data.category_id
        )
        return await self.repo.create(product)
    
    async def update_product(
        self, 
        product_id: int, 
        data: ProductUpdate
    ) -> Product:
        product = await self.get_product(product_id)
        
        if data.name is not None:
            product.name = data.name
        if data.description is not None:
            product.description = data.description
        if data.price is not None:
            product.price = data.price
        if data.stock is not None:
            product.stock = data.stock
        if data.category_id is not None:
            product.category_id = data.category_id
        
        return await self.repo.update(product)
    
    async def delete_product(self, product_id: int) -> None:
        product = await self.get_product(product_id)
        await self.repo.delete(product)
```

### Step 6: Define Exceptions

**`app/modules/products/exceptions.py`**:
```python
from app.core.exceptions import NotFoundException

class ProductNotFoundException(NotFoundException):
    def __init__(self, product_id: int):
        super().__init__(
            message=f"Product with ID {product_id} not found",
            details={"product_id": product_id}
        )
```

### Step 7: Create Router

**`app/modules/products/router.py`**:
```python
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.modules.products.services import ProductService
from app.modules.products.schemas import (
    ProductCreate, 
    ProductUpdate, 
    ProductResponse
)
from app.dependencies import ActiveUser

router = APIRouter(prefix="/products", tags=["products"])

def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    return ProductService(db)

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    current_user: ActiveUser,
    service: ProductService = Depends(get_product_service)
):
    """Create a new product."""
    return await service.create_product(data)

@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    service: ProductService = Depends(get_product_service)
):
    """List all products."""
    return await service.list_products(skip, limit, category_id)

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service)
):
    """Get product by ID."""
    return await service.get_product(product_id)

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    current_user: ActiveUser,
    service: ProductService = Depends(get_product_service)
):
    """Update product."""
    return await service.update_product(product_id, data)

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    current_user: ActiveUser,
    service: ProductService = Depends(get_product_service)
):
    """Delete product."""
    await service.delete_product(product_id)
```

### Step 8: Register Router

**Edit `app/main.py`**:
```python
from app.modules.products.router import router as products_router

# Add to application
app.include_router(products_router, prefix=settings.API_V1_PREFIX)
```

### Step 9: Create Migration

```bash
# Import models in alembic/env.py
from app.modules.products.models import Product, Category

# Create migration
alembic revision --autogenerate -m "Add products module"

# Apply migration
alembic upgrade head
```

### Step 10: Write Tests

**`app/modules/products/tests.py`**:
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_product():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/products/",
            json={
                "name": "Test Product",
                "price": 99.99,
                "category_id": 1
            },
            headers={"Authorization": "Bearer <token>"}
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Test Product"
```

---

## Authentication Integration

### 1. Protecting Routes

#### Basic Authentication

```python
from app.dependencies import CurrentUser, ActiveUser

@router.get("/protected")
async def protected_route(current_user: CurrentUser):
    """Requires valid JWT token."""
    return {"user": current_user.email}

@router.get("/active-only")
async def active_only_route(current_user: ActiveUser):
    """Requires valid JWT token and active account."""
    return {"user": current_user.email}
```

#### With Permission Check

```python
from app.dependencies import require_permission

@router.delete("/products/{id}")
async def delete_product(
    id: int,
    user = Depends(require_permission("products", "delete"))
):
    """Requires 'delete' permission on 'products' resource."""
    # Delete product logic
    pass
```

### 2. Client-Side Integration

#### Login Flow

```python
import httpx

# Login
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/auth/login",
        json={
            "email": "user@example.com",
            "password": "SecurePass123!"
        }
    )
    
    data = response.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    
    # Store tokens securely
    # localStorage for web apps
    # Keychain for mobile apps
```

#### Making Authenticated Requests

```python
# Use access token in headers
headers = {"Authorization": f"Bearer {access_token}"}

response = await client.get(
    "http://localhost:8000/api/v1/users/me",
    headers=headers
)
```

#### Refresh Token Flow

```python
# When access token expires
response = await client.post(
    "http://localhost:8000/api/v1/auth/refresh",
    json={"refresh_token": refresh_token}
)

new_access_token = response.json()["access_token"]
```

### 3. Frontend Integration Examples

#### JavaScript/TypeScript

```typescript
// auth.service.ts
class AuthService {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  async login(email: string, password: string) {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email, password})
    });
    
    const data = await response.json();
    this.accessToken = data.access_token;
    this.refreshToken = data.refresh_token;
    
    localStorage.setItem('access_token', this.accessToken);
    localStorage.setItem('refresh_token', this.refreshToken);
  }

  async makeAuthenticatedRequest(url: string, options: RequestInit = {}) {
    options.headers = {
      ...options.headers,
      'Authorization': `Bearer ${this.accessToken}`
    };
    
    let response = await fetch(url, options);
    
    // If unauthorized, try refreshing token
    if (response.status === 401) {
      await this.refreshAccessToken();
      response = await fetch(url, options);
    }
    
    return response;
  }

  async refreshAccessToken() {
    const response = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({refresh_token: this.refreshToken})
    });
    
    const data = await response.json();
    this.accessToken = data.access_token;
    localStorage.setItem('access_token', this.accessToken);
  }
}
```

---

## RBAC Integration

### 1. Initial Setup

#### Create Base Permissions

```python
# scripts/init_permissions.py
from app.database import AsyncSessionLocal
from app.modules.roles.models import Permission, Role

async def init_permissions():
    async with AsyncSessionLocal() as db:
        # Define permissions
        permissions = [
            # User management
            Permission(name="users:create", resource="users", action="create"),
            Permission(name="users:read", resource="users", action="read"),
            Permission(name="users:update", resource="users", action="update"),
            Permission(name="users:delete", resource="users", action="delete"),
            
            # Product management
            Permission(name="products:create", resource="products", action="create"),
            Permission(name="products:read", resource="products", action="read"),
            Permission(name="products:update", resource="products", action="update"),
            Permission(name="products:delete", resource="products", action="delete"),
        ]
        
        db.add_all(permissions)
        await db.commit()
        
        # Create roles
        admin_role = Role(
            name="admin",
            description="Administrator with full access",
            is_system=True
        )
        admin_role.permissions = permissions  # All permissions
        
        editor_role = Role(
            name="editor",
            description="Can manage products"
        )
        # Add only product permissions
        editor_role.permissions = [p for p in permissions if p.resource == "products"]
        
        db.add_all([admin_role, editor_role])
        await db.commit()

import asyncio
asyncio.run(init_permissions())
```

### 2. Using RBAC in Routes

#### Method 1: Dependency Injection

```python
from app.dependencies import require_permission

@router.post("/products")
async def create_product(
    data: ProductCreate,
    user = Depends(require_permission("products", "create"))
):
    # User has permission, proceed
    pass
```

#### Method 2: Manual Check

```python
from app.modules.roles.services import RoleService

@router.post("/products")
async def create_product(
    data: ProductCreate,
    current_user: ActiveUser,
    db: AsyncSession = Depends(get_db)
):
    # Check permission manually
    role_service = RoleService(db)
    has_permission = await role_service.check_permission(
        current_user.role_id,
        "products",
        "create"
    )
    
    if not has_permission and not current_user.is_superuser:
        raise ForbiddenException()
    
    # Proceed with logic
    pass
```

### 3. Dynamic Permission Management

```python
# Add permission to role
from app.modules.roles.services import RoleService

async def add_permissions_to_role():
    async with AsyncSessionLocal() as db:
        service = RoleService(db)
        
        # Add permissions to editor role
        await service.add_permissions_to_role(
            role_id=2,  # editor role
            permission_ids=[5, 6, 7, 8]  # product permissions
        )
        
        await db.commit()
```

---

## Email & SMS Integration

### 1. Sending Welcome Email

```python
from app.utils.email import email_service

async def send_welcome_email(user: User):
    await email_service.send_templated_email(
        to_emails=[user.email],
        subject="Welcome to Our Platform",
        template_path="users/templates/welcome_email.html",
        context={
            "username": user.username,
            "login_url": "https://yourapp.com/login"
        }
    )
```

### 2. Sending Custom Emails

```python
# With attachments
pdf_content = generate_pdf_report()

await email_service.send_email(
    to_emails=["recipient@example.com"],
    subject="Your Monthly Report",
    body_html="<h1>Report Attached</h1>",
    body_text="Report Attached",
    attachments=[
        {
            "filename": "report.pdf",
            "content": pdf_content
        }
    ]
)
```

### 3. Sending SMS

```python
from app.utils.sms import sms_service
from app.database import AsyncSessionLocal

async def send_2fa_code(phone: str, code: str):
    async with AsyncSessionLocal() as db:
        await sms_service.send_templated_sms(
            db=db,
            phone_number=phone,
            template_name="2fa_code",
            variables={"code": code}
        )
```

### 4. Creating Email Templates

Create new template in `app/modules/your_module/templates/`:

```html
<!-- app/modules/products/templates/low_stock_alert.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Low Stock Alert</title>
</head>
<body>
    <h1>Low Stock Alert</h1>
    <p>Hello {{ admin_name }},</p>
    <p>The following products are running low on stock:</p>
    <ul>
    {% for product in products %}
        <li>{{ product.name }}: {{ product.stock }} units remaining</li>
    {% endfor %}
    </ul>
</body>
</html>
```

Use in code:
```python
await email_service.send_templated_email(
    to_emails=["admin@example.com"],
    subject="Low Stock Alert",
    template_path="products/templates/low_stock_alert.html",
    context={
        "admin_name": "Admin",
        "products": low_stock_products
    }
)
```

---

## Testing Guide

### 1. Setup Test Environment

**`tests/conftest.py`**:
```python
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient
from app.main import app
from app.database import get_db, Base
from app.config import settings

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
```

### 2. Writing Tests

**`tests/modules/test_users.py`**:
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    """Test user login."""
    # First register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!"
        }
    )
    
    # Then login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    """Test getting current user profile."""
    # Register and login
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!"
        }
    )
    
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
    )
    
    token = login_response.json()["access_token"]
    
    # Get profile
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
```

### 3. Testing Services

**`tests/modules/test_user_service.py`**:
```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.users.services import UserService
from app.modules.users.exceptions import UserAlreadyExistsException

@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """Test creating a user via service."""
    service = UserService(db_session)
    
    user = await service.create_user(
        email="test@example.com",
        username="testuser",
        password="SecurePass123!",
        first_name="Test",
        last_name="User"
    )
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.username == "testuser"

@pytest.mark.asyncio
async def test_duplicate_email(db_session: AsyncSession):
    """Test that duplicate email raises exception."""
    service = UserService(db_session)
    
    # Create first user
    await service.create_user(
        email="test@example.com",
        username="testuser1",
        password="SecurePass123!"
    )
    
    # Try to create second user with same email
    with pytest.raises(UserAlreadyExistsException):
        await service.create_user(
            email="test@example.com",
            username="testuser2",
            password="SecurePass123!"
        )
```

### 4. Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/modules/test_users.py

# Run specific test function
pytest tests/modules/test_users.py::test_register_user

# Run with verbose output
pytest -v

# Run and stop at first failure
pytest -x
```

---

## Deployment Guide

### 1. Docker Deployment

#### Create Dockerfile

**`Dockerfile`**:
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Create Docker Compose

**`docker-compose.yml`**:
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: fastapi_db
      POSTGRES_USER: fastapi_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U fastapi_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://fastapi_user:secure_password@db:5432/fastapi_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - SES_SENDER_EMAIL=${SES_SENDER_EMAIL}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: >
      sh -c "alembic upgrade head &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000"

  celery_worker:
    build: .
    environment:
      - DATABASE_URL=postgresql+asyncpg://fastapi_user:secure_password@db:5432/fastapi_db
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    depends_on:
      - redis
      - db
    command: celery -A app.celery_app worker --loglevel=info

volumes:
  postgres_data:
```

#### Build and Run

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### 2. Production Deployment (Ubuntu Server)

#### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip \
    postgresql postgresql-contrib redis-server nginx supervisor

# Create application user
sudo useradd -m -s /bin/bash fastapi
sudo su - fastapi
```

#### Step 2: Application Setup

```bash
# Clone repository
git clone <your-repo-url> app
cd app

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
nano .env
# Add production settings

# Run migrations
alembic upgrade head

# Test application
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Step 3: Gunicorn Configuration

**`gunicorn_config.py`**:
```python
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/log/fastapi/access.log"
errorlog = "/var/log/fastapi/error.log"
loglevel = "info"

# Process naming
proc_name = "fastapi_app"

# Server mechanics
daemon = False
pidfile = "/var/run/fastapi.pid"
user = "fastapi"
group = "fastapi"
```

#### Step 4: Supervisor Configuration

**`/etc/supervisor/conf.d/fastapi.conf`**:
```ini
[program:fastapi]
command=/home/fastapi/app/venv/bin/gunicorn -c /home/fastapi/app/gunicorn_config.py app.main:app
directory=/home/fastapi/app
user=fastapi
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/fastapi/app.log
environment=PATH="/home/fastapi/app/venv/bin"
```

Start with Supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start fastapi
sudo supervisorctl status fastapi
```

#### Step 5: Nginx Configuration

**`/etc/nginx/sites-available/fastapi`**:
```nginx
upstream fastapi_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 50M;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://fastapi_backend;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 6: SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (already set up by certbot)
sudo certbot renew --dry-run
```

### 3. Environment Variables for Production

**`.env` (Production)**:
```bash
# Application
APP_NAME=FastAPI Production App
DEBUG=False
API_V1_PREFIX=/api/v1

# Database
DATABASE_URL=postgresql+asyncpg://user:strong_password@localhost:5432/prod_db
DB_ECHO=False

# Security - USE STRONG SECRETS
SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
SES_SENDER_EMAIL=noreply@yourdomain.com

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS - Restrict to your domains
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
```

### 4. Monitoring & Logging

#### Setup Log Rotation

**`/etc/logrotate.d/fastapi`**:
```
/var/log/fastapi/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 fastapi fastapi
    sharedscripts
    postrotate
        supervisorctl restart fastapi > /dev/null
    endscript
}
```

#### Monitor with Systemd Journal

```bash
# View application logs
sudo journalctl -u supervisor -f

# View specific service logs
sudo tail -f /var/log/fastapi/app.log
```

---

## Common Integration Patterns

### 1. Background Tasks with Celery

#### Setup Celery

**`app/celery_app.py`**:
```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    "fastapi_app",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
```

#### Create Tasks

**`app/modules/users/tasks.py`**:
```python
from app.celery_app import celery_app
from app.utils.email import email_service
import asyncio

@celery_app.task
def send_welcome_email_task(email: str, username: str):
    """Background task to send welcome email."""
    asyncio.run(
        email_service.send_templated_email(
            to_emails=[email],
            subject="Welcome",
            template_path="users/templates/welcome_email.html",
            context={"username": username}
        )
    )

@celery_app.task
def cleanup_expired_tokens():
    """Periodic task to clean up expired tokens."""
    from app.database import AsyncSessionLocal
    from app.modules.users.repository import RefreshTokenRepository
    
    async def _cleanup():
        async with AsyncSessionLocal() as db:
            repo = RefreshTokenRepository(db)
            count = await repo.delete_expired()
            await db.commit()
            return count
    
    count = asyncio.run(_cleanup())
    return f"Deleted {count} expired tokens"
```

#### Use in Service

```python
from app.modules.users.tasks import send_welcome_email_task

async def create_user(self, data: UserCreate):
    user = await self.repo.create(user_obj)
    
    # Send email asynchronously
    send_welcome_email_task.delay(user.email, user.username)
    
    return user
```

#### Run Celery Worker

```bash
celery -A app.celery_app worker --loglevel=info
```

#### Setup Periodic Tasks

**`app/celery_app.py`**:
```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-expired-tokens': {
        'task': 'app.modules.users.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
}
```

Run Celery Beat:
```bash
celery -A app.celery_app beat --loglevel=info
```

### 2. File Upload Handling

```python
from fastapi import UploadFile, File
from typing import List
import aiofiles
import os

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: ActiveUser
):
    """Upload a file."""
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "application/pdf"]
    if file.content_type not in allowed_types:
        raise ValidationException("Invalid file type")
    
    # Validate file size (5MB max)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise ValidationException("File too large")
    
    # Save file
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{current_user.id}_{file.filename}")
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(contents)
    
    return {"filename": file.filename, "size": len(contents)}

@router.post("/upload-multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    current_user: ActiveUser
):
    """Upload multiple files."""
    results = []
    
    for file in files:
        contents = await file.read()
        # Process each file
        results.append({
            "filename": file.filename,
            "size": len(contents)
        })
    
    return {"files": results}
```

### 3. Pagination Helper

```python
from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

async def paginate(
    query,
    page: int = 1,
    size: int = 50
) -> PaginatedResponse:
    """Generic pagination helper."""
    # Get total count
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    
    # Get items
    items = await db.execute(
        query.offset((page - 1) * size).limit(size)
    )
    
    return PaginatedResponse(
        items=list(items.scalars().all()),
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )

# Usage
@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = 1,
    size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    query = select(User)
    return await paginate(query, page, size)
```

### 4. Rate Limiting

```python
from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, data: LoginRequest):
    """Login endpoint with rate limiting."""
    # Login logic
    pass
```

### 5. Caching with Redis

```python
import redis.asyncio as redis
import json
from typing import Optional

class RedisCache:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
    
    async def get(self, key: str) -> Optional[dict]:
        """Get value from cache."""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: dict, expire: int = 300):
        """Set value in cache."""
        await self.redis.set(
            key,
            json.dumps(value),
            ex=expire
        )
    
    async def delete(self, key: str):
        """Delete key from cache."""
        await self.redis.delete(key)

cache = RedisCache()

# Usage in service
async def get_user(self, user_id: int):
    # Try cache first
    cache_key = f"user:{user_id}"
    cached = await cache.get(cache_key)
    if cached:
        return User(**cached)
    
    # Get from database
    user = await self.repo.get_by_id(user_id)
    
    # Cache result
    if user:
        await cache.set(cache_key, user.__dict__)
    
    return user
```

### 6. API Versioning

```python
# v1 router
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(users_router)
v1_router.include_router(products_router)

# v2 router
v2_router = APIRouter(prefix="/api/v2")
v2_router.include_router(users_v2_router)

# Add to app
app.include_router(v1_router)
app.include_router(v2_router)
```

### 7. Health Checks

```python
from fastapi import status

@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}

@app.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with dependencies."""
    checks = {
        "api": "healthy",
        "database": "unknown",
        "redis": "unknown"
    }
    
    # Check database
    try:
        await db.execute(select(1))
        checks["database"] = "healthy"
    except Exception:
        checks["database"] = "unhealthy"
    
    # Check Redis
    try:
        await cache.redis.ping()
        checks["redis"] = "healthy"
    except Exception:
        checks["redis"] = "unhealthy"
    
    is_healthy = all(v == "healthy" for v in checks.values())
    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(content=checks, status_code=status_code)
```

---

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check PostgreSQL is running
   sudo systemctl status postgresql
   
   # Check connection
   psql -U fastapi_user -d fastapi_db -h localhost
   ```

2. **Migration Issues**
   ```bash
   # Check current revision
   alembic current
   
   # Check pending migrations
   alembic history
   
   # Downgrade if needed
   alembic downgrade -1
   ```

3. **AWS SES/SNS Errors**
   ```bash
   # Verify AWS credentials
   aws sts get-caller-identity
   
   # Test SES
   aws ses verify-email-identity --email noreply@yourdomain.com
   ```

4. **Import Errors**
   ```bash
   # Ensure all __init__.py files exist
   find app -type d -exec touch {}/__init__.py \;
   ```

This comprehensive guide covers all aspects of integrating and implementing the FastAPI modular application!