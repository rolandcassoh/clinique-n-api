"""Cas d'utilisation — module rendez-vous."""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from app.modules.rendez_vous.domain.entites import (
    Appointment,
    AppointmentStatus,
    AppointmentTransaction,
    AppointmentType,
    PaymentStatus,
)
from app.modules.rendez_vous.domain.exceptions import (
    AppointmentNotFoundError,
    AppointmentPermissionError,
    InvalidPaymentGatewayError,
    PaymentAlreadyProcessedError,
    SlotNotAvailableError,
)
from app.modules.rendez_vous.domain.depots import (
    AppointmentRepository,
    AppointmentTransactionRepository,
)
from app.modules.rendez_vous.domain.services import (
    CancellationPolicyService,
    CancellationResult,
    SlotAvailabilityService,
)
from app.shared.schemas.pagination import PaginationParams


# ---------------------------------------------------------------------------
# Commandes (objets de transfert de données)
# ---------------------------------------------------------------------------


@dataclass
class BookAppointmentCommand:
    id_clinique: int
    id_medecin: int
    id_patient: int
    programme_le: datetime
    type: AppointmentType = AppointmentType.IN_PERSON
    passerelle_paiement: Optional[str] = None
    notes: Optional[str] = None
    est_suivi: bool = False
    id_rdv_parent: Optional[int] = None
    # Métadonnées médecin injectées depuis l'extérieur (pas de dépôt doctor dans ce module)
    honoraires_consultation: Decimal = Decimal("0")
    session_duration: int = 30


# ---------------------------------------------------------------------------
# Prise de rendez-vous
# ---------------------------------------------------------------------------


class BookAppointmentUseCase:
    def __init__(
        self,
        repo: AppointmentRepository,
        slot_service: SlotAvailabilityService,
        redis: Any,
    ) -> None:
        self._repo = repo
        self._slot_service = slot_service
        self._redis = redis

    async def execute(self, cmd: BookAppointmentCommand) -> Appointment:
        # 1. Récupérer les créneaux déjà réservés (cache Redis ou DB)
        cle_cache = f"slots:{cmd.id_medecin}:{cmd.programme_le.date()}"
        creneaux_reserves = await self._get_booked_slots(cmd.id_medecin, cmd.programme_le, cle_cache)

        # 2. Vérifier la disponibilité du créneau
        if not self._slot_service.is_slot_available(cmd.programme_le, creneaux_reserves):
            raise SlotNotAvailableError(cmd.programme_le)

        # 3. Générer une référence unique
        reference = f"APT-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(100000, 999999)}"

        # 4. Créer le rendez-vous
        rendez_vous = Appointment(
            id=0,
            reference=reference,
            id_clinique=cmd.id_clinique,
            id_medecin=cmd.id_medecin,
            id_patient=cmd.id_patient,
            programme_le=cmd.programme_le,
            duree_minutes=cmd.session_duration,
            statut=AppointmentStatus.PENDING,
            type=cmd.type,
            montant=cmd.honoraires_consultation,
            montant_avance=Decimal("0"),
            statut_paiement=PaymentStatus.PENDING,
            passerelle_paiement=cmd.passerelle_paiement,
            notes=cmd.notes,
            est_suivi=cmd.est_suivi,
            id_rdv_parent=cmd.id_rdv_parent,
        )
        sauvegarde = await self._repo.save(rendez_vous)

        # 5. Invalider le cache Redis pour ce créneau
        await self._redis.delete(cle_cache)

        return sauvegarde

    async def _get_booked_slots(
        self, id_medecin: int, programme_le: datetime, cle_cache: str
    ) -> list[datetime]:
        """Récupère les créneaux occupés depuis la base (cache Redis désactivé en test)."""
        try:
            import json

            en_cache = await self._redis.get(cle_cache)
            if en_cache:
                brut: list[str] = json.loads(en_cache)
                return [datetime.fromisoformat(s) for s in brut]
        except Exception:
            pass

        reserves = await self._repo.get_booked_slots(id_medecin, programme_le.date())
        return reserves


# ---------------------------------------------------------------------------
# Annulation de rendez-vous
# ---------------------------------------------------------------------------


class CancelAppointmentUseCase:
    def __init__(
        self,
        repo: AppointmentRepository,
        redis: Any,
    ) -> None:
        self._repo = repo
        self._redis = redis
        self._policy = CancellationPolicyService()

    async def execute(
        self, id_rendez_vous: int, id_utilisateur: int, motif: str, is_admin: bool = False
    ) -> CancellationResult:
        rendez_vous = await self._repo.find_by_id(id_rendez_vous)
        if rendez_vous is None:
            raise AppointmentNotFoundError(id_rendez_vous)

        # Vérifier la propriété (le patient annule son propre RDV) sauf administrateur
        if not is_admin and rendez_vous.id_patient != id_utilisateur:
            raise AppointmentPermissionError(
                "Vous ne pouvez pas annuler le rendez-vous d'un autre patient."
            )

        maintenant = datetime.utcnow()
        resultat = self._policy.evaluate(rendez_vous, maintenant)

        rendez_vous.cancel(motif)
        await self._repo.save(rendez_vous)

        # Invalider le cache des créneaux
        await self._redis.delete(
            f"slots:{rendez_vous.id_medecin}:{rendez_vous.programme_le.date()}"
        )

        return resultat


