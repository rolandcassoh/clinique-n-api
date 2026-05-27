"""Router principal du module appointment."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.core.cache.redis_client import get_redis
from app.database import get_db
from app.modules.appointment.api.schemas import (
    AppointmentResponse,
    BookAppointmentRequest,
    CancelRequest,
    CancellationResponse,
    ForceStatusRequest,
    PayAppointmentRequest,
    PaymentStatusResponse,
    RazorpayOrderRequest,
    RazorpayOrderResponse,
    RefundRequest,
    StatsResponse,
    StripeIntentRequest,
    StripeIntentResponse,
)
from app.modules.appointment.application.use_cases import (
    BookAppointmentCommand,
    BookAppointmentUseCase,
    CancelAppointmentUseCase,
    CompleteAppointmentUseCase,
    ConfirmAppointmentUseCase,
    CreateRazorpayOrderUseCase,
    CreateStripeIntentUseCase,
    ForceStatusUseCase,
    GetPaymentStatusUseCase,
    GetStatsUseCase,
    MarkNoShowUseCase,
    PayAppointmentUseCase,
    RefundAppointmentUseCase,
)
from app.modules.appointment.domain.exceptions import (
    AppointmentNotFoundError,
    AppointmentPermissionError,
    SlotNotAvailableError,
)
from app.modules.appointment.domain.services import SlotAvailabilityService
from app.modules.appointment.infrastructure.repositories import (
    SQLAlchemyAppointmentRepository,
    SQLAlchemyAppointmentTransactionRepository,
)
from app.shared.exceptions.domain import EntityNotFoundError
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_payment_adapter(gateway: str) -> Any:
    from app.core.payments.factory import get_payment_adapter
    return get_payment_adapter(gateway)


def _make_apt_repo(db: AsyncSession) -> SQLAlchemyAppointmentRepository:
    return SQLAlchemyAppointmentRepository(db)


def _make_tx_repo(db: AsyncSession) -> SQLAlchemyAppointmentTransactionRepository:
    return SQLAlchemyAppointmentTransactionRepository(db)


# ---------------------------------------------------------------------------
# Patient endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/appointments",
    status_code=status.HTTP_201_CREATED,
    response_model=AppointmentResponse,
    tags=["Appointments"],
)
async def book_appointment(
    body: BookAppointmentRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Any = Depends(get_redis),
) -> AppointmentResponse:
    repo = _make_apt_repo(db)
    slot_service = SlotAvailabilityService()
    use_case = BookAppointmentUseCase(repo=repo, slot_service=slot_service, redis=redis)
    cmd = BookAppointmentCommand(
        clinic_id=body.clinic_id,
        doctor_id=body.doctor_id,
        patient_id=user["id"],
        scheduled_at=body.scheduled_at,
        type=body.type,
        payment_gateway=body.payment_gateway,
        notes=body.notes,
        is_followup=body.is_followup,
        parent_appointment_id=body.parent_appointment_id,
        consultation_fee=body.consultation_fee,
        session_duration=body.session_duration,
    )
    try:
        appointment = await use_case.execute(cmd)
    except SlotNotAvailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return AppointmentResponse(**appointment.__dict__)


@router.get(
    "/appointments",
    response_model=Page[AppointmentResponse],
    tags=["Appointments"],
)
async def list_my_appointments(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Page[AppointmentResponse]:
    repo = _make_apt_repo(db)
    params = PaginationParams(page=page, per_page=per_page)
    appointments, total = await repo.list_for_patient(
        patient_id=user["id"],
        params=params,
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
    )
    data = [AppointmentResponse(**apt.__dict__) for apt in appointments]
    return Page.create(data=data, total=total, params=params)


@router.get(
    "/appointments/{appointment_id}",
    response_model=AppointmentResponse,
    tags=["Appointments"],
)
async def get_appointment(
    appointment_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    repo = _make_apt_repo(db)
    appointment = await repo.find_by_id(appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable")
    # Vérif accès : patient ou médecin concerné
    if appointment.patient_id != user["id"] and appointment.doctor_id != user["id"]:
        if "admin" not in user.get("roles", []):
            raise HTTPException(status_code=403, detail="Accès refusé")
    return AppointmentResponse(**appointment.__dict__)


@router.delete(
    "/appointments/{appointment_id}",
    response_model=CancellationResponse,
    tags=["Appointments"],
)
async def cancel_my_appointment(
    appointment_id: int,
    body: CancelRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Any = Depends(get_redis),
) -> CancellationResponse:
    repo = _make_apt_repo(db)
    use_case = CancelAppointmentUseCase(repo=repo, redis=redis)
    try:
        result = await use_case.execute(
            appointment_id=appointment_id,
            user_id=user["id"],
            reason=body.reason,
        )
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AppointmentPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return CancellationResponse(
        message="Rendez-vous annulé avec succès.",
        is_full_refund=result.is_full_refund,
        refund_amount=result.refund_amount,
        policy_applied=result.policy_applied,
    )


# ---------------------------------------------------------------------------
# Doctor endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/doctor/appointments",
    response_model=Page[AppointmentResponse],
    tags=["Doctor Appointments"],
)
async def list_doctor_appointments(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    user: dict = Depends(require_role("doctor", "admin")),
    db: AsyncSession = Depends(get_db),
) -> Page[AppointmentResponse]:
    repo = _make_apt_repo(db)
    params = PaginationParams(page=page, per_page=per_page)
    appointments, total = await repo.list_for_doctor(
        doctor_id=user["id"],
        params=params,
        date_from=date_from,
        date_to=date_to,
        status=status_filter,
    )
    data = [AppointmentResponse(**apt.__dict__) for apt in appointments]
    return Page.create(data=data, total=total, params=params)


@router.patch(
    "/doctor/appointments/{appointment_id}/confirm",
    response_model=AppointmentResponse,
    tags=["Doctor Appointments"],
)
async def confirm_appointment(
    appointment_id: int,
    user: dict = Depends(require_role("doctor", "admin")),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    repo = _make_apt_repo(db)
    use_case = ConfirmAppointmentUseCase(repo=repo)
    try:
        appointment = await use_case.execute(appointment_id=appointment_id, doctor_id=user["id"])
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AppointmentPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return AppointmentResponse(**appointment.__dict__)


@router.patch(
    "/doctor/appointments/{appointment_id}/complete",
    response_model=AppointmentResponse,
    tags=["Doctor Appointments"],
)
async def complete_appointment(
    appointment_id: int,
    user: dict = Depends(require_role("doctor", "admin")),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    repo = _make_apt_repo(db)
    use_case = CompleteAppointmentUseCase(repo=repo)
    try:
        appointment = await use_case.execute(appointment_id=appointment_id, doctor_id=user["id"])
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AppointmentPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return AppointmentResponse(**appointment.__dict__)


@router.patch(
    "/doctor/appointments/{appointment_id}/no-show",
    response_model=AppointmentResponse,
    tags=["Doctor Appointments"],
)
async def mark_no_show(
    appointment_id: int,
    user: dict = Depends(require_role("doctor", "admin")),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    repo = _make_apt_repo(db)
    use_case = MarkNoShowUseCase(repo=repo)
    try:
        appointment = await use_case.execute(appointment_id=appointment_id, doctor_id=user["id"])
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AppointmentPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return AppointmentResponse(**appointment.__dict__)


# ---------------------------------------------------------------------------
# Payment endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/appointments/{appointment_id}/pay",
    tags=["Appointment Payments"],
)
async def pay_appointment(
    appointment_id: int,
    body: PayAppointmentRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = _make_apt_repo(db)
    tx_repo = _make_tx_repo(db)
    adapter = _get_payment_adapter(body.gateway)
    use_case = PayAppointmentUseCase(repo=repo, tx_repo=tx_repo, payment_adapter=adapter)
    try:
        return await use_case.execute(
            appointment_id=appointment_id,
            patient_id=user["id"],
            gateway=body.gateway,
            currency=body.currency,
        )
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AppointmentPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/appointments/{appointment_id}/payment-status",
    response_model=PaymentStatusResponse,
    tags=["Appointment Payments"],
)
async def get_payment_status(
    appointment_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentStatusResponse:
    repo = _make_apt_repo(db)
    tx_repo = _make_tx_repo(db)
    use_case = GetPaymentStatusUseCase(repo=repo, tx_repo=tx_repo)
    try:
        result = await use_case.execute(appointment_id=appointment_id, user_id=user["id"])
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AppointmentPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return PaymentStatusResponse(**result)


@router.post(
    "/appointments/{appointment_id}/stripe-intent",
    response_model=StripeIntentResponse,
    tags=["Appointment Payments"],
)
async def create_stripe_intent(
    appointment_id: int,
    body: StripeIntentRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StripeIntentResponse:
    from app.core.payments.adapters.stripe_adapter import StripeAdapter

    repo = _make_apt_repo(db)
    use_case = CreateStripeIntentUseCase(repo=repo, stripe_adapter=StripeAdapter())
    try:
        result = await use_case.execute(
            appointment_id=appointment_id,
            patient_id=user["id"],
            currency=body.currency,
        )
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AppointmentPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return StripeIntentResponse(**result)


@router.post(
    "/appointments/{appointment_id}/razorpay-order",
    response_model=RazorpayOrderResponse,
    tags=["Appointment Payments"],
)
async def create_razorpay_order(
    appointment_id: int,
    body: RazorpayOrderRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RazorpayOrderResponse:
    from app.core.payments.adapters.razorpay_adapter import RazorpayAdapter

    repo = _make_apt_repo(db)
    use_case = CreateRazorpayOrderUseCase(repo=repo, razorpay_adapter=RazorpayAdapter())
    try:
        result = await use_case.execute(
            appointment_id=appointment_id,
            patient_id=user["id"],
            currency=body.currency,
        )
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AppointmentPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return RazorpayOrderResponse(**result)


@router.post(
    "/appointments/{appointment_id}/refund",
    tags=["Appointment Payments"],
)
async def refund_appointment(
    appointment_id: int,
    body: RefundRequest,
    user: dict = Depends(require_role("admin", "super-admin")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = _make_apt_repo(db)
    tx_repo = _make_tx_repo(db)
    appointment = await repo.find_by_id(appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable")
    gateway = appointment.payment_gateway or "stripe"
    adapter = _get_payment_adapter(gateway)
    use_case = RefundAppointmentUseCase(repo=repo, tx_repo=tx_repo, payment_adapter=adapter)
    try:
        return await use_case.execute(appointment_id=appointment_id, amount=body.amount)
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/admin/appointments",
    response_model=Page[AppointmentResponse],
    tags=["Admin Appointments"],
)
async def admin_list_appointments(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    doctor_id: Optional[int] = Query(default=None),
    patient_id: Optional[int] = Query(default=None),
    clinic_id: Optional[int] = Query(default=None),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    _user: dict = Depends(require_role("admin", "super-admin")),
    db: AsyncSession = Depends(get_db),
) -> Page[AppointmentResponse]:
    repo = _make_apt_repo(db)
    params = PaginationParams(page=page, per_page=per_page)
    appointments, total = await repo.list_all(
        params=params,
        status=status_filter,
        doctor_id=doctor_id,
        patient_id=patient_id,
        clinic_id=clinic_id,
        date_from=date_from,
        date_to=date_to,
    )
    data = [AppointmentResponse(**apt.__dict__) for apt in appointments]
    return Page.create(data=data, total=total, params=params)


@router.patch(
    "/admin/appointments/{appointment_id}/status",
    response_model=AppointmentResponse,
    tags=["Admin Appointments"],
)
async def admin_force_status(
    appointment_id: int,
    body: ForceStatusRequest,
    _user: dict = Depends(require_role("admin", "super-admin")),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    repo = _make_apt_repo(db)
    use_case = ForceStatusUseCase(repo=repo)
    try:
        appointment = await use_case.execute(
            appointment_id=appointment_id, new_status=body.status.value
        )
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return AppointmentResponse(**appointment.__dict__)


@router.get(
    "/admin/appointments/stats",
    response_model=StatsResponse,
    tags=["Admin Appointments"],
)
async def admin_stats(
    clinic_id: Optional[int] = Query(default=None),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    _user: dict = Depends(require_role("admin", "super-admin")),
    db: AsyncSession = Depends(get_db),
) -> StatsResponse:
    repo = _make_apt_repo(db)
    use_case = GetStatsUseCase(repo=repo)
    result = await use_case.execute(
        clinic_id=clinic_id, date_from=date_from, date_to=date_to
    )
    return StatsResponse(**result)


@router.get(
    "/admin/appointments/{appointment_id}/invoice",
    tags=["Admin Appointments"],
)
async def admin_get_invoice(
    appointment_id: int,
    _user: dict = Depends(require_role("admin", "super-admin")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Délégué au module billing — retourne un lien stub."""
    repo = _make_apt_repo(db)
    appointment = await repo.find_by_id(appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable")
    return {
        "appointment_id": appointment_id,
        "invoice_url": f"/api/billing/invoices/appointment/{appointment_id}",
        "reference": appointment.reference,
    }
