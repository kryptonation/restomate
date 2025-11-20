# app/database.py

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Create async engine
engine = create_async_engine(
    settings.db_url,
    echo=settings.db_echo,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("database_session_error", error=str(e))
            raise
        finally:
            await session.close()