# ---------------------------------------------------------------------------
# Confirmation de rendez-vous
# ---------------------------------------------------------------------------


class ConfirmAppointmentUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(self, id_rendez_vous: int, id_medecin: int) -> Appointment:
        rendez_vous = await self._repo.find_by_id(id_rendez_vous)
        if rendez_vous is None:
            raise AppointmentNotFoundError(id_rendez_vous)
        if rendez_vous.id_medecin != id_medecin:
            raise AppointmentPermissionError(
                "Ce rendez-vous n'appartient pas à ce médecin."
            )
        rendez_vous.confirm()
        return await self._repo.save(rendez_vous)


# ---------------------------------------------------------------------------
# Clôture de rendez-vous
# ---------------------------------------------------------------------------


class CompleteAppointmentUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(self, id_rendez_vous: int, id_medecin: int) -> Appointment:
        rendez_vous = await self._repo.find_by_id(id_rendez_vous)
        if rendez_vous is None:
            raise AppointmentNotFoundError(id_rendez_vous)
        if rendez_vous.id_medecin != id_medecin:
            raise AppointmentPermissionError(
                "Ce rendez-vous n'appartient pas à ce médecin."
            )
        rendez_vous.complete()
        return await self._repo.save(rendez_vous)


# ---------------------------------------------------------------------------
# Marquage absence patient
# ---------------------------------------------------------------------------


class MarkNoShowUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(self, id_rendez_vous: int, id_medecin: int) -> Appointment:
        rendez_vous = await self._repo.find_by_id(id_rendez_vous)
        if rendez_vous is None:
            raise AppointmentNotFoundError(id_rendez_vous)
        if rendez_vous.id_medecin != id_medecin:
            raise AppointmentPermissionError(
                "Ce rendez-vous n'appartient pas à ce médecin."
            )
        rendez_vous.mark_no_show()
        return await self._repo.save(rendez_vous)


# ---------------------------------------------------------------------------
# Paiement d'un rendez-vous
# ---------------------------------------------------------------------------


class PayAppointmentUseCase:
    def __init__(
        self,
        repo: AppointmentRepository,
        tx_repo: AppointmentTransactionRepository,
        payment_adapter: Any,
    ) -> None:
        self._repo = repo
        self._tx_repo = tx_repo
        self._payment = payment_adapter

    async def execute(
        self,
        id_rendez_vous: int,
        id_patient: int,
        passerelle: str,
        devise: str = "XAF",
    ) -> dict:
        rendez_vous = await self._repo.find_by_id(id_rendez_vous)
        if rendez_vous is None:
            raise AppointmentNotFoundError(id_rendez_vous)
        if rendez_vous.id_patient != id_patient:
            raise AppointmentPermissionError()
        if rendez_vous.statut_paiement == PaymentStatus.PAID:
            raise PaymentAlreadyProcessedError(id_rendez_vous)

        # Paiement par portefeuille : traitement direct
        if passerelle == "wallet":
            rendez_vous.statut_paiement = PaymentStatus.PAID
            rendez_vous.passerelle_paiement = "wallet"
            await self._repo.save(rendez_vous)
            await self._tx_repo.create(
                id_rendez_vous=id_rendez_vous,
                montant=rendez_vous.montant,
                devise=devise,
                passerelle="wallet",
                reference_transaction=f"WALLET-{id_rendez_vous}",
                statut="succeeded",
            )
            return {"statut": "paid", "passerelle": "wallet"}

        # Paiement via passerelle externe
        intention = await self._payment.create_payment_intent(
            montant=rendez_vous.montant,
            devise=devise,
            metadata={"id_rendez_vous": str(id_rendez_vous), "reference": rendez_vous.reference},
        )
        rendez_vous.passerelle_paiement = passerelle
        await self._repo.save(rendez_vous)

        return {
            "client_secret": intention.client_secret,
            "payment_intent_id": intention.id,
            "passerelle": passerelle,
        }


# ---------------------------------------------------------------------------
# Création d'intention de paiement Stripe
# ---------------------------------------------------------------------------


class CreateStripeIntentUseCase:
    def __init__(
        self,
        repo: AppointmentRepository,
        stripe_adapter: Any,
    ) -> None:
        self._repo = repo
        self._stripe = stripe_adapter

    async def execute(
        self,
        id_rendez_vous: int,
        id_patient: int,
        devise: str = "XAF",
    ) -> dict:
        rendez_vous = await self._repo.find_by_id(id_rendez_vous)
        if rendez_vous is None:
            raise AppointmentNotFoundError(id_rendez_vous)
        if rendez_vous.id_patient != id_patient:
            raise AppointmentPermissionError()

        intention = await self._stripe.create_payment_intent(
            montant=rendez_vous.montant,
            devise=devise,
            metadata={
                "id_rendez_vous": str(id_rendez_vous),
                "reference": rendez_vous.reference,
            },
        )
        return {
            "client_secret": intention.client_secret,
            "payment_intent_id": intention.id,
        }


