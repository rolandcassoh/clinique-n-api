"""Router principal du module appointment."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status as statut
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.core.cache.redis_client import get_redis
from app.database import get_db
from app.modules.rendez_vous.api.schemas import (
    AppointmentResponse,
    BookAppointmentRequest,
    CancelRequest,
    CancellationResponse,
    DoctorPatientSummary,
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
from app.modules.rendez_vous.application.cas_utilisation import (
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
from app.modules.rendez_vous.domain.exceptions import (
    AppointmentNotFoundError,
    AppointmentPermissionError,
    SlotNotAvailableError,
)
from app.modules.rendez_vous.domain.services import SlotAvailabilityService
from app.modules.rendez_vous.infrastructure.depots import (
    SQLAlchemyAppointmentRepository,
    SQLAlchemyAppointmentTransactionRepository,
)
from app.shared.exceptions.domain import EntityNotFoundError
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_payment_adapter(passerelle: str) -> Any:
    from app.core.payments.factory import get_payment_adapter
    return get_payment_adapter(passerelle)


def _make_apt_repo(db: AsyncSession) -> SQLAlchemyAppointmentRepository:
    return SQLAlchemyAppointmentRepository(db)


def _make_tx_repo(db: AsyncSession) -> SQLAlchemyAppointmentTransactionRepository:
    return SQLAlchemyAppointmentTransactionRepository(db)


async def _resolve_id_medecin(user: dict, db: AsyncSession) -> int:
    """Résout medecins.id à partir de l'utilisateur connecté.

    Les endpoints "médecin" de ce routeur confondaient auparavant
    utilisateurs.id (l'identifiant du compte connecté) avec medecins.id
    (la ligne de profil médecin liée à ce compte) — deux espaces d'id
    distincts. Un admin appelant ces routes n'a pas de profil médecin :
    on retombe alors sur user["id"] pour ne pas casser son accès.
    """
    from sqlalchemy import select

    from app.modules.clinic.infrastructure.modeles import DoctorModel

    q = select(DoctorModel.id).where(DoctorModel.id_utilisateur == user["id"])
    id_medecin = (await db.execute(q)).scalar_one_or_none()
    if id_medecin is None:
        return user["id"]
    return id_medecin


# ---------------------------------------------------------------------------
# Patient endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/rendez-vous",
    status_code=statut.HTTP_201_CREATED,
    response_model=AppointmentResponse,
    tags=["Rendez-vous"],
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
        id_clinique=body.id_clinique,
        id_medecin=body.id_medecin,
        id_patient=user["id"],
        programme_le=body.programme_le,
        type=body.type,
        passerelle_paiement=body.passerelle_paiement,
        notes=body.notes,
        est_suivi=body.est_suivi,
        id_rdv_parent=body.id_rdv_parent,
        honoraires_consultation=body.honoraires_consultation,
        session_duration=body.session_duration,
    )
    try:
        appointment = await use_case.execute(cmd)
    except SlotNotAvailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflit lors de la création du rendez-vous (référence en double). Veuillez réessayer.",
        ) from exc
    return AppointmentResponse(**appointment.__dict__)


@router.get(
    "/rendez-vous",
    response_model=Page[AppointmentResponse],
    tags=["Rendez-vous"],
)
async def list_my_appointments(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="statut"),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Page[AppointmentResponse]:
    repo = _make_apt_repo(db)
    params = PaginationParams(page=page, per_page=per_page)
    appointments, total = await repo.list_for_patient(
        id_patient=user["id"],
        params=params,
        statut=status_filter,
        date_from=date_from,
        date_to=date_to,
    )
    data = [AppointmentResponse(**apt.__dict__) for apt in appointments]
    return Page.create(data=data, total=total, params=params)


@router.get(
    "/rendez-vous/{id_rendez_vous}",
    response_model=AppointmentResponse,
    tags=["Rendez-vous"],
)
async def get_appointment(
    id_rendez_vous: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    repo = _make_apt_repo(db)
    appointment = await repo.find_by_id(id_rendez_vous)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable")
    # Vérif accès : patient ou médecin concerné
    if appointment.id_patient != user["id"] and appointment.id_medecin != user["id"]:
        if "admin" not in user.get("roles", []):
            raise HTTPException(status_code=403, detail="Accès refusé")
    return AppointmentResponse(**appointment.__dict__)


@router.delete(
    "/rendez-vous/{id_rendez_vous}",
    response_model=CancellationResponse,
    tags=["Rendez-vous"],
)
async def cancel_my_appointment(
    id_rendez_vous: int,
    body: CancelRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Any = Depends(get_redis),
) -> CancellationResponse:
    repo = _make_apt_repo(db)
    use_case = CancelAppointmentUseCase(repo=repo, redis=redis)
    try:
        result = await use_case.execute(
            id_rendez_vous=id_rendez_vous,
            id_utilisateur=user["id"],
            motif=body.motif,
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
    "/medecin/rendez-vous",
    response_model=Page[AppointmentResponse],
    tags=["Rendez-vous Medecin"],
)
async def list_doctor_appointments(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="statut"),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    user: dict = Depends(require_role("doctor", "admin")),
    db: AsyncSession = Depends(get_db),
) -> Page[AppointmentResponse]:
    repo = _make_apt_repo(db)
    id_medecin = await _resolve_id_medecin(user, db)
    params = PaginationParams(page=page, per_page=per_page)
    appointments, total = await repo.list_for_doctor(
        id_medecin=id_medecin,
        params=params,
        date_from=date_from,
        date_to=date_to,
        statut=status_filter,
    )
    data = [AppointmentResponse(**apt.__dict__) for apt in appointments]
    return Page.create(data=data, total=total, params=params)


@router.get(
    "/medecin/patients",
    response_model=Page[DoctorPatientSummary],
    tags=["Rendez-vous Medecin"],
)
async def list_doctor_patients(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(require_role("doctor", "admin")),
    db: AsyncSession = Depends(get_db),
) -> Page[DoctorPatientSummary]:
    """Patients distincts ayant eu (ou ayant) un rendez-vous avec le médecin connecté.

    Aucun module « patient » propre au médecin n'existe côté API : cette liste est
    dérivée des rendez-vous du médecin (id_patient), croisés avec les comptes
    utilisateurs pour le nom/courriel/téléphone.
    """
    from sqlalchemy import func, select

    from app.modules.auth.infrastructure.modeles import UserModel
    from app.modules.rendez_vous.infrastructure.modeles import AppointmentModel

    id_medecin = await _resolve_id_medecin(user, db)

    sous_requete = (
        select(
            AppointmentModel.id_patient.label("id_patient"),
            func.count(AppointmentModel.id).label("nombre_rdv"),
            func.max(AppointmentModel.programme_le).label("dernier_rdv"),
        )
        .where(
            AppointmentModel.id_medecin == id_medecin,
            AppointmentModel.deleted_at.is_(None),
        )
        .group_by(AppointmentModel.id_patient)
        .subquery()
    )

    total: int = (
        await db.execute(select(func.count()).select_from(sous_requete))
    ).scalar_one()

    params = PaginationParams(page=page, per_page=per_page)
    requete = (
        select(
            sous_requete.c.id_patient,
            sous_requete.c.nombre_rdv,
            sous_requete.c.dernier_rdv,
            UserModel.nom,
            UserModel.courriel,
            UserModel.telephone,
        )
        .join(UserModel, UserModel.id == sous_requete.c.id_patient)
        .order_by(sous_requete.c.dernier_rdv.desc())
        .offset(params.offset)
        .limit(params.per_page)
    )
    lignes = (await db.execute(requete)).all()

    # Dernier statut de rendez-vous par patient (requête simple par ligne — page courte)
    id_patients = [ligne.id_patient for ligne in lignes]
    derniers_statuts: dict[int, str] = {}
    if id_patients:
        for id_patient in id_patients:
            statut_req = (
                select(AppointmentModel.statut)
                .where(
                    AppointmentModel.id_medecin == id_medecin,
                    AppointmentModel.id_patient == id_patient,
                    AppointmentModel.deleted_at.is_(None),
                )
                .order_by(AppointmentModel.programme_le.desc())
                .limit(1)
            )
            derniers_statuts[id_patient] = (await db.execute(statut_req)).scalar_one()

    data = [
        DoctorPatientSummary(
            id_patient=ligne.id_patient,
            nom=ligne.nom,
            courriel=ligne.courriel,
            telephone=ligne.telephone,
            nombre_rdv=ligne.nombre_rdv,
            dernier_rdv=ligne.dernier_rdv,
            dernier_statut=derniers_statuts[ligne.id_patient],
        )
        for ligne in lignes
    ]
    return Page.create(data=data, total=total, params=params)


@router.patch(
    "/medecin/rendez-vous/{id_rendez_vous}/confirmer",
    response_model=AppointmentResponse,
    tags=["Rendez-vous Medecin"],
)
async def confirm_appointment(
    id_rendez_vous: int,
    user: dict = Depends(require_role("doctor", "admin")),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    repo = _make_apt_repo(db)
    use_case = ConfirmAppointmentUseCase(repo=repo)
    id_medecin = await _resolve_id_medecin(user, db)
    try:
        appointment = await use_case.execute(id_rendez_vous=id_rendez_vous, id_medecin=id_medecin)
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AppointmentPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return AppointmentResponse(**appointment.__dict__)


@router.patch(
    "/medecin/rendez-vous/{id_rendez_vous}/terminer",
    response_model=AppointmentResponse,
    tags=["Rendez-vous Medecin"],
)
async def complete_appointment(
    id_rendez_vous: int,
    user: dict = Depends(require_role("doctor", "admin")),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    repo = _make_apt_repo(db)
    use_case = CompleteAppointmentUseCase(repo=repo)
    id_medecin = await _resolve_id_medecin(user, db)
    try:
        appointment = await use_case.execute(id_rendez_vous=id_rendez_vous, id_medecin=id_medecin)
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AppointmentPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return AppointmentResponse(**appointment.__dict__)


@router.patch(
    "/medecin/rendez-vous/{id_rendez_vous}/absent",
    response_model=AppointmentResponse,
    tags=["Rendez-vous Medecin"],
)
async def mark_no_show(
    id_rendez_vous: int,
    user: dict = Depends(require_role("doctor", "admin")),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    repo = _make_apt_repo(db)
    use_case = MarkNoShowUseCase(repo=repo)
    id_medecin = await _resolve_id_medecin(user, db)
    try:
        appointment = await use_case.execute(id_rendez_vous=id_rendez_vous, id_medecin=id_medecin)
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
    "/rendez-vous/{id_rendez_vous}/payer",
    tags=["Paiements Rendez-vous"],
)
async def pay_appointment(
    id_rendez_vous: int,
    body: PayAppointmentRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = _make_apt_repo(db)
    tx_repo = _make_tx_repo(db)
    adapter = _get_payment_adapter(body.passerelle)
    use_case = PayAppointmentUseCase(repo=repo, tx_repo=tx_repo, payment_adapter=adapter)
    try:
        return await use_case.execute(
            id_rendez_vous=id_rendez_vous,
            id_patient=user["id"],
            passerelle=body.passerelle,
            devise=body.devise,
        )
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AppointmentPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/rendez-vous/{id_rendez_vous}/statut-paiement",
    response_model=PaymentStatusResponse,
    tags=["Paiements Rendez-vous"],
)
async def get_payment_status(
    id_rendez_vous: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentStatusResponse:
    repo = _make_apt_repo(db)
    tx_repo = _make_tx_repo(db)
    use_case = GetPaymentStatusUseCase(repo=repo, tx_repo=tx_repo)
    try:
        result = await use_case.execute(id_rendez_vous=id_rendez_vous, id_utilisateur=user["id"])
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AppointmentPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return PaymentStatusResponse(**result)


@router.post(
    "/rendez-vous/{id_rendez_vous}/intention-stripe",
    response_model=StripeIntentResponse,
    tags=["Paiements Rendez-vous"],
)
async def create_stripe_intent(
    id_rendez_vous: int,
    body: StripeIntentRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StripeIntentResponse:
    from app.core.payments.adapters.stripe_adapter import StripeAdapter

    repo = _make_apt_repo(db)
    use_case = CreateStripeIntentUseCase(repo=repo, stripe_adapter=StripeAdapter())
    try:
        result = await use_case.execute(
            id_rendez_vous=id_rendez_vous,
            id_patient=user["id"],
            devise=body.devise,
        )
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AppointmentPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return StripeIntentResponse(**result)


@router.post(
    "/rendez-vous/{id_rendez_vous}/commande-razorpay",
    response_model=RazorpayOrderResponse,
    tags=["Paiements Rendez-vous"],
)
async def create_razorpay_order(
    id_rendez_vous: int,
    body: RazorpayOrderRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RazorpayOrderResponse:
    from app.core.payments.adapters.razorpay_adapter import RazorpayAdapter

    repo = _make_apt_repo(db)
    use_case = CreateRazorpayOrderUseCase(repo=repo, razorpay_adapter=RazorpayAdapter())
    try:
        result = await use_case.execute(
            id_rendez_vous=id_rendez_vous,
            id_patient=user["id"],
            devise=body.devise,
        )
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AppointmentPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return RazorpayOrderResponse(**result)


@router.post(
    "/rendez-vous/{id_rendez_vous}/rembourser",
    tags=["Paiements Rendez-vous"],
)
async def refund_appointment(
    id_rendez_vous: int,
    body: RefundRequest,
    user: dict = Depends(require_role("admin", "super-admin")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = _make_apt_repo(db)
    tx_repo = _make_tx_repo(db)
    appointment = await repo.find_by_id(id_rendez_vous)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable")
    passerelle = appointment.passerelle_paiement or "stripe"
    adapter = _get_payment_adapter(passerelle)
    use_case = RefundAppointmentUseCase(repo=repo, tx_repo=tx_repo, payment_adapter=adapter)
    try:
        return await use_case.execute(id_rendez_vous=id_rendez_vous, montant=body.montant)
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/admin/rendez-vous",
    response_model=Page[AppointmentResponse],
    tags=["Admin Rendez-vous"],
)
async def admin_list_appointments(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="statut"),
    id_medecin: Optional[int] = Query(default=None),
    id_patient: Optional[int] = Query(default=None),
    id_clinique: Optional[int] = Query(default=None),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    _user: dict = Depends(require_role("admin", "super-admin")),
    db: AsyncSession = Depends(get_db),
) -> Page[AppointmentResponse]:
    repo = _make_apt_repo(db)
    params = PaginationParams(page=page, per_page=per_page)
    appointments, total = await repo.list_all(
        params=params,
        statut=status_filter,
        id_medecin=id_medecin,
        id_patient=id_patient,
        id_clinique=id_clinique,
        date_from=date_from,
        date_to=date_to,
    )
    data = [AppointmentResponse(**apt.__dict__) for apt in appointments]
    return Page.create(data=data, total=total, params=params)


@router.patch(
    "/admin/rendez-vous/{id_rendez_vous}/statut",
    response_model=AppointmentResponse,
    tags=["Admin Rendez-vous"],
)
async def admin_force_status(
    id_rendez_vous: int,
    body: ForceStatusRequest,
    _user: dict = Depends(require_role("admin", "super-admin")),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    repo = _make_apt_repo(db)
    use_case = ForceStatusUseCase(repo=repo)
    try:
        appointment = await use_case.execute(
            id_rendez_vous=id_rendez_vous, new_status=body.statut.value
        )
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return AppointmentResponse(**appointment.__dict__)


@router.get(
    "/admin/rendez-vous/statistiques",
    response_model=StatsResponse,
    tags=["Admin Rendez-vous"],
)
async def admin_stats(
    id_clinique: Optional[int] = Query(default=None),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    _user: dict = Depends(require_role("admin", "super-admin")),
    db: AsyncSession = Depends(get_db),
) -> StatsResponse:
    repo = _make_apt_repo(db)
    use_case = GetStatsUseCase(repo=repo)
    result = await use_case.execute(
        id_clinique=id_clinique, date_from=date_from, date_to=date_to
    )
    return StatsResponse(**result)


@router.get(
    "/admin/rendez-vous/{id_rendez_vous}/facture",
    tags=["Admin Rendez-vous"],
)
async def admin_get_invoice(
    id_rendez_vous: int,
    _user: dict = Depends(require_role("admin", "super-admin")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Délégué au module billing — retourne un lien stub."""
    repo = _make_apt_repo(db)
    appointment = await repo.find_by_id(id_rendez_vous)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable")
    return {
        "id_rendez_vous": id_rendez_vous,
        "invoice_url": f"/api/billing/invoices/appointment/{id_rendez_vous}",
        "reference": appointment.reference,
    }
