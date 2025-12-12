# src/main.py

"""
Main FastAPI Application Entry Point
Initializes the application with all middleware, routers, and event handlers.
"""

import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.config import settings
from src.core.database import DatabaseManager
from src.core.exceptions import AppException
from src.core.logging import LoggingMiddleware, get_logger, setup_logging
from src.core.redis import RedisManager

# Initialize logging first
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info(
        "Starting application",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    # Initialize database
    try:
        from src.core.database import get_engine
        engine = get_engine()
        logger.info("Database engine initialized")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise

    # Initialize Redis
    try:
        from src.core.redis import RedisManager
        redis_client = await RedisManager.get_client()
        is_connected = await redis_client.ping()
        if is_connected:
            logger.info("Redis connected successfully")
        else:
            logger.warning("Redis connection test failed")

    except Exception as e:
        logger.error("Failed to connect to Redis", error=str(e))
        raise

    logger.info("Application startup completed")

    yield

    # Shutdown
    logger.info("Shutting down application")

    # Close database connections
    await DatabaseManager.close()
    logger.info("Database connections closed")

    # Close Redis connections
    await RedisManager.close()
    logger.info("Redis connection closed")

    logger.info("Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production grade Restaurant Fleet Management Platform",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)

# ==========================================================================
# Middleware Configuration
# ==========================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# GZip Middleware for compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted Host Middleware (production)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"], # Configure with actual hosts in production
    )

# Custom Logging Middleware
app.add_middleware(LoggingMiddleware)

# ==========================================================================
# Exception Handlers
# ==========================================================================

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions."""
    logger.error(
        "Application exception",
        error_code=exc.error_code,
        message=exc.message,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": None,
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": None,
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.warning(
        "Validation error",
        errors=exc.errors(),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": exc.errors(),
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        exc_info=True,
    )

    # Don't expose internal errors in production
    if settings.is_production:
        message = "An internal server error occurred."
    else:
        message = str(exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "message": message,
            "details": None,
        }
    )


# ==========================================================================
# Health Check Endpoints
# ==========================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Basic health check endpoint
    Returns application status and version
    """
    return {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check with dependency statuss
    Checks database and Redis connectivity
    """
    health_status = {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": time.time(),
        "checks": {}
    }

    # Check database
    try:
        from src.core.database import get_engine
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }
        logger.error("Database health check failed", error=str(e))

    # Check Redis
    try:
        from src.core.redis import RedisManager
        redis_client = await RedisManager.get_client()
        await redis_client.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis error: {str(e)}"
        }
        logger.error("Redis health check failed", error=str(e))

    # Return appropriate status code
    status_code = (
        status.HTTP_200_OK
        if health_status["status"] == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(content=health_status, status_code=status_code)


# ==========================================================================
# Root Endpoint
# ==========================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information
    """
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "documentation": "/docs" if not settings.is_production else "Documentation disabled in production",
        "health_check": "/health",
        "api_prefix": settings.api_v1_prefix,
    }


# ==========================================================================
# API Router Registration
# ==========================================================================

# TODO: Import and register your API routers here
# Example:
# from src.api.v1.api import api_router as api_v1_router
# app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

# For now, let's add a simple test router
from fastapi import APIRouter
test_router = APIRouter(prefix="/api/v1/test", tags=["Test"])

@test_router.get("/")
async def test_endpoint():
    """Test endpoint to verify API is working."""
    logger.info("Test endpoint called")
    return {
        "message": "Test endpoint working",
        "timestamp": time.time(),
        "environment": settings.environment,
    }


@test_router.get("/db")
async def test_database():
    """Test database connection."""
    from sqlalchemy import text
    from src.core.database import get_db_context

    try:
        async with get_db_context() as db:
            result = await db.execute(text("SELECT 1 as test"))
            row = result.first()

        logger.info("Database test successful")
        return {
            "message": "Database connection successful",
            "result": row[0] if row else None,
        }
    except Exception as e:
        logger.error("Database test failed", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": "Database connection failed",
                "error": str(e)
            }
        )
    

@test_router.get("/redis")
async def test_redis():
    """Test Redis connection"""
    from src.core.redis import redis_service

    try:
        # Set a test value
        await redis_service.set("test_key", "test_value", expire=60)

        # Get the value
        value = await redis_service.get("test_key")

        # Delete the test key
        await redis_service.delete("test_key")

        logger.info("Redis test successful")
        return {
            "message": "Redis connection successful",
            "test_value": value,
        }
    except Exception as e:
        logger.error("Redis test failed", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": "Redis connection failed",
                "error": str(e),
            }
        )
    

@test_router.get("/log")
async def test_logging():
    """Test logging functionality."""
    logger.debug("Debug log message")
    logger.info("Info log message", user_id="test_user", action="test")
    logger.warning("Warning log message")
    logger.error("Error log message", error_code="TEST_ERROR")

    return {
        "message": "Log messages sent",
        "check": "Check your logs to verify structured logging is working",
    }

# Register test router
app.include_router(test_router)

# ==========================================================================
# Request/Response Middleware for Timing
# ==========================================================================

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# ==========================================================================
# Development only endpoints
# ==========================================================================

if settings.is_development:

    @app.get("/debug/config", tags=["Debug"])
    async def debug_config():
        """
        Debug endpoint to view configuration (development only)
        WARNING: Never expose this in production!
        """
        return {
            "environment": settings.environment,
            "debug": settings.debug,
            "database_url": settings.db_name,
            "redis_url": settings.redis_url.split("@")[-1],  # Hide password
            "log_level": settings.log_level,
            "cors_origins": settings.cors_origins,
        }
    
    @app.get("/debug/routes", tags=["Debug"])
    async def debug_routes():
        """List all registered routes (development only)"""
        routes = []
        for route in app.routes:
            if hasattr(route, "methods"):
                routes.append({
                    "path": route.path,
                    "name": route.name,
                    "methods": list(route.methods),
                })
        return routes
    

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )