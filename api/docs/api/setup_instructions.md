# Restaurant Fleet Platform - Backend Setup Guide

## Quick Start Guide

This guide will help you set up and run the FastAPI backend application.

## Prerequisites

1. **Python 3.11 or higher**
   ```bash
   python --version  # Should be 3.11+
   ```

2. **PostgreSQL 14 or higher**
   - Installation: https://www.postgresql.org/download/
   - Or use Docker (recommended)

3. **Redis 7 or higher**
   - Installation: https://redis.io/download
   - Or use Docker (recommended)

## Installation Steps

### Step 1: Clone and Navigate to Project

```bash
cd restaurant-fleet-platform
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# For development (includes testing and code quality tools)
pip install -r requirements-dev.txt
```

### Step 4: Set Up Database and Redis

#### Option A: Using Docker (Recommended)

Create a `docker-compose.yml` file in the project root:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: restaurant_fleet_db
    environment:
      POSTGRES_DB: restaurant_fleet
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: restaurant_fleet_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

Start the services:

```bash
docker-compose up -d
```

#### Option B: Manual Installation

**PostgreSQL:**
1. Install PostgreSQL
2. Create database:
   ```sql
   CREATE DATABASE restaurant_fleet;
   ```

**Redis:**
1. Install Redis
2. Start Redis server:
   ```bash
   redis-server
   ```

### Step 5: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your settings
# Minimum required configuration:
# - POSTGRES_* settings (if not using defaults)
# - REDIS_* settings (if not using defaults)
# - SECRET_KEY (generate a secure key)
```

Generate a secure SECRET_KEY:

```bash
# Using Python
python -c "import secrets; print(secrets.token_hex(32))"

# Using OpenSSL
openssl rand -hex 32
```

Update the `.env` file with the generated key:

```bash
SECRET_KEY=your-generated-secret-key-here
```

### Step 6: Initialize Database

Create the necessary directory structure:

```bash
# Create required directories
mkdir -p src/apps/authentication
mkdir -p src/apps/users
mkdir -p src/apps/restaurants
mkdir -p src/apps/orders
mkdir -p src/apps/delivery
mkdir -p src/apps/payments
mkdir -p src/apps/notifications
mkdir -p src/apps/analytics
mkdir -p src/apps/ai_services
mkdir -p src/apps/admin
mkdir -p logs
mkdir -p uploads

# Create __init__.py files
touch src/__init__.py
touch src/core/__init__.py
touch src/apps/__init__.py
touch src/apps/authentication/__init__.py
touch src/apps/users/__init__.py
touch src/apps/restaurants/__init__.py
touch src/apps/orders/__init__.py
touch src/apps/delivery/__init__.py
touch src/apps/payments/__init__.py
touch src/apps/notifications/__init__.py
touch src/apps/analytics/__init__.py
touch src/apps/ai_services/__init__.py
touch src/apps/admin/__init__.py

# Create placeholder models.py files
echo "from src.core.base_models import Base" > src/apps/authentication/models.py
echo "from src.core.base_models import Base" > src/apps/users/models.py
echo "from src.core.base_models import Base" > src/apps/restaurants/models.py
echo "from src.core.base_models import Base" > src/apps/orders/models.py
echo "from src.core.base_models import Base" > src/apps/delivery/models.py
echo "from src.core.base_models import Base" > src/apps/payments/models.py
echo "from src.core.base_models import Base" > src/apps/notifications/models.py
echo "from src.core.base_models import Base" > src/apps/analytics/models.py
echo "from src.core.base_models import Base" > src/apps/ai_services/models.py
echo "from src.core.base_models import Base" > src/apps/admin/models.py
```

Initialize Alembic (for database migrations):

```bash
# Initialize Alembic
alembic init alembic

# Edit alembic.ini to use your database URL
# Or use the auto-generated configuration from settings
```

### Step 7: Run the Application

```bash
# Development mode (with auto-reload)
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main.py directly
python src/main.py
```

## Verify Installation

### 1. Check Application is Running

Open your browser and navigate to:
- **API Root**: http://localhost:8000/
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### 2. Test Health Check

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check (includes DB and Redis)
curl http://localhost:8000/health/detailed
```

Expected response:
```json
{
  "status": "healthy",
  "application": "Restaurant Fleet Platform",
  "version": "1.0.0",
  "environment": "development"
}
```

