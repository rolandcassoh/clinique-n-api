"""Tests unitaires du domaine wallet."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.modules.wallet.domain.entities import PatientWallet, TransactionType
from app.modules.wallet.domain.exceptions import InsufficientFundsError


class TestPatientWallet:
    def _make_wallet(self, balance: float = 10000.0) -> PatientWallet:
        return PatientWallet(id=1, user_id=42, balance=Decimal(str(balance)), currency="XAF")

    # ---------------------------------------------------------------------------
    # Credit
    # ---------------------------------------------------------------------------

    def test_credit_increases_balance(self):
        wallet = self._make_wallet(5000)
        tx = wallet.credit(Decimal("3000"), "Rechargement")
        assert wallet.balance == Decimal("8000")

    def test_credit_returns_transaction(self):
        wallet = self._make_wallet(5000)
        tx = wallet.credit(Decimal("2000"), "Test")
        assert tx.type == TransactionType.CREDIT.value
        assert tx.amount == Decimal("2000")
        assert tx.balance_after == Decimal("7000")

    def test_credit_zero_raises(self):
        wallet = self._make_wallet(5000)
        with pytest.raises(ValueError, match="positive"):
            wallet.credit(Decimal("0"))

    def test_credit_negative_raises(self):
        wallet = self._make_wallet(5000)
        with pytest.raises(ValueError, match="positive"):
            wallet.credit(Decimal("-100"))

    def test_credit_with_reference(self):
        wallet = self._make_wallet(0)
        tx = wallet.credit(Decimal("5000"), reference="REF-001")
        assert tx.reference == "REF-001"

    # ---------------------------------------------------------------------------
    # Debit
    # ---------------------------------------------------------------------------

    def test_debit_decreases_balance(self):
        wallet = self._make_wallet(10000)
        tx = wallet.debit(Decimal("3000"), "Paiement RDV")
        assert wallet.balance == Decimal("7000")

    def test_debit_returns_transaction(self):
        wallet = self._make_wallet(10000)
        tx = wallet.debit(Decimal("4000"))
        assert tx.type == TransactionType.DEBIT.value
        assert tx.amount == Decimal("4000")
        assert tx.balance_after == Decimal("6000")

    def test_debit_exact_balance(self):
        """Débit exact du solde disponible — doit réussir."""
        wallet = self._make_wallet(5000)
        tx = wallet.debit(Decimal("5000"))
        assert wallet.balance == Decimal("0")

    def test_debit_insufficient_raises(self):
        wallet = self._make_wallet(1000)
        with pytest.raises(InsufficientFundsError):
            wallet.debit(Decimal("1500"))

    def test_debit_insufficient_error_message(self):
        wallet = self._make_wallet(500)
        with pytest.raises(InsufficientFundsError) as exc_info:
            wallet.debit(Decimal("1000"))
        assert "500" in str(exc_info.value.message)
        assert "1000" in str(exc_info.value.message)

    def test_balance_cannot_go_negative(self):
        """Après InsufficientFundsError, la balance ne doit pas changer."""
        wallet = self._make_wallet(200)
        try:
            wallet.debit(Decimal("300"))
        except InsufficientFundsError:
            pass
        assert wallet.balance == Decimal("200")

    def test_debit_zero_raises(self):
        wallet = self._make_wallet(5000)
        with pytest.raises(ValueError, match="positive"):
            wallet.debit(Decimal("0"))

    # ---------------------------------------------------------------------------
    # Scénarios combinés
    # ---------------------------------------------------------------------------

    def test_credit_then_debit(self):
        wallet = self._make_wallet(0)
        wallet.credit(Decimal("10000"))
        wallet.debit(Decimal("3000"))
        assert wallet.balance == Decimal("7000")

    def test_multiple_debits(self):
        wallet = self._make_wallet(15000)
        wallet.debit(Decimal("5000"))
        wallet.debit(Decimal("3000"))
        wallet.debit(Decimal("7000"))
        assert wallet.balance == Decimal("0")

    def test_debit_after_reaching_zero_raises(self):
        wallet = self._make_wallet(5000)
        wallet.debit(Decimal("5000"))
        with pytest.raises(InsufficientFundsError):
            wallet.debit(Decimal("1"))
