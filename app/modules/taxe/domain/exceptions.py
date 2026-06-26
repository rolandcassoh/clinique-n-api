from app.shared.exceptions.domain import DomainException


class TaxNotFoundError(DomainException):
    def __init__(self, id_taxe: int) -> None:
        super().__init__(f"Taxe avec l'identifiant '{id_taxe}' introuvable.")
        self.id_taxe = id_taxe


class NoDefaultTaxError(DomainException):
    def __init__(self) -> None:
        super().__init__("Aucune taxe par défaut configurée.")
