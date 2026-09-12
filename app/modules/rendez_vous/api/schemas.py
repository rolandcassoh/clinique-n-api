"""Schémas Pydantic v2 pour l'API appointment."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.rendez_vous.domain.entites import AppointmentStatus, AppointmentType, PaymentStatus


# ---------------------------------------------------------------------------
# Requêtes
# ---------------------------------------------------------------------------


class BookAppointmentRequest(BaseModel):
    id_clinique: int
    id_medecin: int
    programme_le: datetime
    type: AppointmentType = AppointmentType.IN_PERSON
    passerelle_paiement: Optional[str] = None
    notes: Optional[str] = None
    est_suivi: bool = False
    id_rdv_parent: Optional[int] = None
    # Champs optionnels que le client peut passer (sinon 0 par défaut)
    honoraires_consultation: Decimal = Field(default=Decimal("0"), ge=0)
    session_duration: int = Field(default=30, ge=10, le=240)


class PayAppointmentRequest(BaseModel):
    passerelle: str = Field(..., description="stripe | razorpay | paypal | wallet")
    devise: str = Field(default="XAF", max_length=3)


class StripeIntentRequest(BaseModel):
    devise: str = Field(default="XAF", max_length=3)


class RazorpayOrderRequest(BaseModel):
    devise: str = Field(default="INR", max_length=3)


class RefundRequest(BaseModel):
    montant: Optional[Decimal] = Field(default=None, ge=0)


class ForceStatusRequest(BaseModel):
    statut: AppointmentStatus


class CancelRequest(BaseModel):
    motif: str = Field(..., min_length=5, max_length=500)


# ---------------------------------------------------------------------------
# Réponses
# ---------------------------------------------------------------------------


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference: str
    id_clinique: int
    id_medecin: int
    id_patient: int
    programme_le: datetime
    duree_minutes: int
    statut: AppointmentStatus
    type: AppointmentType
    montant: Decimal
    montant_avance: Decimal
    statut_paiement: PaymentStatus
    passerelle_paiement: Optional[str] = None
    notes: Optional[str] = None
    motif_annulation: Optional[str] = None
    est_suivi: bool
    id_rdv_parent: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class DoctorPatientSummary(BaseModel):
    """Résumé d'un patient vu par un médecin — dérivé de ses rendez-vous."""

    id_patient: int
    nom: str
    courriel: str
    telephone: Optional[str] = None
    nombre_rdv: int
    dernier_rdv: datetime
    dernier_statut: AppointmentStatus


class CancellationResponse(BaseModel):
    message: str
    is_full_refund: bool
    refund_amount: Decimal
    policy_applied: str


class PaymentStatusResponse(BaseModel):
    id_rendez_vous: int
    statut_paiement: str
    passerelle_paiement: Optional[str]
    montant: str
    transactions: list[dict]


class StatsResponse(BaseModel):
    by_status: dict[str, int]
    total_revenue: str


class StripeIntentResponse(BaseModel):
    client_secret: Optional[str]
    payment_intent_id: str


class RazorpayOrderResponse(BaseModel):
    id_commande: str
    montant: str
    devise: str