### 3. Test Database Connection

```bash
curl http://localhost:8000/api/v1/test/db
```

Expected response:
```json
{
  "message": "Database connection successful",
  "result": 1
}
```

### 4. Test Redis Connection

```bash
curl http://localhost:8000/api/v1/test/redis
```

Expected response:
```json
{
  "message": "Redis connection successful",
  "test_value": "test_value"
}
```

### 5. Test Logging

```bash
curl http://localhost:8000/api/v1/test/log
```

Check your console/logs to verify structured logging is working.

## Project Structure Verification

Your project should now have this structure:

```
restaurant-fleet-platform/
├── .env                          # Your environment variables
├── .env.example                  # Example environment variables
├── .gitignore                    # Git ignore file
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── docker-compose.yml            # Docker services (optional)
├── alembic.ini                   # Alembic configuration
├── alembic/                      # Database migrations
│   ├── versions/
│   └── env.py
├── src/
│   ├── __init__.py
│   ├── main.py                   # Application entry point
│   ├── core/                     # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── redis.py
│   │   ├── logging.py
│   │   ├── base_models.py
│   │   └── exceptions.py
│   └── apps/                     # Feature modules
│       ├── __init__.py
│       ├── authentication/
│       ├── users/
│       ├── restaurants/
│       ├── orders/
│       ├── delivery/
│       ├── payments/
│       ├── notifications/
│       ├── analytics/
│       ├── ai_services/
│       └── admin/
├── logs/                         # Application logs
└── uploads/                      # File uploads
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_specific.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with Black
black src/

# Sort imports with isort
isort src/

# Lint with flake8
flake8 src/

# Type checking with mypy
mypy src/
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Viewing Logs

Logs will be output to the console in development mode. For structured logging:

```bash
# Development (readable console output)
LOG_FORMAT=console python src/main.py

# Production-style (JSON format)
LOG_FORMAT=json python src/main.py
```

## Available Endpoints

### Root & Health
- `GET /` - API information
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health check with dependencies

### Test Endpoints (Development)
- `GET /api/v1/test/` - Test endpoint
- `GET /api/v1/test/db` - Test database connection
- `GET /api/v1/test/redis` - Test Redis connection
- `GET /api/v1/test/log` - Test logging functionality

### Debug Endpoints (Development Only)
- `GET /debug/config` - View configuration (sanitized)
- `GET /debug/routes` - List all registered routes

## Production Deployment

### Using Gunicorn with Uvicorn Workers

```bash
gunicorn src.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Using Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run application
CMD ["gunicorn", "src.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]
```

Build and run:

```bash
# Build image
docker build -t restaurant-fleet-backend .

# Run container
docker run -p 8000:8000 --env-file .env restaurant-fleet-backend
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres
# or
pg_isready -h localhost -p 5432

# Check database exists
psql -h localhost -U postgres -c "\l"

# Test connection manually
psql -h localhost -U postgres -d restaurant_fleet
```

### Redis Connection Issues

```bash
# Check Redis is running
docker ps | grep redis
# or
redis-cli ping

# Test connection
redis-cli
> ping
PONG
```

### Import Errors

```bash
# Make sure you're in the project root and virtual environment is activated
pwd  # Should be in project root
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn src.main:app --port 8001
```

## Environment Variables Reference

See `.env.example` for all available configuration options.

### Critical Settings

**Production:**
```bash
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<strong-random-key>
COOKIE_SECURE=true
COOKIE_SAMESITE=strict
LOG_FORMAT=json
LOG_LEVEL=INFO
```

**Development:**
```bash
ENVIRONMENT=development
DEBUG=true
RELOAD=true
LOG_FORMAT=console
LOG_LEVEL=DEBUG
```

## Next Steps

1. **Implement Authentication App**
   - Create User model
   - Implement JWT authentication
   - Add login/logout endpoints

2. **Build Core Features**
   - Restaurant management
   - Menu management
   - Order processing
   - Delivery management

3. **Add AI Features**
   - Recommendation engine
   - Demand prediction
   - Route optimization

4. **Set Up Testing**
   - Write unit tests
   - Add integration tests
   - Set up CI/CD pipeline

## Support

For issues or questions:
1. Check the logs: Console output or log files
2. Review the documentation in `docs/` directory
3. Check the API documentation at `/docs`
4. Review the comprehensive implementation documentation

## License

[Your License Here]