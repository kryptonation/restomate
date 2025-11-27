# app/modules/seeder/router.py

from typing import Optional

from fastapi import APIRouter, Depends, status, Query

from app.database import get_db
from app.dependencies import ActiveUser, require_permission
from app.modules.seeder.services import SeederService
from app.modules.seeder.schemas import (
    SeederExecutionResponse, SeederExecutionRequest,
    SeederRestoreRequest, SeederExecutionListResponse,
    SeederResultResponse, DatabaseResetResponse,
    DatabaseRestoreResponse
)
from app.modules.seeder.models import SeederStatus

router = APIRouter(prefix="/seeders", tags=["seeders"])


def get_seeder_service(db=Depends(get_db)) -> SeederService:
    """Dependency to get seeder service."""
    return SeederService(db)


@router.post(
    "/execute",
    response_model=SeederResultResponse,
    status_code=status.HTTP_200_OK,
)
async def execute_seeder(
    request: SeederExecutionRequest,
    current_user: ActiveUser,
    service: SeederService = Depends(get_seeder_service),
    _: None = Depends(require_permission("seeders", "execute"))
):
    """
    Execute all database seeders.

    **Requires permission:** seeders:execute

    This will:
    - Create a backup (if requested)
    - Run all seeders in sequence
    - Return execution results
    """
    return await service.execute_seeder(
        create_backup=request.create_backup,
        user_id=current_user.id
    )

@router.post(
    "/reset",
    response_model=DatabaseResetResponse,
    status_code=status.HTTP_200_OK,
)
async def reset_database(
    current_user: ActiveUser,
    service: SeederService = Depends(get_seeder_service),
    _: None = Depends(require_permission("seeders", "execute"))
):
    """
    Reset database and re-run all seeders.

    **Requires permission:** seeders:execute

    **WARNING:** This will delete all data and recreate from seeders.
    A backup is automatically created before reset.
    """
    return await service.reset_database(user_id=current_user.id)

@router.post(
    "/restore",
    response_model=DatabaseRestoreResponse,
    status_code=status.HTTP_200_OK
)
async def restore_database(
    request: SeederRestoreRequest,
    current_user: ActiveUser,
    service: SeederService = Depends(get_seeder_service),
    _: None = Depends(require_permission("seeders", "execute"))
):
    """
    Restore database from backup.

    **Requires permission:** seeders:execute

    Provide either `s3_key` or `execution_id`. If neither is provided,
    the latest successful backup will be used.
    """
    return await service.restore_from_backup(
        s3_key=request.s3_key,
        execution_id=request.execution_id,
        user_id=current_user.id
    )

@router.get(
    "/",
    response_model=SeederExecutionListResponse
)
async def list_seeder_executions(
    current_user: ActiveUser,
    service: SeederService = Depends(get_seeder_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    seeder_name: Optional[str] = None,
    status: Optional[SeederStatus] = None,
    _: None = Depends(require_permission("seeders", "read"))
):
    """
    List seeder execution history.

    **Requires permission:** seeders:read
    """
    executions, total = await service.list_executions(
        skip=skip, limit=limit, seeder_name=seeder_name, status=status
    )

    return {
        "executions": executions,
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit
    }

@router.get(
    "/{execution_id}",
    response_model=SeederExecutionResponse
)
async def get_seeder_execution(
    execution_id: int,
    current_user: ActiveUser,
    service: SeederService = Depends(get_seeder_service),
    _: None = Depends(require_permission("seeders", "read"))
):
    """
    Get seeder execution details.

    **Requires permission:** seeders:read
    """
    return await service.get_execution(execution_id=execution_id)

