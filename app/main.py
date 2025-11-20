# app/main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.exceptions import BaseAppException
from app.core.middleware import LoggingMiddleware, RequestIDMiddleware
from app.modules.users.router import router as users_router, auth_router
from app.modules.roles.router import router as roles_router
from app.database import engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_logging()
    logger.info("application_startup", version=settings.app_version)

    # Create database tables (for development - use Alembic in production)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown
    logger.info("application_shutdown")
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)

# ========== Exception Handlers ==========

@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    """Handle application exceptions."""
    logger.error(
        "application_exception",
        error=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(
        "validation_error",
        errors=exc.errors(),
        path=request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": "Validation error",
            "details": exc.errors()
        }
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy errors."""
    logger.error(
        "database_error",
        error=str(exc),
        path=request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database error occurred",
            "details": {}
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "details": {}
        }
    )

# ========== Routes ==========

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version
    }

# ========== Include Routers ==========

app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(roles_router, prefix=settings.api_v1_prefix)


