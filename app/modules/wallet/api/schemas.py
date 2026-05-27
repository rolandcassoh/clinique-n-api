"""Schémas Pydantic v2 du module wallet."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WalletSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    balance: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime


class WalletHistorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wallet_id: int
    amount: Decimal
    type: str
    reference: Optional[str]
    description: Optional[str]
    balance_after: Decimal
    created_at: datetime
    updated_at: datetime


class TopUpRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Montant à créditer en XAF")
    gateway: str = Field(..., description="Passerelle de paiement (stripe, razorpay, etc.)")
    reference: Optional[str] = Field(None, description="Référence de transaction externe")


class PayAppointmentRequest(BaseModel):
    appointment_id: int = Field(..., description="ID du rendez-vous à payer")
    amount: Decimal = Field(..., gt=0, description="Montant du rendez-vous en XAF")
