"""Schémas Pydantic v2 du module facturation."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BillingItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_facture: int
    description: str
    quantite: int
    prix_unitaire: Decimal
    sous_total: Decimal
    taux_taxe: Decimal
    created_at: datetime
    updated_at: datetime


class BillingRecordSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_rendez_vous: int
    id_patient: int
    reference: str
    sous_total: Decimal
    montant_remise: Decimal
    montant_taxe: Decimal
    total: Decimal
    statut: str
    items: list[BillingItemSchema] = Field(default_factory=list)
    date_echeance: Optional[date]
    paye_le: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class BillingItemCreateRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    quantite: int = Field(default=1, gt=0)
    prix_unitaire: Decimal = Field(..., gt=0)
    taux_taxe: Decimal = Field(default=Decimal("0"), ge=0)


class CreateInvoiceRequest(BaseModel):
    items: list[BillingItemCreateRequest] = Field(..., min_length=1)
    montant_remise: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = None


class GetOrCreateInvoiceRequest(BaseModel):
    id_patient: int
    honoraires_consultation: Decimal = Field(..., gt=0)
    taux_taxe: Decimal = Field(default=Decimal("0"), ge=0)
    montant_remise: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = None


class UpdateBillingStatusRequest(BaseModel):
    statut: str = Field(..., pattern="^(issued|paid|cancelled)$")


class BillingStatsSchema(BaseModel):
    total_paid: float
    total_issued: float
    counts_by_status: dict[str, int]
