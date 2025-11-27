# app/main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.exceptions import BaseAppException
from app.core.middleware import LoggingMiddleware, RequestIDMiddleware
from app.modules.users.router import router as users_router, auth_router
from app.modules.roles.router import router as roles_router
from app.modules.files.router import router as files_router
from app.modules.seeder.router import router as seeder_router
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
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
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

# ========== Custom OpenAPI Schema ==========

def custom_openapi():
    """Custom OpenAPI schema with security definitions."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description="Food Fleet API - Multi-tenant restaurant management platform",
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token"
        }
    }
    
    # Add security to all endpoints (except public ones)
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method in ["get", "post", "put", "delete", "patch"]:
                # Skip auth endpoints
                if "/auth/" not in path or path.endswith("/login") or path.endswith("/register") or path.endswith("/refresh"):
                    if "security" not in openapi_schema["paths"][path][method]:
                        openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

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

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with CDN assets."""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{settings.app_name} - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        init_oauth={
            "usePkceWithAuthorizationCodeGrant": True,
            "clientId": "swagger-ui",
            "appName": settings.app_name,
        },
        swagger_ui_parameters={
            "persistAuthorization": True,
            "displayRequestDuration": True,
            "filter": True,
            "tryItOutEnabled": True,
            "syntaxHighlight.theme": "monokai",
        }
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """ReDoc documentation."""
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{settings.app_name} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )

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
app.include_router(files_router, prefix=settings.api_v1_prefix)
app.include_router(seeder_router, prefix=settings.api_v1_prefix)

