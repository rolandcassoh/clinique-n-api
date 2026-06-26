"""Cas d'utilisation du module billing."""
from __future__ import annotations

import random
import string
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from app.core.pdf.invoice_generator import InvoiceGenerator
from app.modules.facturation.domain.entites import BillingRecord, BillingStatus
from app.modules.facturation.domain.exceptions import (
    BillingNotFoundError,
    InvoiceAlreadyExistsError,
    InvalidStatusTransitionError,
)
from app.modules.facturation.domain.depots import BillingRepository
from app.shared.schemas.pagination import Page, PaginationParams


def _generate_reference() -> str:
    """Génère une référence facture INV-{YYYYMMDD}-{6 chiffres aléatoires}."""
    date_part = datetime.utcnow().strftime("%Y%m%d")
    rand_part = "".join(random.choices(string.digits, k=6))
    return f"INV-{date_part}-{rand_part}"


class GetOrCreateInvoiceUseCase:
    """Récupère la facture d'un RDV ou la crée automatiquement si absente."""

    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_rendez_vous: int,
        id_patient: int,
        honoraires_consultation: Decimal,
        taux_taxe: Decimal = Decimal("0"),
        montant_remise: Decimal = Decimal("0"),
        notes: Optional[str] = None,
    ) -> BillingRecord:
        existing = await self._repo.get_by_appointment(id_rendez_vous)
        if existing and existing.statut != BillingStatus.CANCELLED:
            return existing

        sous_total = honoraires_consultation
        montant_taxe = (sous_total * taux_taxe / Decimal("100")).quantize(Decimal("0.01"))
        total = BillingRecord.calculate_total(sous_total, montant_remise, montant_taxe)
        reference = _generate_reference()
        date_echeance = (datetime.utcnow() + timedelta(days=30)).date()

        return await self._repo.create(
            id_rendez_vous=id_rendez_vous,
            id_patient=id_patient,
            reference=reference,
            sous_total=sous_total,
            montant_remise=montant_remise,
            montant_taxe=montant_taxe,
            total=total,
            items=[
                {
                    "description": "Consultation médicale",
                    "quantite": 1,
                    "prix_unitaire": float(honoraires_consultation),
                    "sous_total": float(sous_total),
                    "taux_taxe": float(taux_taxe),
                }
            ],
            date_echeance=date_echeance,
            notes=notes,
        )


class CreateInvoiceUseCase:
    """Crée ou remplace une facture pour un RDV."""

    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_rendez_vous: int,
        id_patient: int,
        items: list[dict],
        montant_remise: Decimal = Decimal("0"),
        notes: Optional[str] = None,
    ) -> BillingRecord:
        existing = await self._repo.get_by_appointment(id_rendez_vous)
        if existing and existing.statut not in (BillingStatus.CANCELLED, BillingStatus.DRAFT):
            raise InvoiceAlreadyExistsError(id_rendez_vous)

        sous_total = Decimal("0")
        montant_taxe = Decimal("0")
        for element in items:
            qte = Decimal(str(element.get("quantite", 1)))
            prix_unitaire = Decimal(str(element["prix_unitaire"]))
            taux_taxe = Decimal(str(element.get("taux_taxe", 0)))
            sous_total_element = (qte * prix_unitaire).quantize(Decimal("0.01"))
            element["sous_total"] = float(sous_total_element)
            sous_total += sous_total_element
            montant_taxe += (sous_total_element * taux_taxe / Decimal("100")).quantize(Decimal("0.01"))

        total = BillingRecord.calculate_total(sous_total, montant_remise, montant_taxe)
        reference = _generate_reference()
        date_echeance = (datetime.utcnow() + timedelta(days=30)).date()

        return await self._repo.create(
            id_rendez_vous=id_rendez_vous,
            id_patient=id_patient,
            reference=reference,
            sous_total=sous_total,
            montant_remise=montant_remise,
            montant_taxe=montant_taxe,
            total=total,
            items=items,
            date_echeance=date_echeance,
            notes=notes,
        )


class GetBillingUseCase:
    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo

    async def execute(self, id_facture: int) -> BillingRecord:
        record = await self._repo.get_by_id(id_facture)
        if record is None:
            raise BillingNotFoundError(id_facture)
        return record


class GenerateInvoicePDFUseCase:
    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo
        self._generator = InvoiceGenerator()

    async def execute(self, id_facture: int, patient_name: str = "Patient") -> bytes:
        record = await self._repo.get_by_id(id_facture)
        if record is None:
            raise BillingNotFoundError(id_facture)

        items_data = [
            {
                "description": item.description,
                "quantite": item.quantite,
                "prix_unitaire": float(item.prix_unitaire),
                "taux_taxe": float(item.taux_taxe),
                "sous_total": float(item.sous_total),
            }
            for item in record.items
        ]

        billing_data = {
            "reference": record.reference,
            "patient_name": patient_name,
            "issued_date": record.created_at.strftime("%d/%m/%Y"),
            "date_echeance": record.date_echeance.strftime("%d/%m/%Y") if record.date_echeance else None,
            "statut": record.statut.valeur,
            "items": items_data,
            "sous_total": float(record.sous_total),
            "montant_remise": float(record.montant_remise),
            "montant_taxe": float(record.montant_taxe),
            "total": float(record.total),
            "notes": record.notes,
        }
        return self._generator.generate(billing_data)


class ListMyInvoicesUseCase:
    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo

    async def execute(self, id_patient: int, params: PaginationParams) -> Page:
        records, total = await self._repo.list_by_patient(id_patient, params)
        return Page.create(records, total, params)


class AdminListBillingUseCase:
    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo

    async def execute(self, params: PaginationParams) -> Page:
        records, total = await self._repo.list_all(params)
        return Page.create(records, total, params)


class AdminUpdateBillingStatusUseCase:
    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo

    async def execute(self, id_facture: int, new_status: str) -> BillingRecord:
        record = await self._repo.get_by_id(id_facture)
        if record is None:
            raise BillingNotFoundError(id_facture)

        transitions_valides: dict[BillingStatus, list[str]] = {
            BillingStatus.DRAFT: ["issued", "cancelled"],
            BillingStatus.ISSUED: ["paid", "cancelled"],
            BillingStatus.PAID: [],
            BillingStatus.CANCELLED: [],
        }
        autorise = transitions_valides.get(record.statut, [])
        if new_status not in autorise:
            raise InvalidStatusTransitionError(record.statut.valeur, new_status)

        paye_le = datetime.utcnow() if new_status == "paid" else None
        mis_a_jour = await self._repo.update_status(id_facture, new_status, paye_le)
        if mis_a_jour is None:
            raise BillingNotFoundError(id_facture)
        return mis_a_jour


class AdminBillingStatsUseCase:
    def __init__(self, repo: BillingRepository) -> None:
        self._repo = repo

    async def execute(self) -> dict:
        return await self._repo.get_stats()
