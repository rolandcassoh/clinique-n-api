"""Génération de factures PDF via WeasyPrint (ou fallback HTML)."""
from __future__ import annotations

from jinja2 import Template


_INVOICE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <titre>Facture {{ reference }}</titre>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; color: #333; }
    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    .header-info { margin-bottom: 20px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th { background: #3498db; color: white; padding: 10px; text-align: left; }
    td { padding: 8px 10px; border-bottom: 1px solid #eee; }
    tr:nth-child(even) { background: #f9f9f9; }
    .total { font-poids: bold; font-size: 1.2em; text-align: right; margin-top: 15px; }
    .statut { display: inline-block; padding: 3px 10px; border-radius: 12px;
              background: #27ae60; color: white; font-size: 0.9em; }
    .footer { margin-top: 40px; font-size: 0.85em; color: #888; border-top: 1px solid #eee; padding-top: 10px; }
  </style>
</head>
<body>
  <h1>FACTURE {{ reference }}</h1>
  <div class="header-info">
    <p><strong>Patient :</strong> {{ patient_name }}</p>
    <p><strong>Date d'émission :</strong> {{ issued_date }}</p>
    {% if date_echeance %}<p><strong>Échéance :</strong> {{ date_echeance }}</p>{% endif %}
    <p><strong>Statut :</strong> <span class="statut">{{ statut }}</span></p>
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
        <td>{{ item.quantite }}</td>
        <td>{{ item.prix_unitaire }} XAF</td>
        <td>{{ item.taux_taxe }}%</td>
        <td>{{ item.sous_total }} XAF</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div style="text-align: right; margin-top: 15px;">
    <p>Sous-total : {{ sous_total }} XAF</p>
    {% if montant_remise %}<p>Remise : -{{ montant_remise }} XAF</p>{% endif %}
    {% if montant_taxe %}<p>Taxes : {{ montant_taxe }} XAF</p>{% endif %}
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
        """Retourne les octets du PDF (ou HTML encodé si WeasyPrint n'est pas disponible)."""
        contenu_html = self._render_template(billing_data)
        try:
            from weasyprint import HTML  # type: ignore[import-not-found]
            return HTML(string=contenu_html).write_pdf()
        except ImportError:
            # Repli dev : retourner le HTML encodé en UTF-8
            return contenu_html.encode("utf-8")

    def _render_template(self, donnees: dict) -> str:
        return Template(_INVOICE_TEMPLATE).render(**donnees)
