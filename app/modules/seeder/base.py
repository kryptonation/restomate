# app/modules/seeder/base.py

import json
import gzip
import traceback
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.logging import get_logger
from app.modules.seeder.models import (
    SeederExecution, SeederStatus, SeederType
)
from app.modules.files.s3_service import s3_service

logger = get_logger(__name__)


class BaseSeeder(ABC):
    """Base class for all seeders."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.name = self.__class__.__name__
        self.execution: Optional[SeederExecution] = None

    @abstractmethod
    async def seed(self) -> Dict[str, Any]:
        """
        Main seeding logic to be implemented by subclasses.

        Returns:
            Dict with statistics: {
                "created": int,
                "updated": int,
                "deleted": int
            }
        """
        pass

    async def execute(
        self, seeder_type: SeederType = SeederType.INITIAL,
        user_id: Optional[int] = None
    ) -> SeederExecution:
        """Execute the seeder with tracking."""
        # Create execution record
        self.execution = SeederExecution(
            seeder_name=self.name,
            seeder_type=seeder_type,
            status=SeederStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            executed_by_id=user_id
        )
        self.db.add(self.execution)
        await self.db.flush()

        try:
            logger.info("seeder_started", seeder=self.name, type=seeder_type)

            # Execute seeding logic
            stats = await self.seed()

            # Update execution record
            self.execution.records_created = stats.get("created", 0)
            self.execution.records_updated = stats.get("updated", 0)
            self.execution.records_deleted = stats.get("deleted", 0)
            self.execution.status = SeederStatus.COMPLETED
            self.execution.completed_at = datetime.now(timezone.utc)

            await self.db.flush()
            await self.db.commit()

            logger.info(
                "seeder_completed",
                seeder=self.name,
                created=stats.get("created", 0),
                updated=stats.get("updated", 0),
                deleted=stats.get("deleted", 0)
            )

            return self.execution
        
        except Exception as e:
            await self.db.rollback()

            self.execution.status = SeederStatus.FAILED
            self.execution.error_message = str(e)
            self.execution.error_traceback = traceback.format_exc()
            self.execution.completed_at = datetime.now(timezone.utc)

            await self.db.flush()
            await self.db.commit()

            logger.error(
                "seeder_failed",
                seeder=self.name,
                error=str(e),
                traceback=traceback.format_exc()
            )

            raise

    async def get_or_create(
        self, model_class, filters: Dict[str, Any], defaults: Dict[str, Any]
    ) -> tuple[Any, bool]:
        """
        Get existing record or create new one.

        Returns:
            Tuple of (instance, created)
        """
        stmt = select(model_class).filter_by(**filters)
        result = await self.db.execute(stmt)
        instance = result.scalar_one_or_none()

        if instance:
            return instance, False
        
        instance = model_class(**filters, **defaults)
        self.db.add(instance)
        await self.db.flush()
        return instance, True
    

class DatabaseBackupRestore:
    """Handle database backup and restore operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_backup(
        self, execution_id: int, tables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create database backup and upload to S3.

        Args:
            execution_id: SeederExecution ID
            tables: List of table names to backup (None = all tables)

        Returns:
            Dict with backup information
        """
        backup_data = {}

        try:
            # Get list of tables
            if tables is None:
                tables = await self._get_all_tables()

            logger.info("backup_started", tables=tables)

            # Export each table
            for table in tables:
                rows = await self._export_table(table)
                backup_data[table] = rows

            # Compress and serialize
            json_data = json.dumps(backup_data, default=str)
            compressed_data = gzip.compress(json_data.encode("utf-8"))

            # Generate S3 key
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            s3_key = f"database-backups/{timestamp}_execution_{execution_id}.json.gz"

            # Upload to S3
            upload_result = await s3_service.upload_file(
                file_contents=compressed_data,
                s3_key=s3_key,
                content_type="application/gzip",
                metadata={
                    "execution_id": str(execution_id),
                    "tables": ",".join(tables),
                    "timestamp": timestamp
                }
            )

            logger.info("backup_completed", s3_key=s3_key, size=len(compressed_data), tables=len(tables))

            return {
                "s3_key": s3_key,
                "file_size": len(compressed_data),
                "tables": tables,
                "etag": upload_result["etag"]
            }
        
        except Exception as e:
            logger.error("backup_failed", error=str(e))
            raise

    async def restore_from_backup(
        self, s3_key: str, execution_id: int
    ) -> Dict[str, Any]:
        """
        Restore database from S3 backup.

        Args:
            s3_key: S3 key of the backup file
            execution_id: SeederExecution ID

        Returns:
            Dict with restore statistics
        """
        try:
            logger.info("restore_started", s3_key=s3_key)

            # Download backup from S3
            compressed_data = await s3_service.download_file_as_bytes(s3_key)

            # Decompress and deserialize
            json_data = gzip.decompress(compressed_data).decode("utf-8")
            backup_data = json.loads(json_data)

            stats = {
                "tables_restored": 0,
                "records_restored": 0
            }

            # Restore each table
            for table, rows in backup_data.items():
                await self._import_table(table, rows)
                stats["tables_restored"] += 1
                stats["records_restored"] += len(rows)

            await self.db.commit()

            logger.info(
                "restore_completed", tables=stats["tables_restored"], records=stats["records_restored"]
            )

            return stats
        
        except Exception as e:
            await self.db.rollback()
            logger.error("restore_failed", error=str(e))
            raise

    async def _get_all_tables(self) -> List[str]:
        """Get list of all tables in database."""
        query = text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE',
            AND table_name != 'alembic_version
            ORDER BY table_name
        """)

        result = await self.db.execute(query)
        return [row[0] for row in result.fetchall()]
    
    async def _export_table(self, table: str) -> List[Dict[str, Any]]:
        """Export all rows from a table."""
        query = text(f"SELECT * FROM {table}")
        result = await self.db.execute(query)

        rows = []
        for row in result.fetchall():
            rows.append(dict(row._mapping))

        return rows
    
    async def _import_table(self, table: str, rows: List[Dict[str, Any]]) -> None:
        """Import rows into a table."""
        if not rows:
            return
        
        # Truncate table first
        await self.db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))

        # Insert rows
        for row in rows:
            columns = ", ".join(row.keys())
            placeholders = ", ".join([f":{key}" for key in row.keys()])
            query = text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})")
            await self.db.execute(query, row)


