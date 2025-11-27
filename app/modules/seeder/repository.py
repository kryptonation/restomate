# app/modules/seeder/repository.py

from typing import Optional, List
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.modules.seeder.models import SeederExecution, SeederStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class SeederRepository:
    """Repository for seeder operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, execution_id: int) -> Optional[SeederExecution]:
        """Get seeder execution by ID."""
        stmt = select(SeederExecution).where(SeederExecution.id == execution_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, skip: int = 0, limit: int = 100,
        seeder_name: Optional[str] = None,
        status: Optional[SeederStatus] = None
    ) -> List[SeederExecution]:
        """Get all seeder executions with filters."""
        stmt = select(SeederExecution)

        filters = []
        if seeder_name:
            filters.append(SeederExecution.seeder_name == seeder_name)
        if status:
            filters.append(SeederExecution.status == status)

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(SeederExecution.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_latest_successful_backup(self) -> Optional[SeederExecution]:
        """Get the latest successful execution with backup."""
        stmt = (
            select(SeederExecution)
            .where(
                and_(
                    SeederExecution.status == SeederStatus.COMPLETED,
                    SeederExecution.backup_s3_key.isnot(None)
                )
            )
            .order_by(SeederExecution.created_at.desc())
            .limit(1)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(self, execution: SeederExecution) -> SeederExecution:
        """Create seeder execution record."""
        self.db.add(execution)
        await self.db.flush()
        await self.db.refresh(execution)
        return execution
    
    async def update(self, execution: SeederExecution) -> SeederExecution:
        """Update seeder execution record."""
        await self.db.flush()
        await self.db.refresh(execution)
        return execution
    
    async def cleanup_old_executions(self, days: int = 30) -> int:
        """Delete old seeder execution records."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = select(SeederExecution).where(
            SeederExecution.created_at < cutoff_date
        )
        result = await self.db.execute(stmt)
        executions = result.scalars().all()

        count = len(executions)
        for execution in executions:
            await self.db.delete(execution)

        await self.db.flush()
        return count
    
