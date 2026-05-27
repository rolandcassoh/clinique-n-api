"""Router FastAPI du module RequestService."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.request_service.api.schemas import (
    RequestServiceCreateRequest,
    RequestServiceSchema,
    RequestServiceStatusUpdateRequest,
)
from app.modules.request_service.application.use_cases import (
    CancelRequestServiceUseCase,
    CreateRequestServiceUseCase,
    GetMyRequestServiceUseCase,
    ListAllRequestServicesUseCase,
    ListMyRequestServicesUseCase,
    UpdateRequestServiceStatusUseCase,
)
from app.modules.request_service.domain.entities import RequestServiceStatus
from app.modules.request_service.domain.exceptions import (
    RequestServiceAccessDeniedError,
    RequestServiceCannotCancelError,
    RequestServiceNotFoundError,
)
from app.modules.request_service.infrastructure.repositories import (
    SQLAlchemyRequestServiceRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["RequestServices"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
UserDep = Annotated[dict[str, Any], Depends(get_current_user)]
AdminDep = Annotated[dict[str, Any], Depends(require_role("admin", "super-admin"))]


def _repo(db: DbDep) -> SQLAlchemyRequestServiceRepository:
    return SQLAlchemyRequestServiceRepository(db)


# ---------------------------------------------------------------------------
# Patient — Mes demandes
# ---------------------------------------------------------------------------

@router.post(
    "/request-services",
    response_model=RequestServiceSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_request_service(
    payload: RequestServiceCreateRequest,
    current_user: UserDep,
    repo: SQLAlchemyRequestServiceRepository = Depends(_repo),
) -> RequestServiceSchema:
    uc = CreateRequestServiceUseCase(repo)
    req = await uc.execute(user_id=current_user["id"], **payload.model_dump())
    return RequestServiceSchema.model_validate(req)


@router.get("/request-services", response_model=Page[RequestServiceSchema])
async def list_my_request_services(
    current_user: UserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyRequestServiceRepository = Depends(_repo),
) -> Page[RequestServiceSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListMyRequestServicesUseCase(repo)
    return await uc.execute(user_id=current_user["id"], params=params)  # type: ignore[return-value]


@router.get("/request-services/{request_id}", response_model=RequestServiceSchema)
async def get_my_request_service(
    request_id: int,
    current_user: UserDep,
    repo: SQLAlchemyRequestServiceRepository = Depends(_repo),
) -> RequestServiceSchema:
    uc = GetMyRequestServiceUseCase(repo)
    try:
        req = await uc.execute(request_id=request_id, user_id=current_user["id"])
    except RequestServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except RequestServiceAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message) from exc
    return RequestServiceSchema.model_validate(req)


@router.delete(
    "/request-services/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_my_request_service(
    request_id: int,
    current_user: UserDep,
    repo: SQLAlchemyRequestServiceRepository = Depends(_repo),
) -> None:
    uc = CancelRequestServiceUseCase(repo)
    try:
        await uc.execute(request_id=request_id, user_id=current_user["id"])
    except RequestServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except RequestServiceAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message) from exc
    except RequestServiceCannotCancelError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@router.get(
    "/admin/request-services",
    response_model=Page[RequestServiceSchema],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_list_request_services(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[RequestServiceStatus | None, Query(alias="status")] = None,
    repo: SQLAlchemyRequestServiceRepository = Depends(_repo),
) -> Page[RequestServiceSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListAllRequestServicesUseCase(repo)
    return await uc.execute(params=params, status=status_filter)  # type: ignore[return-value]


@router.patch(
    "/admin/request-services/{request_id}/status",
    response_model=RequestServiceSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_request_service_status(
    request_id: int,
    payload: RequestServiceStatusUpdateRequest,
    repo: SQLAlchemyRequestServiceRepository = Depends(_repo),
) -> RequestServiceSchema:
    uc = UpdateRequestServiceStatusUseCase(repo)
    try:
        req = await uc.execute(request_id=request_id, new_status=payload.status)
    except RequestServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return RequestServiceSchema.model_validate(req)
