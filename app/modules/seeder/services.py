# app/modules/seeder/services.py

from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.seeder.models import (
    SeederExecution, SeederStatus, SeederType
)
from app.modules.seeder.repository import SeederRepository
from app.modules.seeder.base import DatabaseBackupRestore
from app.modules.seeder.seeders import MasterSeeder
from app.modules.seeder.exceptions import (
    SeederNotFoundException, SeederExecutionException
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class SeederService:
    """Service for seeder management"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SeederRepository(db)
        self.backup_restore = DatabaseBackupRestore(db)

    async def execute_seeder(
        self, create_backup: bool = True, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute all seeders.

        Args:
            create_backup: Whether to create backup before seeding.
            user_id: ID of user executing seeders.

        Returns:
            Dict with execution results.
        """
        try:
            # Create backup if requested
            backup_info = None
            if create_backup:
                backup_info = await self._create_pre_seed_backup(user_id)

            # Run seeders
            master_seeder = MasterSeeder(self.db)
            results = await master_seeder.run_all(
                seeder_type=SeederType.INITIAL,
                user_id=user_id
            )

            # Update backup info on last execution
            if backup_info and results["seeders"]:
                last_seeder_name = list(results["seeders"].keys())[-1]
                stmt = self.db.query(SeederExecution).filter(
                    SeederExecution.seeder_name == last_seeder_name
                ).order_by(SeederExecution.created_at.desc()).limit(1)

                from sqlalchemy import select
                execution_stmt = (
                    select(SeederExecution)
                    .where(SeederExecution.seeder_name == last_seeder_name)
                    .order_by(SeederExecution.created_at.desc())
                    .limit(1)
                )
                result = await self.db.execute(execution_stmt)
                execution = result.scalar_one_or_none()

                if execution:
                    execution.backup_s3_key = backup_info["s3_key"]
                    execution.backup_file_size = backup_info["file_size"]
                    await self.repo.update(execution)

            logger.info("seeders_executed", results=results)

            return {
                "success": True,
                "backup_created": create_backup,
                "backup_s3_key": backup_info["s3_key"] if backup_info else None,
                "results": results
            }
        
        except Exception as e:
            logger.error("seeder_execution_failed", error=str(e))
            raise SeederExecutionException(str(e)) from e
        
    async def reset_database(
        self, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Reset database and re-run seeders.

        Args:
            user_id: ID of user executing reset.

        Returns:
            Dict with reset results.
        """
        try:
            logger.info("database_reset_started")

            # Create backup before reset
            backup_info = await self._create_pre_seed_backup(user_id)

            # Truncate all tables except alembic_version
            await self._truncate_all_tables()

            # Run seeders
            master_seeder = MasterSeeder(self.db)
            results = await master_seeder.run_all(
                seeder_type=SeederType.RESET,
                user_id=user_id
            )

            logger.info("database_reset_completed", results=results)

            return {
                "success": True,
                "backup_s3_key": backup_info["s3_key"],
                "results": results
            }
        except Exception as e:
            logger.error("database_reset_failed", error=str(e))
            raise SeederExecutionException(f"Database reset failed: {str(e)}") from e
        
    async def restore_from_backup(
        self, s3_key: Optional[str] = None,
        execution_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Restore database from backup.

        Args:
            s3_key: S3 key of backup (if None, uses latest)
            execution_id: Execution ID to restore from
            user_id: ID of user executing restore.

        Returns:
            Dict with restore results.
        """
        try:
            # Determine backup to restore
            if not s3_key:
                if execution_id:
                    execution = await self.repo.get_by_id(execution_id)
                    if not execution or not execution.backup_s3_key:
                        raise SeederNotFoundException(
                            f"No backup found for execution {execution_id}"
                        )
                    s3_key = execution.backup_s3_key
                else:
                    # Use latest backup
                    execution = await self.repo.get_latest_successful_backup()
                    if not execution:
                        raise SeederNotFoundException("No backup available for restore")
                    s3_key = execution.backup_s3_key

            logger.info("database_restore_started", s3_key=s3_key)

            # Create execution record
            execution = SeederExecution(
                seeder_name="DatabaseRestore",
                seeder_type=SeederType.RESTORE,
                status=SeederStatus.RUNNING,
                backup_s3_key=s3_key,
                executed_by_id=user_id
            )
            execution = await self.repo.create(execution)

            # Restore from backup
            stats = await self.backup_restore.restore_from_backup(
                s3_key=s3_key,
                execution_id=execution.id,
            )

            # Update execution record
            execution.status = SeederStatus.COMPLETED
            execution.records_created = stats["records_created"]
            await self.repo.update(execution)

            logger.info("database_restore_completed", stats=stats)

            return {
                "success": True,
                "s3_key": s3_key,
                "tables_restored": stats["tables_restored"],
                "records_restored": stats["records_created"]
            }
        
        except Exception as e:
            logger.error("database_restore_failed", error=str(e))
            raise SeederExecutionException(f"Database restore failed: {str(e)}") from e
        
    async def list_executions(
        self, skip: int = 0, limit: int = 100,
        seeder_name: Optional[str] = None,
        status: Optional[SeederStatus] = None
    ) -> tuple[List[SeederExecution], int]:
        """List seeder executions with pagination and filters."""
        executions = await self.repo.get_all(
            skip=skip, limit=limit, seeder_name=seeder_name, status=status
        )

        # Get total count
        from sqlalchemy import select, func
        stmt = select(func.count(SeederExecution.id))

        filters = []
        if seeder_name:
            filters.append(SeederExecution.seeder_name == seeder_name)
        if status:
            filters.append(SeederExecution.status == status)

        if filters:
            from sqlalchemy import and_
            stmt = stmt.where(and_(*filters))

        result = await self.db.execute(stmt)
        total = result.scalar_one()

        return executions, total
    
    async def get_execution(self, execution_id: int) -> SeederExecution:
        """Get seeder execution by ID."""
        execution = await self.repo.get_by_id(execution_id)
        if not execution:
            raise SeederNotFoundException(execution_id)
        return execution
    
    async def _create_pre_seed_backup(
        self, user_id: Optional[int]
    ) -> Dict[str, Any]:
        """Create a backup before seeding."""
        # Create temporary execution for backup
        execution = SeederExecution(
            seeder_name="PreSeedBackup",
            seeder_type=SeederType.INITIAL,
            status=SeederStatus.RUNNING,
            executed_by_id=user_id
        )
        execution = await self.repo.create(execution)

        # Create backup
        backup_info = await self.backup_restore.create_backup(
            execution_id=execution.id
        )

        # Update execution
        execution.status = SeederStatus.COMPLETED
        execution.backup_s3_key = backup_info["s3_key"]
        execution.backup_file_size = backup_info["file_size"]
        await self.repo.update(execution)

        return backup_info
    
    async def _truncate_all_tables(self) -> None:
        """Truncate all tables except alembic_version."""
        from sqlalchemy import text

        # Get all tables
        query = text("""
           SELECT table_name
           FROM information_schema.tables
           WHERE table_schema = 'public'
           AND table_type = 'BASE TABLE'
           AND table_name != 'alembic_version'        
        """)

        result = await self.db.execute(query)
        tables = [row[0] for row in result.fetchall()]

        # Disable foreign key checks
        await self.db.execute(text("SET CONSTRAINTS ALL DEFERRED"))

        # Truncate each table
        for table in tables:
            await self.db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))

        # Re-enable foreign key checks
        await self.db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))

        await self.db.commit()