# ---------------------------------------------------------------------------
# Création d'une commande Razorpay
# ---------------------------------------------------------------------------


class CreateRazorpayOrderUseCase:
    def __init__(
        self,
        repo: AppointmentRepository,
        razorpay_adapter: Any,
    ) -> None:
        self._repo = repo
        self._razorpay = razorpay_adapter

    async def execute(
        self,
        id_rendez_vous: int,
        id_patient: int,
        devise: str = "INR",
    ) -> dict:
        rendez_vous = await self._repo.find_by_id(id_rendez_vous)
        if rendez_vous is None:
            raise AppointmentNotFoundError(id_rendez_vous)
        if rendez_vous.id_patient != id_patient:
            raise AppointmentPermissionError()

        commande = await self._razorpay.create_payment_intent(
            montant=rendez_vous.montant,
            devise=devise,
            metadata={"id_rendez_vous": str(id_rendez_vous)},
        )
        return {
            "id_commande": commande.id,
            "montant": str(rendez_vous.montant),
            "devise": devise,
        }


# ---------------------------------------------------------------------------
# Remboursement d'un rendez-vous
# ---------------------------------------------------------------------------


class RefundAppointmentUseCase:
    def __init__(
        self,
        repo: AppointmentRepository,
        tx_repo: AppointmentTransactionRepository,
        payment_adapter: Any,
    ) -> None:
        self._repo = repo
        self._tx_repo = tx_repo
        self._payment = payment_adapter

    async def execute(
        self,
        id_rendez_vous: int,
        montant: Optional[Decimal] = None,
    ) -> dict:
        rendez_vous = await self._repo.find_by_id(id_rendez_vous)
        if rendez_vous is None:
            raise AppointmentNotFoundError(id_rendez_vous)

        montant_remboursement = montant or rendez_vous.montant
        ref_paiement = rendez_vous.reference_paiement or f"ref_{id_rendez_vous}"

        resultat_remboursement = await self._payment.refund(
            payment_intent_id=ref_paiement, montant=montant_remboursement
        )
        rendez_vous.statut_paiement = PaymentStatus.REFUNDED
        await self._repo.save(rendez_vous)

        await self._tx_repo.create(
            id_rendez_vous=id_rendez_vous,
            montant=montant_remboursement,
            devise="XAF",
            passerelle=rendez_vous.passerelle_paiement or "unknown",
            reference_transaction=resultat_remboursement.id,
            statut="refunded",
        )
        return {"refund_id": resultat_remboursement.id, "montant": str(montant_remboursement), "statut": resultat_remboursement.statut}


# ---------------------------------------------------------------------------
# Statut de paiement d'un rendez-vous
# ---------------------------------------------------------------------------


class GetPaymentStatusUseCase:
    def __init__(
        self,
        repo: AppointmentRepository,
        tx_repo: AppointmentTransactionRepository,
    ) -> None:
        self._repo = repo
        self._tx_repo = tx_repo

    async def execute(self, id_rendez_vous: int, id_utilisateur: int) -> dict:
        rendez_vous = await self._repo.find_by_id(id_rendez_vous)
        if rendez_vous is None:
            raise AppointmentNotFoundError(id_rendez_vous)
        if rendez_vous.id_patient != id_utilisateur:
            raise AppointmentPermissionError()

        transactions = await self._tx_repo.list_for_appointment(id_rendez_vous)
        return {
            "id_rendez_vous": id_rendez_vous,
            "statut_paiement": rendez_vous.statut_paiement,
            "passerelle_paiement": rendez_vous.passerelle_paiement,
            "montant": str(rendez_vous.montant),
            "transactions": [
                {
                    "ref": tx.reference_transaction,
                    "montant": str(tx.montant),
                    "statut": tx.statut,
                    "passerelle": tx.passerelle,
                }
                for tx in transactions
            ],
        }


# ---------------------------------------------------------------------------
# Forçage de statut (admin)
# ---------------------------------------------------------------------------


class ForceStatusUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(self, id_rendez_vous: int, new_status: str) -> Appointment:
        rendez_vous = await self._repo.find_by_id(id_rendez_vous)
        if rendez_vous is None:
            raise AppointmentNotFoundError(id_rendez_vous)
        rendez_vous.statut = AppointmentStatus(new_status)
        return await self._repo.save(rendez_vous)


# ---------------------------------------------------------------------------
# Statistiques des rendez-vous (admin)
# ---------------------------------------------------------------------------


class GetStatsUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_clinique: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> dict:
        par_statut = await self._repo.count_by_status(id_clinique=id_clinique)
        chiffre_affaires = await self._repo.sum_revenue(
            id_clinique=id_clinique, date_from=date_from, date_to=date_to
        )
        return {
            "by_status": par_statut,
            "total_revenue": str(chiffre_affaires),
        }
