# src/core/database.py

"""
Async database configuration and session management
Uses SQLAlchemy 2.x async engine and sessions
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
)
from sqlalchemy.pool import NullPool, QueuePool

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """
    Database manager for handling async SQLAlchemy engine and sessions
    Implements singleton pattern to ensure single engine instance
    """

    _engine: AsyncEngine | None = None
    _session_factory: async_sessionmaker[AsyncSession] | None = None

    @classmethod
    def get_engine(cls) -> AsyncEngine:
        """
        Get or create async database engine
        Configured with connection pooling for production
        """
        if cls._engine is None:
            logger.info("Creating database engine", url=settings.db_name)

            # Choose pool class based on environment
            if settings.is_production:
                pool_class = QueuePool
            else:
                pool_class = NullPool if settings.debug else QueuePool

            if pool_class is NullPool:
                cls._engine = create_async_engine(
                    settings.db_url,
                    echo=settings.db_echo,
                    future=True,
                )
            else:
                cls._engine = create_async_engine(
                    settings.db_url,
                    echo=settings.db_echo,
                    future=True,
                    pool_size=settings.db_pool_size,
                    max_overflow=settings.db_max_overflow,
                    pool_timeout=settings.db_pool_timeout,
                    pool_recycle=settings.db_pool_recycle,
                    pool_pre_ping=True,
                    poolclass=pool_class,
                )

            logger.info(
                "Database engine created",
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow
            )

        return cls._engine
    
    @classmethod
    def get_session_factory(cls) -> async_sessionmaker[AsyncSession]:
        """
        Get or create async session factory
        """
        if cls._session_factory is None:
            engine = cls.get_engine()
            cls._session_factory = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            logger.info("Session factory created")

        return cls._session_factory
    
    @classmethod
    async def close(cls) -> None:
        """
        Close database engine and cleanup resources
        Call this on application shutdown
        """
        if cls._engine is not None:
            logger.info("Closing database engine")
            await cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
            logger.info("Database engine closed")


# Convinience functions
def get_engine() -> AsyncEngine:
    """Get database engine instance"""
    return DatabaseManager.get_engine()

def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get session factory instance"""
    return DatabaseManager.get_session_factory()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session
    Use this in FastAPI route dependencies

    Example:
        @router.get("/items)
        async def get_items(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database session
    Use this outside of FastAPI routes

    Example:
        async with get_db_context() as db:
            result = await db.execute(query)
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db() -> None:
    """
    Initialize database - create all tables
    Use this for development/testing, not in production
    Use Alembic migrations for production
    """
    from src.core.base_model import Base

    logger.info("Initializing database")
    engine = get_engine()

    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        import_all_models()

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized successfully")


async def drop_db() -> None:
    """
    Drop all database tables
    WARNING: Use only in development/testing
    """
    from src.core.base_model import Base

    logger.warning("Dropping all database tables")
    engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    logger.info("All database tables dropped")


def import_all_models() -> None:
    """
    Import all mdoels to ensure they're registered with SQLAlchemy
    This is necessary for migrations and table creation
    """
    # Import all model modules here
    # This ensures SQLAlchemy knows about all tables
    from src.apps.authentication import models as auth_models
    from src.apps.users import models as user_models
    from src.apps.restaurants import models as restaurant_models
    from src.apps.orders import models as order_models
    from src.apps.delivery import models as delivery_models
    from src.apps.payments import models as payment_models
    from src.apps.notifications import models as notification_models
    from src.apps.analytics import models as analytics_models
    from src.apps.ai_services import models as ai_models
    from src.apps.admin import models as admin_models


