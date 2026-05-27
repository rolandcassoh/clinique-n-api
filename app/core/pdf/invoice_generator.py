"""Génération de factures PDF via WeasyPrint (ou fallback HTML)."""
from __future__ import annotations

from jinja2 import Template


_INVOICE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Facture {{ reference }}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; color: #333; }
    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    .header-info { margin-bottom: 20px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th { background: #3498db; color: white; padding: 10px; text-align: left; }
    td { padding: 8px 10px; border-bottom: 1px solid #eee; }
    tr:nth-child(even) { background: #f9f9f9; }
    .total { font-weight: bold; font-size: 1.2em; text-align: right; margin-top: 15px; }
    .status { display: inline-block; padding: 3px 10px; border-radius: 12px;
              background: #27ae60; color: white; font-size: 0.9em; }
    .footer { margin-top: 40px; font-size: 0.85em; color: #888; border-top: 1px solid #eee; padding-top: 10px; }
  </style>
</head>
<body>
  <h1>FACTURE {{ reference }}</h1>
  <div class="header-info">
    <p><strong>Patient :</strong> {{ patient_name }}</p>
    <p><strong>Date d'émission :</strong> {{ issued_date }}</p>
    {% if due_date %}<p><strong>Échéance :</strong> {{ due_date }}</p>{% endif %}
    <p><strong>Statut :</strong> <span class="status">{{ status }}</span></p>
  </div>

  <table>
    <thead>
      <tr>
        <th>Description</th>
        <th>Qté</th>
        <th>Prix unitaire</th>
        <th>Taxe (%)</th>
        <th>Sous-total</th>
      </tr>
    </thead>
    <tbody>
      {% for item in items %}
      <tr>
        <td>{{ item.description }}</td>
        <td>{{ item.quantity }}</td>
        <td>{{ item.unit_price }} XAF</td>
        <td>{{ item.tax_rate }}%</td>
        <td>{{ item.subtotal }} XAF</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div style="text-align: right; margin-top: 15px;">
    <p>Sous-total : {{ subtotal }} XAF</p>
    {% if discount_amount %}<p>Remise : -{{ discount_amount }} XAF</p>{% endif %}
    {% if tax_amount %}<p>Taxes : {{ tax_amount }} XAF</p>{% endif %}
    <p class="total">TOTAL : {{ total }} XAF</p>
  </div>

  {% if notes %}<div style="margin-top:20px;"><p><strong>Notes :</strong> {{ notes }}</p></div>{% endif %}

  <div class="footer">
    <p>Ce document est généré automatiquement par le système de gestion clinique.</p>
  </div>
</body>
</html>"""


class InvoiceGenerator:
    """Génère une facture PDF depuis un template HTML Jinja2."""

    def generate(self, billing_data: dict) -> bytes:
        """Retourne les bytes du PDF (ou HTML encodé si WeasyPrint non disponible)."""
        html = self._render_template(billing_data)
        try:
            from weasyprint import HTML  # type: ignore[import-not-found]
            return HTML(string=html).write_pdf()
        except ImportError:
            # Fallback dev : retourner HTML encodé
            return html.encode("utf-8")

    def _render_template(self, data: dict) -> str:
        return Template(_INVOICE_TEMPLATE).render(**data)
