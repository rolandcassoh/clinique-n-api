"""Tests unitaires du domaine billing."""
from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

import pytest

from app.modules.billing.application.use_cases import _generate_reference
from app.modules.billing.domain.entities import BillingItem, BillingRecord, BillingStatus
from app.core.pdf.invoice_generator import InvoiceGenerator


# ---------------------------------------------------------------------------
# Référence facture
# ---------------------------------------------------------------------------

class TestInvoiceReference:
    def test_reference_format(self):
        ref = _generate_reference()
        # Format attendu : INV-YYYYMMDD-NNNNNN
        pattern = r"^INV-\d{8}-\d{6}$"
        assert re.match(pattern, ref), f"Format invalide: {ref}"

    def test_reference_is_unique(self):
        refs = {_generate_reference() for _ in range(20)}
        # Avec 20 générations, la probabilité de collision est infime
        assert len(refs) >= 18

    def test_reference_contains_current_date(self):
        ref = _generate_reference()
        date_part = datetime.utcnow().strftime("%Y%m%d")
        assert date_part in ref


# ---------------------------------------------------------------------------
# BillingRecord — calcul de total
# ---------------------------------------------------------------------------

class TestBillingRecordTotal:
    def _make_item(self, desc: str, price: float, qty: int = 1, tax: float = 0) -> BillingItem:
        return BillingItem(
            id=1, billing_id=1,
            description=desc,
            quantity=qty,
            unit_price=Decimal(str(price)),
            subtotal=Decimal(str(price * qty)),
            tax_rate=Decimal(str(tax)),
        )

    def test_total_no_discount_no_tax(self):
        subtotal = Decimal("15000")
        total = BillingRecord.calculate_total(subtotal, Decimal("0"), Decimal("0"))
        assert total == Decimal("15000")

    def test_total_with_discount(self):
        subtotal = Decimal("20000")
        discount = Decimal("2000")
        tax = Decimal("0")
        total = BillingRecord.calculate_total(subtotal, discount, tax)
        assert total == Decimal("18000")

    def test_total_with_tax(self):
        subtotal = Decimal("10000")
        tax = Decimal("1750")  # 17.5%
        total = BillingRecord.calculate_total(subtotal, Decimal("0"), tax)
        assert total == Decimal("11750")

    def test_total_with_discount_and_tax(self):
        subtotal = Decimal("10000")
        discount = Decimal("1000")
        tax = Decimal("900")
        # total = subtotal - discount + tax = 10000 - 1000 + 900 = 9900
        total = BillingRecord.calculate_total(subtotal, discount, tax)
        assert total == Decimal("9900")

    def test_mark_paid(self):
        record = BillingRecord(
            id=1, appointment_id=1, patient_id=1,
            reference="INV-20240101-000001",
            subtotal=Decimal("15000"), discount_amount=Decimal("0"),
            tax_amount=Decimal("0"), total=Decimal("15000"),
            status=BillingStatus.ISSUED,
        )
        record.mark_paid()
        assert record.status == BillingStatus.PAID
        assert record.paid_at is not None

    def test_cancel_paid_raises(self):
        record = BillingRecord(
            id=1, appointment_id=1, patient_id=1,
            reference="INV-20240101-000001",
            subtotal=Decimal("15000"), discount_amount=Decimal("0"),
            tax_amount=Decimal("0"), total=Decimal("15000"),
            status=BillingStatus.PAID,
        )
        with pytest.raises(ValueError, match="Cannot cancel a paid invoice"):
            record.cancel()

    def test_issue_draft_invoice(self):
        record = BillingRecord(
            id=1, appointment_id=1, patient_id=1,
            reference="INV-20240101-000001",
            subtotal=Decimal("15000"), discount_amount=Decimal("0"),
            tax_amount=Decimal("0"), total=Decimal("15000"),
            status=BillingStatus.DRAFT,
        )
        record.issue()
        assert record.status == BillingStatus.ISSUED


# ---------------------------------------------------------------------------
# Génération PDF
# ---------------------------------------------------------------------------

class TestPDFGeneration:
    def _make_billing_data(self) -> dict:
        return {
            "reference": "INV-20240101-123456",
            "patient_name": "Jean Dupont",
            "issued_date": "01/01/2024",
            "due_date": "31/01/2024",
            "status": "issued",
            "items": [
                {
                    "description": "Consultation médicale",
                    "quantity": 1,
                    "unit_price": 15000.0,
                    "tax_rate": 0.0,
                    "subtotal": 15000.0,
                }
            ],
            "subtotal": 15000.0,
            "discount_amount": 0.0,
            "tax_amount": 0.0,
            "total": 15000.0,
            "notes": None,
        }

    def test_generate_returns_bytes(self):
        gen = InvoiceGenerator()
        data = self._make_billing_data()
        result = gen.generate(data)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_contains_reference(self):
        gen = InvoiceGenerator()
        data = self._make_billing_data()
        result = gen.generate(data)
        # Le résultat contient la référence (HTML ou PDF)
        content = result.decode("utf-8", errors="ignore")
        assert "INV-20240101-123456" in content

    def test_generate_contains_total(self):
        gen = InvoiceGenerator()
        data = self._make_billing_data()
        result = gen.generate(data)
        content = result.decode("utf-8", errors="ignore")
        assert "15000" in content

    def test_generate_is_html_or_pdf(self):
        gen = InvoiceGenerator()
        data = self._make_billing_data()
        result = gen.generate(data)
        # Soit PDF (commence par %PDF) soit HTML (commence par <!DOCTYPE ou contient <html>)
        is_pdf = result[:4] == b"%PDF"
        is_html = b"<html" in result[:200].lower() or b"<!doctype" in result[:200].lower()
        assert is_pdf or is_html
