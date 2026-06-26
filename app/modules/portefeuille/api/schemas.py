"""Schémas Pydantic v2 du module wallet."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WalletSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_utilisateur: int
    solde: Decimal
    devise: str
    created_at: datetime
    updated_at: datetime


class WalletHistorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_portefeuille: int
    montant: Decimal
    type: str
    reference: Optional[str]
    description: Optional[str]
    solde_apres: Decimal
    created_at: datetime
    updated_at: datetime


class TopUpRequest(BaseModel):
    montant: Decimal = Field(..., gt=0, description="Montant à créditer en XAF")
    passerelle: str = Field(..., description="Passerelle de paiement (stripe, razorpay, etc.)")
    reference: Optional[str] = Field(None, description="Référence de transaction externe")


class PayAppointmentRequest(BaseModel):
    id_rendez_vous: int = Field(..., description="ID du rendez-vous à payer")
    montant: Decimal = Field(..., gt=0, description="Montant du rendez-vous en XAF")
